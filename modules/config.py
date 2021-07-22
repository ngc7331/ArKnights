import json
import logging
from PyQt5.QtWidgets import QApplication
from modules import REQUIRED_CONF_VERSION
from modules.logger import logger

def GenerateConfigFile() -> dict:
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

def LoadConfig() -> dict:
    try:
        with open('./config.json', 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        logger.info('config.json not found, created')
        conf = GenerateConfigFile()
    logger.debug(conf)
    logger.SetLevel(conf['logging_level'], 'file')
    return conf