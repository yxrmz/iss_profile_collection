from ophyd import (EpicsMotor, Device, Component as Cpt, PseudoPositioner, PseudoSingle)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)
import numpy as np


class Mirror(Device):
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')
    roll = Cpt(EpicsMotor, '-Ax:R}Mtr')
    xd = Cpt(EpicsMotor, '-Ax:XD}Mtr')  # downstream
    xu = Cpt(EpicsMotor, '-Ax:XU}Mtr')  # upstream
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    ydi = Cpt(EpicsMotor, '-Ax:YDI}Mtr')  # downstream inboard
    ydo = Cpt(EpicsMotor, '-Ax:YDO}Mtr')  # downstream outboard
    yu = Cpt(EpicsMotor, '-Ax:YU}Mtr')
    yaw = Cpt(EpicsMotor, '-Ax:Yaw}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    
    def home_motors(self):
        self.pitch.move(0)
        self.roll.move(0)
        self.y.move(0)


cm1 = Mirror('XF:08IDA-OP{Mir:1-CM', name='cm1')
cm2 = Mirror('XF:08IDA-OP{Mir:2-CM', name='cm2')
fm = Mirror('XF:08IDA-OP{Mir:FM', name='fm')

h = 20 # mm

def fix_exit_trig_formula(theta):
    return h/(2*np.cos(np.deg2rad(theta)))

def energy2theta(energy):
    return np.rad2deg(np.arcsin(12400/energy/2/3.1356))

class HHM(Device):
    "high heat load monochrometer"
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')
    roll = Cpt(EpicsMotor, '-Ax:R}Mtr')
    theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')  # degrees

class HHM_FixedExit(PseudoPositioner):
    # do not set values to actual theta!
    actual_theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')
    theta = Cpt(PseudoSingle, '')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        return self.RealPosition(actual_theta=-pseudo_pos.theta,
                                 y=fix_exit_trig_formula(-pseudo_pos.theta))

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(theta=-real_pos.actual_theta)

class HHM_Energy(PseudoPositioner):
    # do not set values to actual theta!
    actual_theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')
    energy = Cpt(PseudoSingle, '')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        pseudo_theta=energy2theta(pseudo_pos.energy)
        return self.RealPosition(actual_theta=-pseudo_theta,
                                 y=fix_exit_trig_formula(-pseudo_theta))

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(energy=-real_pos.actual_theta)


hhm_fe = HHM_FixedExit('XF:08IDA-OP{Mono:HHM', name='fixed_exit', read_attrs=['theta', 'y'])
hhm_en = HHM_Energy('XF:08IDA-OP{Mono:HHM', name='hhm_en', read_attrs=['energy','y'])
hhm = HHM('XF:08IDA-OP{Mono:HHM', name='hhm')

  




