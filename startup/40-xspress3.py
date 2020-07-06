'''


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

from pathlib import PurePath
from nslsii.detectors.xspress3 import (XspressTrigger, Xspress3Detector,
                                       Xspress3Channel, Xspress3FileStore, logger)
from databroker.assets.handlers import Xspress3HDF5Handler
db.reg.register_handler(Xspress3HDF5Handler.HANDLER_NAME, Xspress3HDF5Handler,
                        overwrite=True)

#from isstools.trajectory.trajectory import trajectory_manager

import bluesky.plans as bp
import bluesky.plan_stubs as bps

import numpy as np
import itertools
import time as ttime
from collections import deque, OrderedDict


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

    def unstage(self):
        """A custom unstage method is needed to avoid these messages:

        Still capturing data .... waiting.
        Still capturing data .... waiting.
        Still capturing data .... waiting.
        Still capturing data .... giving up.
        """
        return super().unstage()


class ISSXspress3Detector(XspressTrigger, Xspress3Detector):
    roi_data = Cpt(PluginBase, 'ROIDATA:')
    channel1 = Cpt(Xspress3Channel, 'C1_', channel_num=1, read_attrs=['rois'])
    channel2 = Cpt(Xspress3Channel, 'C2_', channel_num=2, read_attrs=['rois'])
    channel3 = Cpt(Xspress3Channel, 'C3_', channel_num=3, read_attrs=['rois'])
    channel4 = Cpt(Xspress3Channel, 'C4_', channel_num=4, read_attrs=['rois'])
    # create_dir = Cpt(EpicsSignal, 'HDF5:FileCreateDir')

    hdf5 = Cpt(Xspress3FileStoreFlyable, 'HDF5:',
               read_path_template='/nsls2/xf08id/data/x3test/',
               root='/nsls2/xf08id/data/',
               write_path_template='/home/xspress3/data/',
               )

    def __init__(self, prefix, *, configuration_attrs=None, read_attrs=None,
                 **kwargs):
        if configuration_attrs is None:
            configuration_attrs = ['external_trig', 'total_points',
                                   'spectra_per_point', 'settings',
                                   'rewindable']
        if read_attrs is None:
            read_attrs = ['channel1', 'channel2', 'channel3', 'channel4', 'hdf5']
        super().__init__(prefix, configuration_attrs=configuration_attrs,
                         read_attrs=read_attrs, **kwargs)
        self.set_channels_for_hdf5()
        # self.create_dir.put(-3)

    def stop(self):
        ret = super().stop()
        self.hdf5.stop()
        return ret

    def stage(self):
        if self.spectra_per_point.get() != 1:
            raise NotImplementedError(
                "multi spectra per point not supported yet")
        ret = super().stage()
        return ret

    def unstage(self):
        self.settings.trigger_mode.put(0)  # 'Software'
        super().unstage()

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

    # Currently only using four channels. Uncomment these to enable more
    # channels:
    # channel5 = C(Xspress3Channel, 'C5_', channel_num=5)
    # channel6 = C(Xspress3Channel, 'C6_', channel_num=6)
    # channel7 = C(Xspress3Channel, 'C7_', channel_num=7)
    # channel8 = C(Xspress3Channel, 'C8_', channel_num=8)


# xs = ISSXspress3Detector('XF:08IDB-ES{Xsp:1}:', name='xs')
# xs.channel2.vis_enabled.put(1)
# xs.channel3.vis_enabled.put(1)
#
# # This is necessary for when the ioc restarts
# # we have to trigger one image for the hdf5 plugin to work correctly
# # else, we get file writing errors
# xs.hdf5.warmup()

# Hints:
for n in [1, 2]:
    getattr(xs, f'channel{n}').rois.roi01.value.kind = 'hinted'

xs.settings.configuration_attrs = ['acquire_period',
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

for n, d in xs.channels.items():
    roi_names = ['roi{:02}'.format(j) for j in [1, 2, 3, 4]]
    d.rois.read_attrs = roi_names
    d.rois.configuration_attrs = roi_names
    for roi_n in roi_names:
        getattr(d.rois, roi_n).value_sum.kind = 'omitted'


def custom_xs_plan(xs_det, num, other_dets=None):
   yield from bps.mv(xs_det.total_points, num)
   all_dets = [xs_det]
   if other_dets is not None:
        all_dets += list(other_dets)
   yield from bp.count(all_dets, num=num)


def xs_list_scan(det, energies):
    energies = list(energies)
    yield from bps.mv(det.total_points, len(energies))
    yield from bp.list_scan([det], hhm.energy, energies)


# energies = np.arange(8959, 9070, 0.4)
# RE(xs_list_scan(xs, energies=energies))
'''