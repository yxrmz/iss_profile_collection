import datetime as dt
import itertools
import os
import time as ttime
import uuid
from collections import deque

import numpy as np
import pandas as pd
import paramiko
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, Kind, set_and_wait
from ophyd.sim import NullStatus
from ophyd.status import SubscriptionStatus

from xas.trajectory import trajectory_manager


class AnalogPizzaBoxTrigger(Device):
    acquire = Cpt(EpicsSignal, 'Mode-SP')
    acquiring = Cpt(EpicsSignal, 'Status-I')
    filename = Cpt(EpicsSignal,'Filename-SP')
    filebin_status = Cpt(EpicsSignalRO,'File:Status-I')
    stream = Cpt(EpicsSignal,'Stream:Mode-SP')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._acquiring = None

        self._asset_docs_cache = deque()
        self._resource_uid = None
        self._datum_counter = None


    # Step-scan interface
    def stage(self, *args, **kwargs):
        file_uid = new_uid()
        # self.filename_target = f'{ROOT_PATH}/data/apb/{dt.datetime.strftime(dt.datetime.now(), "%Y/%m/%d")}/{file_uid}'
        # Note: temporary static file name in GPFS, due to the limitation of 40 symbols in the filename field.
        # self.filename = f'{ROOT_PATH}/data/apb/{file_uid[:8]}'
        self.fn = f'{ROOT_PATH}/data/apb/{dt.datetime.strftime(dt.datetime.now(), "%Y/%m/%d")}/{file_uid}.bin'
        self.filename.put(f'{self.fn}')

        self._resource_uid = new_uid()
        resource = {'spec': 'APB_TRIGGER',
                    'root': ROOT_PATH,  # from 00-startup.py (added by mrakitin for future generations :D)
                    'resource_path': f'{self.fn}',
                    'resource_kwargs': {},
                    'path_semantics': os.name,
                    'uid': self._resource_uid}
        self._asset_docs_cache.append(('resource', resource))
        self._datum_counter = itertools.count()
        self.acquire.put(2)
        self.stream.put(1)
        return super().stage(*args, **kwargs)

    # def trigger(self):
    #     def callback(value, old_value, **kwargs):
    #         print(f'{ttime.time()} {old_value} ---> {value}')
    #         if self._acquiring and int(round(old_value)) == 1 and int(round(value)) == 0:
    #             self._acquiring = False
    #             return True
    #         else:
    #             self._acquiring = True
    #             return False
    #
    #     status = SubscriptionStatus(self.acquiring, callback)
    #     self.acquire.set(2)
    #     return status
    #
    def unstage(self, *args, **kwargs):
        self._datum_counter = None
        self.acquire.put(0)
        return super().unstage(*args, **kwargs)


    # # Fly-able interface

    # Not sure if we need it here or in FlyerAPB (see 63-...)
    # def kickoff(self):
    #     status = self.stage()
    #     status &= self.trigger()
    #     return status

    def complete(self, *args, **kwargs):
        def callback_saving(value, old_value, **kwargs):
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                self.acquire.put(0)
                self.stream.put(0)
                return True
            else:
                return False

        filebin_st = SubscriptionStatus(self.filebin_status, callback_saving)
        # filetxt_st = SubscriptionStatus(self.filetxt_status, callback_saving)

        self._datum_ids = []
        datum_id = '{}/{}'.format(self._resource_uid, next(self._datum_counter))
        datum = {'resource': self._resource_uid,
                 'datum_kwargs': {},
                 'datum_id': datum_id}
        self._asset_docs_cache.append(('datum', datum))
        self._datum_ids.append(datum_id)
        return filebin_st #& filetxt_st


    def collect(self):
        # print(f'APB collect is complete {ttime.ctime(ttime.time())}')

        # Copied from 10-detectors.py (class EncoderFS)
        now = ttime.time()
        for datum_id in self._datum_ids:
            data = {self.name: datum_id}
            yield {'data': data,
                   'timestamps': {key: now for key in data}, 'time': now,
                   'filled': {key: False for key in data}}
            # print(f'yield data {ttime.ctime(ttime.time())}')

        # self.unstage()


    def describe_collect(self):
        return_dict = {self.name:
                           {f'{self.name}': {'source': 'APB_TRIGGER',
                                             'dtype': 'array',
                                             'shape': [-1, -1],
                                             'filename': f'{self.fn}',
                                             'external': 'FILESTORE:'}}}
        return return_dict


    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item


    def calc_num_points(self):
        tr = trajectory_manager(hhm)
        info = tr.read_info(silent=True)
        lut = str(int(hhm.lut_number_rbv.get()))
        traj_duration = int(info[lut]['size']) / 16000
        acq_num_points = traj_duration * self.acq_rate.get() * 1000 * 1.3
        self.num_points = int(round(acq_num_points, ndigits=-3))


apb_trigger = AnalogPizzaBoxTrigger(prefix="XF:08IDB-CT{PBA:1}:Pulse:1:", name="apb_trigger")




