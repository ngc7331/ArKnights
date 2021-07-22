import os
import time
import logging

class Logger(logging.RootLogger):
    def __init__(self):
        super().__init__(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")

        self._consolehandler = logging.StreamHandler()
        self._consolehandler.setLevel(logging.DEBUG)
        self._consolehandler.setFormatter(formatter)
        self.addHandler(self._consolehandler)

        if (not os.path.exists('log')):
            os.mkdir('log')
        logfile = os.path.join('log', '%s.log' % time.strftime('%Y%m%d%H%M', time.localtime(time.time())))
        self._filehandler = logging.FileHandler(logfile, 'w')
        self._filehandler.setLevel(logging.INFO)
        self._filehandler.setFormatter(formatter)
        self.addHandler(self._filehandler)

    def SetLevel(self, level:int, handler:str = 'console') -> None:
        handler = handler.lower()
        if (handler == 'file'):
            self._filehandler.setLevel(level)
        else:
            self._consolehandler.setLevel(level)

logger = Logger()