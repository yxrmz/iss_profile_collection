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
