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
        self._acquire = None
        # self._datum_counter = None




    def stage(self, acq_rate, traj_time, *args, **kwargs):
        super().stage(*args, **kwargs)
        # deal with expected number of points
        self.set_expected_number_of_points(acq_rate, traj_time)

        # deal with acquire time
        acquire_period = 1 / acq_rate
        acquire_time = acquire_period - self.readout
        self.cam.acquire_period.put(acquire_period)
        self.cam.acquire_time.put(acquire_time)

        # deal with the trigger
        self.cam.trigger_mode.put(3)
        pil100k.cam.image_mode.put(1)



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
        self.cam.acquire.put(1)
        return status



    def unstage(self, *args, **kwargs):
        # self._datum_counter = None
        # st = self.stream.set(0)
        super().unstage(*args, **kwargs)
        self.cam.trigger_mode.put(0)
        pil100k.cam.image_mode.put(0)




    # def complete(self, *args, **kwargs):
        # def callback_saving(value, old_value, **kwargs):
        #     # print(f'     !!!!! {datetime.now()} callback_saving\n{value} --> {old_value}')
        #     if int(round(old_value)) == 1 and int(round(value)) == 0:
        #         # print(f'     !!!!! {datetime.now()} callback_saving')
        #         return True
        #     else:
        #         return False
        # filebin_st = SubscriptionStatus(self.filebin_status, callback_saving)
        # filetxt_st = SubscriptionStatus(self.filetxt_status, callback_saving)

        # self._datum_ids = []
        # datum_id = '{}/{}'.format(self._resource_uid, next(self._datum_counter))
        # datum = {'resource': self._resource_uid,
        #          'datum_kwargs': {},
        #          'datum_id': datum_id}
        # self._asset_docs_cache.append(('datum', datum))
        # self._datum_ids.append(datum_id)
        # return NullStatus()






    def set_expected_number_of_points(self, acq_rate, traj_time):
        self.set_num_images(int(acq_rate * traj_time * 1.3 ))
        self.cam.array_counter.put(0)

    # def calc_num_of_points(self):
    #     tr = trajectory_manager(hhm)
    #     info = tr.read_info(silent=True)
    #     lut = str(int(hhm.lut_number_rbv.get()))
    #     traj_duration = int(info[lut]['size']) / 16000
    #
    #     acq_rate = 1/self.cam.acquire_period.get()
    #
    #     acq_num_points = traj_duration * acq_rate * 1000 * 1.3
    #     self.num_points = int(round(acq_num_points, ndigits=-3))




pil100k_stream = PilatusStream("XF:08IDB-ES{Det:PIL1}:", name="pil100k")






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
