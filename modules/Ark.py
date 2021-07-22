import sys
import json
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from modules import REQUIRED_ACTION, REQUIRED_CONF_VERSION
from modules.logger import logger
from modules.config import LoadConfig
from modules.Knight import Knight

class Ark(QWidget):
    def __init__(self):
        super().__init__()
        self.conf = LoadConfig()
        self.should_close = False
        self.mouse_locked = self.conf['mouse_locked']
        self.knights = {}
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
        self.conf = LoadConfig()
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