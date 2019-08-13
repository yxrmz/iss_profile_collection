import time as ttime
import datetime
from ophyd import Device, Component as Cpt, EpicsSignal, Kind, set_and_wait
from ophyd.status import SubscriptionStatus
import paramiko


class Electrometer(Device):
    acquire = Cpt(EpicsSignal, 'FA:SoftTrig-SP', kind=Kind.omitted)
    acquiring = Cpt(EpicsSignal, 'FA:Busy-I', kind=Kind.omitted)

    stream = Cpt(EpicsSignal,'FA:Stream-SP', kind=Kind.omitted)
    streaming = Cpt(EpicsSignal,'FA:Streaming-I', kind=Kind.omitted)

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
        self._acquiring = None
        self.ssh = paramiko.SSHClient()

    def stage(self, *args, **kwargs):
        super().stage(*args, **kwargs)
        st = self.trig_source.set(1)
        return st

    def trigger(self):
        def callback(value, old_value, **kwargs):
            print(f'{ttime.time()} {old_value} ---> {value}')
            if self._acquiring and int(round(old_value)) == 1 and int(round(value)) == 0:
                self._acquiring = False
                return True
            else:
                self._acquiring = True
                return False

        status = SubscriptionStatus(self.acquiring, callback)
        self.acquire.set(1)
        return status

    def collect(self):
        self.ssh.connect('10.8.0.22', username='root')
        with self.ssh.open_sftp() as sftp:
            sftp.get('/home/Save/FAstream.bin',
                     f'/tmp/test-{datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d%H%M%S")}.bin')


class Flyer:
    def __init__(self, det, motor):
        self.det = det
        self.motor = motor
        self._motor_status = None

    def kickoff(self, *args, **kwargs):
        set_and_wait(self.det.trig_source, 1)
        # TODO: handle it on the plan level
        # set_and_wait(self.mono, 'prepare')

        def callback(value, old_value, **kwargs):
            print(f'{ttime.time()} {old_value} ---> {value}')
            if int(round(old_value)) == 0 and int(round(value)) == 1:
                # Now start mono move
                self._motor_status = self.motor.set('start')
                return True
            else:
                return False

        streaming_st = SubscriptionStatus(self.det.streaming, callback)
        self.det.stream.set(1)
        return streaming_st

    def complete(self):
        def callback_det(value, old_value, **kwargs):
            print(f'{ttime.time()} {old_value} ---> {value}')
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                return True
            else:
                return False
        streaming_st = SubscriptionStatus(self.det.streaming, callback_det)

        def callback_motor(*args, **kwargs):
            print(f'{ttime.time()}\nargs: {args}\nkwargs: {kwargs}')
            return False
        self._motor_status.add_callback(callback_motor)

        return streaming_st & self._motor_status

    def describe_collect(self):
        return {}

    def collect(self):
        return self.det.collect()


em1 = Electrometer('PBPM:', name='em1')
for i in [1, 2, 3, 4]:
    getattr(em1, f'ch{i}_current').kind = 'hinted'

flyer = Flyer(det=em1, motor=hhm)

def excecute_trajectory_with_em():
    pass


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
        while em1.acquiring.get():
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