print(ttime.ctime() + ' >>>> ' + __file__)
from ophyd import (Device, Component as Cpt,
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
        elif value == 6:
            string = 'Shutdown'
        # elif value == 6:
        #     string = 'Unscheduled ops'
        elif value == 8:
            string = 'Decay mode'
        else:
            string = 'Unknown'
        return string

    @property
    def status_str(self):
        return self.return_status_string()

    def get_energy_str(self):
        return self.energy_str

nsls_ii=Accelerator('SR', name='nsls_ii')

class FrontEnd(Device):
    slit_top = Cpt(EpicsSignal, '{Slt:12-Ax:Y}xp')
    slit_inb = Cpt(EpicsSignal,'{Slt:12-Ax:X}xp')
    slit_bottom = Cpt(EpicsSignal, '{Slt:12-Ax:Y}xn')
    slit_outb = Cpt(EpicsSignal, '{Slt:12-Ax:X}xn')

    slit_vert_gap = Cpt(EpicsSignal, '{Slt:12-Ax:Y}size')
    slit_vert_pos = Cpt(EpicsSignal, '{Slt:12-Ax:Y}center')
    slit_horiz_gap = Cpt(EpicsSignal, '{Slt:12-Ax:X}size')
    slit_horiz_pos = Cpt(EpicsSignal, '{Slt:12-Ax:X}center')

    sync_horiz = Cpt(EpicsSignal,'{Slt:12-Ax:X}sync.PROC')
    sync_vert = Cpt(EpicsSignal,'{Slt:12-Ax:Y}sync.PROC')

    def sync_slits(self):
        self.sync_horiz.put(1)
        self.sync_vert.put(1)

front_end = FrontEnd('FE:C08A-OP', name= 'front_end')

