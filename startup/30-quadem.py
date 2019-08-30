import datetime as dt
import itertools
import os
import time as ttime
import uuid
from collections import deque

import numpy as np
import pandas as pd
import paramiko
from ophyd import Device, Component as Cpt, EpicsSignal, Kind, set_and_wait
from ophyd.sim import NullStatus
from ophyd.status import SubscriptionStatus


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
        self.filename_bin = None
        self.filename_txt = None

        self._asset_docs_cache = deque()
        self._resource_uid = None
        self._datum_counter = None

    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item

    def stage(self, *args, **kwargs):
        file_uid = str(uuid.uuid4())
        filename = f'{ROOT_PATH}/data/electrometer/{dt.datetime.strftime(dt.datetime.now(), "%Y/%m/%d")}/{file_uid}'
        self.filename_bin = f'{filename}.bin'
        self.filename_txt = f'{filename}.txt'

        self._resource_uid = str(uuid.uuid4())
        resource = {'spec': 'ELECTROMETER',
                    'root': ROOT_PATH,  # from 00-startup.py (added by mrakitin for future generations :D)
                    'resource_path': self.filename_bin,
                    'resource_kwargs': {},
                    'path_semantics': os.name,
                    'uid': self._resource_uid}
        self._asset_docs_cache.append(('resource', resource))
        self._datum_counter = itertools.count()

        st = self.trig_source.set(1)
        super().stage(*args, **kwargs)
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

    def complete(self, *args, **kwargs):
        self._datum_ids = []
        datum_id = '{}/{}'.format(self._resource_uid,  next(self._datum_counter))
        datum = {'resource': self._resource_uid,
                 'datum_kwargs': {},
                 'datum_id': datum_id}
        self._asset_docs_cache.append(('datum', datum))
        self._datum_ids.append(datum_id)
        return NullStatus()

    def collect(self):
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        server = '10.8.0.22'
        self.ssh.connect(server, username='root')
        with self.ssh.open_sftp() as sftp:
            print(f'Saving a binary file from {server} to {self.filename_bin}')
            sftp.get('/home/Save/FAstream.bin',  # TODO: make it configurable
                     self.filename_bin)
            print(f'Saving a text   file from {server} to {self.filename_txt}')
            sftp.get('/home/Save/FAstreamSettings.txt',  # TODO: make it configurable
                     self.filename_txt)

        # Copied from 10-detectors.py (class EncoderFS)
        now = ttime.time()
        for datum_id in self._datum_ids:
            data = {self.name: datum_id}
            yield {'data': data,
                   'timestamps': {key: now for key in data}, 'time': now,
                   'filled': {key: False for key in data}}

    def unstage(self, *args, **kwargs):
        self._datum_counter = None
        st = self.stream.set(0)
        super().unstage(*args, **kwargs)
        return st


em1 = Electrometer('PBPM:', name='em1')
for i in [1, 2, 3, 4]:
    getattr(em1, f'ch{i}_current').kind = 'hinted'


