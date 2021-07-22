import sys
from modules.Ark import Ark
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ark = Ark()
    sys.exit(app.exec_())