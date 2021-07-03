import os
import re
import sys
import json
import time
import random
import logging
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtGui

REQUIERD_CONF_VERSION = '0.1a'

if (not os.path.exists('log')):
    os.mkdir('log')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
consolehandler = logging.StreamHandler()
consolehandler.setLevel(logging.DEBUG)
consolehandler.setFormatter(formatter)
logfile = os.path.join('log', '%s.log' % time.strftime('%Y%m%d%H%M', time.localtime(time.time())))
filehandler = logging.FileHandler(logfile, 'w')
filehandler.setLevel(logging.INFO)
filehandler.setFormatter(formatter)
logger.addHandler(consolehandler)
logger.addHandler(filehandler)

class Ark(QWidget):
    def __init__(self, conf:dict):
        super().__init__()
        self.conf = conf
        self.mouse_locked = self.conf['mouse_locked']
        global REQUIERD_CONF_VERSION
        if (conf['version'] != REQUIERD_CONF_VERSION):
            self.RaiseError(
                '错误：配置文件版本不正确',
                '[Error] Ark:\n需求版本：%s\n实际版本：%s\n您可以尝试删除目录下的conf.json以使得程序自动生成新的配置文件' % (REQUIERD_CONF_VERSION, conf['version']),
                'warning'
            )
            logger.error('Ark: Mismatched config file version: %s ~ %s' % (REQUIERD_CONF_VERSION, conf['version']))
        self.error = False
        self.InitWindow()
        self.InitTrayIcon()
        self.knights = {}
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
            '鼠标锁定': ['resources/icon/locked.svg' if self.mouse_locked else 'resources/icon/unlocked.svg', self.MouseLock],
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

    def InitKnights(self) -> None:
        for knight_name, knight_conf in self.conf['knights'].items():
            if (not knight_conf['enabled']):
                continue
            logger.info('Create %s' % knight_name)
            knight = Knight(self, knight_name)
            if (self.error):
                logger.warning('Create %s failed' % knight_name)
            else:
                self.knights[knight_name] = knight
        logger.info('Created knights: %s' % self.knights)

    def RaiseError(self, title: str, text: str, type: str) -> None:
        box = QMessageBox()
        if (type == 'warning'):
            choice = box.warning(self, title, text, QMessageBox.Ignore|QMessageBox.Abort)
        elif (type == 'critical'):
            choice = box.critical(self, title, text, QMessageBox.Abort)
        else:
            choice = box.information(self, title, text, QMessageBox.Yes)
        if (choice == QMessageBox.Abort):
            logger.critical('An error occurred, user abort.')
            self.Quit()

    def MouseLock(self) -> None:
        self.mouse_locked = not self.mouse_locked
        self._menu_action['鼠标锁定'].setIcon(QIcon('resources/icon/locked.svg' if self.mouse_locked else 'resources/icon/unlocked.svg'))

    def Reload(self) -> None:
        for knight in list(self.knights.values()):
            logger.info('Stop %s' % knight.name)
            knight.close()
            self.knights.pop(knight.name)
        self.InitKnights()

    def Quit(self) -> None:
        self.should_close = True
        for knight in list(self.knights.values()):
            logger.info('Stop %s' % knight.name)
            knight.close()
            self.knights.pop(knight.name)
        logger.info('Stop Ark')
        self.close()
        sys.exit()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if (self.should_close):
            a0.accept()
        else:
            a0.ignore()
            self.hide()

class Knight(QWidget):
    def __init__(self, ark: Ark, name: str):
        super().__init__()
        self.ark, self.name, self.conf, self.fps = ark, name, ark.conf['knights'][name], ark.conf['fps']
        self.InitWindow()
        self.InitModelHolder()
        self.stat_rec = ['Idle', 'Idle']
        try:
            self.InitModel()
        except FileNotFoundError as e:
            logger.error('resources/model/%s not found, please check!' % self.name, exc_info=True)
            ark.RaiseError('错误：文件未找到', '[Error] %s:\n%s' % (self.name, e), 'warning')
            ark.error = True
            self.close()
        self.following_mouse = False
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
        model_dir = 'resources/model'
        dir_list = os.listdir(model_dir)
        for dir in dir_list:
            if (not os.path.isdir(os.path.join(model_dir, dir))):
                dir_list.remove(dir)
        img_list = os.listdir(os.path.join(model_dir, self.name))
        for img in img_list:
            if (not img.endswith('.png')):
                continue
            action = re.match(r'(\D*)', img).group(1)
            if (action not in self.model.keys()):
                self.model[action] = []
            self.model[action].append(LoadImage(os.path.join(model_dir, self.name, img)))
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
        logger.debug('%s: rand=%s hit_wall=%s click=%s' % (self.name, rand, hit_wall, self.stat=='Click'))
        if (rand > 80 or hit_wall or self.stat == 'Click'):
            if (self.stat_rec[0] == 'Idle' and self.stat_rec[1] == 'Move' and hit_wall):
                logger.debug('%s: Force change status to Move' % self.name)
                self.stat = 'Move'
            else:
                logger.debug('%s: Randomly change status' % self.name)
                self.stat = ['Idle', 'Move'][random.randint(0, 1)]
            if (self.stat == 'Move'):
                if (hit_wall):
                    self.heading = 1 - self.heading
                else:
                    if (self.stat_rec[1] != 'Move' or random.randint(0,100) > 80):
                        self.heading = random.randint(0, 1)
            logger.debug('%s: %s -> %s, heading=%s' % (self.name, self.stat_rec[1], self.stat, 'Left' if self.heading else 'Right'))
        self.i = 0
        self.playing = True

    def RunModel(self):
        if (not self.playing or self.i >= len(self.model[self.stat])):
            self.RandomAction()
        frame = self.model[self.stat][int(self.i)]
        #logger.debug('%s: %5s %5s %5s' % (self.name, self.stat, int(self.i), ['Right', 'Left'][self.heading]))
        if (self.stat == 'Move'):
            screenRect = QApplication.desktop().screenGeometry()
            x = self.pos().x()
            x += 2 * (0.5-self.heading)
            if ((x<=0 and self.heading == 1) or (x>=screenRect.width()-self.size().width() and self.heading == 0)):
                logger.info('%s Hit Wall' % self.name)
                self.RandomAction(hit_wall = True)
                return None
            self.move(x, self.pos().y())
        self.holder.setPixmap(QPixmap.fromImage(frame.mirrored(self.heading, False)))
        self.i += self.conf['fps']/self.fps

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if (a0.button() == Qt.LeftButton and not ark.mouse_locked):
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
                logger.warning('%s: Click anim not found' % self.name)
                return None
            if (self.stat == 'Click'):
                return None
            logger.debug('%s: %s -> Click' % (self.name, self.stat))
            self.stat = 'Click'
            self.i = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open('./conf.json', 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        screenRect = QApplication.desktop().screenGeometry()
        conf = {
            'version': REQUIERD_CONF_VERSION,
            'fps': 60,
            'knights': {
                'FrostNova': {
                    'init_pos': [screenRect.width()-256, screenRect.height()-256], #[x, y]
                    'size': [256, 256], #[x, y]
                    'enabled': True,
                    'fps': 60
                },
                "Amiya": {
                    "init_pos": [0, screenRect.height()-256],
                    "size": [256, 256],
                    "enabled": False,
                    "fps": 60
                }
            },
            'mouse_locked': True
        }
        with open('./conf.json', 'w') as f:
            f.write(json.dumps(conf, ensure_ascii = False, indent = 4, separators=(',', ': ')))
    logger.info(conf)
    ark = Ark(conf)
    sys.exit(app.exec_())
