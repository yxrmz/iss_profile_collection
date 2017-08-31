from ophyd import (Component as Cpt,
                   EpicsSignal, Device)
import bluesky.plans as bp


class MFC(Device):
    flow = Cpt(EpicsSignal, '-RB', write_pv='-SP')

gas_he = MFC('XF:08IDB-OP{IC}FLW:He', name='gas_he')
gas_n2 = MFC('XF:08IDB-OP{IC}FLW:N2', name='gas_n2')


class WPS(Device):
    hv300 = Cpt(EpicsSignal, '-HV:u300}V-Sense', write_pv='-HV:u300}V-Set')
    hv301 = Cpt(EpicsSignal, '-HV:u301}V-Sense', write_pv='-HV:u301}V-Set')
    hv302 = Cpt(EpicsSignal, '-HV:u302}V-Sense', write_pv='-HV:u302}V-Set')
    hv303 = Cpt(EpicsSignal, '-HV:u303}V-Sense', write_pv='-HV:u303}V-Set')
    hv304 = Cpt(EpicsSignal, '-HV:u304}V-Sense', write_pv='-HV:u304}V-Set')
    hv305 = Cpt(EpicsSignal, '-HV:u305}V-Sense', write_pv='-HV:u305}V-Set')
    hv306 = Cpt(EpicsSignal, '-HV:u306}V-Sense', write_pv='-HV:u306}V-Set')
    hv307 = Cpt(EpicsSignal, '-HV:u307}V-Sense', write_pv='-HV:u307}V-Set')

    lv0 = Cpt(EpicsSignal, '-LV:u0}V-Sense', write_pv='-LV:u0}V-Set')
    lv1 = Cpt(EpicsSignal, '-LV:u1}V-Sense', write_pv='-LV:u1}V-Set')
    lv2 = Cpt(EpicsSignal, '-LV:u2}V-Sense', write_pv='-LV:u2}V-Set')
    lv3 = Cpt(EpicsSignal, '-LV:u3}V-Sense', write_pv='-LV:u3}V-Set')
    lv4 = Cpt(EpicsSignal, '-LV:u4}V-Sense', write_pv='-LV:u4}V-Set')
    lv5 = Cpt(EpicsSignal, '-LV:u5}V-Sense', write_pv='-LV:u5}V-Set')
    lv6 = Cpt(EpicsSignal, '-LV:u6}V-Sense', write_pv='-LV:u6}V-Set')
    lv7 = Cpt(EpicsSignal, '-LV:u7}V-Sense', write_pv='-LV:u7}V-Set')

wps1 = WPS('XF:08IDB-OP{WPS:01', name='wps1')


class Shutter():

    def __init__(self, name):
        self.name = name
        if pb4.connected:
            self.output = pb4.do3.default_pol
            if self.output.value == 1:
                self.state = 'closed'
            elif self.output.value == 0:
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
        if value == 1:
            self.state = 'closed'
        elif value == 0:
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

    def open_plan(self):
        yield from bp.mv(self.opn, 1)

    def close_plan(self):
        yield from bp.mv(self.cls, 1)

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
