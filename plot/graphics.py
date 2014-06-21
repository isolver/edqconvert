from __future__ import division
__author__ = 'Sol'
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import colors
from timeit import default_timer
from collections import OrderedDict

class EyeSampleTracePlot(pg.PlotWidget):
    def __init__(self,time_series, parent=None, background='default', color_pallete=None, **kwargs):
        pg.PlotWidget.__init__(self, parent, background, **kwargs)

        self._time_series = time_series

        self._data_streams = {}

        self.setLimits(xMin=time_series.min, xMax=time_series.max, minXRange=0.1, maxXRange=time_series.range)
        self._region = None
        self._update_region_callback = None
        self._associated_plot_for_region = None

        self._crosshairs = None
        self._trace_pen_infos = dict()

        self._next_default_pen_index = -1
        self._default_trace_pens = []
        self._default_trace_styles = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine]
        if color_pallete is None:
            color_pallete = colors.ColorPalettes[0]()
        for ps in self._default_trace_styles:
            for c in color_pallete.colors:
                apen = pg.mkPen(c, width=1, style=ps)
                self._default_trace_pens.append(apen)

        self._traces = {}
# 'suffix': 's', 'siPrefix': True
        self.setLabel('bottom', "Time", suffix='s',siPrefix=True )
        self.setLabel('left', "Position", 'degrees')
        # THE BELOW SHOULD BE SETTABLE VIA THE CONFIG TREE
        self.getPlotItem().addLegend()
        self.setMenuEnabled(False)

    def addTrace(self, data_stream, label=None, color=None, style='solid', connect='valid'):

        if label is None:
            label = data_stream.label
        if label in self._traces.keys():
            raise ValueError("Trace label already in use: %s"%(label))

        if connect == 'valid':
            connect = data_stream.connect_mask # np.isnan(data_stream.data) == False#

        if color is None and color == style:
            self._next_default_pen_index+=1
            pen = self._default_trace_pens[self._next_default_pen_index%len(self._default_trace_pens)]
        else:
            if style.lower() == 'solid':
                style = QtCore.Qt.SolidLine
            elif style.lower() == 'dash':
                style = QtCore.Qt.DashLine
            pen = pg.mkPen(color, width=1, style=style)

        self._data_streams[label] = data_stream
        self._trace_pen_infos[label]={'color':color,'style':style,'width':1}
        #print "adding data stream:",label,data_stream.min,data_stream.max,data_stream.range,data_stream.data
        self._traces[label] = self.plot(x=self._time_series.series,
                                        y=data_stream.data,
                                        pen=pen,
                                        connect=connect,
                                        stepMode=True,
                                        name=label)

    def changePlotAttribute(self, param_tree_key, new_value):
        for trace_name, trace in self._traces.items():
            si = param_tree_key.find(trace_name)
            if si>=0:
                trace_name_len = len(trace_name)
                attr_info_str = param_tree_key[si+trace_name_len+1:]
                attr_token, subattr_token = attr_info_str.split('_')
                if attr_token == 'pen':
                    pen_args = self._trace_pen_infos[trace_name]
                    if subattr_token == 'color':
                        pen_args[subattr_token] = new_value
                        trace.setPen(**pen_args)
                x = pg.PlotDataItem()

    def getRegionBounds(self):
        if self._region:
            return self._region.getRegion()
        return None

    def setRegionBounds(self, rmin, rmax):
        if self._region:
            self._region.setRegion((rmin, rmax))

    def enableRegion(self, initial_bounds, update_callback = lambda x: x, associated_plot = None, zvalue = 10):
        self._region = pg.LinearRegionItem()
        self._region.setZValue(zvalue)
        # Add the LinearRegionItem to the ViewBox,
        # but tell the ViewBox to exclude this
        # item when doing auto-range calculations.

        self.addItem(self._region, ignoreBounds=True)

        self._update_region_callback = update_callback
        self._associated_plot_for_region = associated_plot

        if self._associated_plot_for_region:
            self._associated_plot_for_region.setRegionAssociation(self._region)

        def update():
            self._region.setZValue(self._region.zValue())
            minX, maxX = self._region.getRegion()
            if self._associated_plot_for_region:
                self._associated_plot_for_region.setXRange(minX, maxX, padding=0)
            self._update_region_callback(minX, maxX)

        self._region.sigRegionChanged.connect(update)

        self._region.setRegion(initial_bounds)

        return self._region

    def setRegionAssociation(self, region):
        self._associated_region = region
        def updateRegion(window, viewRange):
            rgn = viewRange[0]
            self._associated_region.setRegion(rgn)
        self.sigRangeChanged.connect(updateRegion)

    def enableMouseCrossHairs(self, mousemove_callback):

        if self._crosshairs is None:
            self._crosshairs=dict()
            #cross hair
            self._crosshairs['vLine'] = pg.InfiniteLine(angle=90, movable=False)
            self._crosshairs['hLine'] = pg.InfiniteLine(angle=0, movable=False)
            self.addItem(self._crosshairs['vLine'], ignoreBounds=True)
            self.addItem(self._crosshairs['hLine'], ignoreBounds=True)

            vb = self.getPlotItem().vb

            self._crosshairs['mousemove_callback']=mousemove_callback

            def mouseMoved(evt):
                pos = evt[0]  ## using signal proxy turns original arguments into a tuple
                if self.sceneBoundingRect().contains(pos):
                    mousePoint = vb.mapSceneToView(pos)
                    mtime = mousePoint.x()

                    if mtime > self._time_series.min and mtime < self._time_series.max:
                        index = self._time_series.indexFromTime(mtime)
                        #xstats['Time'] = mtime
                        #xstats['Sample Index'] = index
                        #xstats['Degrees'] = mousePoint.y()
                        #region_tree.setData(region_stats, hideRoot=True)
                        self._crosshairs['mousemove_callback'](mousePoint , self._time_series.min, self._time_series.max)

                    self._crosshairs['vLine'].setPos(mousePoint.x())
                    self._crosshairs['hLine'].setPos(mousePoint.y())

            self._mmproxy = pg.SignalProxy(self.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)

    def tunePlot(self):
        self.getPlotItem().setDownsampling(auto=True, mode='peak')
        #self.getPlotItem().setClipToView(True)

    def remove(self):
        self._time_series = None

        self._data_streams.clear()
        self._region = None
        self._update_region_callback = None
        self._associated_plot_for_region = None

        self._crosshairs = None
        self._trace_pen_infos.clear()

        del self._default_trace_pens[:]

        self._default_trace_styles = [QtCore.Qt.SolidLine, QtCore.Qt.DashLine]

        self._traces.clear()
        self.close()

