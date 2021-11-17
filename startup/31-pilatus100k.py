from ophyd import (Component as Cpt, Device,
                   EpicsSignal, ROIPlugin, OverlayPlugin,
                   Signal, HDF5Plugin, set_and_wait)
from ophyd.areadetector.plugins import ROIStatPlugin_V34, ROIStatNPlugin_V22

from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite, FileStoreHDF5IterativeWrite
from ophyd.areadetector.cam import PilatusDetectorCam
from ophyd.areadetector.detectors import PilatusDetector
from ophyd.areadetector.base import EpicsSignalWithRBV as SignalWithRBV
from ophyd.areadetector import TIFFPlugin
from ophyd.sim import NullStatus
from nslsii.ad33 import StatsPluginV33
from nslsii.ad33 import SingleTriggerV33
from ophyd.areadetector.base import DDC_SignalWithRBV, DDC_EpicsSignalRO
import itertools
from collections import deque, OrderedDict

print(__file__)
class PilatusDetectorCamV33(PilatusDetectorCam):
    '''This is used to update the Pilatus to AD33.'''

    wait_for_plugins = Cpt(EpicsSignal, 'WaitForPlugins',
                           string=True, kind='config')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs['wait_for_plugins'] = 'Yes'

    def ensure_nonblocking(self):
        self.stage_sigs['wait_for_plugins'] = 'Yes'
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, 'ensure_nonblocking'):
                cpt.ensure_nonblocking()

    file_path = Cpt(SignalWithRBV, 'FilePath', string=True)
    file_name = Cpt(SignalWithRBV, 'FileName', string=True)
    file_template = Cpt(SignalWithRBV, 'FileName', string=True)
    file_number = Cpt(SignalWithRBV, 'FileNumber')


