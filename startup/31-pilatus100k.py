from ophyd import (Component as Cpt, Device,
                   EpicsSignal, ROIPlugin, OverlayPlugin,
                   Signal)

from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd.areadetector.cam import PilatusDetectorCam
from ophyd.areadetector.detectors import PilatusDetector
from ophyd.areadetector.base import EpicsSignalWithRBV as SignalWithRBV
from ophyd.areadetector import TIFFPlugin
from ophyd.sim import NullStatus
from nslsii.ad33 import StatsPluginV33
from nslsii.ad33 import SingleTriggerV33
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


class PilatusDetector(PilatusDetector):
    cam = Cpt(PilatusDetectorCamV33, 'cam1:')


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    ...


class Pilatus(SingleTriggerV33, PilatusDetector):
    tiff = Cpt(TIFFPluginWithFileStore,
               suffix="TIFF1:",
               # write_path_template="/GPFS/xf12id1/data/PLACEHOLDER",  # override this on instances using instance.tiff.write_file_path
               #write_path_template="/home/det/PilatusData/",
               root='/',
               write_path_template="/nsls2/xf08id/data/pil100k/%Y/%m/%d",
               # root='/nsls2/xf08id/data/',
               )

    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')

    stats1 = Cpt(StatsPluginV33, 'Stats1:', read_attrs=['total', 'max_value'])
    stats2 = Cpt(StatsPluginV33, 'Stats2:', read_attrs=['total'])
    stats3 = Cpt(StatsPluginV33, 'Stats3:', read_attrs=['total'])
    stats4 = Cpt(StatsPluginV33, 'Stats4:', read_attrs=['total'])

    over1 = Cpt(OverlayPlugin, 'Over1:')

    readout = 0.0025 # seconds

    def set_primary_roi(self, num):
        st = f'stats{num}'
        self.read_attrs = [st, 'tiff']
        getattr(self, st).kind = 'hinted'

    def set_exposure_time(self, exp_t):
        self.cam.acquire_time.put(exp_t)
        self.cam.acquire_period.put(exp_t + self.readout)

    def set_num_images(self, num):
        self.cam.num_images.put(num)
        self.tiff.num_capture.put(num)

    def det_next_file(self, n):
        self.cam.file_number.put(n)



pil100k = Pilatus("XF:08IDB-ES{Det:PIL1}:", name="pil100k")  # , detector_id="SAXS")
pil100k.set_primary_roi(1)

pil100k.tiff.write_path_template = '/nsls2/xf08id/data/pil100k/%Y/%m/%d'
pil100k.tiff.read_path_template = '/nsls2/xf08id/data/pil100k/%Y/%m/%d'

# pil100k.tiff.write_path_template = '/home/det/PilatusData/'
# pil100k.tiff.read_path_template = '/home/xf08id/pilatusTest/'

pil100kroi1 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats1:Total_RBV', name='pil100kroi1')
pil100kroi2 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats2:Total_RBV', name='pil100kroi2')
pil100kroi3 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats3:Total_RBV', name='pil100kroi3')
pil100kroi4 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats4:Total_RBV', name='pil100kroi4')




class PilatusStream(Pilatus):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._asset_docs_cache = deque()
        self._datum_counter = None
        self._acquire = None
        # self._datum_counter = None



    # TODO: change blocking to NO upon staging of this class !!!
    def stage(self, acq_rate, traj_time, *args, **kwargs):
        super().stage(*args, **kwargs)
        # deal with expected number of points
        self.set_expected_number_of_points(acq_rate, traj_time)

        # deal with acquire time
        acquire_period = 1 / acq_rate
        acquire_time = acquire_period - self.readout
        self.cam.acquire_period.put(acquire_period)
        self.cam.acquire_time.put(acquire_time)

        # saving files
        self.tiff.file_write_mode.put(2)

        # deal with the trigger
        self.cam.trigger_mode.put(3)
        self.cam.image_mode.put(1)

        self._datum_counter = itertools.count()


    def trigger(self):
        def callback(value, old_value, **kwargs):
            # print(f'{ttime.time()} {old_value} ---> {value}')
            if self._acquire and int(round(old_value)) == 1 and int(round(value)) == 0:
                self._acquire = False
                return True
            else:
                self._acquire = True
                return False

        status = SubscriptionStatus(self.cam.acquire, callback)
        self.tiff.capture.put(1)
        self.cam.acquire.put(1)
        return status


    def unstage(self, *args, **kwargs):
        # self._datum_counter = None
        # st = self.stream.set(0)
        super().unstage(*args, **kwargs)
        self.cam.trigger_mode.put(0)
        self.cam.image_mode.put(0)
        self.tiff.file_write_mode.put(0)
        self.tiff.capture.put(0)
        self._datum_counter = None


    def complete(self, *args, **kwargs):
        for resource in self.tiff._asset_docs_cache:
            self._asset_docs_cache.append(('resource', resource[1]))

        self._datum_ids = []

        num_frames = self.tiff.num_captured.get()

        # print(f'\n!!! num_frames: {num_frames}\n')

        for frame_num in range(num_frames):
            datum_id = '{}/{}'.format(self.tiff._resource_uid, next(self._datum_counter))
            datum = {'resource': self.tiff._resource_uid,
                     # 'datum_kwargs': {'frame': frame_num},
                     'datum_kwargs': {'frame': frame_num},
                     'datum_id': datum_id}
            self._asset_docs_cache.append(('datum', datum))
            self._datum_ids.append(datum_id)

        return NullStatus()


    def collect(self):
        num_frames = len(self._datum_ids)

        for frame_num in range(num_frames):
            datum_id = self._datum_ids[frame_num]
            data = {self.name: datum_id}

            ts = ttime.time()

            yield {'data': data,
                   'timestamps': {key: ts for key in data},
                   'time': ts,  # TODO: use the proper timestamps from the mono start and stop times
                   'filled': {key: False for key in data}}


    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item


    def describe_collect(self):
        return_dict = {self.name:
                           {f'{self.name}': {'source': 'pil100k',
                                             'dtype': 'array',
                                             'shape': [self.cam.num_images.get(),
                                                       #self.settings.array_counter.get()
                                                       self.tiff.array_size.height.get(),
                                                       self.tiff.array_size.width.get()],
                                            'filename': f'{self.tiff.full_file_name.get()}',
                                             'external': 'FILESTORE:'}}}
        return return_dict





    def set_expected_number_of_points(self, acq_rate, traj_time):
        n = int(acq_rate * (traj_time + 1 ))
        self.set_num_images(n)
        self.cam.array_counter.put(0)


