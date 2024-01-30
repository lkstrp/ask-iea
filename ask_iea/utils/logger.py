"""Contains a custom logger class which uses some extra filters, handlers and adjustments.

To initialize a logger, use the following code:
.utils.logger import Logger
log = Logger('<package_name>')
"""
import datetime as dt
import logging
import os
from logging.handlers import SMTPHandler

logging.addLevelName(logging.DEBUG, 'D')
logging.addLevelName(logging.INFO, 'I')
logging.captureWarnings(True)


# noinspection PyUnresolvedReferences,PyAttributeOutsideInit
class FilterTimeTaker(logging.Filter):

    """A custom filter for the logging module.

    This class calculates the time difference between the current log
    record and the last one, and adds this information to the log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Modify each log record in place by adding a new attribute 'time_relative'.

        'time_relative' contains the time difference between the current log record and the last one.

        Args:
        ----
            record (logging.LogRecord): The log record to be modified.

        Returns:
        -------
            bool: Always returns True so that the log record is not filtered out.

        """
        try:
            last = self.last
        except AttributeError:
            last = record.relativeCreated

        delta = dt.datetime.fromtimestamp(record.relativeCreated / 1000.0) - dt.datetime.fromtimestamp(last / 1000.0)

        duration_minutes = delta.seconds // 60  # Get the whole minutes
        duration_seconds = delta.seconds % 60  # Get the remaining seconds

        record.time_relative = f'{duration_minutes:02d}:{duration_seconds:02d}'
        self.last = record.relativeCreated

        return True


