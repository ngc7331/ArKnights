import os
import sys
import json
import time
import random
import logging
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtGui

REQUIRED_CONF_VERSION = '0.1d'
REQUIRED_ACTION = ['Idle', 'Move']

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
    def __init__(self):
        super().__init__()
        self.LoadConfig()
        self.should_close = False
        self.mouse_locked = self.conf['mouse_locked']
        self.knights = {}
        global REQUIRED_CONF_VERSION
        if (self.conf['version'] != REQUIRED_CONF_VERSION):
            self.RaiseError(
                '错误：配置文件版本不正确',
                '[Error] Ark:\n需求版本：%s\n实际版本：%s\n您可以尝试删除目录下的config.json以使得程序自动生成新的配置文件\n您亦可尝试点击忽略此问题（可能会遇到问题）' %
                (REQUIRED_CONF_VERSION, self.conf['version']),
                'warning'
            )
            logger.error('Ark: Mismatched config file version: %s (%s required)' % (self.conf['version'], REQUIRED_CONF_VERSION))
        self._error = False
        self.InitWindow()
        self.InitTrayIcon()
        self.UpdateKnights()
        self._tray_icon.show()

    def LoadConfig(self) -> None:
        try:
            with open('./config.json', 'r') as f:
                conf = json.load(f)
        except FileNotFoundError:
            logger.info('config.json not found, created')
            conf = self.GenerateConfigFile()
        logger.info(conf)
        filehandler.setLevel(conf['logging_level'])
        self.conf = conf

    def GenerateConfigFile(self) -> dict:
        screenRect = QApplication.desktop().screenGeometry()
        conf = {
            'version': REQUIRED_CONF_VERSION,
            'fps': 60,
            'knights': {
                'FrostNova_1': {
                    'init_pos': [screenRect.width()-256, screenRect.height()-256], #[x, y]
                    'size': [256, 256], #[x, y]
                    'frames': {'Idle': 180, 'Move': 180, 'Click': 180},
                    'weight': {'Idle': 1, 'Move': 1, 'Click': 1},
                    'enabled': False,
                    'fps': 60
                },
                'FrostNova_2': {
                    'init_pos': [screenRect.width()-256, screenRect.height()-256],
                    'size': [256, 256],
                    'frames': {'Idle': 240, 'Move': 96, 'Clickn': 96, 'Clicka': 180, 'Clicks': 220},
                    'weight': {'Idle': 1, 'Move': 1, 'Clickn': 2, 'Clicka': 2, 'Clicks': 1},
                    'enabled': True,
                    'fps': 60
                },
                "Amiya_test1": {
                    "init_pos": [0, screenRect.height()-256],
                    "size": [256, 256],
                    'frames': {'Idle': 60, 'Move': 68, 'Clicks': 810, 'Clickn': 60},
                    'weight': {'Idle': 1, 'Move': 1, 'Clicks': 1, 'Clickn': 4},
                    "enabled": False,
                    "fps": 60
                },
                "W_epoque7": {
                    "init_pos": [int((screenRect.width()-256)/2), screenRect.height()-256],
                    "size": [256, 256],
                    'frames': {'Idle': 360, 'Move': 80, 'Clicks': 2440, 'Clickn': 120},
                    'weight': {'Idle': 1, 'Move': 1, 'Clicks': 1, 'Clickn': 4},
                    "enabled": False,
                    "fps": 60
                }
            },
            'mouse_locked': True,
            'logging_level': logging.INFO
        }
        with open('./config.json', 'w') as f:
            f.write(json.dumps(conf, ensure_ascii = False, indent = 4, separators=(',', ': ')))
        return conf

    def InitWindow(self) -> None:
        '''TODO 初始化设置界面'''
        self.setWindowTitle('ArKnights - 设置')
        self.resize(300, 300)
        txt = QLabel('本页面仍在开发中！')
        btn_close = QPushButton('关闭')
        btn_close.clicked.connect(self.hide)
        btn_test = QPushButton('退出')
        btn_test.clicked.connect(self.Quit)
        layout = QVBoxLayout()
        layout.addWidget(txt)
        layout.addWidget(btn_test)
        layout.addWidget(btn_close)
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
            '关于': ['resources/icon/about.svg', self.About],
            '关于Qt': ['resources/icon/about.svg', self.AboutQt],
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

    def Reload(self) -> None:
        '''处理菜单栏-重载的点击事件，关闭并根据self.conf重新打开所有Knights'''
        for knight_name in list(self.knights.keys()):
            self.StopKnight(knight_name)
        self.LoadConfig()
        self.UpdateKnights()

    def About(self) -> None:
        title = '关于'
        text = '''
ArKnights: 基于PyQt5编写的明日方舟桌宠
模型素材来源于https://prts.wiki/，其版权属于上海鹰角网络科技有限公司
这只是一个学习PyQt5过程中的一个练手之作，我菜的要死，请轻喷
本项目开源于https://github.com/ngc7331/ArKnights
如果您有兴趣，欢迎issue及PR
        '''
        box = QMessageBox()
        box.about(self, title, text)
        box.show() # 没整明白，不加这一行会导致程序直接退出（本程序依赖此bug运行，勿删.jpg）
    def AboutQt(self) -> None:
        box = QMessageBox()
        box.aboutQt(self, 'About Qt')
        box.show() # 没整明白，不加这一行会导致程序直接退出（本程序依赖此bug运行，勿删.jpg）

    def RaiseError(self, title: str, text: str, type: str) -> None:
        '''弹窗提示错误'''
        box = QMessageBox()
        if (type == 'warning'):
            choice = box.warning(self, title, text, QMessageBox.Ignore|QMessageBox.Abort)
        elif (type == 'critical'):
            choice = box.critical(self, title, text, QMessageBox.Abort)
        else:
            choice = box.information(self, title, text, QMessageBox.Yes)
        box.show()
        if (choice == QMessageBox.Abort):
            logger.critical('An error occurred, user abort.')
            self.Quit()

    def Quit(self) -> None:
        '''退出程序'''
        #关闭所有Knights
        logger.info('Stop Knights')
        for knight_name in list(self.knights.keys()):
            self.StopKnight(knight_name)
        #保存config.json
        logger.info('Save config')
        self.conf['mouse_locked'] = self.mouse_locked
        with open('./config.json', 'w') as f:
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
            self.ark.RaiseError('错误：文件未找到', '[Error] %s:\n%s' % (self.name, e), 'warning')
            self.ark._error = True
            self.close()
        except KeyError as e:
            logger.error('%s: KeyError' % self.name, exc_info=True)
            self.ark.RaiseError('错误：字典键错误', '[Error] %s:\n%s\n这可能是配置文件不正确导致的' % (self.name, e), 'warning')
            self.ark._error = True
            self.close()
        self._following_mouse = False
        self._mouse_pos = self.pos()
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
            if(img.isNull()):
                return False
            img = img.scaled(self.size(), Qt.KeepAspectRatio)
            return img
        #初始化QLabel
        self.holder = QLabel(self)
        self.holder.setPixmap(QPixmap.fromImage(LoadImage('resources/Loading.png')))
        #导入模型文件
        self.model = dict.fromkeys(self.conf['frames'].keys(), [])
        self.action_list = {'click': [], 'normal': []}
        model_dir = 'resources/model/%s' % self.name
        for action in self.conf['frames'].keys():
            frames = self.conf['frames'][action]
            #载入图像
            b = len(str(frames))
            for i in range(0, frames):
                i_str = '{i:0>{b}d}'.format(i=i, b=b)
                filepath = os.path.join(model_dir, '%s%s.png'%(action, i_str))
                img = LoadImage(filepath)
                if (img):
                    self.model[action] = self.model[action] + [img]
                else:
                    logger.warning('%s not found, please check!' % filepath)
                    self.ark.RaiseError(
                        '警告：文件未找到', '[Error] %s:\n文件%s未找到，请检查' %
                        (self.name, filepath),
                        'warning'
                    )
                print(sys.getsizeof(self.model))
            #校验
            if (len(self.model[action]) != frames):
                logger.warning(
                    '%s: There should be %d frames of action [%s], there are actually %d' %
                    (self.name, self.conf['frames'][action], action, len(self.model[action]))
                )
                self.ark.RaiseError(
                    '警告：资源不完整', '[Warn] %s:\nresources/model/%s下[%s]动作资源应有%d帧，实际读取了%d帧' %
                    (self.name, self.name, action, self.conf['frames'][action], len(self.model[action])),
                    'warning'
                )
            #分类
            if (action.startswith('Click')):
                self.action_list['click'].extend([action] * self.conf['weight'][action])
            else:
                self.action_list['normal'].extend([action] * self.conf['weight'][action])
        #初始化模型相关变量
        logger.debug('%s: Click actions=%s' % (self.name, self.action_list['click']))
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
        rand = random.randint(0, 100)
        logger.debug('%s: rand=%s hit_wall=%s click=%s stat_rec=%s' % (self.name, rand, hit_wall, self.stat.startswith('Click'), self.stat_rec))
        if (rand > 80 or hit_wall or self.stat.startswith('Click')):
            if (self.stat_rec[0] != 'Move' and self.stat_rec[1] == 'Move' and hit_wall):
                self.stat = 'Move'
            else:
                self.stat = random.choice(self.action_list['normal'])
            if (self.stat == 'Move'):
                if (hit_wall):
                    self.heading = 0 if self.pos().x()<=1 else 1
                else:
                    if (self.stat_rec[1] != 'Move' or random.randint(0, 100) > 80):
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
            if (self.round >= 180/len(self.model[self.stat]) or self.stat.startswith('Click')):
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
            self._following_mouse = True
            self._mouse_pos = a0.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))
            a0.accept()
    def mouseMoveEvent(self, a0: QMouseEvent) -> None:
        if (self._following_mouse):
            self.move(a0.globalPos() - self._mouse_pos)
            a0.accept()
    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        self._following_mouse = False
        self.unsetCursor()
        a0.accept()

    def mouseDoubleClickEvent(self, a0: QMouseEvent) -> None:
        '''重写mouseDoubleClickEvent实现相应双击交互'''
        if (a0.button() == Qt.LeftButton):
            if (not self.action_list['click']):
                logger.warning('%s: Click anim not found' % self.name)
                return None
            if (self.stat.startswith('Click')):
                return None
            action = random.choice(self.action_list['click'])
            logger.debug('%s: %s -> %s' % (self.name, self.stat, action))
            self.stat = action
            self.i = 0
            a0.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ark = Ark()
    sys.exit(app.exec_())
