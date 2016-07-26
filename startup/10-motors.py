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
    pitch = Cpt(EpicsMotor, 'Mono:HHM-Ax:P}Mtr')
    roll = Cpt(EpicsMotor, 'Mono:HHM-Ax:R}Mtr')
    theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr')
    y = Cpt(EpicsMotor, 'Mono:HHM-Ax:Y}Mtr')
    theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr')  # degrees

  # The following are related to trajectory motion
    lut_number = Cpt(EpicsSignal, 'MC:06}LUT-Set')
    lut_number_rbv = Cpt(EpicsSignal, 'MC:06}LUT-Read')
    lut_start_transfer = Cpt(EpicsSignal, 'MC:06}TransferLUT')
    lut_transfering = Cpt(EpicsSignal, 'MC:06}TransferLUT-Read')
    traj_mode = Cpt(EpicsSignal, 'MC:06}TrajFlag1-Set')
    traj_mode_rbv = Cpt(EpicsSignal, 'MC:06}TrajFlag1-Read')
    enable_ty = Cpt(EpicsSignal, 'MC:06}TrajFlag2-Set')
    enable_ty_rbv = Cpt(EpicsSignal, 'MC:06}TrajFlag2-Read')
    cycle_limit = Cpt(EpicsSignal, 'MC:06}TrajRows-Set')
    cycle_limit_rbv = Cpt(EpicsSignal, 'MC:06}TrajRows-Read')

    prepare_trajectory = Cpt(EpicsSignal, 'MC:06}PrepareTraj')
    start_trajectory = Cpt(EpicsSignal, 'MC:06}StartTraj')
    stop_trajectory = Cpt(EpicsSignal, 'MC:06}StopTraj')

class HHM_FixedExit(PseudoPositioner):
    # do not set values to actual theta!
    actual_theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr')
    theta = Cpt(PseudoSingle, '')
    y = Cpt(EpicsMotor, 'Mono:HHM-Ax:Y}Mtr')

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
    actual_theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr')
    energy = Cpt(PseudoSingle, '')
    y = Cpt(EpicsMotor, 'Mono:HHM-Ax:Y}Mtr')

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        '''Run a forward (pseudo -> real) calculation'''
        pseudo_theta=energy2theta(pseudo_pos.energy)
        return self.RealPosition(actual_theta=-pseudo_theta, y=self.y.read()['hhm_en_y']['value'])

    @real_position_argument
    def inverse(self, real_pos):
        '''Run an inverse (real -> pseudo) calculation'''
        return self.PseudoPosition(energy=-real_pos.actual_theta)


class HHM_Energy_FE(PseudoPositioner):
    # do not set values to actual theta!
    actual_theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr')
    energy = Cpt(PseudoSingle, '')
    y = Cpt(EpicsMotor, 'Mono:HHM-Ax:Y}Mtr')

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


hhm_fe = HHM_FixedExit('XF:08IDA-OP{', name='fixed_exit', read_attrs=['theta', 'y'])
hhm_en = HHM_Energy('XF:08IDA-OP{', name='hhm_en', read_attrs=['energy','y'])
hhm = HHM('XF:08IDA-OP{', name='hhm')

  




