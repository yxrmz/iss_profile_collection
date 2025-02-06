# -*- coding: utf-8 -*-
"""
Created on Wed Jan 22 23:40:18 2025

@author: roman
"""
import logging
logger = logging.getLogger(__name__)
from ophyd import EpicsSignal, Signal, SignalWithRBV, EpicsSignalRO, Kind
from ophyd.device import (BlueskyInterface, Staged)
from ophyd.device import (Device,
                          DynamicDeviceComponent as DDC,
                          Component as Cpt)
from ophyd.areadetector.plugins import PluginBase
from ophyd.areadetector.filestore_mixins import FileStorePluginBase
from ophyd.areadetector.plugins import HDF5Plugin
from ophyd.areadetector import (DetectorBase, CamBase)
import time
from collections import OrderedDict
import h5py



#class Xspress3FileStore(FileStorePluginBase, HDF5Plugin):
class XIAXMAPFileStore(FileStorePluginBase, HDF5Plugin):
    '''XIA XMAP acquisition -> filestore'''
    num_capture_calc = Cpt(EpicsSignal, 'NumCapture_CALC')
    num_capture_calc_disable = Cpt(EpicsSignal, 'NumCapture_CALC.DISA')
    filestore_spec = XIAXMAPHDF5Handler.HANDLER_NAME
#    filestore_spec = Xspress3HDF5Handler.HANDLER_NAME

    def __init__(self, basename, *, config_time=0.5,
                 mds_key_format='{self.settings.name}_ch{chan}', parent=None,
                 **kwargs):
        super().__init__(basename, parent=parent, **kwargs)
        det = parent
        self.settings = det.settings

        # Use the EpicsSignal file_template from the detector
        self.stage_sigs[self.blocking_callbacks] = 1
        self.stage_sigs[self.enable] = 1
        self.stage_sigs[self.compression] = 'zlib'
        self.stage_sigs[self.file_template] = '%s%s_%6.6d.h5'

        self._filestore_res = None
#        self.channels = list(range(1, len([_ for _ in det.component_names
#                                           if _.startswith('chan')]) + 1))
        self.channels = list(range(1, int(det.num_channels)+1))
        # this was in original code, but I kinda-sorta nuked because
        # it was not needed for SRX and I could not guess what it did
        self._master = None

        self._config_time = config_time
        self.mds_keys = {chan: mds_key_format.format(self=self, chan=chan)
                         for chan in self.channels}

    def stop(self, success=False):
        ret = super().stop(success=success)
        self.capture.put(0)
        return ret

    def kickoff(self):
        # need implementation
        raise NotImplementedError()

    def collect(self):
        # (hxn-specific implementation elsewhere)
        raise NotImplementedError()

    def make_filename(self):
        fn, rp, write_path = super().make_filename()
        if self.parent.make_directories.get():
            makedirs(write_path)
        return fn, rp, write_path

    def unstage(self):
        try:
            i = 0
            # this needs a fail-safe, RE will now hang forever here
            # as we eat all SIGINT to ensure that cleanup happens in
            # orderly manner.
            # If we are here this is a sign that we have not configured the xs3
            # correctly and it is expecting to capture more points than it
            # was triggered to take.
            while self.capture.get() == 1:  # HDF5 plugin .capture
                i += 1
                if (i % 50) == 0:
                    logger.warning('Still capturing data .... waiting.')
                time.sleep(0.1)
                if i > 150:
                    logger.warning('Still capturing data .... giving up.')
                    logger.warning('Check that the XIA XMAP is configured to take the right '
                                   'number of frames '
                                   f'(it is trying to take {self.parent.settings.num_images.get()})')
                    self.capture.put(0)
                    break

        except KeyboardInterrupt:
            self.capture.put(0)
            logger.warning('Still capturing data .... interrupted.')

        return super().unstage()

    def generate_datum(self, key, timestamp, datum_kwargs):
        sn, n = next((f'channel{j}', j)  # TODO:
                     for j in self.channels
                     if getattr(self.parent.channels, f'mca{j:1d}').name == key)
        datum_kwargs.update({'frame': self.parent._abs_trigger_count,
                             'channel': int(sn[7:])})  # No idea what's happening here
        self.mds_keys[n] = key
        super().generate_datum(key, timestamp, datum_kwargs)

    def stage(self):
        # if should external trigger
        ext_trig = self.parent.external_trig.get()

        logger.debug('Stopping XIA XMAP acquisition')
        # really force it to stop acquiring
        self.settings.acquire.put(0, wait=True)

        total_points = self.parent.total_points.get()
        if total_points < 1:
            raise RuntimeError("You must set the total points")