pil100k_stream = PilatusStream("XF:08IDB-ES{Det:PIL1}:", name="pil100k_stream")






# class FakeDetector(Device):
#     acq_time = Cpt(Signal, value=10)
#
#     _default_configuration_attrs = ('acq_time',)
#     _default_read_attrs = ()
#
#     def trigger(self):
#         st = self.st = DeviceStatus(self)
#
#         from threading import Timer
#
#         self.t = Timer(self.acq_time.get(), st._finished)
#         self.t.start()
#         return st
#
#
# fd = FakeDetector(name='fd')

pil100k.stats1.kind = 'hinted'
pil100k.stats1.total.kind = 'hinted'
pil100k.stats2.kind = 'hinted'
pil100k.stats2.total.kind = 'hinted'
pil100k.stats3.kind = 'hinted'
pil100k.stats3.total.kind = 'hinted'
pil100k.stats4.kind = 'hinted'
pil100k.stats4.total.kind = 'hinted'
pil100k.cam.ensure_nonblocking()


def pil_count(acq_time:int = 1, num_frames:int =1):
    yield from bp.count([pil100k])



from itertools import product
import pandas as pd
from databroker.assets.handlers import HandlerBase, PilatusCBFHandler, AreaDetectorTiffHandler


#
#     # def __init__(self, *args, **kwargs):
#     #     super().__init__(*args, **kwargs)
#     #     self._roi_data = None
#     #     self._num_channels = None
#     #
#     # def _get_dataset(self): # readpout of the following stuff should be done only once, this is why I redefined _get_dataset method - Denis Leshchev Feb 9, 2021
#     #     # dealing with parent
#     #     super()._get_dataset()
#     #
#     #     # finding number of channels
#     #     if self._num_channels is not None:
#     #         return
#     #     print('determening number of channels')
#     #     shape = self.dataset.shape
#     #     if len(shape) != 3:
#     #         raise RuntimeError(f'The ndim of the dataset is not 3, but {len(shape)}')
#     #     self._num_channels = shape[1]
#     #
#     #     if self._roi_data is not None:
#     #         return
#     #     print('reading ROI data')
#     #     self.chanrois = [f'CHAN{c}ROI{r}' for c, r in product([1, 2, 3, 4], [1, 2, 3, 4])]
#     #     _data_columns = [self._file['/entry/instrument/detector/NDAttributes'][chanroi][()] for chanroi in
#     #                      self.chanrois]
#     #     data_columns = np.vstack(_data_columns).T
#     #     self._roi_data = pd.DataFrame(data_columns, columns=self.chanrois)
#
#     def __call__(self, *args, frame=None, **kwargs):
#             self._get_dataset()
#
#             grrr
#             return_dict = {f'ch_{i+1}' : self._dataset[frame, i, :] for i in range(self._num_channels)}
#             return_dict_rois = {chanroi: self._roi_data[chanroi][frame] for chanroi in self.chanrois}
#             return {**return_dict, **return_dict_rois}
#
#

 # class ISSPilatusTIFFHandler(PilatusCBFHandler):


class ISSPilatusTIFFHandler(AreaDetectorTiffHandler):

    def __init__(self, fpath, template, filename, frame_per_point=1):
        super().__init__(fpath, template, filename,
                         frame_per_point=1)


    def __call__(self, *args, frame=None, **kwargs):
        return super().__call__(*args, point_number=frame, **kwargs)


db.reg.register_handler('AD_TIFF',
                         ISSPilatusTIFFHandler, overwrite=True)
