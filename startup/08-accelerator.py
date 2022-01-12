from ophyd import (EpicsMotor, Device, Component as Cpt,
                   EpicsSignal)
#import numpy as np


class Accelerator(Device):
    beam_current = Cpt(EpicsSignal, ':OPS-BI{DCCT:1}I:Real-I')
    life_time = Cpt(EpicsSignal, ':OPS-BI{DCCT:1}Lifetime-I')
    status = Cpt(EpicsSignal,'-OPS{}Mode-Sts')
    energy_str = '3 GeV'

    def return_status_string(self):
        value = self.status.get()
        if value == 0:
            string = 'Beam available'
        elif value == 1:
            string = 'Setup'
        elif value == 2:
            string = 'Accelerator studies'
        elif value == 3:
            string = 'Beam has dumped'
        elif value == 4:
            string = 'Maintenance'
        elif value == 5:
            string = 'Shutdown'
        elif value == 6:
            string = 'Unscheduled ops'
        elif value == 8:
            string = 'Decay mode'
        else:
            string = 'Unknown'
        return string

    @property
    def status_str(self):
        return self.return_status_string()

nsls_ii=Accelerator('SR', name='nsls_ii')