#        spec_per_point = self.parent.spectra_per_point.get()
#        total_capture = total_points * spec_per_point

        # stop previous acquisition
        self.stage_sigs[self.settings.acquire] = 0

        # re-order the stage signals and disable the calc record which is
        # interfering with the capture count
        self.stage_sigs.pop(self.num_capture, None)
        self.stage_sigs.pop(self.settings.num_images, None)
        self.stage_sigs[self.num_capture_calc_disable] = 1

        if ext_trig:
            logger.debug('Setting up external triggering')
            self.stage_sigs[self.settings.collection_mode] = 2  # SCA Mapping
            self.stage_sigs[self.settings.trigger_mode] = 0  # Gate
#            self.stage_sigs[self.settings.trigger_mode] = 'TTL Veto Only'
            self.stage_sigs[self.settings.num_images] = total_points
        else:
            logger.debug('Setting up internal triggering')
            # self.settings.trigger_mode.put('Internal')
            # self.settings.num_images.put(1)
            self.stage_sigs[self.settings.collection_mode] = 0  # MCA Spectra
            self.stage_sigs[self.settings.preset_mode] = 1  # Real Time
#            self.stage_sigs[self.settings.trigger_mode] = 'Internal'
#            self.stage_sigs[self.settings.num_images] = spec_per_point

        self.stage_sigs[self.auto_save] = 'No'
        logger.debug('Configuring other filestore stuff')

        logger.debug('Making the filename')
        filename, read_path, write_path = self.make_filename()

        logger.debug('Setting up hdf5 plugin: ioc path: %s filename: %s',
                     write_path, filename)

        logger.debug('Erasing old spectra')
        self.settings.erase.put(1, wait=True)

        # this must be set after self.settings.num_images because at the Epics
        # layer  there is a helpful link that sets this equal to that (but
        # not the other way)
        self.stage_sigs[self.num_capture] = total_points

        # actually apply the stage_sigs
        ret = super().stage()

        self._fn = self.file_template.get() % (self._fp,
                                               self.file_name.get(),
                                               self.file_number.get())

        if not self.file_path_exists.get():
            raise IOError("Path {} does not exits on IOC!! Please Check"
                          .format(self.file_path.get()))

        logger.debug('Inserting the filestore resource: %s', self._fn)
        self._generate_resource({})
        self._filestore_res = self._asset_docs_cache[-1][-1]

        # this gets auto turned off at the end
        self.capture.put(1)

        # Xspress3 needs a bit of time to configure itself...
        # this does not play nice with the event loop :/
        time.sleep(self._config_time)

        return ret

    def configure(self, total_points=0, master=None, external_trig=False,
                  **kwargs):
        raise NotImplementedError()

    def describe(self):
        # should this use a better value?
        size = (self.width.get(), )

        spec_desc = {'external': 'FILESTORE:',
                     'dtype': 'array',
                     'shape': size,
                     'source': 'FileStore:'
                     }

        desc = OrderedDict()
        for chan in self.channels:
            key = self.mds_keys[chan]
            desc[key] = spec_desc

        return desc


