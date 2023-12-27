"""TODO DOCSTRING."""
import pandas as pd

from .ask import ask
from .indexer import ReportIndexer
from .vectorstores import VectorStore

__all__ = ['ReportIndexer', 'VectorStore', 'ask']

# Adjust some dependency settings
pd.set_option('display.max_columns', None)  # Show all columns when printing
pd.set_option('display.width', None)  # Don't wrap columns when printing
