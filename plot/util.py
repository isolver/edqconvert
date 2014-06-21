__author__ = 'Sol'

import os

def nabs(file_path):
    return os.path.normcase(os.path.normpath(os.path.abspath(file_path)))