class XIAXMAPDetectorSettings(CamBase):
#class Xspress3DetectorSettings(CamBase):
    '''Quantum Detectors Xspress3 detector'''

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = []
        if configuration_attrs is None:
            configuration_attrs = ['config_path', 'config_save_path',
                                   ]
        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, **kwargs)

    acquire_period = Cpt(SignalWithRBV,'ACQUIRE_PERIOD')
    gain = Cpt(SignalWithRBV,'GAIN')
    config_path = Cpt(SignalWithRBV, 'CONFIG_PATH', string=True)
    config_save_path = Cpt(SignalWithRBV, 'CONFIG_SAVE_PATH', string=True)
    ctrl_mca_roi = Cpt(SignalWithRBV, 'CTRL_MCA_ROI')
    debounce = Cpt(SignalWithRBV, 'DEBOUNCE')
    run_flags = Cpt(SignalWithRBV, 'RUN_FLAGS')
    invert_f0 = Cpt(SignalWithRBV, 'INVERT_F0')
    invert_veto = Cpt(SignalWithRBV, 'INVERT_VETO')
    image_mode = Cpt(SignalWithRBV, 'IMAGE_MODE')
    manufacturer = Cpt(SignalWithRBV, 'MANUFACTURER')
    model = Cpt(SignalWithRBV, 'MODEL')
    max_spectra = Cpt(SignalWithRBV, 'MAX_SPECTRA')
    num_channels = Cpt(SignalWithRBV, 'NUM_CHANNELS')
    num_exposures = Cpt(SignalWithRBV, 'NUM_EXPOSURES')
    num_frames_config = Cpt(SignalWithRBV, 'NUM_FRAMES_CONFIG')
    xsp_name = Cpt(SignalWithRBV, 'NAME')
    trigger_signal = Cpt(SignalWithRBV, 'TRIGGER')

    start = Cpt(EpicsSignal,'EraseStart')
    acquire = Cpt(EpicsSignal,'Start')  # TODO:
    erase = Cpt(EpicsSignal,'Erase')
    stop_all = Cpt(EpicsSignal,'StopAll')
    acquiring = Cpt(EpicsSignal,'Acquiring')
    preset_mode =  Cpt(EpicsSignal,'PresetMode')
    real_time = Cpt(EpicsSignal,'PresetReal')
    acquire_time = Cpt(EpicsSignal,'PresetReal')
    # MCA Spectra=0, MCA Mapping=1, SCA Mapping=2, List Mapping=3
    collection_mode = Cpt(EpicsSignal,'CollectMode')
    num_images = Cpt(EpicsSignal, 'PixelsPerRun')
    trigger_mode = Cpt(EpicsSignal, 'PixelAdvanceMode')
#    xsp_name = Cpt(EpicsSignal, 'NAME')
#    trigger_signal = Cpt(EpicsSignal, 'TRIGGER')


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


class XIAXMAPDetector(DetectorBase):
#class Xspress3Detector(DetectorBase):
    settings = Cpt(XIAXMAPDetectorSettings, '')

    _channels = DDC(make_channels(range(1, 33)))

    external_trig = Cpt(Signal, value=False,
                        doc='Use external triggering')
    total_points = Cpt(Signal, value=-1,
                       doc='The total number of points to acquire overall')
    make_directories = Cpt(Signal, value=False,
                           doc='Make directories on the DAQ side')
    rewindable = Cpt(Signal, value=False,
                     doc='XIA XMAP cannot safely be rewound in bluesky')  # WTF

    # XF:03IDC-ES{Xsp:1}           C1_   ...
    # channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1)

    data_key = XRF_DATA_KEY

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None,
                 # to remove?
                 file_path='', ioc_file_path='', default_channels=None,
                 channel_prefix=None,
                 roi_sums=False,
                 # to remove?
                 **kwargs):

#        if read_attrs is None:
#            read_attrs = ['channel1', ]

        if configuration_attrs is None:
            configuration_attrs = ['settings']  # Do we need channel1.rois?
#            configuration_attrs = ['channel1.rois', 'settings']

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)

        # get all sub-device instances
#        sub_devices = {attr: getattr(self, attr)
#                       for attr in self._sub_devices}

        # filter those sub-devices, just giving channels
#        channels = {dev.channel_num: dev
#                    for attr, dev in sub_devices.items()
#                    if isinstance(dev, Xspress3Channel)
#                    }
#        
        

        # make an ordered dictionary with the channels in order
#        self._channelsDict = OrderedDict(sorted(channels.items()))
        self._channelsDict = {chn: getattr(self.channels, f"mca{chn:1d}") for chn in range(1, 33)}


    @property
    def channelsDict(self):
        return self._channels

    @property
    def all_rois(self):
        for ch_num, channel in self._channels.items():
            for roi in channel.all_rois:
                yield roi

    @property
    def enabled_rois(self):
        for roi in self.all_rois:
            if roi.enable.get():
                yield roi

    def read_hdf5(self, fn, *, rois=None, max_retries=2):  # TODO:
        pass
        '''Read ROI data from an HDF5 file using the current ROI configuration

        Parameters
        ----------
        fn : str
            HDF5 filename to load
        rois : sequence of Xspress3ROI instances, optional

        '''
