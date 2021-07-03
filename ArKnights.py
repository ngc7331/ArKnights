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
    def __init__(self, conf: dict):
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
        self._error = False
        self.InitWindow()
        self.InitTrayIcon()
        self.knights = {}
        self.UpdateKnights()
        self._tray_icon.show()

    def InitWindow(self) -> None:
        '''TODO 初始化设置界面'''
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

    def InitTrayIcon(self) -> None:
        '''初始化任务栏菜单'''
        self._menu_action = {
            'knights': {}
        }
        menu = QMenu(self)
        #角色子菜单
        menu_knights = menu.addMenu(QIcon('resources/icon/knights.svg'), '角色')
        menu_knights.triggered.connect(self.KnightSwitch)
        for knight_name, knight_conf in self.conf['knights'].items():
            self._menu_action['knights'][knight_name] = QAction(knight_name, self)
            self._menu_action['knights'][knight_name].setIcon(QIcon('resources/icon/checked.svg' if knight_conf['enabled'] else None))
            menu_knights.addAction(self._menu_action['knights'][knight_name])
        #菜单其它部分
        obj_list = {
            '鼠标锁定': ['resources/icon/locked.svg' if self.mouse_locked else 'resources/icon/unlocked.svg', self.MouseLock],
            '设置': ['resources/icon/setting.svg', self.show],
            '重载': ['resources/icon/reload.svg', self.Reload],
            '退出': ['resources/icon/quit.svg', self.Quit]
        }
        for obj in obj_list.keys():
            self._menu_action[obj] = QAction(obj, self, triggered=obj_list[obj][1])
            self._menu_action[obj].setIcon(QIcon(obj_list[obj][0]))
            menu.addAction(self._menu_action[obj])
        #载入菜单
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(QIcon('resources/favicon.ico'))
        self._tray_icon.setContextMenu(menu)

    def UpdateKnights(self) -> None:
        '''根据self.conf['knights'][knight_name]['enabled']启用或关闭Knight并更新self.knights'''
        for knight_name, knight_conf in self.conf['knights'].items():
            if (knight_name in self.knights.keys() and not knight_conf['enabled']): #未启用但存在 -> 关闭
                self.StopKnight(knight_name)
            if (knight_name in self.knights.keys() or not knight_conf['enabled']): #未启用或已存在 -> 跳过创建
                continue
            logger.info('Create %s' % knight_name)
            knight = Knight(self, knight_name)
            if (self._error):
                logger.warning('Create %s failed' % knight_name)
            else:
                self.knights[knight_name] = knight
        logger.info('Created knights: %s' % self.knights)

    def StopKnight(self, knight_name: str) -> None:
        '''关闭self.knights[knight_name]并从self.knights中移除'''
        logger.info('Stop %s' % knight_name)
        self.knights[knight_name].close()
        self.knights.pop(knight_name)

    def KnightSwitch(self, a0: QAction) -> None:
        '''处理菜单栏-角色-Knight的点击事件，改变对应Knight的enabled状态'''
        self.conf['knights'][a0.text()]['enabled'] = not self.conf['knights'][a0.text()]['enabled']
        a0.setIcon(QIcon('resources/icon/checked.svg' if self.conf['knights'][a0.text()]['enabled'] else None))
        self.UpdateKnights()

    def MouseLock(self) -> None:
        '''处理菜单栏-鼠标锁定的点击事件，改变self.mouse_locked状态'''
        self.mouse_locked = not self.mouse_locked
        self._menu_action['鼠标锁定'].setIcon(QIcon('resources/icon/locked.svg' if self.mouse_locked else 'resources/icon/unlocked.svg'))

    def RaiseError(self, title: str, text: str, type: str) -> None:
        '''弹窗提示错误'''
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

    def Reload(self) -> None:
        '''关闭并根据self.conf重新打开所有Knights'''
        for knight_name in list(self.knights.keys()):
            self.StopKnight(knight_name)
        self.UpdateKnights()

    def Quit(self) -> None:
        '''退出程序'''
        #关闭所有Knights
        logger.info('Stop Knights')
        for knight_name in list(self.knights.keys()):
            self.StopKnight(knight_name)
        #保存conf.json
        logger.info('Save config')
        with open('./conf.json', 'w') as f:
            f.write(json.dumps(self.conf, ensure_ascii = False, indent = 4, separators=(',', ': ')))
        #关闭Ark
        logger.info('Stop Ark')
        self.should_close = True
        self.close()
        sys.exit()

    def closeEvent(self, a0: QCloseEvent) -> None:
        '''重写closeEvent，避免错误关闭'''
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
        self.stat_rec = ['Idle', 'Idle']
        try:
            self.InitModel()
        except FileNotFoundError as e:
            logger.error('resources/model/%s not found, please check!' % self.name, exc_info=True)
            ark.RaiseError('错误：文件未找到', '[Error] %s:\n%s' % (self.name, e), 'warning')
            ark._error = True
            self.close()
        self.following_mouse = False
        self.mouse_pos = self.pos()
        self.InitTimer()
        self.show()

    def InitWindow(self) -> None:
        '''初始化窗口'''
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        # 设置大小和位置
        self.resize(self.conf['size'][0], self.conf['size'][1])
        self.move(self.conf['init_pos'][0], self.conf['init_pos'][1])

    def InitModel(self) -> None:
        '''导入模型文件'''
        def LoadImage(imgpath: str) -> QImage:
            '''从imgpath读取图像，返回缩放后的QImage'''
            img = QImage()
            img.load(imgpath)
            img = img.scaled(self.size())
            return img
        #初始化QLabel
        self.holder = QLabel(self)
        img = QImage()
        img.load('resources/Loading.png')
        self.holder.setPixmap(QPixmap.fromImage(img))
        #导入模型文件
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
        #初始化模型相关变量
        self.stat = 'Idle'
        self.i = 0
        self.heading = 0 # 0=Right, 1=Left
        self.playing = False
        self.round = 0

    def InitTimer(self) -> None:
        '''初始化计时器'''
        self.timer = QTimer()
        self.timer.timeout.connect(self.RunModel)
        self.timer.start(int(1000/self.fps))

    def RandomAction(self, hit_wall: bool = False) -> None:
        '''
        生成随机动作
        0~100的随机数大于80 或 撞墙 或 完成Click事件 -> 从动作列表中随机选择动作
        如果状态是Move   -> 未撞墙 -> 0~100的随机数大于80 -> 随机选择方向
                        -> 撞墙   -> 走向屏幕内
        '''
        self.stat_rec = [self.stat_rec[1], self.stat]
        rand = random.randint(0,100)
        logger.debug('%s: rand=%s hit_wall=%s click=%s stat_rec=%s' % (self.name, rand, hit_wall, self.stat=='Click', self.stat_rec))
        if (rand > 80 or hit_wall or self.stat == 'Click'):
            if (self.stat_rec[0] == 'Idle' and self.stat_rec[1] == 'Move' and hit_wall):
                self.stat = 'Move'
            else:
                self.stat = ['Idle', 'Move'][random.randint(0, 1)]
            if (self.stat == 'Move'):
                if (hit_wall):
                    self.heading = 0 if self.pos().x()<=0 else 1
                else:
                    if (self.stat_rec[1] != 'Move' or random.randint(0,100) > 80):
                        self.heading = random.randint(0, 1)
            logger.debug('%s: %s -> %s, heading=%s' % (self.name, self.stat_rec[1], self.stat, 'Left' if self.heading else 'Right'))
        self.i = 0
        self.playing = True
        self.round = 0

    def RunModel(self) -> None:
        '''运行模型'''
        if (not self.playing):
            self.RandomAction()
        elif (self.i >= len(self.model[self.stat])):
            if (self.round >= 180/len(self.model[self.stat]) or self.stat == 'Click'):
                self.RandomAction()
            else:
                self.i = 0
                self.round += 1
        frame = self.model[self.stat][int(self.i)]
        if (self.stat == 'Move'):
            screenRect = QApplication.desktop().screenGeometry()
            x = self.pos().x()
            x += int(2 * (0.5-self.heading))
            if ((x<=0 and self.heading == 1) or (x>=screenRect.width()-self.size().width() and self.heading == 0)):
                logger.debug('%s: Hit Wall' % self.name)
                self.RandomAction(hit_wall = True)
                return None
            self.move(x, self.pos().y())
        self.holder.setPixmap(QPixmap.fromImage(frame.mirrored(self.heading, False)))
        self.i += self.conf['fps']/self.fps

    '''重写鼠标相关Event实现拖动效果'''
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if (a0.button() == Qt.LeftButton and not ark.mouse_locked):
            self.following_mouse = True
            self.mouse_pos = a0.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            a0.accept()
    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        if (self.following_mouse):
            self.move(a0.globalPos() - self.mouse_pos)
            a0.accept()
    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        self.following_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        '''重写mouseDoubleClickEvent实现相应双击交互'''
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
