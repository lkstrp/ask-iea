"""TODO DOCSTRING."""
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import OutputFixingParser
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.output_parsers.list import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .prompts import (
    prompt_check_for_scope,
    prompt_get_reports_from_question,
    prompt_get_reports_from_scope,
    prompt_qa,
    prompt_retrieve_keywords,
    prompt_retrieve_keywords_fix,
    prompt_summarize,
)
from .utils.logger import Logger

# Define a logger
log = Logger(__name__)

# -----
# Index preprocessing
# -----

# Retrieve keywords: Used to get the abstract information in the index more concisely
chain_retrieve_keywords = (
    prompt_retrieve_keywords
    | ChatOpenAI()
    | OutputFixingParser(
        parser=SimpleJsonOutputParser(),
        prompt=prompt_retrieve_keywords_fix,
        max_retries=3,
    )
)

# -----
# Question answering retrieval: Preselect reports (scope, before using FAISS)
# -----

# Get scope of question, if any report is referenced explicitly
chain_check_for_scope = prompt_check_for_scope | ChatOpenAI(model='gpt-4')
prompt_retrieve_reports_list_fix = PromptTemplate(
    input_variables=[],
    template='Please only return a list of keys, separated by commas. Do not return any other information. ',
)

# If scope is given in question, get the corresponding reports
chain_get_reports_from_scope = (
    prompt_get_reports_from_scope
    | ChatOpenAI(model='gpt-3.5-turbo')
    | OutputFixingParser(
        parser=CommaSeparatedListOutputParser(),
        prompt=prompt_retrieve_reports_list_fix,
        max_retries=3,
    )
)

# If no scope is given in question, get the 10 most relevant reports for the question
chain_get_reports_from_question = (
    prompt_get_reports_from_question
    | ChatOpenAI(model='gpt-3.5-turbo')
    | OutputFixingParser(
        parser=CommaSeparatedListOutputParser(),
        prompt=prompt_retrieve_reports_list_fix,
        max_retries=7,
    )
)

# -----
# chain = summary_prompt | llm | StrOutputParser()
# -----
chain_summarize = prompt_summarize | ChatOpenAI(model='gpt-3.5-turbo') | StrOutputParser()

chain_qa = prompt_qa | ChatOpenAI(model='gpt-3.5-turbo') | StrOutputParser()