#        if rois is None:
#            rois = self.enabled_rois

        num_points = self.settings.num_images.get()
        if isinstance(fn, h5py.File):
            hdf = fn
        else:
            hdf = h5py.File(fn, 'r')

        RoiTuple = Xspress3ROI.get_device_tuple()

        handler = Xspress3HDF5Handler(hdf, key=self.data_key)
        for roi in self.enabled_rois:
            roi_data = handler.get_roi(chan=roi.channel_num,
                                       bin_low=roi.bin_low.get(),
                                       bin_high=roi.bin_high.get(),
                                       max_points=num_points)

            roi_info = RoiTuple(bin_low=roi.bin_low.get(),
                                bin_high=roi.bin_high.get(),
                                ev_low=roi.ev_low.get(),
                                ev_high=roi.ev_high.get(),
                                value=roi_data,
                                value_sum=None,
                                enable=None)

            yield roi.name, roi_info

class XIAXMAPTrigger(BlueskyInterface):  # See existing implementation
    """Base class for trigger mixin classes

    Subclasses must define a method with this signature:

    `acquire_changed(self, value=None, old_value=None, **kwargs)`
    """
    # TODO **
    # count_time = self.settings.acquire_period

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # settings
        self._status = None
        self._acquisition_signal = self.settings.acquire
        self._abs_trigger_count = 0

    def stage(self):
        self._abs_trigger_count = 0
        self._acquisition_signal.subscribe(self._acquire_changed)
        return super().stage()

    def unstage(self):
        ret = super().unstage()
        self._acquisition_signal.clear_sub(self._acquire_changed)
        self._status = None
        return ret

    def _acquire_changed(self, value=None, old_value=None, **kwargs):
        "This is called when the 'acquire' signal changes."
        if self._status is None:
            return
        if (old_value == 1) and (value == 0):
            # Negative-going edge means an acquisition just finished.
            self._status._finished()

    def trigger(self):
        if self._staged != Staged.yes:
            raise RuntimeError("not staged")

        self._status = DeviceStatus(self)
        self._acquisition_signal.put(1, wait=False)
        trigger_time = ttime.time()

        for sn in self.read_attrs:
            if sn.startswith('channel') and '.' not in sn:
                ch = getattr(self, sn)
                self.dispatch(ch.name, trigger_time)

        self._abs_trigger_count += 1
        return self._status


#class Xspress3FileStoreFlyable(Xspress3FileStore):
    
# SEE CURRENT IMPLEMENTATION
class XIAXMAPFileStoreFlyable(XIAXMAPFileStore):
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
        sigs = OrderedDict([  # (self.parent.settings.array_callbacks, 1),
                            (self.parent.settings.trigger_mode, 'Internal'),
                            # just in case the acquisition time is set very long...
                            (self.parent.settings.acquire_time, 1),
                            # (self.capture, 1),
                            (self.parent.settings.acquire, 1)])

        original_vals = {sig: sig.get() for sig in sigs}

        # Remove the hdf5.capture item here to avoid an error as it should reset back to 0 itself
        # del original_vals[self.capture]

        for sig, val in sigs.items():
            ttime.sleep(0.1)  # abundance of caution
            sig.set(val).wait()

        ttime.sleep(2)  # wait for acquisition

        for sig, val in reversed(list(original_vals.items())):
            ttime.sleep(0.1)
            sig.set(val).wait()
        print_to_gui("done")


class ISSXIAXMAPDetector(XIAXMAPTrigger, XIAXMAPDetector):  # For step scans
#class ISSXspress3Detector(XspressTrigger, Xspress3Detector):
#    roi_data = Cpt(PluginBase, 'ROIDATA:')
#    channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
#    channel2 = Cpt(Xspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
#    channel3 = Cpt(Xspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
#    channel4 = Cpt(Xspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
#    # create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')
#
#    mca1_sum = Cpt(EpicsSignal, 'ARRSUM1:ArrayData')
#    mca2_sum = Cpt(EpicsSignal, 'ARRSUM2:ArrayData')
#    mca3_sum = Cpt(EpicsSignal, 'ARRSUM3:ArrayData')
#    mca4_sum = Cpt(EpicsSignal, 'ARRSUM4:ArrayData')
#
#    mca1 = Cpt(EpicsSignal, 'ARR1:ArrayData')
#    mca2 = Cpt(EpicsSignal, 'ARR2:ArrayData')
#    mca3 = Cpt(EpicsSignal, 'ARR3:ArrayData')
#    mca4 = Cpt(EpicsSignal, 'ARR4:ArrayData')

    hdf5 = Cpt(XIAXMAPFileStoreFlyable, 'HDF5:',
               read_path_template=f'{ROOT_PATH}/{RAW_PATH}/xspress3/%Y/%m/%d/',
               root=f'{ROOT_PATH}/{RAW_PATH}/',
               write_path_template=f'{ROOT_PATH}/{RAW_PATH}/xspress3/%Y/%m/%d/',
               )


    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None, **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig',
                                   'total_points',