class DataStats(pg.DataTreeWidget):
    def __init__(self, data_region_plot, data_source):
        self._stat_resources = data_region_plot

        self.indexFromTime = data_region_plot._time_series.indexFromTime

        self._tree_widget_data=None
        self.buildTreeWidgetData()

        pg.DataTreeWidget.__init__(self, data=self._tree_widget_data)
        self.hideColumn(1)

        self.updateFileDataFilters(data_source)
        self.updateSessionMetaData(data_source.current_session)


    def buildTreeWidgetData(self):
        self._tree_widget_data = OrderedDict()

        datafile_filters_stats = OrderedDict()
        datafile_filters_stats['File Name'] = ""
        datafile_filters_stats['Sessions'] = OrderedDict()
        datafile_filters_stats['Sessions']['Count'] = 0
        datafile_filters_stats['Sessions']['Selected'] = 0
        datafile_filters_stats['Sessions']['Start Time'] = 0
        datafile_filters_stats['Sessions']['End Time'] = 0
        datafile_filters_stats['Sessions']['Duration'] = 0
        datafile_filters_stats['Trial Set'] = OrderedDict()
        datafile_filters_stats['Trial Set']['Count'] = 0
        datafile_filters_stats['Trial Set']['Selected'] = np.zeros((2,),dtype=np.uint8)
        datafile_filters_stats['Trial Set']['Selection Start'] = 0.0
        datafile_filters_stats['Trial Set']['Selection End'] = 0.0
        datafile_filters_stats['Trial Set']['Duration']=0
        self._tree_widget_data['Data File'] = datafile_filters_stats

        session_meta_data = OrderedDict()
        session_meta_data['Operator Code'] = ""
        session_meta_data["Eye Tracker"] = OrderedDict()
        et_info = session_meta_data["Eye Tracker"]
        et_info['Model'] = ""
        et_info['ID'] = ""
        et_info['Sampling Rate'] = 0
        et_info['Tracking Mode'] = 0

        session_meta_data["Calibration Screen"] = OrderedDict()
        screen_info = session_meta_data["Calibration Screen"]
        screen_info['Pixel Resolution'] = OrderedDict()
        screen_info['Pixel Resolution']['Horizontal'] = 0
        screen_info['Pixel Resolution']['Vertical'] = 0
        screen_info['Size ( mm )'] =  OrderedDict()
        screen_info['Size ( mm )']['width']  = 0
        screen_info['Size ( mm )']['height'] = 0
        screen_info['Eye Distance'] = 0

        self._tree_widget_data['Session Meta Data'] = session_meta_data

        crosshair_stats = OrderedDict()
        crosshair_stats['Time'] = 0.0
        crosshair_stats['Degrees'] = 0.0
        self._tree_widget_data['Crosshair'] = crosshair_stats

        region_stats = OrderedDict()
        region_stats['Start Time']=0.0
        region_stats['End Time']=0.0
        region_stats['Duration']=0.0

        region_stats['Left Eye']=OrderedDict()
        region_stats['Left Eye']['Sample Count'] = 0
        region_stats['Left Eye']['Number Invalid'] = 0
        region_stats['Left Eye']['% Invalid'] = 0
        region_stats['Left Eye']['Position']=OrderedDict()
        region_stats['Left Eye']['Position']['x']=OrderedDict()
        region_stats['Left Eye']['Position']['y']=OrderedDict()
        region_stats['Right Eye']=OrderedDict()
        region_stats['Right Eye']['Sample Count'] = 0
        region_stats['Right Eye']['Number Invalid'] = 0
        region_stats['Right Eye']['% Invalid'] = 0
        region_stats['Right Eye']['Position']=OrderedDict()
        region_stats['Right Eye']['Position']['x']=OrderedDict()
        region_stats['Right Eye']['Position']['y']=OrderedDict()

        self._tree_widget_data['Selection Region'] = region_stats

    def updateFileDataFilters(self, data_source):
        data_filters_info = self._tree_widget_data['Data File']

        data_filters_info['File Name'] = data_source._file_path
        data_filters_info['Sessions']['Count'] = len(data_source._session_ids)
        data_filters_info['Sessions']['Selected'] = data_source.current_session_id
        csession = data_source.current_session
        data_filters_info['Sessions']['Start Time'] = csession['start_time']
        data_filters_info['Sessions']['End Time'] = csession['end_time']
        data_filters_info['Sessions']['Duration'] = csession['end_time']- csession['start_time']
        data_filters_info['Trial Set']['Count'] = len(csession['trial_ids'])
        st_ix = csession['selected_trial_ids'][0]
        et_ix = csession['selected_trial_ids'][-1]
        data_filters_info['Trial Set']['Selected'][0] = st_ix
        data_filters_info['Trial Set']['Selected'][1] = et_ix
        data_filters_info['Trial Set']['Selection Start'] = csession['trials'][st_ix]['target_onset_time']
        data_filters_info['Trial Set']['Selection End'] = csession['trials'][et_ix]['target_offset_time']
        data_filters_info['Trial Set']['Duration']=data_filters_info['Trial Set']['Selection End'] - data_filters_info['Trial Set']['Selection Start']

        self.setData(self._tree_widget_data, True)

    def updateSessionMetaData(self, session_info):
        meta_data=session_info['meta-data']
        session_meta_data = self._tree_widget_data['Session Meta Data']
        session_meta_data['Operator Code'] = meta_data['operator']
        et_info = session_meta_data["Eye Tracker"]
        et_info['Model'] = meta_data['eyetracker_model']
        et_info['ID'] = meta_data['eyetracker_id']
        et_info['Sampling Rate'] = meta_data['eyetracker_sampling_rate']
        et_info['Tracking Mode'] = meta_data['eyetracker_mode']
        screen_info = session_meta_data["Calibration Screen"]
        screen_info['Pixel Resolution']['Horizontal'] = meta_data['display_width_pix']
        screen_info['Pixel Resolution']['Vertical'] = meta_data['display_height_pix']
        screen_info['Size ( mm )']['width'] = meta_data['screen_width']
        screen_info['Size ( mm )']['height'] = meta_data['screen_height']
        screen_info['Eye Distance'] = meta_data['eye_distance']
        self.setData(self._tree_widget_data, True)

    def updateRegionRelatedStats(self, minX, maxX):

        region_stats = self._tree_widget_data['Selection Region']
        region_stats['Start Time'] = minX
        region_stats['End Time'] = maxX
        region_stats['Duration'] = maxX-minX

        s_ix = self.indexFromTime(minX)
        e_ix = self.indexFromTime(maxX)

        data_streams = self._stat_resources._data_streams
        left_angle_x = data_streams['left_angle_x']
        left_angle_y = data_streams['left_angle_y']
        right_angle_x = data_streams['right_angle_x']
        right_angle_y = data_streams['right_angle_y']

        lscount = left_angle_x.count(s_ix, e_ix, valid_only=False)
        if lscount > 0:
            region_stats['Left Eye']['Sample Count'] =lscount
            region_stats['Left Eye']['Number Invalid'] = left_angle_x.invalid_count(s_ix, e_ix)
            region_stats['Left Eye']['% Invalid'] = left_angle_x.invalid_count(s_ix, e_ix)/lscount*100.0

            region_stats['Left Eye']['Position']['x'] = left_angle_x.stats(s_ix, e_ix)
            region_stats['Left Eye']['Position']['y'] = left_angle_y.stats(s_ix, e_ix)

        rscount = right_angle_x.count(s_ix, e_ix, valid_only=False)
        if lscount > 0:
            region_stats['Right Eye']['Sample Count'] =rscount
            region_stats['Right Eye']['Number Invalid'] = right_angle_x.invalid_count(s_ix, e_ix)
            region_stats['Right Eye']['% Invalid'] = right_angle_x.invalid_count(s_ix, e_ix)/rscount*100.0

            region_stats['Right Eye']['Position']['x'] = right_angle_x.stats(s_ix, e_ix)
            region_stats['Right Eye']['Position']['y'] = right_angle_y.stats(s_ix, e_ix)

        self._tree_widget_data['Selection Region']=region_stats
        self.setData(self._tree_widget_data, True)
        #target_angle_x = self._stat_resources._data_streams['target_angle_x']
        #target_angle_y = self._stat_resources._data_streams['target_angle_y']

    def updateCrosshairStats(self, mousePoint, minX, maxX):
        self._tree_widget_data['Crosshair']['Time'] = mousePoint.x()
        self._tree_widget_data['Crosshair']['Degrees'] = mousePoint.y()

        self.setData(self._tree_widget_data, True)