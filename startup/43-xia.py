print(ttime.ctime() + ' >>>> ' + __file__)

#from nslsii.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
#                                       Xspress3Channel, Xspress3FileStore, Xspress3ROI, logger)

from ophyd.device import (
    Device,
    Component as Cpt,
    DynamicDeviceComponent as DDC,
    FormattedComponent as FC)

from ophyd.areadetector import DetectorBase, CamBase
import bluesky.plans as bp
import bluesky.plan_stubs as bps
# bp.list_scan
import numpy as np
import itertools
import time as ttime
from collections import deque, OrderedDict
from itertools import product
import pandas as pd
import warnings


#class XIADetectorSettings(CamBase):
#    '''Quantum Detectors Xspress3 detector'''
#
#    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
#                 **kwargs):
#        if read_attrs is None:
#            read_attrs = []
#        if configuration_attrs is None:
#            configuration_attrs = ['config_path', 'config_save_path',
#                                   ]
#        super().__init__(prefix, read_attrs=read_attrs,
#                         configuration_attrs=configuration_attrs, **kwargs)
#
#    config_path = Cpt(SignalWithRBV, 'CONFIG_PATH', string=True)
#    config_save_path = Cpt(SignalWithRBV, 'CONFIG_SAVE_PATH', string=True)
#    connect = Cpt(EpicsSignal, 'CONNECT')
#    connected = Cpt(EpicsSignal, 'CONNECTED')
#    ctrl_dtc = Cpt(SignalWithRBV, 'CTRL_DTC')
#    ctrl_mca_roi = Cpt(SignalWithRBV, 'CTRL_MCA_ROI')
#    debounce = Cpt(SignalWithRBV, 'DEBOUNCE')
#    disconnect = Cpt(EpicsSignal, 'DISCONNECT')
#    erase = Cpt(EpicsSignal, 'ERASE')
#    # erase_array_counters = Cpt(EpicsSignal, 'ERASE_ArrayCounters')
#    # erase_attr_reset = Cpt(EpicsSignal, 'ERASE_AttrReset')
#    # erase_proc_reset_filter = Cpt(EpicsSignal, 'ERASE_PROC_ResetFilter')
#    frame_count = Cpt(EpicsSignalRO, 'FRAME_COUNT_RBV')
#    invert_f0 = Cpt(SignalWithRBV, 'INVERT_F0')
#    invert_veto = Cpt(SignalWithRBV, 'INVERT_VETO')
#    max_frames = Cpt(EpicsSignalRO, 'MAX_FRAMES_RBV')
#    max_frames_driver = Cpt(EpicsSignalRO, 'MAX_FRAMES_DRIVER_RBV')
#    max_num_channels = Cpt(EpicsSignalRO, 'MAX_NUM_CHANNELS_RBV')
#    max_spectra = Cpt(SignalWithRBV, 'MAX_SPECTRA')
#    xsp_name = Cpt(EpicsSignal, 'NAME')
#    num_cards = Cpt(EpicsSignalRO, 'NUM_CARDS_RBV')
#    num_channels = Cpt(SignalWithRBV, 'NUM_CHANNELS')
#    num_frames_config = Cpt(SignalWithRBV, 'NUM_FRAMES_CONFIG')
#    reset = Cpt(EpicsSignal, 'RESET')
#    restore_settings = Cpt(EpicsSignal, 'RESTORE_SETTINGS')
#    run_flags = Cpt(SignalWithRBV, 'RUN_FLAGS')
#    save_settings = Cpt(EpicsSignal, 'SAVE_SETTINGS')
#    trigger_signal = Cpt(EpicsSignal, 'TRIGGER')
#    # update = Cpt(EpicsSignal, 'UPDATE')
#    # update_attr = Cpt(EpicsSignal, 'UPDATE_AttrUpdate')

class XmapMCA(Device):
    val = Cpt(EpicsSignal, ".VAL", kind=Kind.hinted)
    R0low = Cpt(EpicsSignal, ".R0LO", kind=Kind.hinted)
    R0high = Cpt(EpicsSignal, ".R0HI", kind=Kind.hinted)
    R0 = Cpt(EpicsSignal, ".R0", kind=Kind.hinted)
    R0nm = Cpt(EpicsSignal, ".R0NM", kind=Kind.hinted)


def make_channels(channels):
    out_dict = OrderedDict()
    for channel in channels:  # [int]
        attr = f'mca{channel:1d}'
        out_dict[attr] = (XmapMCA, attr, dict())
        # attr = f"preamp{channel:1d}_gain"
        # out_dict[attr] = (EpicsSignal, f"dxp{channel:1d}.PreampGain", dict())
    return out_dict


class XMAPFileStoreFlyable(Xspress3FileStore):
    def warmup(self):
        """
        A convenience method for 'priming' the plugin.
        The plugin has to 'see' one acquisition before it is ready to capture.
        This sets the array size, etc.
        NOTE : this comes from:
            https://github.com/NSLS-II/ophyd/blob/master/ophyd/areadetector/plugins.py
        We had to replace "cam" with "settings" here.
        Also modified the stage sigs.
        """
        print_to_gui("warming up the hdf5 plugin...")
        self.enable.set(1).wait()

        self.parent.collection_mode.put(2).wait()