#                                   'spectra_per_point',
                                   'settings',
                                   'rewindable']
        if read_attrs is None:
#            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5', 'settings.acquire_time']
            read_attrs = ['hdf5', 'settings.acquire_time']

        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.set_channels_for_hdf5()
        # self.create_dir.put(-3)
#        self.spectra_per_point.put(1)
#        self.channel1.rois.roi01.configuration_attrs.append('bin_low')

        self._asset_docs_cache = deque()
        # self._datum_counter = None
        self.warmup()

    # Step-scan interface methods.
    # def stage(self):
    #     staged_list = super().stage()
    #
    #     return staged_list

    # def unstage(self):
    #
    #     return super().unstage()

#    def trigger(self):
#
#        self._status = DeviceStatus(self)
#        self.settings.erase.put(1)
#        # self.settings.erase.put(1)    # this was
#        self._acquisition_signal.put(1, wait=False)
#        trigger_time = ttime.time()
#
#        for sn in self.read_attrs:
#            if sn.startswith('channel') and '.' not in sn:
#                ch = getattr(self, sn)
#                self.dispatch(ch.name, trigger_time)
#
#        self._abs_trigger_count += 1
#        return self._status

    def set_exposure_time(self, new_exp_time):
        self.settings.acquire_time.set(new_exp_time).wait()

    def read_exposure_time(self):
        return self.settings.acquire_time.get()

    def test_exposure(self, acq_time=1, num_images=1):
        # THIS MUST WORK WITH STEP MODE
        _old_acquire_time = self.settings.acquire_time.value
#        _old_num_images = self.settings.num_images.value
        # self.settings.acquire_time.set(acq_time).wait()
        self.set_exposure_time(acq_time)
#        self.settings.num_images.set(num_images).wait()
        self.settings.erase.put(1)
        self._acquisition_signal.put(1, wait=True)
        # self.settings.acquire_time.set(_old_acquire_time).wait()
        self.set_exposure_time(_old_acquire_time)
#        self.settings.num_images.set(_old_num_images).wait()

    def set_channels_for_hdf5(self, channels=list(range(1, 33))):
        """
        Configure which channels' data should be saved in the resulted hdf5 file.
        Parameters
        ----------
        channels: tuple, optional
            the channels to save the data for
        """
        # The number of channel
#        for n in channels:
#            getattr(self, f'channel{n}').rois.read_attrs = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]

        for n in channels:
            getattr(self.channels, f'mca{n:1d}').read_attrs = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]


        self.hdf5.num_extra_dims.put(0)
        self.settings.num_channels.put(len(channels))

    def warmup(self, hdf5_warmup=False):
#        self.channel1.vis_enabled.put(1)
#        self.channel2.vis_enabled.put(1)
#        self.channel3.vis_enabled.put(1)
#        self.channel4.vis_enabled.put(1)
        self.total_points.put(1)
        if hdf5_warmup:
            self.hdf5.warmup()

        # Hints:
        for n in range(1, 5):
            getattr(self, f'channel{n}').rois.roi01.value.kind = 'hinted'

        self.settings.configuration_attrs = ['acquire_period',
                                           'acquire_time',
                                           'gain',
                                           'image_mode',
                                           'manufacturer',
                                           'model',
                                           'num_exposures',
                                           'num_images',
                                           'temperature',
                                           'temperature_actual',
                                           'trigger_mode',
                                           'config_path',
                                           'config_save_path',
                                           'invert_f0',
                                           'invert_veto',
                                           'xsp_name',
                                           'num_channels',
                                           'num_frames_config',
                                           'run_flags',
                                           'trigger_signal']

        for key, channel in self.channels.items():
            roi_names = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]
            channel.rois.read_attrs = roi_names
            channel.rois.configuration_attrs = roi_names
            for roi_n in roi_names:
                getattr(channel.rois, roi_n).value_sum.kind = 'omitted'

    def set_limits_for_roi(self, energy_nom, roi=1, window='auto'):

        for ch_index in range(1, self.num_channels+1):
            if window == 'auto':
                print("USING HARDCODED WINDOW OF 250EV AROUND THE PEAK FOR CHANNEL", ch_index)
                energy = energy_nom
                w = 125
            #     w = _compute_window_for_xs_roi_energy(energy_nom)
            # else:
            #     w = int(window)
            # energy = _convert_xs_energy_nom2act(energy_nom, ch_index)
            ev_low_new = int((energy - w / 2) / 5)  # TODO: divide by bin size?
            ev_high_new = int((energy + w / 2) / 5)

