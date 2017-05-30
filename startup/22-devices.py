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

    def __init__(self, name):
        self.name = name
        if(pb4.connected):
            self.output = pb4.do3.default_pol
            if(self.output.value == 1):
                self.state = 'closed'
            elif(self.output.value == 0):
                self.state = 'open'
            self.function_call = None
            self.output.subscribe(self.update_state)
        else:
            self.state = 'unknown'

    def subscribe(self, function):
        self.function_call = function

    def unsubscribe(self):
        self.function_call = None
        
    def update_state(self, pvname=None, value=None, char_value=None, **kwargs):
        if(value == 1):
            self.state = 'closed'
        elif(value == 0):
            self.state = 'open'
        if self.function_call is not None:
            self.function_call(pvname=pvname, value=value, char_value=char_value, **kwargs)
        
    def open(self):
        print('Opening {}'.format(self.name))
        self.output.put(0)
        self.state = 'open'
        
    def close(self):
        print('Closing {}'.format(self.name))
        self.output.put(1)
        self.state = 'closed'

    def open_plan(self):
        print('Opening {}'.format(self.name))
        yield from bp.abs_set(self.output, 0, wait=True)
        self.state = 'open'

    def close_plan(self):
        print('Closing {}'.format(self.name))
        yield from bp.abs_set(self.output, 1, wait=True)
        self.state = 'closed'

shutter = Shutter(name = 'SP Shutter')
shutter.shutter_type = 'SP'

class EPS_Shutter(Device):
    state = Cpt(EpicsSignal, 'Pos-Sts')
    cls = Cpt(EpicsSignal, 'Cmd:Cls-Cmd')
    opn = Cpt(EpicsSignal, 'Cmd:Opn-Cmd')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color = 'red'

    def open(self):
        print('Opening {}'.format(self.name))
        self.opn.put(1)

    def close(self):
        print('Closing {}'.format(self.name))
        self.cls.put(1)

shutter_fe = EPS_Shutter('XF:08ID-PPS{Sh:FE}', name = 'FE Shutter')
shutter_fe.shutter_type = 'FE'
shutter_ph = EPS_Shutter('XF:08IDA-PPS{PSh}', name = 'PH Shutter')
shutter_ph.shutter_type = 'PH'
