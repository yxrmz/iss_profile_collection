import time as ttime
from ophyd import Device, Component as Cpt, EpicsSignal, Kind
from ophyd.status import SubscriptionStatus


class Electrometer(Device):
    acquire = Cpt(EpicsSignal, 'FA:SoftTrig-SP', kind=Kind.omitted)
    busy = Cpt(EpicsSignal, 'FA:Busy-I', kind=Kind.omitted)
    stream = Cpt(EpicsSignal,'FA:Stream-SP', kind=Kind.omitted)

    ch1_mean = Cpt(EpicsSignal, 'FA:A:Mean-I')
    ch2_mean = Cpt(EpicsSignal, 'FA:B:Mean-I')
    ch3_mean = Cpt(EpicsSignal, 'FA:C:Mean-I')
    ch4_mean = Cpt(EpicsSignal, 'FA:D:Mean-I')

    ch1_current = Cpt(EpicsSignal, 'Current:A-Calc')
    ch2_current = Cpt(EpicsSignal, 'Current:B-Calc')
    ch3_current = Cpt(EpicsSignal, 'Current:C-Calc')
    ch4_current = Cpt(EpicsSignal, 'Current:D-Calc')

    ch1_gain = Cpt(EpicsSignal, 'ADC:A:Gain-SP')
    ch2_gain = Cpt(EpicsSignal, 'ADC:B:Gain-SP')
    ch3_gain = Cpt(EpicsSignal, 'ADC:C:Gain-SP')
    ch4_gain = Cpt(EpicsSignal, 'ADC:D:Gain-SP')

    ch1_offset = Cpt(EpicsSignal, 'ADC:A:Offset-SP')
    ch2_offset = Cpt(EpicsSignal, 'ADC:B:Offset-SP')
    ch3_offset = Cpt(EpicsSignal, 'ADC:C:Offset-SP')
    ch4_offset = Cpt(EpicsSignal, 'ADC:D:Offset-SP')

    trig_source = Cpt(EpicsSignal, 'Machine:Clk-SP')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capturing = None
        self._ready_to_collect = False

    def stage(self, *args, **kwargs):
        self.trig_source.set(1)
        super().stage(*args, **kwargs)

    def trigger(self):
        def callback(value, old_value, **kwargs):
            print(f'{ttime.time()} {old_value} ---> {value}')
            if self._capturing and int(round(old_value)) == 1 and int(round(value)) == 0:
                self._capturing = False
                return True
            else:
                self._capturing = True
                return False

        status = SubscriptionStatus(self.busy, callback)
        self.acquire.set(1)
        return status


    # def trigger(self):
    #     self.acquire.set(1)
    #     time.sleep(0.3)
    #     st = DeviceStatus(self)
    #     while self.busy.get():
    #         time.sleep(0.05)
    #     st._finished()
    #     return st

    def kickoff(self):
        self.stream.set(1)
        self._ready_to_collect = True

    def complete(self):
        if not self._ready_to_collect:
            raise RuntimeError("must called kickoff() method before calling complete()")
        self.stream.set(0)


em1 = Electrometer('PBPM:', name='em1')
for i in [1, 2, 3, 4]:
    getattr(em1, f'ch{i}_current').kind = 'hinted'








def step_scan_with_electrometer(energy_list):

    DATA={}

    export_fp = '/tmp/export.dat'
    if os.path.exists(export_fp):
        os.remove(export_fp)
        with open(export_fp, 'w') as f:
            f.write('# ')

        ch1_gain = em1.ch1_gain.get()
        ch2_gain = em1.ch2_gain.get()
        ch3_gain = em1.ch3_gain.get()
        ch4_gain = em1.ch4_gain.get()

        ch1_offset = em1.ch1_offset.get()
        ch2_offset = em1.ch2_offset.get()
        ch3_offset = em1.ch3_offset.get()
        ch4_offset = em1.ch4_offset.get()

    for energy in energy_list:
        # move to next energy
        print(f'Energy is {energy}')

        em1.acquire.set(1)
        time.sleep(0.3)
        while em1.busy.get(): 
            time.sleep(0.05)

        ch1 = (em1.ch1_mean.get() - ch1_offset) / ch1_gain
        ch2 = (em1.ch2_mean.get() - ch2_offset) / ch2_gain
        ch3 = (em1.ch3_mean.get() - ch3_offset) / ch3_gain
        ch4 = (em1.ch4_mean.get() - ch4_offset) / ch4_gain

        print('Channel 1: {:.8e}'.format(ch1))
        print('Channel 2: {:.8e}'.format(ch2))
        print('Channel 3: {:.8e}'.format(ch3))
        print('Channel 4: {:.8e}'.format(ch4))

        DATA['i0'].append(ch1)













    # stats2 = Cpt(StatsPlugin, 'Stats2:')
    # roi1 = Cpt(ROIPlugin, 'ROI1:')
    # roi2 = Cpt(ROIPlugin, 'ROI2:')
    # counts = Cpt(EpicsSignal, 'Pos:Counts')
    # exp_time = Cpt(EpicsSignal, 'cam1:AcquireTime_RBV', write_pv='cam1:AcquireTime')
    # image_mode = Cpt(EpicsSignal,'cam1:ImageMode')
    # acquire = Cpt(EpicsSignal, 'cam1:Acquire')
    #
    # # Actuator
    # insert = Cpt(EpicsSignal, 'Cmd:In-Cmd')
    # inserted = Cpt(EpicsSignalRO, 'Sw:InLim-Sts')
    #
    # retract = Cpt(EpicsSignal, 'Cmd:Out-Cmd')
    # retracted = Cpt(EpicsSignal, 'Sw:OutLim-Sts')
    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.stage_sigs['cam.image_mode'] = 'Single'
    #     self.polarity = 'pos'
    #     # self._inserting = None
    #     # self._retracting = None
    #
    # def set(self, command):
    #     def callback(value, old_value, **kwargs):
    #         if value == 1:
    #             return True
    #         return False
    #
    #     if command.lower() == 'insert':
    #         status = SubscriptionStatus(self.inserted, callback)
    #         self.insert.set('Insert')
    #         return status
    #
    #     if command.lower() == 'retract':
    #         status = SubscriptionStatus(self.retracted, callback)
    #         self.retract.set('Retract')
    #         return status


