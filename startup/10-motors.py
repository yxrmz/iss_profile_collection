from ophyd import (EpicsMotor, Device, Component as Cpt, PseudoPositioner, PseudoSingle,
                   EpicsSignal)
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
    

cm1 = Mirror('XF:08IDA-OP{Mir:1-CM', name='cm1')
cm2 = Mirror('XF:08IDA-OP{Mir:2-CM', name='cm2')
fm = Mirror('XF:08IDA-OP{Mir:FM', name='fm')

h = 20 # mm

def fix_exit_trig_formula(theta):
    return h/(2*np.cos(np.deg2rad(theta)))

def energy2theta(energy):
    return np.rad2deg(np.arcsin(12400/energy/2/3.1356))

class HHM(Device):
    _default_configuration_attrs = ('pitch', 'roll', 'theta', 'y', 'energy')
    _default_read_attrs = ('pitch', 'roll', 'theta', 'y', 'energy')
    "High Heat Load Monochromator"
    pitch = Cpt(EpicsMotor, 'Mono:HHM-Ax:P}Mtr')
    roll = Cpt(EpicsMotor, 'Mono:HHM-Ax:R}Mtr')
    y = Cpt(EpicsMotor, 'Mono:HHM-Ax:Y}Mtr')
    theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr')
    energy = Cpt(EpicsMotor, 'Mono:HHM-Ax:E}Mtr')

    # The following are related to trajectory motion
    lut_number = Cpt(EpicsSignal, 'MC:06}LUT-Set')
    lut_number_rbv = Cpt(EpicsSignal, 'MC:06}LUT-Read')
    lut_start_transfer = Cpt(EpicsSignal, 'MC:06}TransferLUT')
    lut_transfering = Cpt(EpicsSignal, 'MC:06}TransferLUT-Read')
    trajectory_loading = Cpt(EpicsSignal, 'MC:06}TrajLoading')
    traj_mode = Cpt(EpicsSignal, 'MC:06}TrajFlag1-Set')
    traj_mode_rbv = Cpt(EpicsSignal, 'MC:06}TrajFlag1-Read')
    enable_ty = Cpt(EpicsSignal, 'MC:06}TrajFlag2-Set')
    enable_ty_rbv = Cpt(EpicsSignal, 'MC:06}TrajFlag2-Read')
    cycle_limit = Cpt(EpicsSignal, 'MC:06}TrajRows-Set')
    cycle_limit_rbv = Cpt(EpicsSignal, 'MC:06}TrajRows-Read')
    enable_loop = Cpt(EpicsSignal, 'MC:06}TrajLoopFlag-Set')
    enable_loop_rbv = Cpt(EpicsSignal, 'MC:06}TrajLoopFlag')

    prepare_trajectory = Cpt(EpicsSignal, 'MC:06}PrepareTraj')
    trajectory_ready = Cpt(EpicsSignal, 'MC:06}TrajInitPlc-Read')
    start_trajectory = Cpt(EpicsSignal, 'MC:06}StartTraj')
    stop_trajectory = Cpt(EpicsSignal, 'MC:06}StopTraj')
    trajectory_running = Cpt(EpicsSignal,'MC:06}TrajRunning', write_pv='MC:06}TrajRunning-Set')
    trajectory_progress = Cpt(EpicsSignal,'MC:06}TrajProgress')
    trajectory_name = Cpt(EpicsSignal, 'MC:06}TrajFilename')

    fb_status = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Sts')
    fb_center = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Center')
    fb_line = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Line')
    fb_nlines = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-NLines')
    fb_nmeasures = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-NMeasures')
    fb_pcoeff = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-PCoeff')

    angle_offset = Cpt(EpicsSignal, 'Mono:HHM-Ax:E}Offset')


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

hhm.read_attrs = ['pitch', 'roll', 'theta', 'y', 'energy']


class HRM(Device):
    "High Resolution Monochromator"
    theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')

hrm = HRM('XF:08IDA-OP{Mono:HRM', name='hrm')


class HHRM(Device):
    "High Harmonics Rejection Mirror"
    yu = Cpt(EpicsMotor, 'Mir:HRM:YU}Mtr')
    yd1 = Cpt(EpicsMotor, 'Mir:HRM:YD1}Mtr')
    yd2 = Cpt(EpicsMotor, 'Mir:HRM:YD2}Mtr')
    mir_pitch = Cpt(EpicsMotor, 'Mir:HRM:P}Mtr')
    hor_translation = Cpt(EpicsMotor, 'Mir:HRM:H}Mtr')

    table_pitch = Cpt(EpicsMotor, 'Mir:HRM:TP}Mtr')
    y = Cpt(EpicsMotor, 'Mir:HRM:TY}Mtr')


hhrm = HHRM('XF:08IDB-OP{', name='hhrm')


class SampleXY(Device):
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')

samplexy = SampleXY('XF:08IDB-OP{SampleXY', name='samplexy')


class Slits(Device):
    v_gap = Cpt(EpicsMotor, '-Ax:V-GAP}Mtr')
    v_pos = Cpt(EpicsMotor, '-Ax:V-POS}Mtr')
    hor_in = Cpt(EpicsMotor, '-Ax:XI}Mtr')
    hor_out = Cpt(EpicsMotor, '-Ax:XO}Mtr')

slits = Slits('XF:08IDB-OP{Slt', name='slits')

class HuberStage(Device):
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')

huber_stage = HuberStage('XF:08IDB-OP{Analyzer', name='huber_stage')

class XBIC(Device):
    dac1 = Cpt(EpicsSignal, 'MC:XBIC}DAC1-I', write_pv='MC:XBIC}DAC1R-SP')#'Mono:HHM-Ax:P}Mtr')
    dac2 = Cpt(EpicsSignal, 'MC:XBIC}DAC2-I', write_pv='MC:XBIC}DAC2R-SP')

xbic = XBIC('XF:08IDB-OP{', name='xbic')

