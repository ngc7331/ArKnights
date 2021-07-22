import os
import time
import logging

formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
logfile = os.path.join('log', '%s.log' % time.strftime('%Y%m%d%H%M', time.localtime(time.time())))
class Logger():
    def __init__(self):
        if (not os.path.exists('log')):
            os.mkdir('log')
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)

        self._consolehandler = logging.StreamHandler()
        self._consolehandler.setLevel(logging.DEBUG)
        self._consolehandler.setFormatter(formatter)
        self._logger.addHandler(self._consolehandler)

        self._filehandler = logging.FileHandler(logfile, 'w')
        self._filehandler.setLevel(logging.INFO)
        self._filehandler.setFormatter(formatter)
        self._logger.addHandler(self._filehandler)

    def SetLevel(self, level:int, handler:str = 'console') -> None:
        handler = handler.lower()
        if (handler == 'file'):
            self._filehandler.setLevel(level)
        else:
            self._consolehandler.setLevel(level)

    def debug(self, msg):
        return self._logger.debug(msg)
    def info(self, msg):
        return self._logger.info(msg)
    def warning(self, msg):
        return self._logger.warning(msg)
    def error(self, msg):
        return self._logger.error(msg)
    def critical(self, msg):
        return self._logger.critical(msg)