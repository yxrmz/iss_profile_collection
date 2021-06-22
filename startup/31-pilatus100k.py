from ophyd import (Component as Cpt, Device,
                   EpicsSignal, ROIPlugin, OverlayPlugin,
                   Signal, HDF5Plugin)
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


class TIFFPluginWithFileStore(TIFFPlugin, FileStoreTIFFIterativeWrite):
    ...

class HDF5PluginWithFileStore(HDF5Plugin, FileStoreHDF5IterativeWrite):
    """Add this as a component to detectors that write HDF5s."""
    def get_frames_per_point(self):
        if not self.parent.is_flying:
            return self.parent.cam.num_images.get()
        else:
            return 1

class TIFFPluginEnsuredOff(TIFFPlugin):
    """Add this as a component to detectors that do not write TIFFs."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([('auto_save', 'No')])


# Making ROIStatPlugin that is actually useful
class ROIStatPlugin(ROIStatPlugin_V34):
    roi1_minx = Cpt(SignalWithRBV, '1:MinX', kind='normal')
    roi2_minx = Cpt(SignalWithRBV, '2:MinX', kind='normal')
    roi3_minx = Cpt(SignalWithRBV, '3:MinX', kind='normal')
    roi4_minx = Cpt(SignalWithRBV, '4:MinX', kind='normal')

    roi1_miny = Cpt(SignalWithRBV, '1:MinY', kind='normal')
    roi2_miny = Cpt(SignalWithRBV, '2:MinY', kind='normal')
    roi3_miny = Cpt(SignalWithRBV, '3:MinY', kind='normal')
    roi4_miny = Cpt(SignalWithRBV, '4:MinY', kind='normal')

    roi1_sizex = Cpt(SignalWithRBV, '1:SizeX', kind='normal')
    roi2_sizex = Cpt(SignalWithRBV, '2:SizeX', kind='normal')
    roi3_sizex = Cpt(SignalWithRBV, '3:SizeX', kind='normal')
    roi4_sizex = Cpt(SignalWithRBV, '4:SizeX', kind='normal')

    roi1_sizey = Cpt(SignalWithRBV, '1:SizeY', kind='normal')
    roi2_sizey = Cpt(SignalWithRBV, '2:SizeY', kind='normal')
    roi3_sizey = Cpt(SignalWithRBV, '3:SizeY', kind='normal')
    roi4_sizey = Cpt(SignalWithRBV, '4:SizeY', kind='normal')

    # for i in range(1,4):
    #     _attr = f'roi{i}'
    #     _attr_min_x = f'min_x'
    #     _attr_min_y = f'min_y'
    #     _pv_min_x = f'{i}:MinX'
    #     _pv_min_y = f'{i}:MinY'
    #     _attr_size_x = f'size_x'
    #     _attr_size_y = f'size_y'
    #     _pv_size_x = f'{i}:SizeX'
    #     _pv_size_y = f'{i}:SizeY'
    #
    #     _attr_instance = DDC_SignalWithRBV(
    #         (_attr_min_x, _pv_min_x),
    #         (_attr_min_y, _pv_min_y),
    #         (_attr_size_x, _pv_size_x),
    #         (_attr_size_y, _pv_size_y),
    #         doc='ROI position and size in XY',
    #         kind='normal',
    #     )
    #     vars()[_attr] = _attr_instance

        # _attr = f'stats{i}'
        # _attr_total = f'total'
        # _pv_total = f'{i}:Total_RBV'
        # _attr_max = f'max_value'
        # _pv_max = f'{i}:MaxValue_RBV'
        # _attr_instance = DDC_EpicsSignalRO(
        #     (_attr_total, _pv_total),
        #     (_attr_max, _pv_max),
        #     doc='ROI stats',
        #     kind='normal',
        # )
        # vars()[_attr] = _attr_instance



class PilatusBase(SingleTriggerV33, PilatusDetectorCam):
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')

    stats1 = Cpt(StatsPluginV33, 'Stats1:', read_attrs=['total', 'max_value'])
    stats2 = Cpt(StatsPluginV33, 'Stats2:', read_attrs=['total'])
    stats3 = Cpt(StatsPluginV33, 'Stats3:', read_attrs=['total'])
    stats4 = Cpt(StatsPluginV33, 'Stats4:', read_attrs=['total'])

    roistat = Cpt(ROIStatPlugin, 'ROIStat1:')
    # roistat = Cpt(ROIStatPlugin_V34, 'ROIStat1:')

    over1 = Cpt(OverlayPlugin, 'Over1:')

    readout = 0.0025 # seconds

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_flying = False

    def set_primary_roi(self, num):
        st = f'stats{num}'
        self.read_attrs = [st, 'tiff']
        getattr(self, st).kind = 'hinted'

    def set_exposure_time(self, exp_t):
        self.cam.acquire_time.put(exp_t - self.readout)
        self.cam.acquire_period.put(exp_t)

    def set_num_images(self, num):
        self.cam.num_images.put(num)
        self.tiff.num_capture.put(num)

    def det_next_file(self, n):
        self.cam.file_number.put(n)

    def enforce_roi_match_between_plugins(self):
        for i in range(1,5):
            _attr = getattr(self, f'roi{i}')
            _x = _attr.min_xyz.min_x.get()
            _y = _attr.min_xyz.min_y.get()
            _xs = _attr.size.x.get()
            _ys = _attr.size.y.get()

            getattr(self.roistat, f'roi{i}_minx').set(_x)
            getattr(self.roistat, f'roi{i}_miny').set(_y)
            getattr(self.roistat, f'roi{i}_sizex').set(_xs)
            getattr(self.roistat, f'roi{i}_sizey').set(_ys)


    @property
    def is_flying(self):
        return self._is_flying

    @is_flying.setter
    def is_flying(self, is_flying):
        self._is_flying = is_flying




class PilatusTIFF(PilatusBase):
    tiff = Cpt(TIFFPluginWithFileStore,
               suffix="TIFF1:",
               # write_path_template="/GPFS/xf12id1/data/PLACEHOLDER",  # override this on instances using instance.tiff.write_file_path
               # write_path_template="/home/det/PilatusData/",
               root='/',
               write_path_template='/nsls2/xf08id/data/pil100k/%Y/%m/%d',
               # root='/nsls2/xf08id/data/',
               )





pil100k = PilatusTIFF("XF:08IDB-ES{Det:PIL1}:", name="pil100k")  # , detector_id="SAXS")
pil100k.set_primary_roi(1)

class PilatusHDF5(PilatusBase):
    hdf5 = Cpt(HDF5PluginWithFileStore,
               suffix='HDF1:',
               root='/',
               write_path_template='/nsls2/xf08id/data/pil100k/%Y/%m/%d',
               )

    def stage(self, *args, **kwargs):
        self.enforce_roi_match_between_plugins()
        super().stage(*args, **kwargs)



pil100k_hdf5 = PilatusHDF5("XF:08IDB-ES{Det:PIL1}:", name="pil100k_hdf5")  # , detector_id="SAXS")


pil100k_hdf5.stats1.kind = 'hinted'
pil100k_hdf5.stats1.total.kind = 'hinted'
pil100k_hdf5.stats2.kind = 'hinted'
pil100k_hdf5.stats2.total.kind = 'hinted'
pil100k_hdf5.stats3.kind = 'hinted'
pil100k_hdf5.stats3.total.kind = 'hinted'
pil100k_hdf5.stats4.kind = 'hinted'
pil100k_hdf5.stats4.total.kind = 'hinted'
pil100k_hdf5.cam.ensure_nonblocking()



# pil100k.tiff.write_path_template = '/nsls2/xf08id/data/pil100k/%Y/%m/%d'
# pil100k.tiff.read_path_template = '/nsls2/xf08id/data/pil100k/%Y/%m/%d'

# pil100k.tiff.write_path_template = '/home/det/PilatusData/'
# pil100k.tiff.read_path_template = '/home/xf08id/pilatusTest/'

# pil100kroi1 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats1:Total_RBV', name='pil100kroi1')
# pil100kroi2 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats2:Total_RBV', name='pil100kroi2')
# pil100kroi3 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats3:Total_RBV', name='pil100kroi3')
# pil100kroi4 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats4:Total_RBV', name='pil100kroi4')




class PilatusStreamTIFF(PilatusTIFF):

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
        # acquire_period = 1 / acq_rate
        self.set_exposure_time(1 / acq_rate)
        # acquire_time = acquire_period - self.readout
        # self.cam.acquire_period.put(acquire_period)
        # self.cam.acquire_time.put(acquire_time)

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
        self.set_num_images(1)
        self.cam.array_counter.put(0)


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


pil100k_stream = PilatusStreamTIFF("XF:08IDB-ES{Det:PIL1}:", name="pil100k_stream")






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
#         self.t.start
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




class ISSPilatusTIFFHandler(AreaDetectorTiffHandler):

    def __init__(self, fpath, template, filename, frame_per_point=1):
        super().__init__(fpath, template, filename,
                         frame_per_point=1)


    def __call__(self, *args, frame=None, **kwargs):
        return super().__call__(*args, point_number=frame, **kwargs)


db.reg.register_handler('AD_TIFF',
                         ISSPilatusTIFFHandler, overwrite=True)