#            roi_obj = getattr(channel.rois, roi)
#            roi_obj = getattr(channel, )
            channel = getattr(self.channels, f"mca{ch_index:1d}")
            if ev_high_new < channel.R0low.get():
                channel.R0low.put(ev_low_new)
                channel.R0high.put(ev_high_new)
            else:
                channel.R0high.put(ev_high_new)
                channel.R0low.put(ev_low_new)
        self.settings.copy_ROI_SCA.put(1)

    def ensure_roi4_covering_total_mca(self, emin=600, emax=40960):
        for channel in self.channelsDict.items():
            channel.R0high.put(emax)
            channel.R0low.put(emin)

    @property
    def roi_metadata(self):
        md = {}
        for ch_index, channel in self.channels.items():
            v = {}
            roi_idx = 1
#            for roi_idx in range(1, 5):
#            roi_str = f'roi{roi_idx:02d}'
            roi_str = f'mca{ch_index:02d}'
#            roi_obj = getattr(channel.rois, roi_str)
            
            v[roi_str] = [channel.R0low.get(), channel.R0high.get()]
            md[f"ch{ch_index:02d}"] = v
        return md

    def read_config_metadata(self):
        md = {'device_name': self.name,
              'roi': self.roi_metadata}
        return md


# def compose_bulk_datum_xs(*, resource_uid, counter, datum_kwargs, validate=True):
#     # print_message_now(datum_kwargs)
#     # any_column, *_ = datum_kwargs
#     # print_message_now(any_column)
#     N = len(datum_kwargs)
#     # print_message_now(N)
#     doc = {'resource': resource_uid,
#            'datum_ids': ['{}/{}'.format(resource_uid, next(counter)) for _ in range(N)],
#            'datum_kwarg_list': datum_kwargs}
#     # if validate:
#     #     schema_validators[DocumentNames.bulk_datum].validate(doc)
#     return doc

