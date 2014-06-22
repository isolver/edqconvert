from __future__ import division
# -*- coding: utf-8 -*-


import os, inspect,pyqtgraph
from timeit import default_timer

def nabs(file_path):
    return os.path.normcase(os.path.normpath(os.path.abspath(file_path)))

def getTime():
    return default_timer()

def module_path(local_function):
    """ returns the module path without the use of __file__.  Requires a function defined
   locally in the module. from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module"""
    return os.path.abspath(inspect.getsourcefile(local_function))

def module_directory(local_function):
    mp=module_path(local_function)
    moduleDirectory,mname=os.path.split(mp)
    return moduleDirectory

# dir location

software_directory=module_directory(getTime)
resource_dir_path=os.path.abspath(os.path.join(software_directory,'./resources'))
icon_dir_path=os.path.abspath(os.path.join(resource_dir_path,'icons'))

def getIconFilePath(icon_file_name):
    return os.path.join(icon_dir_path,icon_file_name)

def getResourceFilePath(resource_file_name):
    return os.path.join(resource_dir_path,resource_file_name)

def getIconFile(iname,size=32,itype='png'):
    return os.path.join(getResourceFilePath(),u"%s_icon&%d.%s"%(iname,size,itype))