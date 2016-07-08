import uuid
import os
import time as ttime
from ophyd import (ProsilicaDetector, SingleTrigger, Component as Cpt,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin)
from ophyd.areadetector.base import ADComponent as ADCpt, EpicsSignalWithRBV
from ophyd import DeviceStatus, set_and_wait
from bluesky.examples import NullStatus
import filestore.api as fs
#fs.api.register_handler('PIZZABOX_FILE', PizzaBoxHandler, overwrite=True)

class BPM(ProsilicaDetector, SingleTrigger):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
    stats2 = Cpt(StatsPlugin, 'Stats2:')
    # Dan Allan guessed about the nature of these signals. Fix them if you need them.
    ins = Cpt(EpicsSignal, 'Cmd:In-Cmd')
    ret = Cpt(EpicsSignal, 'Cmd:Out-Cmd')
    counts = Cpt(EpicsSignal, 'Pos:Counts')
    switch_insert = Cpt(EpicsSignalRO, 'Sw:InLim-Sts')
    switch_retract = Cpt(EpicsSignalRO, 'Sw:OutLim-Sts')

    def insert(self):
        self.ins.put(1)

    def retract(self):
        self.ret.put(1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.clear()  # default stage sigs do not apply

bpm_fm = BPM('XF:08IDA-BI{BPM:FM}', name='bpm_fm')
bpm_cm = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_cm')
bpm_bt1 = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_bt1')
bpm_bt2 = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_bt2')

for bpm in [bpm_fm, bpm_cm, bpm_bt1, bpm_bt2]:
    bpm.read_attrs = ['stats1']
    bpm.stats1.read_attrs = ['total', 'centroid']

tc_mask2_4 = EpicsSignal('XF:08IDA-OP{Mir:2-CM}T:Msk2_4-I',name='tc_mask2_4')
tc_mask2_3 = EpicsSignal('XF:08IDA-OP{Mir:2-CM}T:Msk2_3-I',name='tc_mask2_3')

class Encoder(Device):
    """This class defines components but does not implement actual reading.

    See EncoderFS and EncoderParser"""
    pos_I = Cpt(EpicsSignal, '}Cnt:Pos-I')
    sec_array = Cpt(EpicsSignal, '}T:sec_Bin_')
    nsec_array = Cpt(EpicsSignal, '}T:nsec_Bin_')
    pos_array = Cpt(EpicsSignal, '}Cnt:Pos_Bin_')
    index_array = Cpt(EpicsSignal, '}Cnt:Index_Bin_')
    data_array = Cpt(EpicsSignal, '}Data_Bin_')
    # The '$' in the PV allows us to write 40 chars instead of 20.
    filepath = Cpt(EpicsSignal, '}ID:File.VAL$', string=True)

    filter_dy = Cpt(EpicsSignal, '}Fltr:dY-SP')
    filter_dt = Cpt(EpicsSignal, '}Fltr:dT-SP')
    reset_counts = Cpt(EpicsSignal, '}Rst-Cmd')
    scan_read = False

    ignore_rb = Cpt(EpicsSignal, '}Ignore-RB')
    ignore_sel = Cpt(EpicsSignal, '}Ignore-Sel')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready_to_collect = False
        if self.connected:
            self.ignore_sel.put(1)
            self.filter_dt.put(10000)
            


class EncoderFS(Encoder):
    "Encoder Device, when read, returns references to data in filestore."

    def stage(self):
        "Set the filename and record it in a 'resource' document in the filestore database."

        if self.scan_read: # Bruno's test
            print(self.name, 'stage')
            DIRECTORY = '/GPFS/xf08id/pizza_box_data'
            filename = str(uuid.uuid4())[:8]
            full_path = os.path.join(DIRECTORY, filename)
            if len(full_path) > 40:
                raise RuntimeError("Stupidly, EPICS limits the file path to 80 characters. "
                               "Choose a different DIRECTORY with a shorter path. (I know....)")
            self.filepath.put(full_path)
            self.resource_uid = fs.insert_resource('PIZZABOX_FILE', full_path)
            self._full_path = full_path  # stash for future reference

            self._ready_to_collect = True # Bruno's test
            set_and_wait(self.ignore_sel, 0) # Part of Bruno's test

        super().stage()

# Bruno's test:
    def unstage(self):
        "set the device to the previous state"
        if self.scan_read:
            print(self.name, 'unstage')
            self._ready_to_collect = False
            set_and_wait(self.ignore_sel, 1)
        super().unstage()

    def kickoff(self):
        print('kickoff', self.name)
        self._ready_to_collect = True
        "Start writing data into the file."
        
        set_and_wait(self.ignore_sel, 0)

        # Return a 'status object' that immediately reports we are 'done' ---
        # ready to collect at any time.
        return NullStatus()

    def complete(self):
        if not self._ready_to_collect:
            raise RuntimeError("must called kickoff() method before calling complete()")
        # Stop adding new data to the file.
        set_and_wait(self.ignore_sel, 1)
        return NullStatus()

    def collect(self):
        """
        Record a 'datum' document in the filestore database for each encoder.

        Return a dictionary with references to these documents.
        """
        print('collect', self.name)
        self._ready_to_collect = False

        now = ttime.time()
        datum_uid = str(uuid.uuid4())
        data = {self.name: datum_uid}
        fs.insert_datum(self.resource_uid, datum_uid, {'line_num': 0})
        yield {'data': data, 'timestamps': {key: now for key in data}, 'time': now}

        # Create an Event document and a datum record in filestore for each line
        # in the text file.
#        now = ttime.time()
#        ttime.sleep(1)  # wait for file to be written by pizza box
#        with open(self._full_path, 'r') as f:
#            linecount = len(list(f))
#        for line_num in range(linecount):
#            datum_uid = str(uuid.uuid4())
#            data = {self.name: datum_uid}
#            fs.insert_datum(self.resource_uid, datum_uid, {'line_num': line_num})
#            yield {'data': data, 'timestamps': {key: now for key in data}, 'time': now}

    def describe_collect(self):
        # TODO Return correct shape (array dims)
        now = ttime.time()
        return {self.name: {self.name:
                     {'source': 'pizzabox-file', 'external': 'FILESTORE:', 'shape': [5,],
                      'dtype': 'array'}}}




class PizzaBoxFS(Device):
    ts_sec = Cpt(EpicsSignal, '}T:sec-I')
    internal_ts_sel = Cpt(EpicsSignal, '}T:Internal-Sel')
    # internal_ts_rb = Cpt(EpicsSignal, '}T:Internal-RB')

    enc1 = Cpt(EncoderFS, ':1')
    enc2 = Cpt(EncoderFS, ':2')
    enc3 = Cpt(EncoderFS, ':3')
    enc4 = Cpt(EncoderFS, ':4')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # must use internal timestamps or no bytes are written
        # self.stage_sigs[self.internal_ts_sel] = 1

    def kickoff(self):
        "Call encoder.kickoff() for every encoder."
        for attr_name in ['enc1', 'enc2', 'enc3', 'enc4']:
            status = getattr(self, attr_name).kickoff()
            print("Eli's test", self.attr_name)
        # it's fine to just return one of the status objects
        return status

    def collect(self):
        "Call encoder.collect() for every encoder."
        # Stop writing data to the file in all encoders.
        for attr_name in ['enc1', 'enc2', 'enc3', 'enc4']:
            set_and_wait(getattr(self, attr_name).ignore_sel, 1)
        # Now collect the data accumulated by all encoders.
        for attr_name in ['enc1', 'enc2', 'enc3', 'enc4']:
            yield from getattr(self, attr_name).collect()

 

pb1 = PizzaBoxFS('XF:08IDA-CT{Enc01', name = 'pb1')
pb2 = PizzaBoxFS('XF:08IDA-CT{Enc02', name = 'pb2')
pb5 = PizzaBoxFS('XF:08IDA-CT{Enc05', name = 'pb5')
pb6 = PizzaBoxFS('XF:08IDA-CT{Enc06', name = 'pb6')
pb7 = PizzaBoxFS('XF:08IDA-CT{Enc07', name = 'pb7')
pb9 = PizzaBoxFS('XF:08IDA-CT{Enc09', name = 'pb9')

class Adc(Device):
    file_size = Cpt(EpicsSignal, '}FileSize')
    reset = Cpt(EpicsSignal, '}Rst-Cmd')
    filepath = Cpt(EpicsSignal, '}ID:File.VAL$', string=True)
    sec_array = Cpt(EpicsSignal, '}T:sec_Bin_')
    nsec_array = Cpt(EpicsSignal, '}T:nsec_Bin_')
    #pos_array = Cpt(EpicsSignal, '}Cnt:Pos_Bin_')
    index_array = Cpt(EpicsSignal, '}Cnt:Index_Bin_')
    data_array = Cpt(EpicsSignal, '}Data_Bin_')
    sample_rate = Cpt(EpicsSignal, '}F:Sample-SP')
    volt_I = Cpt(EpicsSignal, '}V-I')

    enable_sel = Cpt(EpicsSignal, '}Ena-Sel')
    enable_rb = Cpt(EpicsSignal, '}Ena-RB')    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready_to_collect = False
        if self.connected:
            self.enable_sel.put(0)
            self.sample_rate.put(5000) # Is 5000 * 10ns a good sample rate?

class AdcFS(Adc):
    "Adc Device, when read, returns references to data in filestore."

    def stage(self):
        "Set the filename and record it in a 'resource' document in the filestore database."
        print(self.name, 'stage')
        DIRECTORY = '/GPFS/xf08id/pizza_box_data' 
        filename = str(uuid.uuid4())[:8]
        full_path = os.path.join(DIRECTORY, filename)
        if len(full_path) > 40:
            raise RuntimeError("Stupidly, EPICS limits the file path to 80 characters. "
                               "Choose a different DIRECTORY with a shorter path. (I know....)")
        self.filepath.put(full_path)
        self.resource_uid = fs.insert_resource('PIZZABOX_FILE', full_path)
        self._full_path = full_path  # stash for future reference

        self._ready_to_collect = True # Bruno's test
        set_and_wait(self.enable_sel, 1) # Part os Bruno's test

        super().stage()

# Bruno's test:
    def unstage(self):
        "set the device to the previous state"
        print(self.name, 'unstage')
        self._ready_to_collect = False
        set_and_wait(self.enable_sel, 0)
        super().unstage()

    def kickoff(self):
        print('kickoff', self.name)
        self._ready_to_collect = True
        "Start writing data into the file."

        set_and_wait(self.enable_sel, 1)

        # Return a 'status object' that immediately reports we are 'done' ---
        # ready to collect at any time.
        return NullStatus()

    def complete(self):
        if not self._ready_to_collect:
            raise RuntimeError("must called kickoff() method before calling complete()")
        # Stop adding new data to the file.
        set_and_wait(self.enable_sel, 0)
        return NullStatus()

    def collect(self):
        """
        Record a 'datum' document in the filestore database for each adc.

        Return a dictionary with references to these documents.
        """
        print('collect', self.name)
        self._ready_to_collect = False

        now = ttime.time()
        datum_uid = str(uuid.uuid4())
        data = {self.name: datum_uid}
        fs.insert_datum(self.resource_uid, datum_uid, {'line_num': 0})
        yield {'data': data, 'timestamps': {key: now for key in data}, 'time': now}

        # Create an Event document and a datum record in filestore for each line
        # in the text file.
#        now = ttime.time()
#        ttime.sleep(1)  # wait for file to be written by pizza box
#        with open(self._full_path, 'r') as f:
#            linecount = len(list(f))
#        for line_num in range(linecount):
#            datum_uid = str(uuid.uuid4())
#            data = {self.name: datum_uid}
#            fs.insert_datum(self.resource_uid, datum_uid, {'line_num': line_num})
#            yield {'data': data, 'timestamps': {key: now for key in data}, 'time': now}

    def describe_collect(self):
        # TODO Return correct shape (array dims)
        now = ttime.time()
        return {self.name: {self.name:
                     {'source': 'pizzabox-file', 'external': 'FILESTORE:', 'shape': [5,],
                      'dtype': 'array'}}}


class PizzaBoxAnalogFS(Device):
    internal_ts_sel = Cpt(EpicsSignal, 'Gen}T:Internal-Sel')

    adc1 = Cpt(AdcFS, 'GP-ADC:1')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # must use internal timestamps or no bytes are written
        # self.stage_sigs[self.internal_ts_sel] = 1
    
    def kickoff(self):
        "Call encoder.kickoff() for every encoder."
        for attr_name in ['adc1']: #, 'adc2', 'adc3', 'adc4']:
            status = getattr(self, attr_name).kickoff()
        # it's fine to just return one of the status objects
        return status

    def collect(self):
        "Call adc.collect() for every encoder."
        # Stop writing data to the file in all encoders.
        for attr_name in ['adc1']: #, 'adc2', 'adc3', 'adc4']:
            set_and_wait(getattr(self, attr_name).enable_sel, 0)
        # Now collect the data accumulated by all encoders.
        for attr_name in ['adc1']: #, 'adc2', 'adc3', 'adc4']:
            yield from getattr(self, attr_name).collect()


pba1 = PizzaBoxAnalogFS('XF:08IDA-CT{', name = 'pba1')

import numpy as np

class PizzaBoxHandler:
    "Read PizzaBox text files using info from filestore."
    def __init__(self, fpath):
        with open(fpath, 'r') as f:
            self.lines = list(f)

    def __call__(self, line_num):
        return [int(val) for val in self.lines[line_num].split()]
        


