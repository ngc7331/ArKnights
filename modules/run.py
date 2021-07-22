import sys
from PyQt5.QtWidgets import QApplication
from modules.Ark import Ark
from modules.logger import Logger

def run() -> None:
    app = QApplication(sys.argv)
    ark = Ark()
    sys.exit(app.exec_())