#        while self.parent.collection_mode.get() != 2:
#            ttime.sleep(1)
      
        self.parent.start.put(1)
        ttime.sleep(1)
        self.parent.stop_all.put(1)

        print_to_gui("done")


class GeDetector(DetectorBase):
#class GeDetector(Device):
    channels = DDC(make_channels(range(1, 33)))
    start = Cpt(EpicsSignal,'EraseStart')
    stop_all = Cpt(EpicsSignal,'StopAll')
    acquiring = Cpt(EpicsSignal,'Acquiring')
    preset_mode =  Cpt(EpicsSignal,'PresetMode')
    real_time = Cpt(EpicsSignal,'PresetReal')
    # MCA Spectra=0, MCA Mapping=1, SCA Mapping=2, List Mapping=3
    collection_mode = Cpt(EpicsSignal,'CollectMode')
    acquisition_time=Cpt(EpicsSignal,'PresetReal')
    total_points = Cpt(EpicsSignal, 'PixelsPerRun')
    trigger_mode = Cpt(EpicsSignal, 'PixelAdvanceMode')
    

    hdf5 = Cpt(XMAPFileStoreFlyable, 'HDF1:',
               read_path_template=f'{ROOT_PATH}/{RAW_PATH}/dxp/%Y/%m/%d/',
               root=f'{ROOT_PATH}/{RAW_PATH}/',
               write_path_template=f'{ROOT_PATH}/{RAW_PATH}/dxp/%Y/%m/%d/',
               )

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None, **kwargs):
#        if configuration_attrs is None:
#            configuration_attrs = ['external_trig', 'total_points',
#                                   'spectra_per_point', 'settings',
#                                   'rewindable']
#        if read_attrs is None:
#            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5', 'settings.acquire_time']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.set_channels_for_hdf5()  # TODO:
        # self.create_dir.put(-3)
#        self.spectra_per_point.put(1)
#        self.channel1.rois.roi01.configuration_attrs.append('bin_low')

#        self._asset_docs_cache = deque()
        # self._datum_counter = None
        self.warmup()  


    def trigger(self):
        return self.get_mca()

    def get_mca(self):
        def is_done(value, old_value, **kwargs):
            if old_value == 1 and value ==0:
                return True
            return False

        status = SubscriptionStatus(self.acquiring, run=False, callback=is_done)
        self.start.put(1)
        return status

    def set_limits_for_roi(self, energy_nom, roi, window='auto'):

        for ch_index, channel in enumerate(self.channels.items()):  # should be mcaN already
            if window == 'auto':
                w = _compute_window_for_xs_roi_energy(energy_nom)
            else:
                w = int(window)
            energy = _convert_xs_energy_nom2act(energy_nom, ch_index)
            ev_low_new = int(energy - w / 2)  # TODO: divide by bin size?
            ev_high_new = int(energy + w / 2)

#            roi_obj = getattr(channel.rois, roi)
#            roi_obj = getattr(channel, )
            if ev_high_new < roi_obj.ev_low.get():
                channel.R0low.put(ev_low_new)
                channel.R0high.put(ev_high_new)
            else:
                channel.R0high.put(ev_high_new)
                channel.R0low.put(ev_low_new)

    
    def warmup(self, hdf5_warmup=False):
#        self.channel1.vis_enabled.put(1)
#        self.channel2.vis_enabled.put(1)
#        self.channel3.vis_enabled.put(1)
#        self.channel4.vis_enabled.put(1)
        self.total_points.put(1)
        if hdf5_warmup:
            self.hdf5.warmup()

    def prepare_to_fly(self, traj_duration):
        acq_rate = self.ext_trigger_device.freq.get()
        self.num_points = int(acq_rate * (traj_duration + 2))
        self.ext_trigger_device.prepare_to_fly(traj_duration)

    def stage(self):
        self._infer_datum_keys()  # TODO: check parent class
        self._datum_counter = itertools.count()  # TODO: check parent class
        self.total_points.put(self.num_points)
        self.hdf5.file_write_mode.put(2)  # Stream.  Can be Capture (1)
        self.external_trig.put(True)
        self.trigger_mode.put(0)  # Gate (0), Sync (1)
        staged_list = super().stage()
        staged_list += self.ext_trigger_device.stage()
        return staged_list

    def unstage(self):
        unstaged_list = super().unstage()
        self._datum_counter = None
        self.hdf5.file_write_mode.put(0)
        self.external_trig.put(False)
        self.trigger_mode.put(1)  # TODO: Should we really change this?
        self.total_points.put(1)
        unstaged_list += self.ext_trigger_device.unstage()
        return unstaged_list


ge_detector = GeDetector('XF:08IDB-ES{GE-Det:1}', name='ge_detector')