class ISSXIAXMAPDetectorStream(ISSXIAXMAPDetector):

    def __init__(self, *args, ext_trigger_device=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ext_trigger_device = ext_trigger_device
        self._datum_counter = None
        self._infer_datum_keys()

    def _infer_datum_keys(self):
        self.datum_keys = []
        for i in range(1, 33): #range(self.hdf5.array_size.height.get()):  # TODO: check hdf5.array_size.height
            # self.datum_keys.append({"name": f"{self.name}",
            #                         "channel": i + 1,
            #                         "type": "spectrum"})
            # self.datum_keys.append({"name": f"{self.name}",
            #                         "channel": i + 1,
            #                         "type": "roi"})
#            self.datum_keys.append({"data_type": "spectrum",
#                                    "channel": i + 1,
#                                    "roi_num" : 0})

#            channel = getattr(self, f"channel{i+1}")
#            for roi_num in range(1, channel.rois.num_rois.get() + 1):  
#            if getattr(channel.rois, f"roi{roi_num:02d}").enable.get() == 1:
#            if getattr(channel.rois, f"roi{roi_num:02d}").enable.get() == 1:  # Only one, always enabled
            self.datum_keys.append({"data_type": "roi",
                                    "channel": i + 1,
                                    "roi_num": 1})

            # self.datum_keys.append(f'{self.name}_ch{i + 1:02d}_roi')

    def format_datum_key(self, input_dict):
        # return f'{input_dict["name"]}_ch{input_dict["channel"]:02d}_{input_dict["type"]}'
#        f'xia_channel{ch:1d}_roi01_value'
#        'xs_channel1_rois_roi01_value'
        output = f'xia_channel{input_dict["channel"]:02d}_{input_dict["data_type"]}{input_dict["roi_num"]:02d}}'
#        if input_dict["data_type"] == 'roi':
#            output += f'{input_dict["roi_num"]:02d}'
        return output

    def prepare_to_fly(self, traj_duration):
        acq_rate = self.ext_trigger_device.freq.get()
        self.num_points = int(acq_rate * (traj_duration + 2))
        self.ext_trigger_device.prepare_to_fly(traj_duration)

    def stage(self):
        self._infer_datum_keys()
        self._datum_counter = itertools.count()
        self.total_points.put(self.num_points)
        self.hdf5.file_write_mode.put(2)
        self.external_trig.put(True)
        self.settings.trigger_mode.put(3)
        staged_list = super().stage()
        staged_list += self.ext_trigger_device.stage()
        return staged_list

    def unstage(self):
        unstaged_list = super().unstage()
        self._datum_counter = None
        self.hdf5.file_write_mode.put(0)
        self.external_trig.put(False)
        self.settings.trigger_mode.put(1)
        self.total_points.put(1)
        unstaged_list += self.ext_trigger_device.unstage()
        return unstaged_list


    def kickoff(self):
        self.settings.acquire.set(1).wait()
        return self.ext_trigger_device.kickoff()

    def complete(self):
        print_to_gui(f'XIA XMAP complete is starting...', add_timestamp=True)

        acquire_status = self.settings.acquire.set(0)  # STOP
        capture_status = self.hdf5.capture.set(0)      # STOP
        (acquire_status and capture_status).wait()


        ext_trigger_status = self.ext_trigger_device.complete()
        for resource in self.hdf5._asset_docs_cache:
            self._asset_docs_cache.append(('resource', resource[1]))

        _resource_uid = self.hdf5._resource_uid
        self._datum_ids = {}

        for datum_key_dict in self.datum_keys:
            datum_key = self.format_datum_key(datum_key_dict)
            datum_id = f'{_resource_uid}/{datum_key}'
            self._datum_ids[datum_key] = datum_id
            doc = {'resource': _resource_uid,
                   'datum_id': datum_id,
                   'datum_kwargs': datum_key_dict}
            self._asset_docs_cache.append(('datum', doc))

        print_to_gui(f'XIA XMAP complete is done.', add_timestamp=True)
        return NullStatus() and ext_trigger_status

    def collect(self):
        print_to_gui(f'XIA XMAP collect is starting...', add_timestamp=True)
        ts = ttime.time()
        yield {'data': self._datum_ids,
               'timestamps': {self.format_datum_key(key_dict): ts for key_dict in self.datum_keys},
               'time': ts,  # TODO: use the proper timestamps from the mono start and stop times
               'filled': {self.format_datum_key(key_dict): False for key_dict in self.datum_keys}}
        print_to_gui(f'XIA XMAP collect is done.', add_timestamp=True)
        yield from self.ext_trigger_device.collect()

    def describe_collect(self):  # TODO: NEEDS TESTING
        xia_spectra_dicts = {}
        for datum_key_dict in self.datum_keys:
            datum_key = self.format_datum_key(datum_key_dict)
            if datum_key_dict['data_type'] == 'spectrum':
                value = {'source': 'XIA',
                         'dtype': 'array',
                         'shape': [self.settings.num_images.get(),
                                   self.hdf5.array_size.width.get()],
                         'dims': ['frames', 'row'],
                         'external': 'FILESTORE:'}
            elif datum_key_dict['data_type'] == 'roi':
                value = {'source': 'XIA',
                         'dtype': 'array',
                         'shape': [self.settings.num_images.get()],
                         'dims': ['frames'],
                         'external': 'FILESTORE:'}
            else:
                raise KeyError(f'data_type={datum_key_dict["data_type"]} not supported')
            xia_spectra_dicts[datum_key] = value

        return_dict_xs = {self.name : xia_spectra_dicts}

        return_dict_trig = self.ext_trigger_device.describe_collect()
        return {**return_dict_xs, **return_dict_trig}

    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        # print_to_gui(f"items = {items}", tag='XS DEBUG')
        self._asset_docs_cache.clear()
        for item in items:
            yield item
        yield from self.ext_trigger_device.collect_asset_docs()

    def read_config_metadata(self):
        md = super().read_config_metadata()
        freq = self.ext_trigger_device.freq.get()
        dc = self.ext_trigger_device.duty_cycle.get()
        md['frame_rate'] = freq
        md['duty_cycle'] = dc
        md['acquire_time'] = 1/freq
        md['exposure_time'] = 1/freq * dc/100
        return md