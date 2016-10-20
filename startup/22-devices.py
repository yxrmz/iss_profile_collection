import uuid
from collections import namedtuple
import os
import time as ttime
from ophyd import (ProsilicaDetector, SingleTrigger, Component as Cpt,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin, ROIPlugin,
                   DeviceStatus)
from ophyd.areadetector.base import ADComponent as ADCpt, EpicsSignalWithRBV
from ophyd import DeviceStatus, set_and_wait
from bluesky.examples import NullStatus
import filestore.api as fs

class Shutter():
    def __init__(self):
        if(pb4.do3.default_pol.value == 1):
            self.state = 'closed'
        elif(pb4.do3.default_pol.value == 0):
            self.state = 'open'
        
    def open(self):
        print('Opening shutter...')
        pb4.do3.default_pol.put(0)
        self.state = 'open'
        
    def close(self):
        print('Closing shutter...')
        pb4.do3.default_pol.put(1)
        self.state = 'closed'

    def open_plan(self):
        print('Opening shutter...')
        yield from bp.abs_set(pb4.do3.default_pol, 0, wait=True)
        self.state = 'open'

    def close_plan(self):
        print('Closing shutter...')
        yield from bp.abs_set(pb4.do3.default_pol, 1, wait=True)
        self.state = 'closed'

shutter = Shutter()
