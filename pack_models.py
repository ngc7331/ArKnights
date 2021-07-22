'''
NOT FINISHED
'''

import os
import sys

root_dir = 'resources/model'
dirs = os.listdir(root_dir)

os.mkdir('packed_models')
for d in dirs:
    path = os.path.join(root_dir, d)