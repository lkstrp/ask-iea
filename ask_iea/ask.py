"""Manages the full pipeline of ask-iea.
"""
from pathlib import Path

from .chains import (
    chain_check_for_scope,
    chain_get_reports_from_question,
    chain_get_reports_from_scope,
    chain_qa,
    chain_retrieve_keywords,
    chain_summarize,
)
from .constants import ASK_IEA_DIR, PATH_FAISS_STORE, PATH_REPORTS_INDEX
from .indexer import ReportIndexer
from .utils.logger import Logger
from .vectorstores import VectorStore

# Define a logger
log = Logger(__name__)

if PATH_REPORTS_INDEX.exists():
    indexer = ReportIndexer(PATH_REPORTS_INDEX)
else:
    indexer = ReportIndexer()
    indexer.add_new_reports(10)
if PATH_FAISS_STORE.exists():
    db = VectorStore(db_path=PATH_FAISS_STORE)
else:
    db = VectorStore(index_df=indexer.df)

df_index = indexer.df[indexer.df['url_pdf'].notna() & indexer.df['_keywords'].notna()]
df_index = df_index.reset_index()


def _add_keywords_to_index(first_n: int = None) -> None:
    global indexer

    if '_keywords' not in indexer.df.columns:
        indexer.df['_keywords'] = None
        indexer.df['_year'] = None

    relevant_rows = indexer.df[indexer.df['url_pdf'].notna()][0:first_n]
    for index, row in relevant_rows[relevant_rows['_keywords'].isna()].iterrows():
        results = chain_retrieve_keywords.invoke(
            {'title': row['title'], 'date_published': row['date_published'], 'abstract': row['abstract']}
        )
        if not results:
            results = {'keywords': [], 'year': None}
        indexer.df.loc[index, '_keywords'] = ','.join([keyword.lower() for keyword in results['keywords']])
        indexer.df.loc[index, '_year'] = results['year']

        indexer.save_to_file(PATH_REPORTS_INDEX)


def update_index(n_newest: int = 150) -> None:
    """Update the index with new reports.

    Args:
    ----
        n_newest (int, optional): Number of newest reports to add. Defaults to 150.

    """
    global indexer

    # Update the index with new reports
    Path(ASK_IEA_DIR).mkdir(parents=True, exist_ok=True)
    indexer.add_new_reports(n_newest=n_newest)
    indexer.save_to_file(PATH_REPORTS_INDEX)

    # Add keywords to the index (using LangChain)
    _add_keywords_to_index(first_n=n_newest)


def update_db(first_n: int = 150) -> None:
    """Update the database with new reports.

    Args:
    ----
        first_n: Number of newest reports to add. Defaults to 150.

    """
    global db

    db.add_new_reports(indexer.df[:first_n])
    db.save_local(PATH_FAISS_STORE)


def update(first_n: int = 50) -> None:
    """Update both the index and the database with new reports.

    Args:
    ----
        first_n: Number of newest reports to add. Defaults to 50.

    """
    update_index(n_newest=first_n)
    update_db(first_n=first_n)


def get_relevant_reports(question: str, num_reports: int) -> list:
    """Get the most relevant reports for a question.

    Args:
    ----
        question: Question to ask.
        num_reports:  Number of reports to return.

    Returns:
    -------
        list: List of report indices.

    """
    scope = chain_check_for_scope.invoke({'question': question})

    if scope.lower() not in ['none']:
        log.debug(f'Scope found: "{scope}"')
        report_indices = chain_get_reports_from_scope.invoke(
            {
                'scope': scope,
                'reports': '\n - '.join(df_index[:num_reports].apply(lambda x: f"{x.name}: {x['title']})", axis=1)),
            }
        )
    else:
        log.debug('No scope in question found. Using all reports.')
        report_indices = chain_get_reports_from_question.invoke(
            {
                'question': question,
                'reports': '\n - '.join(
                    df_index[:num_reports].apply(lambda x: f"{x.name}:{int(x['_year'])}:{x['title']}", axis=1)
                ),
            }
        )

    report_indices = [int(i) for i in report_indices]
    log.debug('Using reports: ' + ', '.join(df_index.loc[report_indices].title))

    return report_indices


def retrieve_docs(question: str, filter_dict: dict, n_docs: int = 5) -> list:
    """Retrieve documents from the database.

    Args:
    ----
        question: Question which is asked.
        filter_dict: Dictionary with filters for the database.
        n_docs: Number of documents to return.

    Returns:
    -------
        list: List of documents.

    """
    global db

    retriever = db.as_retriever(search_kwargs={'k': n_docs, 'filter': filter_dict})
    docs = retriever.invoke(question)
    log.debug(f'Retrieved {len(docs)} documents from DB.')

    return docs


def ask(question: str, num_reports: int = 100) -> str:
    """Ask a question and return the answer. Runs the full pipeline.

    Args:
    ----
        question: Question to ask.
        num_reports: Number of reports which are taken into account.

    Returns:
    -------
        str: Answer to the question.

    """
    global db

    log.debug(f'question: "{question}", num_reports: "{num_reports}"')
    report_indices = get_relevant_reports(question, num_reports=num_reports)
    report_ids = df_index.loc[report_indices, 'report_id'].tolist()

    filter_dict = {'report_id': report_ids}
    docs = retrieve_docs(question, filter_dict)

    relevant_docs = []
    for doc in docs:
        summary = chain_summarize.invoke(
            {
                'text': doc.page_content,
                'report': doc.metadata['title'],
                'question': question,
                'summary_length': 'around 60 words',
            }
        )
        if any(item in summary.lower() for item in ['not applicable', 'not relevant', 'does not provide']):
            continue
        relevant_docs.append(
            {
                'doc': doc,
                'summary': summary,
            }
        )

    def format_for_print(relevant_docs_: list) -> str:
        """Format the docs for printing.

        Args:
        ----
            relevant_docs_ (list): List of relevant documents.

        Returns:
        -------
            str: Formatted string.

        """
        total_string = 'Sources:\n\n'
        for doc_ in relevant_docs_:
            string = (
                f"{doc_['summary']}\n"
                f"Page {doc_['doc'].metadata['page']} | {doc_['doc'].metadata['title']}\n"
                f"Link: {doc_['doc'].metadata['source']}#page={doc_['doc'].metadata['page']}\n\n"
            )
            total_string += string
        return total_string

    if relevant_docs:
        total_sum_out = chain_qa.invoke(
            {
                'context': format_for_print(relevant_docs),
                'answer_length': 'around 100 words',
                'question': question,
            }
        )

        final_answer = f'Answer:\n{total_sum_out}\n\n\n{format_for_print(relevant_docs)}'

    else:
        final_answer = 'Could not find any relevant references.'

    final_answer += '\n\nChecked the following reports:\n'
    for report_id in report_ids:
        report_name = df_index[df_index.report_id == report_id].title.values[0]
        final_answer += f'\t- {report_name}\n'

    return final_answer
