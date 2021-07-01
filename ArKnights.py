import os
import re
import sys
import json
import random
import logging
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtGui

class Ark(QWidget):
    def __init__(self, conf:dict):
        super().__init__()
        self.conf = conf
        self.mouse_locked = self.conf['mouse_locked']
        self.InitWindow()
        self.InitTrayIcon()
        self.InitKnights()
        self._tray_icon.show()

    def InitWindow(self):
        self.setWindowTitle('ArKnights - 设置')
        self.resize(200, 200)
        self.should_close = False
        self.btn_close = QPushButton('关闭')
        self.btn_close.clicked.connect(self.hide)
        self.btn_test = QPushButton('退出')
        self.btn_test.clicked.connect(self.Quit)
        layout = QVBoxLayout()
        layout.addWidget(self.btn_test)
        layout.addWidget(self.btn_close)
        self.setLayout(layout)

    def InitTrayIcon(self):
        '''初始化任务栏菜单'''
        self._tray_icon = QSystemTrayIcon(self)
        tray_icon_menu = QMenu(self)
        obj_list = {
            '鼠标锁定': [None, self.MouseLock],
            '设置': ['resources/icon/setting.svg', self.show],
            '重载': ['resources/icon/reload.svg', self.Reload],
            '退出': ['resources/icon/quit.svg', self.Quit]
        }
        self._menu_action = {}
        for obj in obj_list.keys():
            self._menu_action[obj] = QAction(obj, self, triggered=obj_list[obj][1])
            self._menu_action[obj].setIcon(QIcon(obj_list[obj][0]))
            tray_icon_menu.addAction(self._menu_action[obj])
        self._tray_icon.setIcon(QIcon('resources/favicon.ico'))
        self._tray_icon.setContextMenu(tray_icon_menu)

    def InitKnights(self):
        self.knights = []
        for knight in list(self.conf['knights'].keys()):
            if (not self.conf['knights'][knight]['enabled']):
                continue
            logging.info('Create %s' % knight)
            self.knights.append(Knight(self, knight))

    def MouseLock(self):
        if (self.mouse_locked):
            self._menu_action['鼠标锁定'].setIcon(QIcon())
        else:
            self._menu_action['鼠标锁定'].setIcon(QIcon('resources/icon/checked.svg'))
        self.mouse_locked = not self.mouse_locked
        for knight in self.knights:
            knight.mouse_locked = self.mouse_locked

    def Reload(self):
        for knight in self.knights:
            logging.info('Stop %s' % knight.name)
            knight.Quit()
        self.InitKnights()

    def Quit(self):
        self.should_close = True
        for knight in self.knights:
            knight.close()
        self.close()
        sys.exit()

    def closeEvent(self, event):
        if (self.should_close):
            event.accept()
        else:
            event.ignore()
            self.hide()