def add_logging_level(level_name: str, level_num: int, method_name: str = None) -> None:
    """Add a new logging level to the `logging` module and the currently configured logging class.

    `level_name` becomes an attribute of the `logging` module with the value
    `level_num`. `method_name` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `method_name` is not specified, `level_name.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example:
    -------
    >>> add_logging_level('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
        # Was already defined in logging module
        return None

    if hasattr(logging, method_name):
        msg = f'{method_name} already defined in logging module'
        raise AttributeError(msg)
    if hasattr(logging.getLoggerClass(), method_name):
        msg = f'{method_name} already defined in logger class'
        raise AttributeError(msg)

    def logForLevel(self: logging.Logger, message: str, *args: list, **kwargs: dict) -> None:
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def logToRoot(message: str, *args: list, **kwargs: dict) -> None:
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)


# noinspection PyAttributeOutsideInit
class Logger(logging.Logger):

    """A custom logger that extends the built-in Logger class from the logging module.

    It provides additional functionality such as changing the log file path, changing the log level,
    and enabling/disabling logging in general.
    """

    def __init__(
        self,
        name: str,
        path: str = 'logs.log',
        stream_level: str or int = 'DEBUG',
        file_level: str or int = 'INFO',
        path_all_logs: str = None,
    ):
        """Initialize the Logger with a name and a path for the log file.

        Args:
        ----
            name (str): The name of the logger.
            path (str, optional): The path to the log file. Defaults to 'logs.log'.
            stream_level (str or int, optional): The log level for the stream handler. Defaults to 'DEBUG'.
            file_level (str or int, optional): The log level for the file handler. Defaults to 'INFO'.
            path_all_logs (str, optional): If path is given, another file handler with the lowest log level (NOTSET)
                will be added to the logger. This handler will write all logs to the given path. Defaults to None.

        """
        self.name = name
        super().__init__(self.name)
        self.setLevel(logging.DEBUG)

        # Create formatters
        self._fmt_stream = logging.Formatter(
            fmt='[%(asctime)s %(time_relative)5s] %(levelname)s:%(lineno)d:%(funcName)s - %(message)s',
            datefmt='%H:%M:%S',
        )
        self._fmt_file = logging.Formatter(
            fmt='[%(asctime)s %(time_relative)5s] %(levelname)s:%(lineno)d:%(funcName)s - %(message)s',
            datefmt='%y%m%d %H:%M:%S',
        )

        # Create stream handler
        h_stream = logging.StreamHandler()
        h_stream.setLevel(stream_level)
        h_stream.setFormatter(self._fmt_stream)
        h_stream.addFilter(FilterTimeTaker())
        self.addHandler(h_stream)

        # Create file handler
        h_file = logging.FileHandler(path, delay=True)
        h_file.setLevel(file_level)
        h_file.setFormatter(self._fmt_file)
        h_file.addFilter(FilterTimeTaker())
        self.addHandler(h_file)

        # Create file handler for all logs
        if path_all_logs:
            h_all_logs = logging.FileHandler(path_all_logs, delay=True)
            h_all_logs.setLevel(logging.NOTSET)
            h_all_logs.setFormatter(self._fmt_file)
            h_all_logs.addFilter(FilterTimeTaker())
            self.addHandler(h_all_logs)

        # Create pre_disabled_methods to allow disabling and enabling logging (see disable_logging and enable_logging)
        self._pre_disabled_methods = {}

    def change_log_file_path(self, new_log_file: str) -> None:
        """Change the path of the log file to the given path.

        Args:
        ----
            new_log_file (str): The new path for the log file.

        """
        # Remove old file handler
        for handler in self.handlers:
            if isinstance(handler, logging.FileHandler):
                self.removeHandler(handler)
                break
        # If new_log_file is given, create a new file handler with it
        if new_log_file:
            # Create the directory if it does not exist
            os.makedirs(os.path.dirname(new_log_file), exist_ok=True)

            new_file_handler = logging.FileHandler(new_log_file)
            new_file_handler.setLevel(logging.DEBUG)
            new_file_handler.setFormatter(self._fmt_file)
            self.addHandler(new_file_handler)

    def change_log_level(self, new_log_level: str or int) -> None:
        """Change the log level to the given level.

        Args:
        ----
            new_log_level (str or int): The new log level. Can be a string (e.g., 'DEBUG', 'INFO') or an integer (0-50).

        """
        level_name_to_level = {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'NOTSET': logging.NOTSET,
        }

        if isinstance(new_log_level, str):
            new_log_level = new_log_level.upper()
            if new_log_level not in level_name_to_level:
                msg = f"Invalid log level name '{new_log_level}'."
                raise ValueError(msg)
            new_log_level = level_name_to_level[new_log_level]

        if isinstance(new_log_level, int) and (0 <= new_log_level <= 50):
            self.setLevel(new_log_level)
        else:
            msg = (
                f"Invalid log level '{new_log_level}'. Log level must be an integer between 0 and 50 or a valid log"
                f' level name.'
            )
            raise ValueError(msg)

    def disable_logging(self) -> None:
        """Disables logging by replacing the logging methods with the standard python print function."""
        self._pre_disabled_methods = {
            'debug': self.debug,
            'info': self.info,
            'warning': self.warning,
            'error': self.error,
            'critical': self.critical,
        }

        self.debug = print
        self.info = print
        self.warning = print
        self.error = print
        self.critical = print

    def enable_logging(self) -> None:
        """Restore the original logging methods to enable logging."""
        try:
            self.debug = self._pre_disabled_methods['debug']
            self.info = self._pre_disabled_methods['info']
            self.warning = self._pre_disabled_methods['warning']
            self.error = self._pre_disabled_methods['error']
            self.critical = self._pre_disabled_methods['critical']
        except KeyError:
            # Ignore since it was not disabled before
            pass

    def add_smtp_handler(
        self,
        subject: str = '[SCRIPT] Message from python logger',
        mailhost: tuple[str, int] = ('smtp.gmail.com', 587),
        to_addrs: str = os.environ.get('MAILGUN_DEFAULT_RECIPIENT'),
        user: str = os.environ.get('MAILGUN_USERNAME'),
        password: str = os.environ.get('MAILGUN_PASSWORD'),
        level_num: int = 35,
        add_email_level: bool = True,
    ) -> None:
        """Add an SMTP handler to the logger.

        Args:
        ----
            self (Logger): The logger to which the SMTP handler should be added.
            subject (str, optional): The subject of the email. Defaults to '[SCRIPT] Message from python logger'.
            mailhost (tuple, optional): The mailhost. Defaults to ('smtp.gmail.com', 587).
            to_addrs (str, optional): The recipient of the email. Defaults to
                os.environ.get('MAILGUN_DEFAULT_RECIPIENT').
            user (str, optional): The username. Defaults to os.environ.get('MAILGUN_USERNAME').
            password (str, optional): The password. Defaults to os.environ.get('MAILGUN_PASSWORD').
            level_num (int, optional): The log level. Defaults to 35.
            add_email_level (bool, optional): Whether to add the 'EMAIL' log level. Defaults to True.

        """
        if not to_addrs:
            msg = 'No recipient given. Please pass one as argument or set it as an environment variable.'
            raise ValueError(msg)
        if not user:
            msg = 'No user given. Please pass one as argument or set it as an environment variable.'
            raise ValueError(msg)
        if not password:
            msg = 'No password given. Please pass one as argument or set it as an environment variable.'
            raise ValueError(msg)

        if add_email_level:
            add_logging_level('EMAIL', level_num)

        smtp_handler = SMTPHandler(
            mailhost=mailhost,
            fromaddr=user,
            toaddrs=[to_addrs],
            subject=subject,
            credentials=(user, password),
            secure=(),
            timeout=15.0,
        )
        smtp_handler.setLevel(level_num)
        smtp_handler.setFormatter(self._fmt_stream)
        self.addHandler(smtp_handler)
