# -*- coding: utf-8 -*-
from __future__ import division
"""
PyDAT - Python Data Analysis Toolbox

Copyright (C) 2012-2013 COPYRIGHT_HOLDER_NAME

Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).
"""

#try:
#    import sip
#    sip.setapi('QString', 2)
#    sip.setapi('QVariant', 2)
#except:
#    print 'PyQt4 api could not be set to V 2.'
    
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager
from pyqtgraph.dockarea import Dock
from weakref import proxy

class EmbeddedIPythonConsole(object):
    def __init__(self):

        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        self.kernel.gui = 'qt4'
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
 
        openning_text="Welcome to the PyDAT IPython 1.1 Embedded Console.\n"
        openning_text+="\nThe following packages have been imported for convience:\n"
        openning_text+="\tnumpy -> np\n\tscipy -> sp\n\tmatplotlib->mpl\n"
        openning_text+="\tmatplotlib.pyplot -> plt\n\tpylab import *\n\tcv2\n\tpsutil -> psu\n"

         
        self.widget = RichIPythonWidget(banner = openning_text, exit_msg = "")
        self.widget.kernel_manager = self.kernel_manager
        self.widget.kernel_client = self.kernel_client
        self.widget.exit_requested.connect(self.stop)
        self.issueStartupCommands()

    def issueStartupCommands(self):
        run_cell=self.kernel.shell.run_cell

        run_cell("import numpy as np")
        run_cell("import scipy as sp")
        run_cell("import matplotlib as mpl")
        run_cell("import matplotlib.pyplot as plt")
        run_cell("from pylab import *")
        run_cell("import cv2 as cv")
        run_cell("import psutil as psu")
        run_cell("import pandas as pd")
        run_cell("import pyqtgraph as pg")

    def getWidget(self):
        return self.widget

    def initDataState(self,edqApp):
        self.udpdateUserNamespace(edqplot_app=edqApp)
        self.udpdateUserNamespace(edq_datasource=edqApp._data_source)

    def clearUserNamespace(self):
        self.udpdateUserNamespace(edqplot_app=None)
        self.udpdateUserNamespace(edq_datasource=None)
            
    def udpdateUserNamespace(self,**kwargs):
        try:
            self.kernel.shell.push(kwargs)
        except:
            raise RuntimeError("Exception in udpdateUserNamespace: {0}".format(kwargs))

    def deleteUserNamespaceKeys(self,key_list):
        for key in key_list:
            try:
                self.kernel.shell.pop(key)
            except Exception, e:
                print '---'
                print 'Error in deleteUserNamespaceKeys. Could not pop:', key
                print 'Exception:', e
                print '---'

    def handleProjectChange(self,old_project,new_project):
        self.udpdateUserNamespace(pydat_project=new_project)
        
    def stop(self):
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()

    def __del__(self):
        self.stop()