class PilatusDetectorCam(PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, 'cam1:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam.ensure_nonblocking()



class HDF5PluginWithFileStore(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """Add this as a component to detectors that write HDF5s."""
    def get_frames_per_point(self):
        return 1
        # if not self.parent.is_flying:
        #     return self.parent.cam.num_images.get()
        # else:
        #     return 1



# Making ROIStatPlugin that is actually useful
class ISSROIStatPlugin(ROIStatPlugin_V34):
    for i in range(1,5):
        _attr = f'roi{i}'
        _attr_min_x = f'min_x'
        _attr_min_y = f'min_y'
        _pv_min_x = f'{i}:MinX'
        _pv_min_y = f'{i}:MinY'
        _attr_size_x = f'size_x'
        _attr_size_y = f'size_y'
        _pv_size_x = f'{i}:SizeX'
        _pv_size_y = f'{i}:SizeY'

        # this does work:
        vars()[_attr] = DDC_SignalWithRBV(
            (_attr_min_x, _pv_min_x),
            (_attr_min_y, _pv_min_y),
            (_attr_size_x, _pv_size_x),
            (_attr_size_y, _pv_size_y),
            doc='ROI position and size in XY',
            kind='normal',
        )

        _attr = f'stats{i}'
        _attr_total = f'total'
        _pv_total = f'{i}:Total_RBV'
        _attr_max = f'max_value'
        _pv_max = f'{i}:MaxValue_RBV'
        vars()[_attr] = DDC_EpicsSignalRO(
            (_attr_total, _pv_total),
            (_attr_max, _pv_max),
            doc='ROI stats',
            kind='normal',
        )



class PilatusBase(SingleTriggerV33, PilatusDetectorCam):
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')

    stats1 = Cpt(StatsPluginV33, 'Stats1:', read_attrs=['total', 'max_value'])
    stats2 = Cpt(StatsPluginV33, 'Stats2:', read_attrs=['total'])
    stats3 = Cpt(StatsPluginV33, 'Stats3:', read_attrs=['total'])
    stats4 = Cpt(StatsPluginV33, 'Stats4:', read_attrs=['total'])

    roistat = Cpt(ISSROIStatPlugin, 'ROIStat1:')
    # roistat = Cpt(ROIStatPlugin_V34, 'ROIStat1:')

    over1 = Cpt(OverlayPlugin, 'Over1:')

    readout = 0.0025 # seconds; actually it is 0.0023, but we are conservative

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hint_channels()
        # self._is_flying = False

    def hint_channels(self):
        self.stats1.kind = 'hinted'
        self.stats1.total.kind = 'hinted'
        self.stats2.kind = 'hinted'
        self.stats2.total.kind = 'hinted'
        self.stats3.kind = 'hinted'
        self.stats3.total.kind = 'hinted'
        self.stats4.kind = 'hinted'
        self.stats4.total.kind = 'hinted'

    def set_exposure_time(self, exp_t):
        self.cam.acquire_time.put(exp_t - self.readout)
        self.cam.acquire_period.put(exp_t)

    def set_num_images(self, num):
        self.cam.num_images.put(num)
        self.hdf5.num_capture.put(num)

    # def det_next_file(self, n):
    #     self.cam.file_number.put(n)

    def enforce_roi_match_between_plugins(self):
        for i in range(1,5):
            _attr = getattr(self, f'roi{i}')
            _x = _attr.min_xyz.min_x.get()
            _y = _attr.min_xyz.min_y.get()
            _xs = _attr.size.x.get()
            _ys = _attr.size.y.get()
            _attr2 = getattr(self.roistat, f'roi{i}')
            _attr2.min_x.set(_x)
            _attr2.min_y.set(_y)
            _attr2.size_x.set(_xs)
            _attr2.size_y.set(_ys)

    def stage(self):
        self.enforce_roi_match_between_plugins()
        return super().stage()


    # @property
    # def is_flying(self):
    #     return self._is_flying
    #
    # @is_flying.setter
    # def is_flying(self, is_flying):
    #     self._is_flying = is_flying








class PilatusHDF5(PilatusBase):
    hdf5 = Cpt(HDF5PluginWithFileStore,
               suffix='HDF1:',
               root='/',
               write_path_template='/nsls2/xf08id/data/pil100k/%Y/%m/%d')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_primary_roi(1)

    def set_primary_roi(self, num):
        st = f'stats{num}'
        # self.read_attrs = [st, 'tiff']
        self.read_attrs = [st, 'hdf5']
        getattr(self, st).kind = 'hinted'


class PilatusStreamHDF5(PilatusHDF5):

    def __init__(self, *args, ext_trigger_device=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ext_trigger_device = ext_trigger_device
        self._asset_docs_cache = deque()
        self._datum_counter = None

        # self._asset_docs_cache = deque()
        # self._datum_counter = None
        # self._acquire = None
        # self._datum_counter = None

    def prepare_to_fly(self, traj_duration):
        self.acq_rate = self.ext_trigger_device.freq.get()
        self.num_points = int(self.acq_rate * (traj_duration + 1))



    # TODO: change blocking to NO upon staging of this class !!!
    def stage(self):
        staged_list = super().stage()
        self._datum_counter = itertools.count()
        # self.is_flying = True
        self.hdf5._asset_docs_cache[0][1]['spec'] = 'PIL100k_HDF5'  # This is to make the files to go to correct handler
        self.hdf5._asset_docs_cache[0][1]['resource_kwargs'] = {}  # This is to make the files to go to correct handler
        self.set_num_images(self.num_points)
        self.set_exposure_time(1 / self.acq_rate)
        self.cam.array_counter.put(0)
        self.cam.trigger_mode.put(3)
        self.cam.image_mode.put(1)
        staged_list += self.ext_trigger_device.stage()
        return staged_list



        # saving files
        # self.tiff.file_write_mode.put(2)
        # self.hdf5.file_write_mode.put(2)

        # deal with the trigger



        # print('>>>>>>>>>>>>>>>> 4', self.hdf5.full_file_name.get())



    # def trigger(self):
    #     def callback(value, old_value):
    #         return (int(round(old_value)) == 0) and (int(round(value)) == 1)
    #
    #     status = SubscriptionStatus(self.cam.acquire, callback)
    #     # self.tiff.capture.put(1)
    #     # self.hdf5.capture.put(1)
    #     self.cam.acquire.put(1)
    #     return status


    def unstage(self):
        self._datum_counter = None
        unstaged_list = super().unstage()

        # st = self.stream.set(0)
        # self.is_flying = False
        self.cam.trigger_mode.put(0)
        self.cam.image_mode.put(0)
        # self.hdf5.capture.put(0)
        self.set_num_images(1)
        self.set_exposure_time(1)
        # self.cam.array_counter.put(0)
        unstaged_list += self.ext_trigger_device.unstage()
        return unstaged_list

    def kickoff(self):
        set_and_wait(self.cam.acquire, 1)
        return self.ext_trigger_device.kickoff()

    def complete(self):
        print(f'{ttime.ctime()} Pilatus100k complete is starting...')
        set_and_wait(self.cam.acquire, 0)
        ext_trigger_status = self.ext_trigger_device.complete()
        for resource in self.hdf5._asset_docs_cache:
            self._asset_docs_cache.append(('resource', resource[1]))
        self._datum_ids = []
        num_frames = self.hdf5.num_captured.get()
        _resource_uid = self.hdf5._resource_uid
        for frame_num in range(num_frames):
            datum_id = '{}/{}'.format(_resource_uid, next(self._datum_counter))
            datum = {'resource': _resource_uid,
                     'datum_kwargs': {'frame': frame_num},
                     # 'datum_kwargs': {},
                     'datum_id': datum_id}
            self._asset_docs_cache.append(('datum', datum))
            self._datum_ids.append(datum_id)
        print(f'{ttime.ctime()} Pilatus100k complete is done.')
        return NullStatus() and ext_trigger_status


    def collect(self):
        print(f'{ttime.ctime()} Pilatus100k collect is starting...')
        num_frames = len(self._datum_ids)

        for frame_num in range(num_frames):
            datum_id = self._datum_ids[frame_num]
            data = {self.name: datum_id}

            ts = ttime.time()

            yield {'data': data,
                   'timestamps': {key: ts for key in data},
                   'time': ts,  # TODO: use the proper timestamps from the mono start and stop times
                   'filled': {key: False for key in data}}
        print(f'{ttime.ctime()} Pilatus100k collect is complete')
        yield from self.ext_trigger_device.collect()

    def describe_collect(self):
        return_dict_pil100k = {self.name:
                           {f'{self.name}': {'source': 'PIL100k_HDF5',
                                             'dtype': 'array',
                                             'shape': [self.cam.num_images.get(),
                                                       #self.settings.array_counter.get()
                                                       self.hdf5.array_size.height.get(),
                                                       self.hdf5.array_size.width.get()],
                                            'filename': f'{self.hdf5.full_file_name.get()}',
                                             'external': 'FILESTORE:'}}}

        return_dict_trig = self.ext_trigger_device.describe_collect()
        return {**return_dict_pil100k, **return_dict_trig}

    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item
        yield from self.ext_trigger_device.collect_asset_docs()




    # def set_expected_number_of_points(self, acq_rate, traj_time):



pil100k = PilatusHDF5("XF:08IDB-ES{Det:PIL1}:", name="pil100k")  # , detector_id="SAXS")
pil100k_stream = PilatusStreamHDF5("XF:08IDB-ES{Det:PIL1}:", name="pil100k_stream", ext_trigger_device=apb_trigger_pil100k)

# pil100k.set_primary_roi(1)


# pil100k.cam.ensure_nonblocking()



def pil_count(acq_time:int = 1, num_frames:int =1, open_shutter:bool=True):
    if open_shutter: yield from shutter.open_plan()
    yield from bp.count([pil100k, apb_ave])
    if open_shutter: yield from shutter.close_plan()



from itertools import product
import pandas as pd
from databroker.assets.handlers import HandlerBase, PilatusCBFHandler, AreaDetectorTiffHandler, Xspress3HDF5Handler





PIL100k_HDF_DATA_KEY = 'entry/instrument/NDAttributes'
class ISSPilatusHDF5Handler(Xspress3HDF5Handler): # Denis: I used Xspress3HDF5Handler as basis since it has all the basic functionality and I more or less understand how it works
    specs = {'PIL100k_HDF5'} | HandlerBase.specs
    HANDLER_NAME = 'PIL100k_HDF5'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, key=PIL100k_HDF_DATA_KEY, **kwargs)
        self._roi_data = None
        self.hdfrois = [f'ROI{i + 1}' for i in range(4)]
        self.chanrois = [f'pil100k_ROI{i + 1}' for i in range(4)]


    def _get_dataset(self):
        if self._dataset is not None:
            return

        _data_columns = [self._file[self._key + f'/_{chanroi}Total'][()] for chanroi in self.hdfrois]
        data_columns = np.vstack(_data_columns).T

        self._roi_data = pd.DataFrame(data_columns, columns=self.chanrois)
        self._dataset = data_columns

    def __call__(self, *args, frame=None,  **kwargs):
        self._get_dataset()
        return_dict_rois = {chanroi: self._roi_data[chanroi][frame] for chanroi in self.chanrois}
        return return_dict_rois
        # return self._roi_data

db.reg.register_handler('PIL100k_HDF5',
                         ISSPilatusHDF5Handler, overwrite=True)