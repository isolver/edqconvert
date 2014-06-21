from __future__ import division
__author__ = 'Sol'
import numpy as np
from collections import OrderedDict
import os
from constants import et_nan_values
from weakref import proxy

class EyeSampleDataSource(object):
    def __init__(self, file_path):
        self._file_path = file_path

        eyetracker_folder_name, file_name = os.path.split(self._file_path)
        self.file_name = file_name
        self._et_model_from_path = eyetracker_folder_name.rsplit(os.path.sep,2)[-1]
        self._et_nan_x, self._et_nan_y = et_nan_values[self._et_model_from_path]

        self._data_table = np.load(self._file_path, 'r+')

        self._session_ids = np.unique(self._data_table['SESSION_ID'])
        self._session_id_dict = dict()
        self._sessions = OrderedDict()
        self._current_session_id = None

        for sid in self._session_ids:
            if self._current_session_id is None:
                self._current_session_id = sid

            self._session_id_dict['Session %d'%(sid)]  = sid
            self._sessions[sid] = OrderedDict()
            self._sessions[sid]['id'] = sid
            self._sessions[sid]['mask'] = self._data_table['SESSION_ID']==sid
            session_data = self._data_table[self._sessions[sid]['mask']]
            self._sessions[sid]['start_time'] = session_data['time'].min()
            self._sessions[sid]['end_time'] = session_data['time'].max()
            self._sessions[sid]['trial_ids'] = np.unique(session_data['trial_id'])
            self._sessions[sid]['selected_trial_ids'] = np.unique(session_data['trial_id'])
            self._sessions[sid]['meta-data'] = session_data[['display_refresh_rate',
                                                             'eyetracker_model',
                                                             'eyetracker_sampling_rate',
                                                             'eyetracker_mode',
                                                             'operator',
                                                             'eyetracker_id',
                                                             'display_width_pix',
                                                             'display_height_pix',
                                                             'screen_width',
                                                             'screen_height',
                                                             'eye_distance']][0]
            self._sessions[sid]['trials'] = OrderedDict()
            for trial_id in self._sessions[sid]['trial_ids'] :
                self._sessions[sid]['trials'][trial_id]=OrderedDict()
                trial_info_dict = self._sessions[sid]['trials'][trial_id]
                trial_info_dict['mask'] = self._sessions[sid]['mask'] & self._data_table['trial_id']==trial_id

                trial_info = session_data[session_data['trial_id']==trial_id][['TRIAL_START', 'TRIAL_END', 'posx', 'posy', 'ROW_INDEX','target_angle_x', 'target_angle_y']][0]
                trial_info_dict['target_onset_time'] = trial_info['TRIAL_START']
                trial_info_dict['target_offset_time'] = trial_info['TRIAL_END']
                trial_info_dict['target_id'] = trial_info['ROW_INDEX']
                trial_info_dict['target_x_pix'] = trial_info['posx']
                trial_info_dict['target_y_pix'] = trial_info['posy']
                trial_info_dict['target_x_degree'] = trial_info['target_angle_x']
                trial_info_dict['target_y_degree'] = trial_info['target_angle_y']

                #print 'trial_info for %d:'%(trial_id),trial_info_dict


        self._time = TimeSeries(self._data_table['time'])

        self.invalid_sample_masks = dict()
        self.invalid_sample_masks['left'] = (self._data_table['left_gaze_x'] == self._et_nan_x) | (self._data_table['left_gaze_y'] == self._et_nan_y)
        self.invalid_sample_masks['right'] = (self._data_table['right_gaze_x'] == self._et_nan_x) | (self._data_table['right_gaze_y'] == self._et_nan_y)


        self._data_table['left_angle_x'][self.invalid_sample_masks['left']] = np.nan
        self._data_table['left_angle_y'][self.invalid_sample_masks['left']] = np.nan
        self._data_table['left_gaze_x'][self.invalid_sample_masks['left']] = np.nan
        self._data_table['left_gaze_y'][self.invalid_sample_masks['left']] = np.nan

        self._data_table['right_angle_x'][self.invalid_sample_masks['right']] = np.nan
        self._data_table['right_angle_y'][self.invalid_sample_masks['right']] = np.nan
        self._data_table['right_gaze_x'][self.invalid_sample_masks['right']] = np.nan
        self._data_table['right_gaze_y'][self.invalid_sample_masks['right']] = np.nan

        self.invalid_sample_masks['left'] = np.isnan(self._data_table['left_gaze_x']) | np.isnan(self._data_table['left_gaze_y'])
        self.invalid_sample_masks['right'] = np.isnan(self._data_table['right_gaze_x']) | np.isnan(self._data_table['right_gaze_y'])

        self.valid_sample_masks = dict()
        self.valid_sample_masks['left'] = ~self.invalid_sample_masks['left']
        self.valid_sample_masks['right'] = ~self.invalid_sample_masks['right']

        self.target_angle_x = DataStream('target_angle_x', self._data_table['target_angle_x'])
        self.target_angle_y = DataStream('target_angle_y', self._data_table['target_angle_y'])
        self.target_pixel_x = DataStream('target_pixel_x', self._data_table['posx'])
        self.target_pixel_y = DataStream('target_pixel_y', self._data_table['posy'])

        self.left_angle_x = DataStream('left_angle_x', self._data_table['left_angle_x'], self.invalid_sample_masks['left'], self.valid_sample_masks['left'])
        self.left_angle_y = DataStream('left_angle_y', self._data_table['left_angle_y'], self.invalid_sample_masks['left'], self.valid_sample_masks['left'])
        self.left_pixel_x = DataStream('left_pixel_x', self._data_table['left_gaze_x'], self.invalid_sample_masks['left'], self.valid_sample_masks['left'])
        self.left_pixel_y = DataStream('left_pixel_y', self._data_table['left_gaze_y'], self.invalid_sample_masks['left'], self.valid_sample_masks['left'])

        self.right_angle_x = DataStream('right_angle_x', self._data_table['right_angle_x'], self.invalid_sample_masks['right'], self.valid_sample_masks['right'])
        self.right_angle_y = DataStream('right_angle_y', self._data_table['right_angle_y'], self.invalid_sample_masks['right'], self.valid_sample_masks['right'])
        self.right_pixel_x = DataStream('right_pixel_x', self._data_table['right_gaze_x'], self.invalid_sample_masks['right'], self.valid_sample_masks['right'])
        self.right_pixel_y = DataStream('right_pixel_y', self._data_table['right_gaze_y'], self.invalid_sample_masks['right'], self.valid_sample_masks['right'])

    @property
    def time(self):
        return self._time

    @property
    def current_session(self):
        return self._sessions[self._current_session_id]

    @property
    def current_session_id(self):
        return self._current_session_id

    @current_session_id.setter
    def current_session_id(self, sid):
        self._current_session_id = sid

    @property
    def session_ids(self):
        return self._session_ids

    @property
    def current_trial_ids(self):
        return self._sessions[self._current_session_id]['selected_trial_ids']

    @current_trial_ids.setter
    def current_trial_ids(self, tids):
        self._sessions[self._current_session_id]['selected_trial_ids']=tids

    @property
    def trial_ids(self):
        return self._sessions[self._current_session_id]['trial_ids']

    @property
    def session_label2id_mapping(self):
        return self._session_id_dict

    def close(self):
        self.invalid_sample_masks.clear()
        self.valid_sample_masks.clear()
        self._sessions.clear()

        self.target_angle_x=None
        self.target_angle_y=None
        self.target_pixel_x=None
        self.target_pixel_y=None

        self.left_angle_x=None
        self.left_angle_y=None
        self.left_pixel_x=None
        self.left_pixel_y=None

        self.right_angle_x=None
        self.right_angle_y=None
        self.right_pixel_x=None
        self.right_pixel_y=None

        del self._data_table


