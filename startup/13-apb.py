import time as ttime

from ophyd import Component as Cpt, Device, EpicsSignal, Kind
from ophyd.status import SubscriptionStatus


class AnalogPizzaBox(Device):
    acquire = Cpt(EpicsSignal, 'FA:SoftTrig-SP', kind=Kind.omitted)
    busy = Cpt(EpicsSignal, 'FA:Busy-I', kind=Kind.omitted)

    ch1_mean = Cpt(EpicsSignal, 'FA:Ch1:Mean-I', kind=Kind.hinted)
    ch2_mean = Cpt(EpicsSignal, 'FA:Ch2:Mean-I', kind=Kind.hinted)
    ch3_mean = Cpt(EpicsSignal, 'FA:Ch3:Mean-I', kind=Kind.hinted)
    ch4_mean = Cpt(EpicsSignal, 'FA:Ch4:Mean-I', kind=Kind.hinted)
    ch5_mean = Cpt(EpicsSignal, 'FA:Ch5:Mean-I', kind=Kind.hinted)
    ch6_mean = Cpt(EpicsSignal, 'FA:Ch6:Mean-I', kind=Kind.hinted)

    ch7_mean = Cpt(EpicsSignal, 'FA:Ch7:Mean-I', kind=Kind.hinted)
    ch8_mean = Cpt(EpicsSignal, 'FA:Ch8:Mean-I', kind=Kind.hinted)
    data_rate = Cpt(EpicsSignal, 'FA:Rate-I')
    divide = Cpt(EpicsSignal, 'FA:Divide-SP')
    sample_len = Cpt(EpicsSignal, 'FA:Samples-SP')
    wf_len = Cpt(EpicsSignal, 'FA:Wfm:Length-SP')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capturing = None
        self._ready_to_collect = False

    def trigger(self):
        def callback(value, old_value, **kwargs):
            #print(f'{ttime.time()} {old_value} ---> {value}')
            if self._capturing and int(round(old_value)) == 1 and int(round(value)) == 0:
                self._capturing = False
                return True
            else:
                self._capturing = True
                return False

        status = SubscriptionStatus(self.busy, callback)
        self.acquire.set(1)
        return status


adaq_pb_step = AnalogPizzaBox(prefix="XF:08IDB-CT{PBA:1}:", name="adaq_pb_step")
