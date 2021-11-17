from ophyd.areadetector import (AreaDetector, PixiradDetectorCam, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin, ROIPlugin, TransformPlugin,
                                OverlayPlugin)
from ophyd.areadetector.plugins import PluginBase
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.device import BlueskyInterface
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing,
                                                 FileStoreTIFF)
from ophyd import Signal, EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.sim import NullStatus  # TODO: remove after complete/collect are defined
from ophyd import Component as Cpt, set_and_wait
from ophyd.status import SubscriptionStatus, DeviceStatus

from pathlib import PurePath
from nslsii.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
                                       Xspress3Channel, Xspress3FileStore, Xspress3ROI, logger)

#from isstools.trajectory.trajectory import trajectory_manager

import bluesky.plans as bp
import bluesky.plan_stubs as bps

import numpy as np
import itertools
import time as ttime
from collections import deque, OrderedDict
from itertools import product
import pandas as pd
from databroker.assets.handlers import HandlerBase, Xspress3HDF5Handler
import warnings


class Xspress3FileStoreFlyable(Xspress3FileStore):
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
        print("warming up the hdf5 plugin...")
        set_and_wait(self.enable, 1)
        sigs = OrderedDict([(self.parent.settings.array_callbacks, 1),
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
            set_and_wait(sig, val)

        ttime.sleep(2)  # wait for acquisition

        for sig, val in reversed(list(original_vals.items())):
            ttime.sleep(0.1)
            set_and_wait(sig, val)
        print("done")

    # def unstage(self):
    #   """A custom unstage method is needed to avoid these messages:
    #
    #   Still capturing data .... waiting.
    #   Still capturing data .... waiting.
    #   Still capturing data .... waiting.
    #   Still capturing data .... giving up.
    #   """
    #   return super().unstage()


# NELM specifies the number of elements that the array will hold NORD is Number
# of Elements Read (at QAS, as of March 25, 2020, .NELM was set to 50000 for
# the PVs below, but .NORD was always returning 1024 elements)
dpb_sec = pb4.di.sec_array
dpb_sec_nelm = EpicsSignalRO(f'{dpb_sec.pvname}.NELM', name='dpb_sec_nelm')

dpb_nsec = pb4.di.nsec_array
dpb_nsec_nelm = EpicsSignalRO(f'{dpb_nsec.pvname}.NELM', name='dpb_nsec_nelm')


class ISSXspress3Detector(XspressTrigger, Xspress3Detector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')
    channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
    channel2 = Cpt(Xspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
    channel3 = Cpt(Xspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
    channel4 = Cpt(Xspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
    # create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    mca1_sum = Cpt(EpicsSignal, 'ARRSUM1:ArrayData')
    mca2_sum = Cpt(EpicsSignal, 'ARRSUM2:ArrayData')
    mca3_sum = Cpt(EpicsSignal, 'ARRSUM3:ArrayData')
    mca4_sum = Cpt(EpicsSignal, 'ARRSUM4:ArrayData')

    mca1 = Cpt(EpicsSignal, 'ARR1:ArrayData')
    mca2 = Cpt(EpicsSignal, 'ARR2:ArrayData')
    mca3 = Cpt(EpicsSignal, 'ARR3:ArrayData')
    mca4 = Cpt(EpicsSignal, 'ARR4:ArrayData')

    hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF5:',
               read_path_template='/nsls2/xf08id/data/xspress3/%Y/%m/%d/',
               root='/nsls2/xf08id/data/',
               write_path_template='/nsls2/xf08id/data/xspress3/%Y/%m/%d/',
               )


    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None, **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'settings',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5', 'settings.acquire_time']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.set_channels_for_hdf5()
        # self.create_dir.put(-3)
        self.spectra_per_point.put(1)
        self.channel1.rois.roi01.configuration_attrs.append('bin_low')

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

    def trigger(self):

        self._status = DeviceStatus(self)
        self.settings.erase.put(1)
        # self.settings.erase.put(1)    # this was
        self._acquisition_signal.put(1, wait=False)
        trigger_time = ttime.time()

        for sn in self.read_attrs:
            if sn.startswith('channel') and '.' not in sn:
                ch = getattr(self, sn)
                self.dispatch(ch.name, trigger_time)

        self._abs_trigger_count += 1
        return self._status

    def set_channels_for_hdf5(self, channels=(1, 2, 3, 4)):
        """
        Configure which channels' data should be saved in the resulted hdf5 file.
        Parameters
        ----------
        channels: tuple, optional
            the channels to save the data for
        """
        # The number of channel
        for n in channels:
            getattr(self, f'channel{n}').rois.read_attrs = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]
        self.hdf5.num_extra_dims.put(0)
        self.settings.num_channels.put(len(channels))

    def warmup(self, hdf5_warmup=False):
        self.channel1.vis_enabled.put(1)
        self.channel2.vis_enabled.put(1)
        self.channel3.vis_enabled.put(1)
        self.channel4.vis_enabled.put(1)
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


class ISSXspress3DetectorStream(ISSXspress3Detector):

    def __init__(self, *args, ext_trigger_device=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ext_trigger_device = ext_trigger_device
        self._datum_counter = None

    def stage(self):
        self._datum_counter = itertools.count()
        self.total_points.put(self.num_points)
        self.hdf5.file_write_mode.put(2)  # put it to Stream |||| IS ALREADY STREAMING
        self.external_trig.put(True)
        self.settings.trigger_mode.put(3) # put the trigger mode to TTL in
        staged_list = super().stage()
        staged_list += self.ext_trigger_device.stage()
        return staged_list

    def unstage(self):
        self._datum_counter = None
        self.hdf5.file_write_mode.put(0)  # put it to Stream |||| IS ALREADY STREAMING
        self.external_trig.put(False)
        self.settings.trigger_mode.put(1)
        self.total_points.put(1)
        unstaged_list = super().unstage()
        unstaged_list += self.ext_trigger_device.unstage()
        return unstaged_list

    def prepare_to_fly(self, traj_duration):
        acq_rate = self.ext_trigger_device.freq.get()
        self.num_points = int(acq_rate * (traj_duration + 1))

    def kickoff(self):
        set_and_wait(self.settings.acquire, 1)
        return self.ext_trigger_device.kickoff()

    def complete(self):
        print(f'{ttime.ctime()} Xspress3 complete is starting...')
        set_and_wait(self.settings.acquire, 0)
        self.ext_trigger_device.complete()
        for resource in self.hdf5._asset_docs_cache:
            self._asset_docs_cache.append(('resource', resource[1]))
        self._datum_ids = []
        num_frames = self.hdf5.num_captured.get()
        _resource_uid = self.hdf5._resource_uid
        for frame_num in range(num_frames):
            datum_id = '{}/{}'.format(_resource_uid, next(self._datum_counter))
            datum = {'resource': _resource_uid,
                     'datum_kwargs': {'frame': frame_num},
                     'datum_id': datum_id}
            self._asset_docs_cache.append(('datum', datum))
            self._datum_ids.append(datum_id)
        print(f'{ttime.ctime()} Xspress3 complete is done.')
        return NullStatus()

    def collect(self):
        print(f'{ttime.ctime()} Xspress3 collect is starting...')
        num_frames = len(self._datum_ids)

        for frame_num in range(num_frames):
            datum_id = self._datum_ids[frame_num]
            data = {self.name: datum_id}

            ts = ttime.time()

            yield {'data': data,
                   'timestamps': {key: ts for key in data},
                   'time': ts,  # TODO: use the proper timestamps from the mono start and stop times
                   'filled': {key: False for key in data}}
        print(f'{ttime.ctime()} Xspress3 collect is complete')
        yield from self.ext_trigger_device.collect()

    # The collect_asset_docs(...) method was removed as it exists on the hdf5 component and should be used there.

    def describe_collect(self):
        return_dict_xs = {self.name:
                           {f'{self.name}': {'source': 'XS',
                                             'dtype': 'array',
                                             'shape': [self.settings.num_images.get(),
                                                       #self.settings.array_counter.get()
                                                       self.hdf5.array_size.height.get(),
                                                       self.hdf5.array_size.width.get()],
                                            'filename': f'{self.hdf5.full_file_name.get()}',
                                             'external': 'FILESTORE:'}}}
        return_dict_trig = self.ext_trigger_device.describe_collect()
        return {**return_dict_xs, **return_dict_trig}



    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item
        yield from self.ext_trigger_device.collect_asset_docs()


xs = ISSXspress3Detector('XF:08IDB-ES{Xsp:1}:', name='xs')
xs_stream = ISSXspress3DetectorStream('XF:08IDB-ES{Xsp:1}:', name='xs_stream', ext_trigger_device=apb_trigger)



class ISSXspress3HDF5Handler(Xspress3HDF5Handler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._roi_data = None
        self._num_channels = None

    def _get_dataset(self): # readpout of the following stuff should be done only once, this is why I redefined _get_dataset method - Denis Leshchev Feb 9, 2021
        # dealing with parent
        super()._get_dataset()

        # finding number of channels
        if self._num_channels is not None:
            return
        print('determening number of channels')
        shape = self.dataset.shape
        if len(shape) != 3:
            raise RuntimeError(f'The ndim of the dataset is not 3, but {len(shape)}')
        self._num_channels = shape[1]

        if self._roi_data is not None:
            return
        print('reading ROI data')
        self.chanrois = [f'CHAN{c}ROI{r}' for c, r in product([1, 2, 3, 4], [1, 2, 3, 4])]
        _data_columns = [self._file['/entry/instrument/detector/NDAttributes'][chanroi][()] for chanroi in
                         self.chanrois]
        data_columns = np.vstack(_data_columns).T
        self._roi_data = pd.DataFrame(data_columns, columns=self.chanrois)

    def __call__(self, *args, frame=None, **kwargs):
            self._get_dataset()
            return_dict = {f'ch_{i+1}' : self._dataset[frame, i, :] for i in range(self._num_channels)}
            return_dict_rois = {chanroi: self._roi_data[chanroi][frame] for chanroi in self.chanrois}
            return {**return_dict, **return_dict_rois}



# heavy-weight file handler
db.reg.register_handler(ISSXspress3HDF5Handler.HANDLER_NAME,
                        ISSXspress3HDF5Handler, overwrite=True)



def xs_count(acq_time:float = 1, num_frames:int =1):

    yield from bps.mv(xs.settings.erase, 0)
    yield from bp.count([xs], acq_time)
