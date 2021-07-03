# ArKnights
一个基于PyQt5编写的明日方舟桌宠

这只是一个学习PyQt5过程中的一个练手之作，我菜的要死，请轻喷

如果您有兴趣，欢迎issue及PR

## 使用方法
### Windows x64 .exe
1. 在[Github Actions](https://github.com/ngc7331/ArKnights/actions)的Artifacts中下载打包好的文件，解压运行
### 源码
1. Clone本仓库，安装python3运行环境
2. 使用`pip install -r requirements.txt`安装依赖
3. 使用`python ArKnights.py`运行即可

## 玩法
- 在任务栏托盘中可设置鼠标锁定（锁定状态下无法用鼠标拖动角色）
- 在任务栏托盘-角色中可设置角色是否启用
- 双击角色可触发交互动作

## TO-DO
- 设置界面
- 可视化添加新模型并生成对应的配置
- 优化？怎么减少这玩意的内存使用啊救命
- 完善错误记录和提示
- 支持`Idle/Move/Click`三大件以外的随机（或交互）动作
  * 写完这条todo以后灵感突然来了所以目前(0.1c)已实现多种Click动作随机选择

## 版权声明
模型素材来源于[PRTS.wiki](https://prts.wiki/)，其版权属于[上海鹰角网络科技有限公司](https://ak.hypergryph.com/)