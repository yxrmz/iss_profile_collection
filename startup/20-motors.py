

from ophyd.status import SubscriptionStatus
from ophyd import utils as ophyd_utils
from xas import xray

print(__file__)

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



class HHMTrajDesc(Device):
    filename = Cpt(EpicsSignal, '-Name')
    elem = Cpt(EpicsSignal, '-Elem')
    edge = Cpt(EpicsSignal, '-Edge')
    e0 = Cpt(EpicsSignal, '-E0')




class HHM(Device):
    _default_configuration_attrs = ('pitch', 'roll', 'theta', 'y', 'energy')
    _default_read_attrs = ('pitch', 'roll', 'theta', 'y', 'energy')
    "High Heat Load Monochromator"
    ip = '10.66.58.106'

    pitch = Cpt(EpicsMotor, 'Mono:HHM-Ax:P}Mtr', kind='hinted')
    roll = Cpt(EpicsMotor, 'Mono:HHM-Ax:R}Mtr', kind='hinted')
    y = Cpt(StuckingEpicsMotor, 'Mono:HHM-Ax:Y}Mtr', kind='hinted')
    theta = Cpt(EpicsMotor, 'Mono:HHM-Ax:Th}Mtr', kind='hinted')
    energy = Cpt(StuckingEpicsMotorThatFlies, 'Mono:HHM-Ax:E}Mtr', kind=Kind.hinted)

    main_motor_res = Cpt(EpicsSignal, 'Mono:HHM-Ax:Th}Mtr.MRES')

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

    traj1 = Cpt(HHMTrajDesc, 'MC:06}Traj:1')
    traj2 = Cpt(HHMTrajDesc, 'MC:06}Traj:2')
    traj3 = Cpt(HHMTrajDesc, 'MC:06}Traj:3')
    traj4 = Cpt(HHMTrajDesc, 'MC:06}Traj:4')
    traj5 = Cpt(HHMTrajDesc, 'MC:06}Traj:5')
    traj6 = Cpt(HHMTrajDesc, 'MC:06}Traj:6')
    traj7 = Cpt(HHMTrajDesc, 'MC:06}Traj:7')
    traj8 = Cpt(HHMTrajDesc, 'MC:06}Traj:8')
    traj9 = Cpt(HHMTrajDesc, 'MC:06}Traj:9')

    fb_status = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Sts')
    fb_center = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Center')
    fb_line = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Line')
    fb_nlines = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-NLines')
    fb_nmeasures = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-NMeasures')
    fb_pcoeff = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-PCoeff')
    fb_hostname = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Hostname')
    fb_heartbeat = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Heartbeat')
    fb_status_err = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-Err')
    fb_status_msg = Cpt(EpicsSignal, 'Mono:HHM-Ax:P}FB-StsMsg', string=True)

    angle_offset = Cpt(EpicsSignal, 'Mono:HHM-Ax:E}Offset', limits=True)
    home_y = Cpt(EpicsSignal, 'MC:06}Home-HHMY')
    y_precise = Cpt(InfirmStuckingEpicsMotor, 'Mono:HHM-Ax:Y}Mtr', kind='hinted')

    servocycle = 16000

    def __init__(self, *args, enc = None, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.pulses_per_deg = 1 / self.main_motor_res.get()
        except ZeroDivisionError:
            self.pulses_per_deg = -1

        self.enc = enc
        self._preparing = None
        self._starting = None
        self.y_precise.append_homing_pv(self.home_y)
        self.y_precise.set_low_lim(low_lim=8.5)

        self.energy.append_flying_status_pv(self.trajectory_running)

    def set(self, command):
        if command == 'prepare':

            # This function will receive Events from the IOC and check whether
            # we are seeing the trajectory_ready go low after having been high.
            def callback(value, old_value, **kwargs):
                if int(round(old_value)) == 1 and int(round(value)) == 0:
                    if self._preparing or self._preparing is None:
                        self._preparing = False
                        return True
                    else:
                        self._preparing = True
                return False

            # Creating this status object subscribes `callback` Events from the
            # IOC. Starting at this line, we are now listening for the IOC to
            # tell us it is done. When it does, this status object will
            # complete (status.done = True).
            status = SubscriptionStatus(self.trajectory_ready, callback)

            # Finally, now that we are litsening to the IOC, prepare the
            # trajectory.
            self.prepare_trajectory.set('1')  # Yes, the IOC requires a string.

            # Return the status object immediately, without waiting. The caller
            # will be able to watch for it to become done.
            return status

        if command == 'start':

            def callback(value, old_value, **kwargs):
                if int(round(old_value)) == 1 and int(round(value)) == 0:
                    if self._starting or self._starting is None:
                        self._starting = False
                        return True
                    else:
                        self._starting = True
                return False

            status = SubscriptionStatus(self.trajectory_running, callback)
            self.start_trajectory.set('1')

            return status

    def home_y_pos(self):
        self.home_y.put('1')


    def set_new_angle_offset(self, value, error_message_func=None):
        try:
            self.angle_offset.put(float(value))
            return True
        except Exception as exc:
            if type(exc) == ophyd_utils.errors.LimitError:
                msg = 'HHM limit error'
                print_to_gui(f'[Energy calibration] {msg}.'.format(exc))
                if error_message_func is not None:
                    error_message_func(msg)
            else:
                msg = f'HHM error. Something went wrong, not the limit: {exc}'
                print_to_gui(f'[Energy calibration] {msg}')
                if error_message_func is not None:
                    error_message_func(msg)
            return False

    def calibrate(self, energy_nominal, energy_actual, error_message_func=None):
        offset_actual = xray.energy2encoder(energy_actual, hhm.pulses_per_deg) / hhm.pulses_per_deg
        offset_nominal = xray.energy2encoder(energy_nominal, hhm.pulses_per_deg) / hhm.pulses_per_deg
        angular_offset_shift = offset_actual - offset_nominal
        new_angular_offset = self.angle_offset.value - angular_offset_shift
        return self.set_new_angle_offset(new_angular_offset, error_message_func=error_message_func)


    def trigger(self, *args, **kwargs):
        start_trigger = ttime.time()
        status = super().trigger(*args, **kwargs)
        print(f'{self.name} took {ttime.time() - start_trigger} to trigger')
        return status

    def abort_trajectory(self):

        if self.trajectory_running.get():
            print('Stopping trajectory ... ', end='')
            self.stop_trajectory.put('1')
            print('done')

    # def stop(self, *args, **kwargs):
    #     print('Stopping trajectory')
    #     if self.trajectory_running.get():
    #         self.stop_trajectory.put('1')
    #     super().stop(*args, **kwargs)
    #     print('Done stopping trajectory')

# # BANDAID THAT HAS TO BE REMOVED AT SOME POINT
# from PyQt5.QtCore import QThread
# class mono_unstuck_thread(QThread):
#     def __init__(self, hhm : HHM):
#         QThread.__init__(self)
#         self.go = False
#         self.hhm = hhm
#
#     def run(self):
#         while self.go:
#             is_mono_moving = hhm.energy.
#             mono_value =
#             for i in range(5):
#                 mono_value_2 =
#                 if (mono_value == mono_value_2) and is_mono_moving:
#                     STOP
#

hhm = HHM('XF:08IDA-OP{', enc = pb9.enc1, name='hhm')
# TODO: move to the HHM class definition.
hhm_z_home = Cpt(EpicsSignal,'XF:08IDA-OP{MC:06}Home-HHMY')

# Try to read it first time to avoid the generic 'object' to be returned
# as an old value from hhm.trajectory_running._readback.
hhm.wait_for_connection()
_ = hhm.trajectory_ready.read()
_ = hhm.trajectory_running.read()


# hhm.hints = {'fields': ['hhm_energy', 'hhm_pitch', 'hhm_roll', 'hhm_theta', 'hhm_y']}
# hinted also is automatically set as read so no need to set read_attrs
hhm.energy.kind = 'hinted'
hhm.pitch.kind = 'hinted'
hhm.roll.kind = 'hinted'
hhm.theta.kind = 'hinted'
hhm.y.kind = 'hinted'

hhm.read_attrs = ['pitch', 'roll', 'theta', 'y', 'energy']


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
    def current_sripe(self):
        pos = self.hor_translation.user_readback.get()
        if pos < 40:
            stripe = 'Pt'
        else:
            stripe = 'Rh'
        return stripe


hhrm = HHRM('XF:08IDB-OP{', name='hhrm')


class SampleXY(Device):
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')

samplexy = SampleXY('XF:08IDB-OP{SampleXY', name='samplexy')
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





