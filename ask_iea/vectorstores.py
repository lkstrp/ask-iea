"""DOCSTRING."""
import uuid

import langchain.vectorstores
import pandas as pd
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .utils.logger import Logger

# Define a logger
log = Logger(__name__)


class VectorStore(langchain.vectorstores.FAISS):

    """DOCSTRING."""

    def __init__(self, db_path:str=None, index_df:pd.DataFrame=None):
        """DOCSTRING."""
        if index_df is None and db_path is None:
            msg = 'Either index_df or db_path must be given.'
            raise ValueError(msg)

        if db_path is not None:
            new_instance = langchain.vectorstores.FAISS.load_local(db_path, OpenAIEmbeddings())
            log.info(f'Loaded {len(new_instance.docstore._dict)} docs from "{db_path}".')
            self.__dict__.update(new_instance.__dict__)
        elif index_df is not None:
            log.info('Creating new vectorstore.')
            docs, ids = self._load_index(index_df)
            new_instance = langchain.vectorstores.FAISS.from_documents(docs, OpenAIEmbeddings(), ids=ids)
            self.__dict__.update(new_instance.__dict__)

    def _load_index(self, index_df: pd.DataFrame) -> (list, list):
        # Only load reports that have a PDF file
        needs_load = index_df[index_df['url_pdf'].notna()]

        try:
            db_sources = [doc.metadata['source'] for doc in self.docstore._dict.values()]
            needs_load = needs_load[~needs_load['url_pdf'].isin(db_sources)]
        except AttributeError:
            pass

        log.info(f'Start adding {len(needs_load)} new reports from {len(index_df)} passed reports.')

        documents = []
        for report_id, row in needs_load.iterrows():
            loader = PyPDFLoader(row.url_pdf)
            doc_pages = loader.load()
            for page in doc_pages:
                page.metadata['url_report'] = row.url_report
                page.metadata['report_id'] = report_id
                page.metadata['title'] = row.title
                page.metadata['abstract'] = row.abstract
                page.metadata['date_published'] = row.date_published
            documents.extend(doc_pages)

        log.debug(f'\tLoaded {len(documents)} pages from {len(needs_load)} reports.')

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        docs = text_splitter.split_documents(documents)

        log.debug(f'\tCreated {len(docs)} docs from {len(documents)} pages.')

        # Create a list of unique ids for each document based on the content
        ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.page_content)) for doc in docs]
        unique_ids = list(set(ids))

        # Ensure that only docs that correspond to unique ids are kept and that only one of the duplicate ids is kept
        seen_ids = set()
        unique_docs = [
            doc for doc, doc_id in zip(docs, ids) if doc_id not in seen_ids and (seen_ids.add(doc_id) or True)
        ]

        # Drop all documents that are already in the vectorstore (from unique_docs and unique_ids)
        try:
            for idx, doc_id in enumerate(unique_ids):
                if doc_id in self.docstore._dict:
                    unique_docs.pop(idx)
                    unique_ids.pop(idx)
        except AttributeError:
            pass

        if len(unique_docs) == 0:
            log.debug('No new documents to add to the database.')

        log.info(f'Added {len(unique_docs)} new unique docs from {len(needs_load)} reports.')

        return unique_docs, unique_ids

    def add_new_reports(self, index_df: pd.DataFrame) -> None:
        """DOCSTRING."""
        docs, ids = self._load_index(index_df)
        if len(docs) > 0:
            self.add_documents(docs, ids=ids)
