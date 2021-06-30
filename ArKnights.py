import sys
import json
from typing import Set
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtGui

class Setting(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle('Setting')
        self.should_close = False
        self.btn_test = QPushButton('btn_test')
        self.btn_test.clicked.connect(parent.Quit)
        self.btn_close = QPushButton('btn_close')
        self.btn_close.clicked.connect(self.close)
        layout = QVBoxLayout()
        layout.addWidget(self.btn_test)
        layout.addWidget(self.btn_close)
        self.setLayout(layout)
    def closeEvent(self, event):
        if (self.should_close):
            event.accept()
        else:
            event.ignore()
            self.hide()
class Knight(QWidget):
    def __init__(self, conf):
        super().__init__()
        self.setting = Setting(self)
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.SubWindow)
        #self.setAutoFillBackground(False)
        #self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 任务栏菜单
        action_setting = QAction('Setting', self, triggered=self.setting.show)
        action_reload = QAction('Reload', self, triggered=self.show)
        action_quit = QAction('退出', self, triggered=self.Quit)
        action_quit.setIcon(QIcon("resources/quit.svg"))
        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(action_setting)
        self.tray_icon_menu.addAction(action_reload)
        self.tray_icon_menu.addAction(action_quit)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("resources/favicon.ico"))
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        self.tray_icon.show()
        # 
        self.resize(conf['size'][0], conf['size'][1])
        self.move(conf['init_pos'][0], conf['init_pos'][1])
    def LoadConf(self, conf):
        pass
    def Quit(self):
        self.setting.should_close = True
        self.setting.close()
        self.close()
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open('./conf.json', 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        conf = {
            'init_pos': [9999, 9999], #[x, y]
            'size': [256, 256], #[x, y]
            'fps': 30
        }
        #with open('./conf.json', 'w') as f:
        #    f.write(json.dumps(
        #        conf,
        #        ensure_ascii = False,
        #        indent = 4,
        #        separators=(',', ': ')
        #    ))
    knight = Knight(conf)
    knight.show()
    sys.exit(app.exec_())
