from ophyd import (Component as Cpt, Device,
                   EpicsSignal, ROIPlugin, OverlayPlugin,
                   Signal)

from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd.areadetector.cam import PilatusDetectorCam
from ophyd.areadetector.detectors import PilatusDetector
from ophyd.areadetector.base import EpicsSignalWithRBV as SignalWithRBV
from ophyd.areadetector import TIFFPlugin

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
               suffix="Proc1:TIFF:",
               # write_path_template="/GPFS/xf12id1/data/PLACEHOLDER",  # override this on instances using instance.tiff.write_file_path
               write_path_template="/home/det/PilatusData/",
               root='/')

    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')

    stats1 = Cpt(StatsPluginV33, 'Stats1:', read_attrs=['total'])
    stats2 = Cpt(StatsPluginV33, 'Stats2:', read_attrs=['total'])
    stats3 = Cpt(StatsPluginV33, 'Stats3:', read_attrs=['total'])
    stats4 = Cpt(StatsPluginV33, 'Stats4:', read_attrs=['total'])

    over1 = Cpt(OverlayPlugin, 'Over1:')

    def set_primary_roi(self, num):
        st = f'stats{num}'
        self.read_attrs = [st, 'tiff']
        getattr(self, st).kind = 'hinted'


pil100k = Pilatus("XF:08IDB-ES{Det:PIL1}:", name="pil100k")  # , detector_id="SAXS")
pil100k.set_primary_roi(1)

pil100k.tiff.write_path_template = '/home/det/PilatusData/'
pil100k.tiff.read_path_template = '/home/xf08id/pilatusTest/'

pil100kroi1 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats1:Total_RBV', name='pil100kroi1')
pil100kroi2 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats2:Total_RBV', name='pil100kroi2')
pil100kroi3 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats3:Total_RBV', name='pil100kroi3')
pil100kroi4 = EpicsSignal('XF:08IDB-ES{Det:PIL1}:Stats4:Total_RBV', name='pil100kroi4')


def det_exposure_time(exp_t, meas_t=1):
    pil100k.cam.acquire_time.put(exp_t)
    pil100k.cam.acquire_period.put(exp_t + 0.002)
    pil100k.cam.num_images.put(int(meas_t / exp_t))


def det_next_file(n):
    pil100k.cam.file_number.put(n)


class FakeDetector(Device):
    acq_time = Cpt(Signal, value=10)

    _default_configuration_attrs = ('acq_time',)
    _default_read_attrs = ()

    def trigger(self):
        st = self.st = DeviceStatus(self)

        from threading import Timer

        self.t = Timer(self.acq_time.get(), st._finished)
        self.t.start()
        return st


fd = FakeDetector(name='fd')

pil100k.stats1.kind = 'hinted'
pil100k.stats1.total.kind = 'hinted'
pil100k.cam.ensure_nonblocking()
