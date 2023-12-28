"""TODO DOCSTRING."""
import time
import uuid
from pathlib import Path

import langchain.vectorstores
import openai
import pandas as pd
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .utils.logger import Logger
from .utils.utils import batch

# Define a logger
log = Logger(__name__)


class VectorStore(langchain.vectorstores.FAISS):

    """TODO DOCSTRING."""

    def __init__(self, db_path: Path = None, index_df: pd.DataFrame = None):
        """TODO DOCSTRING."""
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
        needs_load = index_df[index_df['url_pdf'].notna() & index_df['_keywords'].notna()]
        if needs_load.empty:
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
                page.metadata['_year'] = row._year
                page.metadata['_keywords'] = row._keywords
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
            unique_docs = [doc for idx, doc in enumerate(unique_docs) if unique_ids[idx] not in self.docstore._dict]
            unique_ids = [doc_id for doc_id in unique_ids if doc_id not in self.docstore._dict]
        except AttributeError:
            pass

        if len(unique_docs) == 0:
            log.debug('No new documents to add to the database.')

        log.info(f'Added {len(unique_docs)} new unique docs from {len(needs_load)} reports.')

        return unique_docs, unique_ids

    def add_new_reports(self, index_df: pd.DataFrame) -> None:
        """TODO DOCSTRING."""
        docs, ids = self._load_index(index_df)
        if len(docs) > 0:
            # Loop over documents in batches to handle potential rate limit errors
            for batch_docs, batch_ids in zip(batch(docs, 100), batch(ids, 100)):
                while True:
                    try:
                        self.add_documents(batch_docs, ids=batch_ids)
                        break
                    except openai.RateLimitError:
                        log.warning('Rate limit reached. Waiting 5 seconds before trying again.')
                        time.sleep(5)
