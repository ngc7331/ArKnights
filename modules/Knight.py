import os
import random
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from modules.logger import logger

class Knight(QWidget):
    def __init__(self, ark, name: str):
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
        if (a0.button() == Qt.LeftButton and not self.ark.mouse_locked):
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