class Knight(QWidget):
    def __init__(self, ark: Ark, name: str):
        super().__init__()
        self.ark, self.name, self.conf, self.fps = ark, name, ark.conf['knights'][name], ark.conf['fps']
        self.InitWindow()
        self.InitModelHolder()
        self.stat_rec = ['Idle', 'Idle']
        self.InitModel()
        self.following_mouse = False
        self.mouse_locked = ark.mouse_locked
        self.mouse_pos = self.pos()
        self.InitTimer()
        self.show()

    def InitWindow(self):
        '''初始化窗口'''
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 设置大小和位置
        self.resize(self.conf['size'][0], self.conf['size'][1])
        self.move(self.conf['init_pos'][0], self.conf['init_pos'][1])

    def InitModelHolder(self):
        self.holder = QLabel(self)
        img = QImage()
        img.load('resources/Loading.png')
        self.holder.setPixmap(QPixmap.fromImage(img))

    def InitModel(self):
        def LoadImage(imgpath):
            img = QImage()
            img.load(imgpath)
            img = img.scaled(self.size())
            return img
        self.model = {}
        root_dir = 'resources/model'
        dir_list = os.listdir(root_dir)
        for dir in dir_list:
            if (not os.path.isdir(os.path.join(root_dir, dir))):
                dir_list.remove(dir)
        if (self.name not in dir_list):
            logging.error('resources/model/%s not found, please check!' % self.name)
            logging.warning('Using %s instead.' % dir_list[0])
            self.name = dir_list[0]
        img_list = os.listdir(os.path.join(root_dir, self.name))
        for img in img_list:
            if (not img.endswith('.png')):
                continue
            action = re.match(r'(\D*)', img).group(1)
            if (action not in self.model.keys()):
                self.model[action] = []
            self.model[action].append(LoadImage(os.path.join(root_dir, self.name, img)))
        self.stat = 'Idle'
        self.i = 0
        self.real_i = 0
        self.heading = 0 # 0=Right, 1=Left
        self.playing = False

    def InitTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.RunModel)
        self.timer.start(1000/self.fps)

    def RandomAction(self, hit_wall: bool = False):
        self.stat_rec = [self.stat_rec[1], self.stat]
        rand = random.randint(0,100)
        logging.debug('%s: rand=%s hit_wall=%s' % (self.name, rand, hit_wall))
        if (rand > 80 or hit_wall or self.stat == 'Click'):
            if (self.stat_rec[0] == 'Idle' and self.stat_rec[1] == 'Move' and hit_wall):
                logging.debug('%s: Force change status to Move' % self.name)
                self.stat = 'Move'
            else:
                logging.debug('%s: Randomly change status' % self.name)
                self.stat = ['Idle', 'Move'][random.randint(0, 1)]
            if (self.stat == 'Move'):
                if (hit_wall):
                    self.heading = 1 - self.heading
                else:
                    if (self.stat_rec[1] != 'Move'):
                        self.heading = random.randint(0, 1)
                    elif (random.randint(0,100) > 80):
                        self.heading = random.randint(0, 1)
        self.i = 0
        self.playing = True

    def RunModel(self):
        if (not self.playing or self.i >= len(self.model[self.stat])):
            self.RandomAction()
        frame = self.model[self.stat][int(self.i)]
        logging.debug('%s: %5s %5s %5s' % (self.name, self.stat, int(self.i), ['Right', 'Left'][self.heading]))
        if (self.stat == 'Move'):
            screenRect = QApplication.desktop().screenGeometry()
            x = self.pos().x()
            x += 2 * (0.5-self.heading)
            if ((x<=0 and self.heading == 1) or (x>=screenRect.width()-self.size().width() and self.heading == 0)):
                logging.info('%s Hit Wall' % self.name)
                self.RandomAction(hit_wall = True)
                return None
            self.move(x, self.pos().y())
        self.holder.setPixmap(QPixmap.fromImage(frame.mirrored(self.heading, False)))
        self.i += self.conf['fps']/self.fps

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if (a0.button() == Qt.LeftButton and not self.mouse_locked):
            self.following_mouse = True
            self.mouse_pos = a0.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            a0.accept()
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        if (self.following_mouse):
            self.move(a0.globalPos() - self.mouse_pos)
            a0.accept()
    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.following_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))
    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if (a0.button() == Qt.LeftButton):
            if ('Click' not in self.model.keys()):
                logging.warning('%s: Click anim not found' % self.name)
                return None
            self.stat = 'Click'
            self.i = 0

    def Quit(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    logging.basicConfig(level=logging.INFO)
    try:
        with open('./conf.json', 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        screenRect = QApplication.desktop().screenGeometry()
        conf = {
            'fps': 60,
            'knights': {
                'FrostNova': {
                    'init_pos': [screenRect.width()-256, screenRect.height()-256], #[x, y]
                    'size': [256, 256] #[x, y]
                }
            },
            'mouse_locked': True
        }
        with open('./conf.json', 'w') as f:
            f.write(json.dumps(conf, ensure_ascii = False, indent = 4, separators=(',', ': ')))
    logging.info(conf)
    ark = Ark(conf)
    sys.exit(app.exec_())
