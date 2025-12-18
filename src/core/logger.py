import logging

from src.config import APP_DIR


class Logger:
    """
    Custom logger class for logging messages with different colors and prefixes.
    """

    def __init__(self, name, debug=False):
        self.__logger = logging.getLogger(name)
        self.__logger.propagate = False

        log_level = logging.DEBUG if debug else logging.INFO
        self.__logger.setLevel(log_level)

        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(APP_DIR.joinpath("logs.txt"))
        stream_handler.setFormatter(self.get_formatter())
        self.__logger.addHandler(stream_handler)
        self.__logger.addHandler(file_handler)

        self.on_info(f"Logger initialized with level {logging.getLevelName(log_level)}")

    def on_info(self, message, prefix=""):
        """
        Logs an information message.
        :param message: The message to be logged.
        :param prefix: An optional prefix to be added to the message.
        """
        self.__logger.info(f"{prefix}{message}")

    def on_debug(self, message, prefix=""):
        """
        Logs a debug message.
        :param message: The message to be logged.
        :param prefix: An optional prefix to be added to the message.
        """
        self.__logger.debug(f"{prefix}{message}")

    def on_error(self, message, prefix=""):
        """
        Logs an error message.
        :param message: The message to be logged.
        :param prefix: An optional prefix to be added to the message.
        """
        self.__logger.error(f"{prefix}{message}")

    @staticmethod
    def get_formatter():
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        return formatter
