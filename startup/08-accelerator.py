from ophyd import (EpicsMotor, Device, Component as Cpt,
                   EpicsSignal)
#import numpy as np


class Accelerator(Device):
    beam_current = Cpt(EpicsSignal, ':OPS-BI{DCCT:1}I:Real-I')
    life_time = Cpt(EpicsSignal, ':OPS-BI{DCCT:1}Lifetime-I')
    status = Cpt(EpicsSignal,'-OPS{}Mode-Sts')

nsls_ii=Accelerator('SR', name='nsls_ii')