class TimeSeries(object):
    """
    TimeSeries contains the time stamps from an event array. Used for x axis
    plotting in TracePlots, etc.
    """
    def __init__(self, time_array):
        self._time_array = time_array

    @property
    def series(self):
        return self._time_array

    @property
    def min(self):
        return self._time_array.min()

    @property
    def max(self):
        return self._time_array.max()

    @property
    def range(self):
        return self.max - self.min

    @property
    def count(self):
        return len(self)

    @property
    def sps(self):
        """
        Samples per second. The number of elements per second in the time series.
        :return: float
        """
        return self.count/self.range

    def indexFromTime(self, mtime):
        return int((mtime - self.min)*self.sps)

    def __len__(self):
        return len(self._time_array)

class DataStream(object):
    def __init__(self, label, data_array, invalid_data_mask=None, valid_data_mask=None):
        self._label = label
        self._data_array = None
        self._plot_connect_mask = None
        self._invalid_mask = invalid_data_mask
        self._valid_mask = valid_data_mask
        self._invalid_periods = None
        self._stats = OrderedDict()
        self.changeDataArray(data_array)

    def changeDataArray(self, new_array):
        self._data_array = new_array
        if self._invalid_mask is not None:
            self._valid_periods = np.ma.notmasked_contiguous(np.ma.array(self._data_array, mask=self._invalid_mask))

            self._plot_connect_mask = self._valid_mask
            invalid_periods = np.ma.notmasked_contiguous(np.ma.array(self._data_array, mask=self._valid_mask))
            for invalid_slice in invalid_periods:
                self._plot_connect_mask[invalid_slice.start-1]=False

        self.stats()

    @property
    def label(self):
        return self._label

    @property
    def data(self):
        return self._data_array

    def _subset(self, s_ix=0, e_ix=-1, valid_only=True):
        if s_ix == 0 and e_ix == -1:
            if valid_only is False or self._valid_mask is None:
                return self._data_array
            return self._data_array[self._valid_mask]
        else:
            if valid_only is False or self._valid_mask is None:
                return self._data_array[s_ix:e_ix]
            #print '_subset:',self._data_array[s_ix:e_ix]
            #print 'valid mask:',self._valid_mask[s_ix:e_ix]
            #print 'invalid_mask:',self._invalid_mask[s_ix:e_ix]
            #print 'valid_only = ',self._data_array[s_ix:e_ix][self._valid_mask[s_ix:e_ix]]
            #print '================'
            return self._data_array[s_ix:e_ix][self._valid_mask[s_ix:e_ix]]

    def average(self, s_ix=0, e_ix=-1, valid_only=True):
        return np.nanmean(self._subset(s_ix, e_ix, valid_only))

    def min(self, s_ix=0, e_ix=-1, valid_only=True):
        return self._subset(s_ix, e_ix, valid_only).min()

    def max(self, s_ix=0, e_ix=-1, valid_only=True):
        return self._subset(s_ix, e_ix, valid_only).max()

    def range(self, s_ix=0, e_ix=-1, valid_only=True):
        return self.max - self.min

    def median(self, s_ix=0, e_ix=-1, valid_only=True):
        return np.median(self._subset(s_ix, e_ix, valid_only))

    def stdev(self, s_ix=0, e_ix=-1, valid_only=True):
        return self._subset(s_ix, e_ix, valid_only).std()

    def rms(self, s_ix=0, e_ix=-1, valid_only=True):
        return np.sqrt(np.nanmean(self._subset(s_ix, e_ix, valid_only)**2))

    def count(self, s_ix=0, e_ix=-1, valid_only=True):
        return self._subset(s_ix, e_ix, valid_only).shape[0]

    def invalid_count(self, s_ix=0, e_ix=-1, valid_only=True):
        if self._valid_mask is not None:
            sub_array = self._subset(s_ix, e_ix, valid_only)
            if sub_array.shape[0] > 0:
                valid_submask = self._valid_mask[s_ix:e_ix]
                valid_submask_count = valid_submask[valid_submask==True].shape[0]
                return valid_submask.shape[0] - valid_submask_count
        return 0

    def stats(self, s_ix=0, e_ix=-1, valid_only=True):
        sub_array = self._subset(s_ix, e_ix, valid_only)
        if sub_array.shape[0] > 0:
            self._stats['min'] = sub_array.min()
            self._stats['max'] = sub_array.max()
            self._stats['range'] = self._stats['max'] - self._stats['min']
            self._stats['mean'] = np.nanmean(sub_array)
            self._stats['median'] = np.median(sub_array)
            self._stats['stdev'] = sub_array.std()
            self._stats['rms'] = np.sqrt(np.nanmean(sub_array**2))
        return self._stats

    @property
    def connect_mask(self):
        return self._plot_connect_mask

    def __len__(self):
        return len(self._data_array)