'''
from ophyd import QuadEM, Component as Cpt, EpicsSignalWithRBV, Signal, DerivedSignal, EpicsSignal
from ophyd.quadem import QuadEMPort

from numpy import log, exp

#run_report(__file__)

## need to do something like this:
##    caput XF:06BM-BI{EM:1}EM180:Current3:MeanValue_RBV.PREC 7
## to get a sensible reporting precision from the Ix channels


class Nanoize(DerivedSignal):
    def forward(self, value):
        return value * 1e-9 / _locked_dwell_time.dwell_time.readback.value
    def inverse(self, value):
        return value * 1e9 * _locked_dwell_time.dwell_time.readback.value

# class Normalized(DerivedSignal):
#     def forward(self, value):
#         return value * self.parent.current1.mean_value.value
#     def inverse(self, value):
#         return value / self.parent.current1.mean_value.value

# class TransXmu(DerivedSignal):
#     def forward(self, value):
#         return self.parent.current1.mean_value.value / exp(value)
#     def inverse(self, value):
#         arg = self.parent.current1.mean_value.value / value
#         return log(abs(arg))

class ISSQuadEM(QuadEM):
    _default_read_attrs = ['I0',
                           'It',
                           'Ir',
                           'Iy']
    port_name = Cpt(Signal, value='EM180')
    conf = Cpt(QuadEMPort, port_name='EM180')
    em_range  = Cpt(EpicsSignalWithRBV, 'Range', string=True)
    
    current1= Cpt(StatsPlugin, 'Current:A:')
    current2= Cpt(StatsPlugin, 'Current:B:')
    current3= Cpt(StatsPlugin, 'Current:C:')
    current4= Cpt(StatsPlugin, 'Current:D:')
    
    I0 = Cpt(Nanoize, derived_from='current1.mean_value')
    Ir = Cpt(Nanoize, derived_from='current3.mean_value')
    Iy = Cpt(Nanoize, derived_from='current4.mean_value')
    It = Cpt(Nanoize, derived_from='current2.mean_value')
    #lni0it = Cpt(TransXmu,   derived_from='current2.mean_value')

    
    state  = Cpt(EpicsSignal, 'Acquire')
    #  = Cpt(EpicsSignal, 'PREC')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #for c in ['current{}'.format(j) for j in range(1, 5)]:
        #     getattr(self, c).read_attrs = ['mean_value']

        # self.read_attrs = ['current{}'.format(j) for j in range(1, 5)]
        self._acquisition_signal = self.acquire
        self.configuration_attrs = ['integration_time', 'averaging_time','em_range','num_averaged','values_per_read']

    def on(self):
        print('Turning {} on'.format(self.name))
        self.acquire_mode.put(0)
        self.acquire.put(1)

    def off(self):
        print('Turning {} off'.format(self.name))
        self.acquire_mode.put(2)
        self.acquire.put(0)

    def on_plan(self):
        yield from abs_set(self.acquire, 1)
        yield from abs_set(self.acquire_mode, 0)

    def off_plan(self):
        yield from abs_set(self.acquire, 0)
        yield from abs_set(self.acquire_mode, 2)


quadem1 = ISSQuadEM('PBPM:', name='quadem1')

def set_precision(pv, val):
    EpicsSignal(pv.pvname + ".PREC", name='').put(val)

set_precision(quadem1.current1.mean_value, 3)
toss = quadem1.I0.describe()
set_precision(quadem1.current2.mean_value, 3)
toss = quadem1.It.describe()
set_precision(quadem1.current3.mean_value, 3)
toss = quadem1.Ir.describe()
set_precision(quadem1.current4.mean_value, 3)
toss = quadem1.Iy.describe()


quadem1.I0.kind = 'hinted'
quadem1.It.kind = 'hinted'
quadem1.Ir.kind = 'hinted'
quadem1.Iy.kind = 'omitted'      # 'hinted'

quadem1.I0.name = 'I0'
quadem1.It.name = 'It'
quadem1.Ir.name = 'Ir'
quadem1.Iy.name = 'Iy'


#quadem1.current4_mean_value_nano.kind = 'omitted'
'''