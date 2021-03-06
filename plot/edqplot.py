from __future__ import division

import sip
try:
    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)
except ValueError, e:
    raise RuntimeError('Could not set API version (%s): did you import PyQt4 directly?' % e)

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import os
from pyqtgraph.dockarea import *
from collections import OrderedDict
from util import nabs, getIconFilePath
from plotparamtree import createPlotParamTree, printParamDict
from datastream import DataStream, TimeSeries, EyeSampleDataSource
from graphics import EyeSampleTracePlot, DataStats
from ipythonConsole import EmbeddedIPythonConsole

APPGUI=dict(size=(1280,1024),
            console_area=('bottom',(.8,.4)),
            data_info_stats_area=('left',(.2,1.0)),
            data_views_area=('right',(.8,.6))
            )

class ContextualStateAction(QtGui.QAction):
    def __init__(self,*args,**kwargs):
        QtGui.QAction.__init__(self,*args,**kwargs)
        self.enableActionsList=[]
        self.disableActionsList=[]

    def enableAndDisableActions(self):
        for ea in self.enableActionsList:
            ea.setEnabled(True)
        for da in self.disableActionsList:
            da.setDisabled(True)

class EyePlot(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self._data_source = None
        self._region=None
        self._data_region_plot = None
        self._file_data_plot = None
        self._region_tree = None
        self._plot_param_tree = None
        self._plot_params = None
        self.createActions()
        self.createMainMenu()
        self.createMainToolbar()

        self._area = DockArea()
        self.setCentralWidget(self._area)
        self.setWindowTitle('EDQview')

        self._file_data_dock=None
        self._data_region_dock=None
        self._region_tree_dock=None
        self._param_tree_dock=None
        self.console_dock=None

        self.createDocks()

        self.resize(*APPGUI.get('size'))

        self.show()


    def clearDocks(self):
        #self._area.docks.clear()
        if self.console_dock:
            self.ipython_console.clearUserNamespace()#deleteUserNamespaceKeys(['edqplot_app','edq_datasource'])
            self.ipython_console.stop()
            self.console_dock.close()
            self.console_dock.destroy()
            self.console_dock.setParent(None)
            self.console_dock.label.setParent(None)

        if self._region_tree_dock:
            self._region_tree_dock.close()
            self._region_tree_dock.destroy()
            self._region_tree_dock.setParent(None)
            self._region_tree_dock.label.setParent(None)

        if self._param_tree_dock:
            self._param_tree_dock.close()
            self._param_tree_dock.destroy()
            self._param_tree_dock.setParent(None)
            self._param_tree_dock.label.setParent(None)


        if self._data_region_dock:
            self._data_region_dock.close()
            self._data_region_dock.destroy()
            self._data_region_dock.setParent(None)
            self._data_region_dock.label.setParent(None)

        if self._file_data_dock:
            self._file_data_dock.close()
            self._file_data_dock.destroy()
            self._file_data_dock.setParent(None)
            self._file_data_dock.label.setParent(None)



    def createDocks(self,file_name="File Data"):

        appsize=APPGUI.get('size')
        pos,(wx,wy) = APPGUI.get('data_info_stats_area')
        wx=wx*appsize[0]
        wy=wy*appsize[1]

        self._param_tree_dock = Dock("Settings",size=(wx,wy))
        self._area.addDock(self._param_tree_dock, pos)

        self._region_tree_dock = Dock("Stats",size=(wx,wy))
        self._area.addDock(self._region_tree_dock, 'above', self._param_tree_dock)


        pos,(wx,wy) = APPGUI.get('data_views_area')
        wx=wx*appsize[0]
        wy=wy*appsize[1]

        self._file_data_dock = Dock(file_name, size=(wx,wy/2))
        self._area.addDock(self._file_data_dock, pos)

        self._data_region_dock = Dock("Selected Region", size=(wx,wy/2))
        self._area.addDock(self._data_region_dock, 'bottom',self._file_data_dock)

        self.createEmbeddedIPythonConsoleDock()


    def createActions(self):
        atext='Open an EDQ npy File.'
        aicon='folder_open_icon&32.png'
        self.openDataFileAction = ContextualStateAction(
                                    QtGui.QIcon(getIconFilePath(aicon)),
                                    'Open',
                                    self)
        self.openDataFileAction.setShortcut('Ctrl+O')
        self.openDataFileAction.setEnabled(True)
        self.openDataFileAction.setStatusTip(atext)
        self.openDataFileAction.triggered.connect(self.openDataFile)

    def createMainMenu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(self.openDataFileAction)

    def createMainToolbar(self):
        self.toolbarFile = self.addToolBar('File')
        self.toolbarFile.addAction(self.openDataFileAction)

    def togglePlotLegendVisibility(self,param_handle, child_name, change, changed_param, show_legends):
        pass
        #if show_legends is True:
        #    self._file_data_plot._legend = self._file_data_plot.getPlotItem().addLegend()
        #    self._data_region_plot._legend = self._data_region_plot.getPlotItem().addLegend()
        #else:
        #    self._data_region_plot.getPlotItem().removeItem(self._data_region_plot._legend)
        #    self._file_data_plot.getPlotItem().removeItem(self._file_data_plot._legend)

    def setSelectedSession(self, param_handle, child_name, change, changed_param, session_id):
        self._data_source.current_session_id=session_id
        if self._region_tree:
            self._region_tree.updateFileDataFilters(self._data_source)
            self._region_tree.updateSessionMetaData(self._data_source.current_session)

    def setSelectedTrials(self, trial_ids):
        trial_ids = np.asanyarray(trial_ids, dtype = np.uint8)
        self._data_source.current_trial_ids = trial_ids
        session_trials = self._data_source.current_session['trials']
        if self._file_data_plot:
            xMin =  session_trials[trial_ids[0]]['target_onset_time']
            xMax = session_trials[trial_ids[-1]]['target_offset_time']
            rbounds = self._file_data_plot.getRegionBounds()
            if rbounds:
                rmin, rmax=rbounds
                duration = rmax - rmin
                if rmin < xMin:
                    rmin = xMin
                    rmax = min(rmin + duration,xMax)
                if rmax > xMax:
                    rmax = xMax
                    rmin = max(rmax-duration, xMin)

                self._file_data_plot.setRegionBounds(rmin, rmax)
                self._file_data_plot._associated_plot_for_region.setXRange(rmin, rmax, padding=0)
                self._file_data_plot._update_region_callback(rmin, rmax)
            # set full data view range; a 0.1 secs to begining and end for some margin
            if self._file_data_plot:
                self._file_data_plot.setLimits(xMin=xMin-0.1, xMax=xMax+0.1)#, minXRange=0.1, maxXRange=time_series.range)
            if self._region_tree:
                self._region_tree.updateFileDataFilters(self._data_source)

    def getSelectedSessionID(self):
        return self._data_source.current_session_id

    def getSelectedTrialIDs(self):
        return self._data_source.current_trial_ids

    def getTrialIDs(self):
        return self._data_source.trial_ids

    def openDataFile(self):
        file_path = QtGui.QFileDialog.getOpenFileName(self, 'Open Data file', '.','*.npy')
        if not file_path:
            return
        file_path = nabs(file_path)
        _, file_name = os.path.split(file_path)

        if self._data_source:
            self._data_source.close()
            del self._data_source

        self._data_source = EyeSampleDataSource(file_path)
        self.ipython_console.initDataState(self)

        #self.createDocks(file_name)

        self.setSelectedSession(None,None,None,None,self._data_source.current_session_id)
        self.setSelectedTrials(self._data_source.current_trial_ids)

        if self._file_data_plot:
            self._file_data_plot.getPlotItem().clear()
            self._file_data_plot.init(self._data_source.time, add_legend=True)
        else:
            self._file_data_plot = EyeSampleTracePlot(self._data_source.time, add_legend=True)
            self._file_data_dock.addWidget(self._file_data_plot)

        self._file_data_plot.addTrace(self._data_source.target_angle_x, label='target_angle_x', color=(127,0,0), style='dash', connect='all')
        self._file_data_plot.addTrace(self._data_source.target_angle_y, label='target_angle_y', color=(255,76,76), style='dash', connect='all')
        self._file_data_plot.addTrace(self._data_source.left_angle_x, label='left_angle_x', color=(46,127,75), style='solid', connect='valid')#, connect='valid')
        self._file_data_plot.addTrace(self._data_source.left_angle_y, label='left_angle_y', color=(82,229,134), style='solid', connect='valid')#, connect='valid')
        self._file_data_plot.addTrace(self._data_source.right_angle_x, label='right_angle_x', color=(10,67,102), style='solid', connect='valid')#, connect='valid')
        self._file_data_plot.addTrace(self._data_source.right_angle_y, label='right_angle_y', color=(11,145,229), style='solid', connect='valid')#, connect='valid')


        if self._data_region_plot:
            self._data_region_plot.getPlotItem().clear()
            self._data_region_plot.init(self._data_source.time)
        else:
            self._data_region_plot = EyeSampleTracePlot(self._data_source.time)
            self._data_region_dock.addWidget(self._data_region_plot)

        self._data_region_plot.addTrace(self._data_source.target_angle_x, label='target_angle_x', color=(127,0,0), style='dash', connect='all')
        self._data_region_plot.addTrace(self._data_source.target_angle_y, label='target_angle_y', color=(255,76,76), style='dash', connect='all')
        self._data_region_plot.addTrace(self._data_source.left_angle_x, label='left_angle_x', color=(46,127,75), style='solid', connect='valid')#, connect='valid')
        self._data_region_plot.addTrace(self._data_source.left_angle_y, label='left_angle_y', color=(82,229,134), style='solid', connect='valid')#, connect='valid')
        self._data_region_plot.addTrace(self._data_source.right_angle_x, label='right_angle_x', color=(10,67,102), style='solid', connect='valid')#, connect='valid')
        self._data_region_plot.addTrace(self._data_source.right_angle_y, label='right_angle_y', color=(11,145,229), style='solid', connect='valid')#, connect='valid')
        self._data_region_plot.setAutoVisible(y=True)


        if self._region_tree:
            self._region_tree.clear()
        else:
            self._region_tree = DataStats()
            self._region_tree_dock.addWidget(self._region_tree)

        self._region_tree.init(self._data_region_plot, self._data_source)


        self._data_region_plot.enableMouseCrossHairs(self._region_tree.updateCrosshairStats)

        self._region = self._file_data_plot.enableRegion([self._data_source.time.min, self._data_source.time.min+2.0],
                             update_callback=self._region_tree.updateRegionRelatedStats,
                             associated_plot=self._data_region_plot)


        if self._plot_param_tree:
            self._plot_param_tree.clear()
            self._plot_params.clearChildren()
            self._plot_params._param_node_dict.clear()
            self._plot_params._plotParamChangeHandlers.clear()

            self._plot_param_tree, self._plot_params = createPlotParamTree(self._data_source.session_label2id_mapping,
                                                                       self.getSelectedSessionID(),
                                                                       self.getTrialIDs(),
                                                                       self.getSelectedTrialIDs(),self._plot_param_tree)
        else:
            self._plot_param_tree, self._plot_params = createPlotParamTree(self._data_source.session_label2id_mapping,
                                                                       self.getSelectedSessionID(),
                                                                       self.getTrialIDs(),
                                                                       self.getSelectedTrialIDs())
            self._param_tree_dock.addWidget(self._plot_param_tree)

        self._plot_params.addParamChangeHandler("left_angle_x_pen_color", "value", self.updateParamSetting)
        self._plot_params.addParamChangeHandler("left_angle_y_pen_color", "value", self.updateParamSetting)
        self._plot_params.addParamChangeHandler("right_angle_x_pen_color", "value", self.updateParamSetting)
        self._plot_params.addParamChangeHandler("right_angle_y_pen_color", "value", self.updateParamSetting)
        self._plot_params.addParamChangeHandler("target_angle_x_pen_color", "value", self.updateParamSetting)
        self._plot_params.addParamChangeHandler("target_angle_y_pen_color", "value", self.updateParamSetting)
        self._plot_params.addParamChangeHandler("session_id_selection", "value", self.setSelectedSession)
        self._plot_params.addParamChangeHandler("show_traceplot_legend", "value", self.togglePlotLegendVisibility)

        self._plot_params.param('Eye Sample Selection','Target Display Index Selection','First Target Index').sigValueChanged.connect(self.firstTargetSelectionChanged)
        self._plot_params.param('Eye Sample Selection','Target Display Index Selection','Plot Target Count').sigValueChanged.connect(self.targetSelectCountChanged)
        self._plot_params.param('Eye Sample Selection','Target Display Index Selection','Last Target Index').sigValueChanged.connect(self.lastTargetSelectionChanged)

    def firstTargetSelectionChanged(self, param, value):
        ltarg = self.getSelectedTrialIDs()[-1]
        self.setSelectedTrials(range(value,ltarg+1))

    def targetSelectCountChanged(self, param, value):
        pass

    def lastTargetSelectionChanged(self, param, value):
        ftarg = self.getSelectedTrialIDs()[0]
        self.setSelectedTrials(range(ftarg,value+1))

    def updateParamSetting(self, param_handle, child_name, change, changed_param, new_value):
        self._data_region_plot.changePlotAttribute(param_handle, new_value)
        self._file_data_plot.changePlotAttribute(param_handle, new_value)

    def createEmbeddedIPythonConsoleDock(self):
        appsize=APPGUI.get('size')
        dock_pos,dock_size_prop=APPGUI.get('console_area')
        dwidth=int(dock_size_prop[0]*appsize[0])
        dheight=int(dock_size_prop[1]*appsize[1])
        self.console_dock = Dock("Console", size=(dwidth,dheight))
        self.ipython_console=EmbeddedIPythonConsole()
        self.console_dock.addWidget(self.ipython_console.getWidget())
        self._area.addDock(self.console_dock, 'bottom',self._data_region_dock)
        #self.sigCurrentProjectChanged.connect(self.ipython_console.handleProjectChange)

    def free(self):
        if self._data_source:
            self._data_source.close()
            del self._data_source

        if self._file_data_plot is not None:
           self._file_data_plot.remove()
           self._file_data_plot=None

        if self._data_region_plot is not None:
           self._data_region_plot.remove()
           self._data_region_plot=None

        if self._region_tree is not None:
            self._region_tree = None

        if self._plot_param_tree is not None:
            self._plot_params._param_node_dict.clear()
            self._plot_params._plotParamChangeHandlers.clear()
            self._plot_param_tree.clear()
            self._plot_param_tree=None

        self._selected_session = None
        self._selected_trials = None

    def __del__(self):
        self.free()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    app = QtGui.QApplication([])

    win = EyePlot()

    QtGui.QApplication.instance().exec_()
