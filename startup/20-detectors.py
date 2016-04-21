from ophyd import (ProsilicaDetector, SingleTrigger, Component as Cpt,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin)
from ophyd.areadetector.base import ADComponent as ADCpt, EpicsSignalWithRBV


class BPM(ProsilicaDetector, SingleTrigger):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
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

bpm_fm = BPM('XF:08IDA-BI{BPM:FM}', name='bpm_fm')
bpm_cm = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_cm')
bpm_bt1 = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_bt1')
bpm_bt2 = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_bt2')

for bpm in [bpm_fm, bpm_cm, bpm_bt1, bpm_bt2]:
    bpm.read_attrs = ['stats1']
    bpm.stats1.read_attrs = ['total', 'centroid']

tc_mask2_4 = EpicsSignal('XF:08IDA-OP{Mir:2-CM}T:Msk2_4-I',name='tc_mask2_4')
tc_mask2_3 = EpicsSignal('XF:08IDA-OP{Mir:2-CM}T:Msk2_3-I',name='tc_mask2_3')

# Trying to get data from pizzabox
#pb1_enc1 = EpicsSignal('XF:08IDA-CT{Enc01:1}Cnt:Pos-I', name = 'pb1_enc1')
#pb1_enc2 = EpicsSignal('XF:08IDA-CT{Enc01:2}Cnt:Pos-I', name = 'pb1_enc2')
#pb1_enc3 = EpicsSignal('XF:08IDA-CT{Enc01:3}Cnt:Pos-I', name = 'pb1_enc3')
#pb1_enc4 = EpicsSignal('XF:08IDA-CT{Enc01:4}Cnt:Pos-I', name = 'pb1_enc4')
#pb1_sec = EpicsSignal('XF:08IDA-CT{Enc01}T:sec-I', name = 'pb1_sec')

#testArray = [tc_mask2_4, tc_mask2_3, pb1_enc1, pb1_enc2, pb1_enc3, pb1_enc4, pb1_sec]

#pb1_enc1_sec_arr = EpicsSignal('XF:08IDA-CT{Enc01:1}T:sec_Bin_', name = 'pb1_enc1_sec_arr')
#pb1_enc1_nsec_arr = EpicsSignal('XF:08IDA-CT{Enc01:1}T:nsec_Bin_', name = 'pb1_enc1_nsec_arr')
#pb1_enc1_pos_arr = EpicsSignal('XF:08IDA-CT{Enc01:1}Cnt:Pos_Bin_', name = 'pb1_enc1_pos_arr')

class PizzaBox(Device):
    enc1_pos_I = Cpt(EpicsSignal, ':1}Cnt:Pos-I')
    enc2_pos_I = Cpt(EpicsSignal, ':2}Cnt:Pos-I')
    enc3_pos_I = Cpt(EpicsSignal, ':3}Cnt:Pos-I')
    enc4_pos_I = Cpt(EpicsSignal, ':4}Cnt:Pos-I')
    ts_sec = Cpt(EpicsSignal, '}T:sec-I')

    enc1_sec_array = Cpt(EpicsSignal, ':1}T:sec_Bin_')
    enc1_nsec_array = Cpt(EpicsSignal, ':1}T:nsec_Bin_')
    enc1_pos_array = Cpt(EpicsSignal, ':1}Cnt:Pos_Bin_')
    enc1_index_array = Cpt(EpicsSignal, ':1}Cnt:Index_Bin_')
    enc1_data_array = Cpt(EpicsSignal, ':1}Data_Bin_')
    enc1_file = Cpt(EpicsSignal, ':1}ID:File')

    enc2_sec_array = Cpt(EpicsSignal, ':2}T:sec_Bin_')
    enc2_nsec_array = Cpt(EpicsSignal, ':2}T:nsec_Bin_')
    enc2_pos_array = Cpt(EpicsSignal, ':2}Cnt:Pos_Bin_')
    enc2_index_array = Cpt(EpicsSignal, ':2}Cnt:Index_Bin_')
    enc2_data_array = Cpt(EpicsSignal, ':2}Data_Bin_')
    enc2_file = Cpt(EpicsSignal, ':2}ID:File')

    enc3_sec_array = Cpt(EpicsSignal, ':3}T:sec_Bin_')
    enc3_nsec_array = Cpt(EpicsSignal, ':3}T:nsec_Bin_')
    enc3_pos_array = Cpt(EpicsSignal, ':3}Cnt:Pos_Bin_')
    enc3_index_array = Cpt(EpicsSignal, ':3}Cnt:Index_Bin_')
    enc3_data_array = Cpt(EpicsSignal, ':3}Data_Bin_')
    enc3_file = Cpt(EpicsSignal, ':3}ID:File')

    enc4_sec_array = Cpt(EpicsSignal, ':4}T:sec_Bin_')
    enc4_nsec_array = Cpt(EpicsSignal, ':4}T:nsec_Bin_')
    enc4_pos_array = Cpt(EpicsSignal, ':4}Cnt:Pos_Bin_')
    enc4_index_array = Cpt(EpicsSignal, ':4}Cnt:Index_Bin_')
    enc4_data_array = Cpt(EpicsSignal, ':4}Data_Bin_')
    enc4_file = Cpt(EpicsSignal, ':4}ID:File')

    ignore_rb = Cpt(EpicsSignal, ':DI}Ignore-RB')
    ignore_sel = Cpt(EpicsSignal, ':DI}Ignore-Sel')

    def ignore(self, value=1):
        self.ignore_sel.put(bool(value))


pb1 = PizzaBox('XF:08IDA-CT{Enc01', name = 'pb1')
pb2 = PizzaBox('XF:08IDA-CT{Enc01', name = 'pb2')

testArray = [tc_mask2_4, tc_mask2_3, pb1.enc1_pos_I, pb1.enc2_pos_I, pb1.enc3_pos_I, pb1.enc4_pos_I, pb1.ts_sec]
