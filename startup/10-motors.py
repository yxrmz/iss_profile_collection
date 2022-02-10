

from ophyd.status import SubscriptionStatus, DeviceStatus
from ophyd import utils as ophyd_utils
from xas import xray


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

# h = 20 # mm
#
#
# def fix_exit_trig_formula(theta):
#     return h/(2*np.cos(np.deg2rad(theta)))




class HRM(Device):
    """High Resolution Monochromator"""
    theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')
    y = Cpt(StuckingEpicsMotor, '-Ax:Y}Mtr')
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')

hrm = HRM('XF:08IDA-OP{Mono:HRM', name='hrm')


class HHRM(Device):
    """High Harmonics Rejection Mirror"""
    yu = Cpt(EpicsMotor, 'Mir:HRM:YU}Mtr')
    yd1 = Cpt(EpicsMotor, 'Mir:HRM:YD1}Mtr')
    yd2 = Cpt(EpicsMotor, 'Mir:HRM:YD2}Mtr')
    mir_pitch = Cpt(EpicsMotor, 'Mir:HRM:P}Mtr')
    hor_translation = Cpt(EpicsMotor, 'Mir:HRM:H}Mtr')

    table_pitch = Cpt(EpicsMotor, 'Mir:HRM:TP}Mtr')
    y = Cpt(StuckingEpicsMotor, 'Mir:HRM:TY}Mtr')

    @property
    def current_stripe(self):
        pos = self.hor_translation.user_readback.get()
        if np.isclose(pos, 0, atol=1):
            stripe = 'Si'
        elif np.isclose(pos, 40, atol=1):
            stripe = 'Pt'
        elif np.isclose(pos, -40, atol=1):
            stripe = 'Rh'
        else:
            stripe = 'undefined'
        return stripe
        # print_to_gui('WARNING HHRM STRIPE IS NOT DEFINED')
        # return 'undefined'


hhrm = HHRM('XF:08IDB-OP{', name='hhrm')


class SampleXY(Device):
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')

# samplexy = SampleXY('XF:08IDB-OP{SampleXY', name='samplexy')
giantxy = SampleXY('XF:08IDB-OP{Stage:Sample', name='giantxy') # this is the important motor

auxxy = SampleXY('XF:08IDB-OP{Stage:Aux1', name='auxxy')


class DetStageXYZ(Device):
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    z = Cpt(EpicsMotor, '-Ax:Z}Mtr')

detstage = DetStageXYZ('XF:08IDB-OP{Stage:Det', name='detstage')


class Usermotor(Device):
    pos = Cpt(EpicsMotor, '}Mtr')


usermotor1 = Usermotor('XF:08IDB-OP{Misc-Ax:1', name='usermotor1')
usermotor2 = Usermotor('XF:08IDB-OP{Misc-Ax:2', name='usermotor2')
usermotor3 = Usermotor('XF:08IDB-OP{Misc-Ax:3', name='usermotor3')

attenuator_motor = Usermotor('XF:08IDB-OP{Misc-Ax:4', name='attenuator_motor')

usermotor2.wait_for_connection()
usermotor3.wait_for_connection()

class IonChamberMotor(Device):
    pos = Cpt(EpicsMotor, '}Mtr')

i0_y = IonChamberMotor('XF:08IDB-OP{IC-Ax:Y:1', name='i0_y')
it_y = IonChamberMotor('XF:08IDB-OP{IC-Ax:Y:2', name='it_y')
ir_y = IonChamberMotor('XF:08IDB-OP{IC-Ax:Y:3', name='ir_y')



class Bender(Device):
    pos = Cpt(EpicsMotor, '}Mtr')
    load_cell = EpicsSignalRO('XF:08IDA-OP{Mir:CM-Ax:Bender}W-I', name='bender_loading')
bender = Bender('XF:08IDA-OP{Mir:CM-Bender', name='bender')


class FilterBox(Device):
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    pos1 = Cpt(EpicsSignal, '}Fltr1:In-Sts')
    pos2 = Cpt(EpicsSignal, '}Fltr2:In-Sts')
    pos3 = Cpt(EpicsSignal, '}Fltr3:In-Sts')
    pos4 = Cpt(EpicsSignal, '}Fltr4:In-Sts')
    pos5 = Cpt(EpicsSignal, '}Fltr5:In-Sts')

    pos_limit = Cpt(EpicsSignal, '-Ax:Y}OvrP-Sts')
    neg_limit = Cpt(EpicsSignal, '-Ax:Y}OvrN-Sts')

filterbox = FilterBox('XF:08IDA-OP{Fltr:FB', name='filterbox')


class Slits(Device):
    v_gap = Cpt(EpicsMotor, '-Ax:V-GAP}Mtr')
    v_pos = Cpt(EpicsMotor, '-Ax:V-POS}Mtr')
    hor_in = Cpt(EpicsMotor, '-Ax:XI}Mtr')
    hor_out = Cpt(EpicsMotor, '-Ax:XO}Mtr')

slits = Slits('XF:08IDB-OP{Slt', name='slits')


class HuberStage(Device):
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')
    z = Cpt(EpicsMotor, '-Ax:Z}Mtr')

huber_stage = HuberStage('XF:08IDB-OP{Analyzer', name='huber_stage')


class XBIC(Device):
    dac1 = Cpt(EpicsSignal, 'MC:XBIC}DAC1-I', write_pv='MC:XBIC}DAC1R-SP')
    dac2 = Cpt(EpicsSignal, 'MC:XBIC}DAC2-I', write_pv='MC:XBIC}DAC2R-SP')

#xbic = XBIC('XF:08IDB-OP{', name='xbic')

class SixAxesStage(Device):
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')
    z = Cpt(EpicsMotor, '-Ax:Z}Mtr')
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')
    yaw = Cpt(EpicsMotor, '-Ax:Yaw}Mtr')
    roll = Cpt(EpicsMotor, '-Ax:R}Mtr')

six_axes_stage = SixAxesStage('XF:08IDB-OP{PCL', name='six_axes_stage')

class FoilWheel(Device):
    wheel1 = Cpt(EpicsMotor, '1:Rot}Mtr')
    wheel2 = Cpt(EpicsMotor, '2:Rot}Mtr')

foil_wheel = FoilWheel('XF:08IDB-OP{FoilWheel', name='foil_wheel')

class GonioMeter(Device):
    th1 = Cpt(EpicsMotor, ':1}Mtr')
    th2 = Cpt(EpicsMotor, ':2}Mtr')

gonio_meter = GonioMeter('XF:08IDB-OP{Gon:Th', name='gonio_meter')


class SampleStage(Device):
    x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Sample-Ax:X}Mtr')
    y = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Sample-Ax:Y}Mtr')
    z = Cpt(EpicsMotor, 'XF:08IDB-OP{Misc-Ax:2}Mtr')
    th = Cpt(EpicsMotor, 'XF:08IDB-OP{Gon:Th:1}Mtr')


sample_stage = SampleStage(name='sample_stage')
# samplexy = SampleXY('XF:08IDB-OP{SampleXY', name='samplexy')
# giantxy = SampleXY('XF:08IDB-OP{Stage:Sample', name='giantxy') # this is the important motor