class Flyer:
    def __init__(self, det, pbs, motor):
        self.name = f'{det.name}-{"-".join([pb.name for pb in pbs])}-flyer'
        self.parent = None
        self.det = det
        self.pbs = pbs  # a list of passed pizza-boxes
        self.motor = motor
        self._motor_status = None

    def kickoff(self, *args, **kwargs):
        set_and_wait(self.det.trig_source, 1)
        # TODO: handle it on the plan level
        # set_and_wait(self.motor, 'prepare')

        def callback(value, old_value, **kwargs):
            print(f'kickoff: {ttime.time()} {old_value} ---> {value}')
            if int(round(old_value)) == 0 and int(round(value)) == 1:
                # Now start mono move
                self._motor_status = self.motor.set('start')
                return True
            else:
                return False

        streaming_st = SubscriptionStatus(self.det.streaming, callback)
        self.det.stream.set(1)
        self.det.stage()
        for pb in self.pbs:
            pb.stage()
            pb.kickoff()
        return streaming_st

    def complete(self):
        def callback_det(value, old_value, **kwargs):
            print(f'complete: {ttime.time()} {old_value} ---> {value}')
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                return True
            else:
                return False
        streaming_st = SubscriptionStatus(self.det.streaming, callback_det)

        def callback_motor():
            print(f'callback_motor {ttime.time()}')
            self.det.stream.set(0)
            self.det.complete()
            for pb in self.pbs:
                pb.complete()

        self._motor_status.add_callback(callback_motor)

        return streaming_st & self._motor_status

    def describe_collect(self):
        return_dict = {self.det.name:
                        {f'{self.det.name}': {'source': 'electrometer',
                                              'dtype': 'array',
                                              'shape': [-1, -1],
                                              'filename_bin': self.det.filename_bin,
                                              'filename_txt': self.det.filename_txt,
                                              'external': 'FILESTORE:'}}}
        # Also do it for all pizza-boxes
        for pb in self.pbs:
            return_dict[pb.name] = pb.describe_collect()[pb.name]

        return return_dict

    def collect_asset_docs(self):
        yield from self.det.collect_asset_docs()
        for pb in self.pbs:
            yield from pb.collect_asset_docs()

    def collect(self):
        self.det.unstage()
        for pb in self.pbs:
            pb.unstage()

        def collect_all():
            for pb in self.pbs:
                yield from pb.collect()
            yield from self.det.collect()

        return collect_all()

flyer = Flyer(det=em1, pbs=[pb9.enc1], motor=hhm)


class ElectrometerBinFileHandler(HandlerBase):
    "Read electrometer *.bin files"
    def __init__(self, fpath):
        # It's a text config file, which we don't store in the resources yet, parsing for now
        fpath_txt = f'{os.path.splitext(fpath)[0]}.txt'

        with open(fpath_txt, 'r') as fp:
            N = int(fp.readline().split(':')[1])
            Gains = [int(x) for x in fp.readline().split(':')[1].split(',')]
            Offsets = [int(x) for x in fp.readline().split(':')[1].split(',')]
            FAdiv = (fp.readline().split(':')[1])
            fp.readline()
            Ranges = [int(x) for x in fp.readline().split(':')[1].split(',')]
            FArate = float(fp.readline().split(':')[1])

            def Range(val):
                ranges = {1: 1,
                          2: 10,
                          4: 100,
                          8: 1000,
                          16: 100087}
                try:
                    ret = ranges[val]
                except:
                    raise ValueError(f'The value "val" can be one of {ranges.keys()}')
                return ret

            # 1566332720 366808768 -4197857 11013120 00
            X = np.fromfile(fpath, dtype=int)
            print(len(X))
            A = []
            B = []
            C = []
            D = []
            T = []
            Ra = Range(Ranges[0])
            Rb = Range(Ranges[1])
            Rc = Range(Ranges[2])
            Rd = Range(Ranges[3])
            dt = 1.0 / FArate / 1000.0

            for i in range(0, len(X), 4):
                A.append(Ra * ((X[i] / 37.0) - Offsets[0]) / Gains[0])
                B.append(Rb * ((X[i + 1] / 37.0) - Offsets[1]) / Gains[1])
                C.append(Rc * ((X[i + 2] / 37.0) - Offsets[2]) / Gains[2])
                D.append(Rd * ((X[i + 3] / 37.0) - Offsets[3]) / Gains[3])
                T.append(i * dt / 4.0)

        data = np.vstack((np.array(T),
                          np.array(A),
                          np.array(B),
                          np.array(C),
                          np.array(D))).T

        self.df = pd.DataFrame(data=data, columns=['timestamp', 'i0', 'it', 'ir', 'iff'])

    def __call__(self):
        return self.df


db.reg.register_handler('ELECTROMETER',
                        ElectrometerBinFileHandler, overwrite=True)


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