"""This file contains all prompts used in the ask_iea project. Change the prompts here if necessary.
"""
from langchain.prompts import PromptTemplate

from .utils.logger import Logger

# Define a logger
log = Logger(__name__)

# -----
# Index preprocessing
# -----

# Retrieve keywords: Used to get the abstract information in the index more concisely
prompt_retrieve_keywords = PromptTemplate(
    input_variables=['title', 'date_published', 'abstract'],
    template='Below is the abstract of a report which was published by the International Energy Agency (IEA). '
    'Provide me a list of keywords, which summarizes the report in a precise way. '
    'It is known that the article is published by the IEA, so ignore all keywords which are unnecessary in this '
    'regard. Provide around 10 keywords. Also provide me the year the article was published.\n'
    'Return the information as a dict with the keys: kewords, year\n. Only return the dict. Nothing else. \n\n'
    '\n'
    'Title: {title}\n'
    'Date Published: {date_published}\n'
    'Abstract: {abstract}',
)
# Fix output
prompt_retrieve_keywords_fix = PromptTemplate(
    input_variables=[],
    template='Please provide a dict as output, with the keys: keywords, year. Only return the dict. Nothing else. '
    'If no keywords are found, return an empty list. If no year is found, return None.',
)

# -----
# Question answering retrieval: Preselect reports (scope, before using FAISS)
# -----

# Get scope of question, if any report is referenced explicitly
prompt_check_for_scope = PromptTemplate(
    input_variables=['question'],
    template='Below is a question. Do not answer the question or provide any additional informations. '
    'Instead just tell me if a specific report or group of reports is explicitly mentioned in the question.'
    "If so, tell me which report(s) are mentioned. If not, reply 'None'. Do not provide any other information."
    ' Dont describe the content of the report(s), if not stated in the question. Do not make up any'
    ' information. \n\n'
    'Question: {question}',
)

# If scope is given in question, get the corresponding reports
prompt_get_reports_from_scope = PromptTemplate(
    input_variables=['scope', 'reports'],
    template='Check which report or group of reports is mentioned in the description below. The reports are from the '
    'International Energy Agency (IEA). Go through each report and see if it matches the description. '
    'If the report could be slightly relevant, list it. \n\n'
    'Only provide me a list of keys, separated by commas. '
    'Do not provide any other information. Do not give'
    'any additional information. Do not make up any information. \n\n'
    'Scope: {scope}\n\n'
    'Reports: \n - {reports}\n\n',
)

# If no scope is given in question, get the 10 most relevant reports for the question
prompt_get_reports_from_question = PromptTemplate(
    input_variables=['question', 'reports'],
    template='Please select the 10 best reports which may help answer the question below. If you are not sure, always '
    'add the World Energy Outlook (WEO). '
    'All reports are from the IEA (International Energy Agency). '
    'Papers are listed as $KEY,$REPORT_PUBLICATION_YEAR,$REPORT_TITLE. '
    'Return a list of keys, separated by commas. Only return the keys. Do not return any other information. '
    'Return "None", if no papers are applicable. '
    'Choose reports timely if the question requires timely information. \n\n'
    'Question: {question}\n\n'
    'Reports: \n - {reports}\n\n',
)

# Fix output
prompt_retrieve_reports_list_fix = PromptTemplate(
    input_variables=[],
    template='Please only return a list of keys, separated by commas. Do not return any other information. ',
)

# -----
# Question answering
# -----
prompt_summarize = PromptTemplate(
    input_variables=['text', 'report', 'question', 'summary_length'],
    template='Summarize the text below to help answer a question. '
    'Do not directly answer the question, instead summarize to give evidence to help answer the question. '
    'Only provide information that is relevant for the question. '
    'Also do not cite the question or mention it in any way. Act as if you would not know the question. '
    'Focus on specific details, including numbers, equations, or specific quotes. '
    'Reply "Not applicable" if text is irrelevant. '
    'Use {summary_length}.'
    '\n\n'
    '{text}\n\n'
    'Excerpt from {report}\n'
    'Question: {question}\n'
    'Relevant Information Summary:',
)

prompt_qa = PromptTemplate(
    input_variables=['context', 'answer_length', 'question'],
    template='Write an answer ({answer_length}) '
    'for the question below based on the provided context. '
    'If the context provides insufficient information and the question cannot be directly answered, '
    'reply "I cannot answer". '
    'Context (with relevance scores):\n {context}\n'
    'Question: {question}\n'
    'Answer: ',
)
