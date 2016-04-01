from ophyd import (ProsilicaDetector, SingleTrigger, Component as Cpt,
                   EpicsSignal, EpicsSignalRO, ImagePlugin, StatsPlugin)
from ophyd.areadetector.base import ADComponent as ADCpt, EpicsSignalWithRBV


class BPM(ProsilicaDetector, SingleTrigger):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
    # Dan Allan guessed about the nature of these signals. Fix them if you need them.
    insert = Cpt(EpicsSignal, 'Cmd:In-Cmd')
    retract = Cpt(EpicsSignal, 'Cmd:Out-Cmd')
    counts = Cpt(EpicsSignal, 'Pos:Counts')
    switch_insert = Cpt(EpicsSignalRO, 'Sw:InLim-Sts')
    switch_retract = Cpt(EpicsSignalRO, 'Sw:OutLim-Sts')

fmcam = BPM('XF:08IDA-BI{BPM:FM}', name='fmcam')
cmcam = BPM('XF:08IDA-BI{BPM:CM}', name='cmcam')
bt1 = BPM('XF:08IDA-BI{BPM:CM}', name='bt1')
bt2 = BPM('XF:08IDA-BI{BPM:CM}', name='bt2')

for cam in [fmcam, cmcam, bt1, bt2]:
    cam.read_attrs = ['stats1']
    cam.stats1.read_attrs = ['total', 'centroid']
