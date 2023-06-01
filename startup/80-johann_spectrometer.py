print(ttime.ctime() + ' >>>> ' + __file__)


import numpy as np
import pandas as pd
from xas.spectrometer import Crystal, analyze_many_elastic_scans
import copy



from ophyd import (PseudoPositioner, PseudoSingle)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)


# def move_crystal_plan(x, y):
#     yield from bps.mv(auxxy.x, x)
#     yield from bps.mv(auxxy.y, y)



# class JohannSpectrometerMotor(PseudoPositioner):
#     energy = Cpt(PseudoSingle, name='emission_energy')
#     motor_crystal_x = auxxy.x
#     motor_crystal_y = auxxy.y
#     motor_detector_y = huber_stage.z
#     _real = ['motor_crystal_x',
#              'motor_crystal_y',F
#              'motor_detector_y']
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.energy0 = None
#         self.cr_x0 = None
#         self.cr_x0=None
#         self.cr_y0=None
#         self.det_y0=None
#         self.spectrometer_root_path = f"{ROOT_PATH}/{USER_PATH}"
#         self._initialized = False
#
#
#     def define_motor_coordinates(self, energy0, R, kind, hkl,
#                                   cr_x0=None, cr_y0=None, det_y0=None,
#                  energy_limits=None):
#
#         self.energy0 = energy0
#         if cr_x0 is None:
#             self.cr_x0 = self.motor_crystal_x.user_readback.get()
#         else:
#             self.cr_x0 = cr_x0
#         if cr_y0 is None:
#             self.cr_y0 = self.motor_crystal_y.user_readback.get()
#         else:
#             self.cr_y0 = cr_y0
#         if det_y0 is None:
#             self.det_y0 = self.motor_detector_y.user_readback.get()
#         else:
#             self.det_y0 = det_y0
#         self.crystal = Crystal(R, 50, hkl, kind)
#         self.crystal.place_E(energy0)
#         self.cr_x0_nom = copy.copy(self.crystal.x)
#         self.cry_0_nom = copy.copy(self.crystal.y)
#         self.det_y0_nom = copy.copy(self.crystal.d_y)
#
#         if energy_limits is not None:
#             condition = ((type(energy_limits) == tuple) and (len(energy_limits)==2))
#             assert condition, 'Invalid limits for emission energy motor'
#             self.energy._limits = energy_limits
#         self.energy_converter = None
#         self._initialized = True
#
#     def append_energy_converter(self, ec):
#         self.energy_converter = ec
#
#     @pseudo_position_argument
#     def forward(self, energy_input_object):
#         energy = energy_input_object.energy
#         if self.energy_converter is not None:
#             energy = self.energy_converter.act2nom(energy)
#         self.crystal.place_E(energy)
#         dcr_x = self.crystal.x - self.cr_x0_nom
#         dcr_y = self.crystal.y - self.cry_0_nom
#         ddet_y = self.crystal.d_y - self.det_y0_nom
#
#         position_detector_y = self.det_y0 - ddet_y
#         position_crystal_y = self.cr_y0 + dcr_y
#         position_crystal_x = self.cr_x0 - dcr_x
#
#         return self.RealPosition(motor_detector_y = position_detector_y,
#                                  motor_crystal_y = position_crystal_y,
#                                  motor_crystal_x = position_crystal_x)
#
#     @real_position_argument
#     def inverse(self, real_pos):
#         x = self.cr_x0 + self.cr_x0_nom  - real_pos.motor_crystal_x
#         y = self.cry_0_nom - self.cr_y0 + real_pos.motor_crystal_y
#         d_y = self.det_y0 + self.det_y0_nom - real_pos.motor_detector_y
#         energy = self.crystal.compute_energy_from_positions(x, y, d_y)
#         if self.energy_converter is not None:
#             energy = self.energy_converter.nom2act(energy)
#         return [energy]


# johann_spectrometer_motor = JohannSpectrometerMotor(name='motor_emission')

# motor_emission_key = 'motor_emission'
#
# motor_emission_dict = {'name': johann_spectrometer_motor.name, 'description' : 'Emission energy', 'object': johann_spectrometer_motor, 'group': 'spectrometer'}
# motor_dictionary['motor_emission'] = motor_emission_dict

# class JohannCrystal(Device):
#     x = Cpt(EpicsMotor, '}X')
#     y = Cpt(EpicsMotor, '}Y')
#     pitch = Cpt(EpicsMotor, '}PITCH')
#     yaw = Cpt(EpicsMotor, '}YAW')
#
#     def __init__(self, *args, leading=True, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.leading = leading
from xas.spectrometer import compute_rowland_circle_geometry
from xas.fitting import Nominal2ActualConverter

from scipy import interpolate
class Nominal2ActualConverterWithLinearInterpolation:

    def __init__(self):
        self.x_nom = []
        self.x_act = []

    def append_point(self, x_nom, x_act):
        if np.any(np.isclose(x_nom, self.x_nom, atol=1e-4)) or np.any(np.isclose(x_act, self.x_act, atol=1e-4)):
            return
        self.x_nom.append(x_nom)
        self.x_act.append(x_act)

    @property
    def npt(self):
        return len(self.x_nom)

    def nom2act(self, x_nom):
        if self.npt == 0:
            return x_nom
        elif self.npt == 1:
            return x_nom - (self.x_nom[0] - self.x_act[0])
        else:
            f = interpolate.interp1d(self.x_nom, self.x_act, kind='linear', fill_value='extrapolate')
            return f(x_nom)

    def act2nom(self, x_act):
        if self.npt == 0:
            return x_act
        elif self.npt == 1:
            return x_act - (self.x_act[0] - self.x_nom[0])
        else:
            f = interpolate.interp1d(self.x_act, self.x_nom, kind='linear', fill_value='extrapolate')
            return f(x_act)

def extrapolate_linearly(x_in, x, y):
    if type(x_in) != np.ndarray:
        x_in = np.array(x_in)
    if len(x) == 0:
        return np.zeros(x_in.shape)
    elif len(x) == 1:
        return y * np.ones(x_in.shape)
    else:
        f = interpolate.interp1d(x, y, kind='linear', fill_value='extrapolate')
        return f(x_in)

from xas.xray import bragg2e, e2bragg, crystal_reflectivity
from xas.spectrometer import compute_rowland_circle_geometry, _compute_rotated_rowland_circle_geometry

_BIG_DETECTOR_ARM_LENGTH = 550 # length of the big arm
_SMALL_DETECTOR_ARM_LENGTH = 91 # distance between the second gon and the sensitive surface of the detector

_johann_det_arm_motor_keys = ['motor_det_x', 'motor_det_th1', 'motor_det_th2']
_johann_cr_assy_motor_keys = ['motor_cr_assy_x', 'motor_cr_assy_y']
_johann_cr_main_motor_keys = ['motor_cr_main_roll', 'motor_cr_main_yaw']
_johann_cr_aux2_motor_keys = ['motor_cr_aux2_x', 'motor_cr_aux2_y', 'motor_cr_aux2_roll', 'motor_cr_aux2_yaw']
_johann_cr_aux3_motor_keys = ['motor_cr_aux3_x', 'motor_cr_aux3_y', 'motor_cr_aux3_roll', 'motor_cr_aux3_yaw']


_johann_cr_all_motor_keys = (_johann_cr_assy_motor_keys +
                             _johann_cr_main_motor_keys +
                             _johann_cr_aux2_motor_keys +
                             _johann_cr_aux3_motor_keys)
_johann_spectrometer_motor_keys = (_johann_det_arm_motor_keys +
                                   _johann_cr_all_motor_keys)

_allowed_roll_offsets = [2.5, 11.5, 20.5]

class RowlandCircle:

    def __init__(self):

        self.json_path = f'{ROOT_PATH_SHARED}/settings/json/johann_config_upd.json'
        self.energy_converter = None

        self.x_src = 0
        self.y_src = 0
        self.bragg_min = 59
        self.bragg_max = 95

        self.allowed_roll_offsets = _allowed_roll_offsets

        self.det_L1 = _BIG_DETECTOR_ARM_LENGTH
        self.det_L2 = _SMALL_DETECTOR_ARM_LENGTH
        self.cr_aux2_z = 139.5 # z-distance between the main and the auxiliary crystal (stack #2)
        self.det_focus_status = 'good'
        self.init_from_settings()


    def load_config(self, file):
        with open(file, 'r') as f:
            config = json.loads(f.read())
        return config

    def save_current_spectrometer_config(self, file):
        with open(file, 'w') as f:
            json.dump(self.config, f)

    def save_current_spectrometer_config_to_settings(self):
        self.save_current_spectrometer_config(self.json_path)

    def init_from_settings(self):
        try:
            config = self.load_config(self.json_path)
        except Exception as e:
            print(f'Spectrometer config could not be loaded from settings. Loading the default configuration.\n\n{e}')
            config = {'R': 1000.0,
                      'crystal': 'Si',
                      'hkl': [5, 3, 1],
                      'parking': {'motor_det_x': -77.0,
                      'motor_det_th1': 0.0,
                      'motor_det_th2': 0.0,
                      'motor_cr_assy_x': -3.0001261410000097,
                      'motor_cr_assy_y': 7.181946,
                      'motor_cr_main_roll': 577.4580000000001,
                      'motor_cr_main_yaw': -185.0,
                      'motor_cr_aux2_x': 0.0,
                      'motor_cr_aux2_y': -8200.0,
                      'motor_cr_aux2_roll': 419.5590000000002,
                      'motor_cr_aux2_yaw': -1160.0,
                      'motor_cr_aux3_x': -2500.0,
                      'motor_cr_aux3_y': -8900.0,
                      'motor_cr_aux3_roll': 1495.426,
                      'motor_cr_aux3_yaw': -506.468},
                      'roll_offset': 2.5,
                      'det_offsets': {'motor_det_th1': 69.0,
                                      'motor_det_th2': -69.0},
                      'det_focus': -5,
                      'bragg_registration': {'bragg': {k : [] for k in _johann_spectrometer_motor_keys},
                                             'pos_nom' : {k : [] for k in _johann_spectrometer_motor_keys},
                                             'pos_act' : {k : [] for k in _johann_spectrometer_motor_keys}},
                       'energy_calibration': {'x_nom': [], 'x_act': [], 'n_poly': 2},
                       'enabled_crystals': {'main': True, 'aux2': True, 'aux3': True},
                       'initialized': False,
                       'energy_limits': [0, 0]}
        self.set_spectrometer_config(config)

    def set_spectrometer_config(self, config):
        # config needs a validation may be
        self.config = config
        self.compute_trajectories()
        if 'energy_calibration' in config.keys():
            config_ec = config['energy_calibration']
            if (len(config_ec['x_nom']) > 0) and (len(config_ec['x_act']) > 0) and (config_ec['n_poly'] > 0):
                self.energy_converter = Nominal2ActualConverter(config_ec['x_nom'], config_ec['x_act'], config_ec['n_poly'])

    def set_spectrometer_calibration(self, x_nom, x_act, n_poly=2):
        self.config['energy_calibration'] = {'x_nom' : x_nom.tolist(), 'x_act' : x_act.tolist(), 'n_poly' : n_poly}
        self.energy_converter = Nominal2ActualConverter(x_nom, x_act, n_poly=n_poly)

    def reset_spectrometer_calibration(self):
        self.config['energy_calibration'] = {'x_nom': [], 'x_act': [], 'n_poly': 2}
        self.energy_converter = None

    def set_det_arm_parking(self, pos_dict):
        self.config['parking']['motor_det_x'] = pos_dict['motor_det_x']
        self.config['det_offsets']['motor_det_th1'] = pos_dict['motor_det_th1']
        self.config['det_offsets']['motor_det_th2'] = pos_dict['motor_det_th2']
        self.save_current_spectrometer_config_to_settings()

    def det_arm_parking(self):
        return (self.config['parking']['motor_det_x'],
                self.config['det_offsets']['motor_det_th1'],
                self.config['det_offsets']['motor_det_th2'])

    def set_main_crystal_parking(self, pos_dict):
        self.config['parking']['motor_cr_assy_x'] = pos_dict['motor_cr_assy_x'] - self.R
        self.config['parking']['motor_cr_assy_y'] = pos_dict['motor_cr_assy_y']
        self.config['parking']['motor_cr_main_roll'] = pos_dict['motor_cr_main_roll'] - 2500
        self.config['parking']['motor_cr_main_yaw'] = pos_dict['motor_cr_main_yaw']
        self.save_current_spectrometer_config_to_settings()

    def main_crystal_parking(self, human_readable=True):
        x, y, roll, yaw = (self.config['parking']['motor_cr_assy_x'],
                           self.config['parking']['motor_cr_assy_y'],
                           self.config['parking']['motor_cr_main_roll'],
                           self.config['parking']['motor_cr_main_yaw'])
        if human_readable:
            x = x + self.R
            roll = (roll + 2500) / 1000
            yaw = yaw / 1000
        return x, y, roll, yaw

    def set_aux2_crystal_parking(self, pos_dict):
        self.config['parking']['motor_cr_aux2_x'] = pos_dict['motor_cr_aux2_x']
        self.config['parking']['motor_cr_aux2_y'] = pos_dict['motor_cr_aux2_y']
        self.config['parking']['motor_cr_aux2_roll'] = pos_dict['motor_cr_aux2_roll'] - 2500
        self.config['parking']['motor_cr_aux2_yaw'] = pos_dict['motor_cr_aux2_yaw']
        self.save_current_spectrometer_config_to_settings()

    def aux2_crystal_parking(self, human_readable=True):
        x, y, roll, yaw = (self.config['parking']['motor_cr_aux2_x'],
                           self.config['parking']['motor_cr_aux2_y'],
                           self.config['parking']['motor_cr_aux2_roll'],
                           self.config['parking']['motor_cr_aux2_yaw'])
        if human_readable:
            x /= 1000
            y /= 1000
            roll = (roll + 2500) / 1000
            yaw /= 1000
        return x, y, roll, yaw

    def set_aux3_crystal_parking(self, pos_dict):
        self.config['parking']['motor_cr_aux3_x'] = pos_dict['motor_cr_aux3_x']
        self.config['parking']['motor_cr_aux3_y'] = pos_dict['motor_cr_aux3_y']
        self.config['parking']['motor_cr_aux3_roll'] = pos_dict['motor_cr_aux3_roll'] - 2500
        self.config['parking']['motor_cr_aux3_yaw'] = pos_dict['motor_cr_aux3_yaw']
        self.save_current_spectrometer_config_to_settings()

    def aux3_crystal_parking(self, human_readable=True):
        x, y, roll, yaw = (self.config['parking']['motor_cr_aux3_x'],
                           self.config['parking']['motor_cr_aux3_y'],
                           self.config['parking']['motor_cr_aux3_roll'],
                           self.config['parking']['motor_cr_aux3_yaw'])
        if human_readable:
            x /= 1000
            y /= 1000
            roll = (roll + 2500) / 1000
            yaw /= 1000
        return x, y, roll, yaw

    @property
    def det_dx(self):
        return self.det_L1 * np.cos(np.deg2rad(self.config['det_offsets']['motor_det_th1'])) - self.det_L2

    @property
    def det_h(self):
        return self.det_L1 * np.sin(np.deg2rad(self.config['det_offsets']['motor_det_th1']))

    @property
    def det_focus(self):
        det_focus_est = self.compute_motor_position('motor_det_x', 90, nom2act=False) - self.config['parking']['motor_det_x']
        if not np.isclose(det_focus_est, self.config['det_focus'], atol=0.1):
            self.det_focus_status = 'bad'
        else:
            self.det_focus_status = 'good'
            # print_to_gui('WARNING: estimated det_focus differs from the config value by >0.1 mm')
        return self.config['det_focus']

    @det_focus.setter
    def det_focus(self, value):
        self.update_nominal_trajectory_for_detector(value)
        self.compute_trajectory_correction()
        self.config['det_focus'] = value
        self.save_current_spectrometer_config_to_settings()

    @property
    def R(self):
        return self.config['R']

    @R.setter
    def R(self, value):
        self.config['parking']['motor_cr_assy_x'] += (self.config['R'] - value)
        self.config['R'] = value
        self.save_current_spectrometer_config_to_settings()

    @property
    def crystal(self):
        return self.config['crystal']

    @crystal.setter
    def crystal(self, value):
        self.config['crystal'] = value

    @property
    def hkl(self):
        return self.config['hkl']

    @hkl.setter
    def hkl(self, value):
        self.config['hkl'] = value

    @property
    def roll_offset(self):
        return self.config['roll_offset']

    @roll_offset.setter
    def roll_offset(self, value):
        assert value in self.allowed_roll_offsets, f'roll_offset value must be equal to one of {self.allowed_roll_offsets}'
        self.config['roll_offset'] = value
        self.compute_trajectories()
        self.save_current_spectrometer_config_to_settings()

    @property
    def enabled_crystals(self):
        return self.config['enabled_crystals']

    def enable_crystal(self, crystal_key, enable):
        self.enabled_crystals[crystal_key] = enable
        self.save_current_spectrometer_config_to_settings()

    @property
    def initialized(self):
        return self.config['initialized']

    @initialized.setter
    def initialized(self, value):
        self.config['initialized'] = value
        self.save_current_spectrometer_config_to_settings()

    @property
    def energy_limits(self):
        return self.config['energy_limits']

    @energy_limits.setter
    def energy_limits(self, value):
        self.config['energy_limits'] = value
        self.save_current_spectrometer_config_to_settings()

    def _compute_nominal_trajectory(self, npt=1000):
        braggs = np.linspace(self.bragg_min, self.bragg_max, npt-1)
        braggs = np.sort(np.hstack((braggs, 90)))

        # pseudos
        det_x = np.zeros(npt)
        det_y = np.zeros(npt)

        cr_main_x = np.zeros(npt)
        cr_main_y = np.zeros(npt)
        cr_main_roll = braggs.copy()
        cr_main_yaw = np.zeros(npt)

        cr_aux2_x = np.zeros(npt)
        cr_aux2_y = np.zeros(npt)
        cr_aux2_roll = np.zeros(npt)
        cr_aux2_yaw = np.zeros(npt)

        for i, bragg in enumerate(braggs):
            cr_main_x[i], cr_main_y[i], det_x[i], det_y[i] = \
                compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, bragg, 0)
            cr_aux2_x[i], cr_aux2_y[i], cr_aux2_roll[i], cr_aux2_yaw[i] = \
                _compute_rotated_rowland_circle_geometry(cr_main_x[i], cr_main_y[i], det_x[i], det_y[i], bragg, self.cr_aux2_z)

        # reals
        # detector
        motor_det_x, motor_det_th1, motor_det_th2 = self._compute_trajectory_for_detector(braggs, det_x, det_y)

        # main crystal
        motor_cr_assy_x = -cr_main_x
        motor_cr_assy_y = cr_main_y
        motor_cr_main_roll = (cr_main_roll - 90 + self.config['roll_offset']) * 1000
        motor_cr_main_yaw = cr_main_yaw * 1000

        # aux crystal2
        _cr_aux2_yaw_0 = np.arcsin(self.cr_aux2_z / self.R)
        _cr_aux2_dx_0 = (-self.R * np.cos(_cr_aux2_yaw_0)) + self.R
        _cr_aux2_dx = cr_aux2_x - cr_main_x
        motor_cr_aux2_x = -(_cr_aux2_dx - _cr_aux2_dx_0) * 1000
        motor_cr_aux2_y = cr_aux2_y * 1000
        motor_cr_aux2_roll = (cr_aux2_roll - 90 + self.config['roll_offset']) * 1000
        motor_cr_aux2_yaw = (cr_aux2_yaw - np.rad2deg(_cr_aux2_yaw_0)) * 1000

        # aux crystal3
        motor_cr_aux3_x = motor_cr_aux2_x.copy()
        motor_cr_aux3_y = motor_cr_aux2_y.copy()
        motor_cr_aux3_roll = motor_cr_aux2_roll.copy()
        motor_cr_aux3_yaw = -motor_cr_aux2_yaw.copy()

        return pd.DataFrame(
               {'bragg' :               braggs,
                'det_x' :               det_x,
                'det_y' :               det_y,
                'cr_main_x' :           cr_main_x,
                'cr_main_y' :           cr_main_y,
                'cr_main_roll' :        cr_main_roll,
                'cr_main_yaw' :         cr_main_yaw,
                'cr_aux2_x':            cr_aux2_x,
                'cr_aux2_y':            cr_aux2_y,
                'cr_aux2_roll':         cr_aux2_roll,
                'cr_aux2_yaw':          cr_aux2_yaw,
                'motor_det_x':          motor_det_x,
                'motor_det_th1':        motor_det_th1,
                'motor_det_th2':        motor_det_th2,
                'motor_cr_assy_x' :     motor_cr_assy_x,
                'motor_cr_assy_y':      motor_cr_assy_y,
                'motor_cr_main_roll':   motor_cr_main_roll,
                'motor_cr_main_yaw':    motor_cr_main_yaw,
                'motor_cr_aux2_x' :     motor_cr_aux2_x,
                'motor_cr_aux2_y':      motor_cr_aux2_y,
                'motor_cr_aux2_roll':   motor_cr_aux2_roll,
                'motor_cr_aux2_yaw':    motor_cr_aux2_yaw,
                'motor_cr_aux3_x':      motor_cr_aux3_x,
                'motor_cr_aux3_y':      motor_cr_aux3_y,
                'motor_cr_aux3_roll':   motor_cr_aux3_roll,
                'motor_cr_aux3_yaw':    motor_cr_aux3_yaw})

    def _compute_trajectory_for_detector(self, braggs, det_x, det_y, det_focus=0):

        _det_bragg_rad = np.deg2rad(braggs)
        det_x = det_x.copy() - det_focus * np.cos(np.pi - 2 * _det_bragg_rad)
        det_y = det_y.copy() - det_focus * np.sin(np.pi - 2 * _det_bragg_rad)

        _phi = np.pi - 2 * _det_bragg_rad
        _sin_th1 = (self.det_h - self.det_L2 * np.sin(_phi) - det_y) / self.det_L1
        motor_det_th1 = np.arcsin(_sin_th1)
        motor_det_th2 = _phi + motor_det_th1
        motor_det_x = -self.det_dx + self.det_L1 * np.cos(motor_det_th1) - self.det_L2 * np.cos(_phi) - det_x
        motor_det_th1 = np.rad2deg(motor_det_th1)
        motor_det_th2 = -np.rad2deg(motor_det_th2)
        return motor_det_x, motor_det_th1, motor_det_th2

    def update_nominal_trajectory_for_detector(self, det_focus, force_update=False):
        if force_update or (not np.isclose(det_focus, self.det_focus, atol=1e-4)):
            # self.det_focus = det_focus
            motor_det_x, motor_det_th1, motor_det_th2 = self._compute_trajectory_for_detector(self.traj_nom['bragg'],
                                                                                              self.traj_nom['det_x'],
                                                                                              self.traj_nom['det_y'],
                                                                                              det_focus=det_focus)
            self.traj_nom['motor_det_x'] = motor_det_x
            self.traj_nom['motor_det_th1'] = motor_det_th1
            self.traj_nom['motor_det_th2'] = motor_det_th2


    def compute_nominal_trajectory(self, npt=250):
        self.traj_nom = self._compute_nominal_trajectory(npt=npt)

    def compute_trajectory_correction(self):
        self.traj_delta = {}
        for motor_key in _johann_spectrometer_motor_keys:
            pos_act = np.array(self.config['bragg_registration']['pos_act'][motor_key])
            pos_nom = np.array(self.config['bragg_registration']['pos_nom'][motor_key])
            delta =  pos_act - pos_nom
            bragg = np.array(self.config['bragg_registration']['bragg'][motor_key])
            bragg_in = self.traj_nom['bragg']
            self.traj_delta[motor_key] = extrapolate_linearly(bragg_in, bragg, delta)
            # self.traj[motor_key] = self.traj[motor_key] + self.traj_delta[motor_key]
        self.traj_delta = pd.DataFrame(self.traj_delta)
        self.traj = self.traj_nom.copy()
        self.traj[self.traj_delta.columns] = self.traj[self.traj_delta.columns] + self.traj_delta

    def compute_trajectories(self):
        self.compute_nominal_trajectory()
        self.update_nominal_trajectory_for_detector(self.det_focus, force_update=True)
        self.compute_trajectory_correction()

    # def _convert_motor_pos_nom2act(self, motor_key, pos):
    #     if motor_key in self.converter_nom2act.keys():
    #         pos = self.converter_nom2act[motor_key].nom2act(pos)
    #     return pos
    #
    # def _convert_motor_pos_act2nom(self, motor_key, pos):
    #     if motor_key in self.converter_nom2act.keys():
    #         pos = self.converter_nom2act[motor_key].act2nom(pos)
    #     return pos

    def register_bragg(self, bragg_act, motor_pos_dict):
        pos_nom = {}
        for motor_key in motor_pos_dict.keys():
            print(motor_key)
            pos_nom[motor_key] = self.compute_motor_position(motor_key, bragg_act, nom2act=False)
        pos_act = {**motor_pos_dict}
        for motor_key in pos_act.keys():
            # self.converter_nom2act[motor_key].append_point(pos_nom[motor_key], pos_act[motor_key])
            self.config['bragg_registration']['bragg'][motor_key].append(bragg_act)
            self.config['bragg_registration']['pos_nom'][motor_key].append(pos_nom[motor_key])
            self.config['bragg_registration']['pos_act'][motor_key].append(pos_act[motor_key])

        self.compute_trajectory_correction()
        self.save_current_spectrometer_config_to_settings()

    # @property
    # def traj(self):
    #
    #     return self.traj_nom + self.traj_delta

    def register_energy(self, energy_act, motor_pos_dict):
        bragg_act = self.e2bragg(energy_act)
        self.register_bragg(bragg_act, motor_pos_dict)

    def reset_bragg_registration(self):
        self.config['bragg_registration'] = {'bragg' :  {k: [] for k in _johann_spectrometer_motor_keys},
                                             'pos_nom': {k: [] for k in _johann_spectrometer_motor_keys},
                                             'pos_act': {k: [] for k in _johann_spectrometer_motor_keys}}
        self.compute_trajectory_correction()
        # for motor_key in _johann_spectrometer_motor_keys:
        #     self.converter_nom2act[motor_key] = Nominal2ActualConverterWithLinearInterpolation()

    def plot_motor_pos_vs_bragg(self, motor_key, fignum=1):
        bragg = self.traj['bragg']
        pos = self.compute_motor_position(motor_key, bragg)
        plt.figure(fignum, clear=True)
        plt.plot(bragg, pos)

    def _compute_motor_position(self, motor_key, bragg, nom2act=True):
        if nom2act:
            pos = np.interp(bragg, self.traj['bragg'], self.traj[motor_key])
        else:
            pos = np.interp(bragg, self.traj_nom['bragg'], self.traj_nom[motor_key])

        if motor_key in self.config['parking'].keys():
            pos0 = self.config['parking'][motor_key]
        else:
            pos0 = 0
        pos += pos0
        return pos

    def compute_motor_position(self, motor_keys, bragg, nom2act=True):
        if type(motor_keys) == str:
            return self._compute_motor_position(motor_keys, bragg, nom2act=nom2act)
        else:
            output = {}
            for motor_key in motor_keys:
                output[motor_key] = self._compute_motor_position(motor_key, bragg, nom2act=nom2act)
            return output

    def compute_motor_position_from_energy(self, motor_keys, energy, nom2act=True, use_energy_calibration=True):
        if use_energy_calibration and (self.energy_converter is not None):
            energy = self.energy_converter.act2nom(energy)
        bragg = e2bragg(energy, self.crystal, self.hkl)
        return self.compute_motor_position(motor_keys, bragg, nom2act=nom2act)

    def compute_bragg_from_motor(self, motor_key, pos, nom2act=True):
        if motor_key in self.config['parking'].keys():
            pos0 = self.config['parking'][motor_key]
        else:
            pos0 = 0

        if nom2act:
            bragg = np.interp(pos - pos0, self.traj[motor_key], self.traj['bragg'])
        else:
            bragg = np.interp(pos - pos0, self.traj_nom[motor_key], self.traj_nom['bragg'])

        # if nom2act:
        #     pos = self.converter_nom2act[motor_key].act2nom(pos)
            # pos = self._convert_motor_pos_act2nom(motor_key, pos)

        # vs = self.traj[motor_key]
        # bs = self.traj['bragg']
        # bragg = np.interp(pos - pos0, vs[bs <= 90],  bs[bs <= 90])

        if bragg > 90:
            bragg = 180 - bragg
        return bragg

    def compute_energy_from_motor(self, motor_key, pos, nom2act=True, use_energy_calibration=True):
        bragg = self.compute_bragg_from_motor(motor_key, pos, nom2act=nom2act)
        energy = bragg2e(bragg, self.crystal, self.hkl)
        if use_energy_calibration and (self.energy_converter is not None):
            energy = self.energy_converter.nom2act(energy)
        return energy

    def compute_bragg_from_motor_dict(self, motor_pos_dict, nom2act=True):
        output = {}
        for motor_key, motor_pos in motor_pos_dict.items():
            output[motor_key] = self._compute_motor_position(motor_key, motor_pos, nom2act=nom2act)

    def e2bragg(self, energy):
        return e2bragg(energy, self.crystal, self.hkl)

    def bragg2e(self, bragg):
        return bragg2e(bragg, self.crystal, self.hkl)

    def e2reflectivity(self, energy):
        bragg = self.e2bragg(energy)
        return crystal_reflectivity(self.crystal, self.hkl, bragg, energy)

    def suggest_roll_offset(self, bragg_target, roll_range=5):
        offsets = np.array(self.allowed_roll_offsets)
        offset_braggs = 90 - offsets
        options = np.isclose(bragg_target, offset_braggs, atol=roll_range)
        return offsets[options][0]

    # def append_energy_converter(self, ec):
    #     self.energy_converter = ec

rowland_circle = RowlandCircle()

# def suggest_roll_offsets(bragg_target, roll_range=5):

# bragg_target = 85
# allowed_roll_offsets = [2.5, 11.5, 20.5]
# offsets = np.array(allowed_roll_offsets)
# offset_braggs = 90 - offsets
#
# print(offsets[options][0])

# rowland_circle.det_focus =
# rowland_circle.update_nominal_trajectory_for_detector(-8)
# johann_det_arm.position_dict
# johann_main_crystal.position_dict

# rowland_circle.plot_motor_pos_vs_bragg('motor_det_th1')
# ___nom = rc.compute_motor_position('motor_cr_assy_x', 85.0, nom2act=False)
# rc.register_bragg(85.1, {'motor_cr_assy_x' : ___nom})
#
# _bragg = np.linspace(65, 90, 101)
# _x_nom = rc.compute_motor_position('motor_cr_assy_x', _bragg, nom2act=False)
# _x_act = rc.compute_motor_position('motor_cr_assy_x', _bragg, nom2act=True)
#
# plt.figure(1, clear=True)
# plt.subplot(211)
# plt.plot(_bragg, _x_nom)
# plt.plot(_bragg, _x_act)
#
# plt.hlines(___nom, 65, 90, colors='k')
# plt.vlines(85.0, _x_nom.min(), _x_nom.max(), colors='k')
# plt.vlines(85.1, _x_nom.min(), _x_nom.max(), colors='k')
#
# plt.subplot(212)
# plt.plot(_bragg, _x_act - _x_nom)
#
#
# rc.compute_motor_position('motor_cr_assy_x', 85.0, nom2act=False) - rc.compute_motor_position('motor_cr_assy_x', 85.1, nom2act=False)
# rc.compute_motor_position('motor_cr_assy_x', 85.2, nom2act=False) - rc.compute_motor_position('motor_cr_assy_x', 85.1, nom2act=False)
#
# rc.compute_motor_position('motor_cr_assy_x', 85.0, nom2act=True) - rc.compute_motor_position('motor_cr_assy_x', 85.1, nom2act=True)
# rc.compute_motor_position('motor_cr_assy_x', 85.1, nom2act=True) - rc.compute_motor_position('motor_cr_assy_x', 85.2, nom2act=True)

from collections import namedtuple
class ISSPseudoPositioner(PseudoPositioner):

    def __init__(self, *args, **kwargs):
        self.pseudo_keys = [k for k, _ in self._get_pseudo_positioners()]
        self.real_keys = [k for k, _ in self._get_real_positioners()]
        self.motor_keys = self.pseudo_keys + self.real_keys
        super().__init__(*args, **kwargs)

    def pseudo_pos2dict(self, pseudo_pos):
        ret = {k: getattr(pseudo_pos, k) for k in self.pseudo_keys}
        for k in ret.keys():
            if ret[k] is None:
                try:
                    ret[k] = getattr(self, k).position
                except:
                    ttime.sleep(1)
                    ret[k] = getattr(self, k).position
        return ret

    def real_pos2dict(self, real_pos):
        ret = {k: getattr(real_pos, k) for k in self.real_keys}
        for k in ret.keys():
            if ret[k] is None:
                try:
                    ret[k] = getattr(self, k).position
                except:
                    ttime.sleep(1)
                    ret[k] = getattr(self, k).position
        return ret

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        pseudo_dict = self.pseudo_pos2dict(pseudo_pos)
        real_dict = self._forward(pseudo_dict)
        return self.RealPosition(**real_dict)

    @real_position_argument
    def inverse(self, real_pos):
        real_dict = self.real_pos2dict(real_pos)
        pseudo_dict = self._inverse(real_dict)
        return self.PseudoPosition(**pseudo_dict)

    @property
    def position_dict(self):
        return self.pseudo_pos2dict(self.position)

    @property
    def real_position_dict(self):
        return self.real_pos2dict(self.real_position)


class JohannPseudoPositioner(ISSPseudoPositioner):
    rowland_circle = rowland_circle

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

# inclinometer1 = 12222 - th1 = 0.0
# inclinometer1 = 12877 - th1 = -7.366
# inclinometer1 = 11780 - th1 = 4.866


class JohannDetectorArm(JohannPseudoPositioner):
    motor_det_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
    motor_det_th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta1}Mtr')  # give better names
    motor_det_th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta2}Mtr')

    bragg = Cpt(PseudoSingle, name='bragg')
    det_focus = Cpt(PseudoSingle, name='det_focus')

    _real = ['motor_det_x', 'motor_det_th1', 'motor_det_th2']
    _pseudo = ['bragg', 'det_focus']

    def _forward(self, pseudo_dict):
        bragg, det_focus = pseudo_dict['bragg'], pseudo_dict['det_focus']
        self.rowland_circle.det_focus = det_focus
        return self.rowland_circle.compute_motor_position(self.real_keys, bragg)

    def _inverse(self, real_dict):
        motor_det_th1 = real_dict['motor_det_th1']
        bragg = self.rowland_circle.compute_bragg_from_motor('motor_det_th1', motor_det_th1)
        det_focus = self.rowland_circle.det_focus
        return {'bragg': bragg, 'det_focus' : det_focus}


johann_det_arm = JohannDetectorArm(name='johann_detector_arm')



class JohannMainCrystal(JohannPseudoPositioner):

    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
    motor_cr_main_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
    motor_cr_main_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')

    bragg = Cpt(PseudoSingle, name='bragg')

    _real = ['motor_cr_assy_x', 'motor_cr_assy_y', 'motor_cr_main_roll', 'motor_cr_main_yaw']
    _pseudo = ['bragg']

    def _forward(self, pseudo_dict):
        bragg = pseudo_dict['bragg']
        return self.rowland_circle.compute_motor_position(self.real_keys, bragg)

    def _inverse(self, real_dict):
        motor_cr_main_roll = real_dict['motor_cr_main_roll']
        bragg = self.rowland_circle.compute_bragg_from_motor('motor_cr_main_roll', motor_cr_main_roll)
        return {'bragg': bragg}

johann_main_crystal = JohannMainCrystal(name='johann_main_crystal')


class JohannAux2Crystal(JohannPseudoPositioner):
    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
    motor_cr_aux2_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:X}Mtr')
    motor_cr_aux2_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Y}Mtr')
    motor_cr_aux2_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Roll}Mtr')
    motor_cr_aux2_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Yaw}Mtr')

    bragg = Cpt(PseudoSingle, name='bragg')
    _real = ['motor_cr_assy_x', 'motor_cr_assy_y',
             'motor_cr_aux2_x', 'motor_cr_aux2_y', 'motor_cr_aux2_roll', 'motor_cr_aux2_yaw']
    _pseudo = ['bragg']

    def _forward(self, pseudo_dict):
        bragg = pseudo_dict['bragg']
        return self.rowland_circle.compute_motor_position(self.real_keys, bragg)

    def _inverse(self, real_dict):
        motor_cr_aux2_roll = real_dict['motor_cr_aux2_roll']
        bragg = self.rowland_circle.compute_bragg_from_motor('motor_cr_aux2_roll', motor_cr_aux2_roll)
        return {'bragg': bragg}

johann_aux2_crystal = JohannAux2Crystal(name='johann_aux2_crystal')

class JohannAux3Crystal(JohannPseudoPositioner):
    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
    motor_cr_aux3_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:X}Mtr')
    motor_cr_aux3_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Y}Mtr')
    motor_cr_aux3_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Roll}Mtr')
    motor_cr_aux3_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Yaw}Mtr')

    bragg = Cpt(PseudoSingle, name='bragg')
    _real = ['motor_cr_assy_x', 'motor_cr_assy_y',
             'motor_cr_aux3_x', 'motor_cr_aux3_y', 'motor_cr_aux3_roll', 'motor_cr_aux3_yaw']
    _pseudo = ['bragg']

    def _forward(self, pseudo_dict):
        bragg = pseudo_dict['bragg']
        return self.rowland_circle.compute_motor_position(self.real_keys, bragg)

    def _inverse(self, real_dict):
        motor_cr_aux3_roll = real_dict['motor_cr_aux3_roll']
        bragg = self.rowland_circle.compute_bragg_from_motor('motor_cr_aux3_roll', motor_cr_aux3_roll)
        return {'bragg': bragg}

johann_aux3_crystal = JohannAux3Crystal(name='johann_aux3_crystal')


class JohannSpectrometerX(JohannPseudoPositioner):
    motor_det_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')

    x = Cpt(PseudoSingle, name='x')

    _real = ['motor_det_x', 'motor_cr_assy_x']
    _pseudo = ['x']

    aligned = True

    def _compute_pos_nom(self):
        # instead of real keys we use hard-coded keys for the motors !
        bragg_det_arm = johann_det_arm.bragg.position
        pos_nom_det_arm = self.rowland_circle.compute_motor_position(['motor_det_x'], bragg_det_arm, nom2act=True)

        bragg_cr_main = johann_main_crystal.bragg.position
        pos_nom_cr_main = self.rowland_circle.compute_motor_position(['motor_cr_assy_x'], bragg_cr_main, nom2act=True)

        return {**pos_nom_det_arm, **pos_nom_cr_main}


    def _forward(self, pseudo_dict):
        x = pseudo_dict['x']
        # bragg = johann_spectrometer.bragg.position
        # pos_nom = self.rowland_circle.compute_motor_position(self.real_keys, bragg, nom2act=False)
        pos_nom = self._compute_pos_nom()
        pos_act = {}
        for key in pos_nom.keys():
            pos_act[key] = pos_nom[key] + x
        return pos_act

    def _inverse(self, pos_act):
        # bragg = johann_spectrometer.bragg.position
        # pos_nom = self.rowland_circle.compute_motor_position(self.real_keys, bragg, nom2act=False)
        pos_nom = self._compute_pos_nom()
        x = [(pos_act[k] - pos_nom[k]) for k in self.real_keys]
        self.aligned = np.all(np.isclose(x, x[0], atol=5e-3))
        return {'x' : np.mean(x)}

johann_spectrometer_x = JohannSpectrometerX(name='johann_spectrometer_x')


class JohannCrystalHoming(Device):
    cr_main_roll_home = Cpt(EpicsSignal, '1:Roll}Mtr.HOMF')
    cr_main_yaw_home = Cpt(EpicsSignal, '1:Yaw}Mtr.HOMF')

    cr_aux2_roll_home = Cpt(EpicsSignal, '2:Roll}Mtr.HOMF')
    cr_aux2_yaw_home = Cpt(EpicsSignal, '2:Yaw}Mtr.HOMF')
    cr_aux2_x_home = Cpt(EpicsSignal, '2:X}Mtr.HOMF')
    cr_aux2_y_home = Cpt(EpicsSignal, '2:Y}Mtr.HOMF')

    cr_aux3_roll_home = Cpt(EpicsSignal, '3:Roll}Mtr.HOMF')
    cr_aux3_yaw_home = Cpt(EpicsSignal, '3:Yaw}Mtr.HOMF')
    cr_aux3_x_home = Cpt(EpicsSignal, '3:X}Mtr.HOMF')
    cr_aux3_y_home = Cpt(EpicsSignal, '3:Y}Mtr.HOMF')

    def home_all_axes(self):
        for component in self.component_names:
            cpt = getattr(self, component)
            cpt.put(1)


class JohannMultiCrystalPseudoPositioner(JohannPseudoPositioner):
    _real = _johann_spectrometer_motor_keys
        # ['motor_det_x', 'motor_det_th1', 'motor_det_th2',
        #      'motor_cr_assy_x', 'motor_cr_assy_y', 'motor_cr_main_roll', 'motor_cr_main_yaw',  # ]
        #      'motor_cr_aux2_x', 'motor_cr_aux2_y', 'motor_cr_aux2_roll', 'motor_cr_aux2_yaw',
        #      'motor_cr_aux3_x', 'motor_cr_aux3_y', 'motor_cr_aux3_roll', 'motor_cr_aux3_yaw']

    aligned = True
    piezo_homing = Cpt(JohannCrystalHoming, 'XF:08IDB-OP{HRS:1-Stk:')

    @property
    def initialized(self):
        return self.rowland_circle.initialized

    @initialized.setter
    def initialized(self, value):
        self.rowland_circle.initialized = value

    def __init__(self, *args, **kwargs):
        self.enabled_crystals = self.rowland_circle.enabled_crystals
        super().__init__(*args, **kwargs)

    def enable_crystal(self, crystal_key, enable):
        self.rowland_circle.enable_crystal(crystal_key, enable)

    @property
    def motor_to_bragg_keys(self):
        keys = ['motor_det_th1']
        if self.enabled_crystals['main']: keys.append('motor_cr_main_roll')
        if self.enabled_crystals['aux2']: keys.append('motor_cr_aux2_roll')
        if self.enabled_crystals['aux3']: keys.append('motor_cr_aux3_roll')
        return keys

    def _compute_new_real_positions_for_enabled_crystals(self, bragg):
        new_real_position = self.rowland_circle.compute_motor_position(self.real_keys, bragg)
        for crystal_key, enabled in self.enabled_crystals.items():
            if not enabled: # then find keys that must be static during the motion of enabled crystals
                if crystal_key == 'main':
                    _motor_keys = _johann_cr_main_motor_keys
                elif crystal_key == 'aux2':
                    _motor_keys = _johann_cr_aux2_motor_keys
                elif crystal_key == 'aux3':
                    _motor_keys = _johann_cr_aux3_motor_keys
                else:
                    raise ValueError('this crystal key is not implemented yet')
                for k in _motor_keys:
                    new_real_position[k] = getattr(self, k).position
        return new_real_position

    def _compute_braggs_from_motors(self, real_dict):
        braggs = []
        for key in self.motor_to_bragg_keys:
            pos = real_dict[key]
            bragg = self.rowland_circle.compute_bragg_from_motor(key, pos)
            braggs.append(bragg)

        self.aligned = np.all(np.isclose(braggs, braggs[0], atol=1e-3))
        return braggs

    def home_crystal_piezos(self):
        self.piezo_homing.home_all_axes()


class JohannAllCrystals(JohannMultiCrystalPseudoPositioner):
    _real = _johann_cr_all_motor_keys
    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
    motor_cr_main_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
    motor_cr_main_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')

    motor_cr_aux2_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:X}Mtr')
    motor_cr_aux2_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Y}Mtr')
    motor_cr_aux2_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Roll}Mtr')
    motor_cr_aux2_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Yaw}Mtr')

    motor_cr_aux3_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:X}Mtr')
    motor_cr_aux3_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Y}Mtr')
    motor_cr_aux3_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Roll}Mtr')
    motor_cr_aux3_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Yaw}Mtr')

    bragg = Cpt(PseudoSingle, name='bragg')

    _pseudo = ['bragg']

    @property
    def motor_to_bragg_keys(self):
        keys = []
        if self.enabled_crystals['main']: keys.append('motor_cr_main_roll')
        if self.enabled_crystals['aux2']: keys.append('motor_cr_aux2_roll')
        if self.enabled_crystals['aux3']: keys.append('motor_cr_aux3_roll')
        return keys

    def _forward(self, pseudo_dict):
        bragg = pseudo_dict['bragg']
        new_real_positions = self._compute_new_real_positions_for_enabled_crystals(bragg)
        return new_real_positions

    def _inverse(self, real_dict):
        braggs = self._compute_braggs_from_motors(real_dict)
        return {'bragg': np.mean(braggs)}

johann_all_crystals = JohannAllCrystals(name='johann_all_crystals')

class JohannSpectrometer(JohannMultiCrystalPseudoPositioner):
    motor_det_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
    motor_det_th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta1}Mtr')  # give better names
    motor_det_th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta2}Mtr')

    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
    motor_cr_main_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
    motor_cr_main_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')

    motor_cr_aux2_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:X}Mtr')
    motor_cr_aux2_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Y}Mtr')
    motor_cr_aux2_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Roll}Mtr')
    motor_cr_aux2_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Yaw}Mtr')

    motor_cr_aux3_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:X}Mtr')
    motor_cr_aux3_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Y}Mtr')
    motor_cr_aux3_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Roll}Mtr')
    motor_cr_aux3_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Yaw}Mtr')

    bragg = Cpt(PseudoSingle, name='bragg')

    _pseudo = ['bragg']

    def _forward(self, pseudo_dict):
        bragg = pseudo_dict['bragg']
        new_real_positions = self._compute_new_real_positions_for_enabled_crystals(bragg)
        return new_real_positions

    def _inverse(self, real_dict):
        braggs = self._compute_braggs_from_motors(real_dict)
        return {'bragg': np.mean(braggs)}

johann_spectrometer = JohannSpectrometer(name='johann_spectrometer')

class JohannEmission(JohannMultiCrystalPseudoPositioner):
    motor_det_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
    motor_det_th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta1}Mtr')  # give better names
    motor_det_th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta2}Mtr')

    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
    motor_cr_main_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
    motor_cr_main_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')

    motor_cr_aux2_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:X}Mtr')
    motor_cr_aux2_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Y}Mtr')
    motor_cr_aux2_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Roll}Mtr')
    motor_cr_aux2_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Yaw}Mtr')

    motor_cr_aux3_x = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:X}Mtr')
    motor_cr_aux3_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Y}Mtr')
    motor_cr_aux3_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Roll}Mtr')
    motor_cr_aux3_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:3:Yaw}Mtr')

    energy = Cpt(PseudoSingle, name='energy')
    _pseudo = ['energy']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        e_lo, e_hi = self.rowland_circle.config['energy_limits']
        self._set_energy_limits(e_lo, e_hi)

    def _forward(self, pseudo_dict):
        energy = pseudo_dict['energy']
        bragg = self.rowland_circle.e2bragg(energy)
        new_real_positions = self._compute_new_real_positions_for_enabled_crystals(bragg)
        return new_real_positions

    def _inverse(self, real_dict):
        braggs = self._compute_braggs_from_motors(real_dict)
        bragg = np.mean(braggs)
        energy = self.rowland_circle.bragg2e(bragg)
        return {'energy': np.mean(energy)}

    # ops functions

    def move_crystals_to_90_deg(self):
        self.set_roll_offset(2.5)
        johann_main_crystal.move(bragg=90)
        johann_aux2_crystal.move(bragg=90)
        johann_aux3_crystal.move(bragg=90)

    def set_det_arm_parking(self):
        self.rowland_circle.set_det_arm_parking(self.real_position_dict)

    def read_det_arm_parking(self):
        return self.rowland_circle.det_arm_parking()

    def set_main_crystal_parking(self):
        self.rowland_circle.set_main_crystal_parking(self.real_position_dict)

    def read_main_crystal_parking(self):
        return self.rowland_circle.main_crystal_parking(human_readable=True)

    def set_aux2_crystal_parking(self):
        self.rowland_circle.set_aux2_crystal_parking(self.real_position_dict)

    def read_aux2_crystal_parking(self):
        return self.rowland_circle.aux2_crystal_parking(human_readable=True)

    def set_aux3_crystal_parking(self):
        self.rowland_circle.set_aux3_crystal_parking(self.real_position_dict)

    def read_aux3_crystal_parking(self):
        return self.rowland_circle.aux3_crystal_parking(human_readable=True)

    def register_energy(self, energy):
        self.rowland_circle.register_energy(energy, self.real_position_dict)

    def reset_config(self):
        self.rowland_circle.reset_bragg_registration()
        self.rowland_circle.reset_spectrometer_calibration()

    def put_detector_to_safe_position(self):
        self.motor_det_x.move(335)
        self.motor_det_th1.move(0)
        self.motor_det_th2.move(0)

    def set_spectrometer_calibration(self, x_nom, x_act, n_poly=2):
        self.rowland_circle.set_spectrometer_calibration(x_nom, x_act, n_poly=n_poly)

    def _set_energy_limits(self, e_lo, e_hi):
        self.energy._limits = (e_lo, e_hi)

    def set_energy_limits(self, e_lo, e_hi):
        self.rowland_circle.energy_limits = [e_lo, e_hi]
        self._set_energy_limits(e_lo, e_hi)

    def reset_energy_limits(self):
        self.rowland_circle.energy_limits = [0, 0]
        self.energy._limits = (0, 0)

    def set_crystal(self, value):
        self.rowland_circle.crystal = value

    def set_hkl(self, value):
        self.rowland_circle.hkl = value

    def set_R(self, value):
        self.rowland_circle.R = value

    def set_roll_offset(self, value):
        self.rowland_circle.roll_offset = value

    @property
    def allowed_roll_offsets(self):
        return self.rowland_circle.allowed_roll_offsets

    def suggest_roll_offset(self, target_bragg):
        return self.rowland_circle.suggest_roll_offset(target_bragg)

    def bragg2e(self, bragg):
        return self.rowland_circle.bragg2e(bragg)

    def e2bragg(self, energy):
        return self.rowland_circle.e2bragg(energy)

    def e2reflectivity(self, energy):
        return self.rowland_circle.e2reflectivity(energy)

    def read_basic_crystal_config(self):
        return self.rowland_circle.crystal, self.rowland_circle.R, self.rowland_circle.hkl, self.rowland_circle.roll_offset

    # def move(self, position, step_size=0.5, **kwargs):
    #     old_position = self.energy.position
    #     n_steps = int(np.abs(position - old_position) / step_size + 1)
    #     _positions = np.linspace(old_position, position, n_steps)[1:]
    #     if _positions.size == 0:
    #         ret = NullStatus()
    #     else:
    #         for _pos in _positions:
    #             print_to_gui(f'Spectrometer moving to {_pos}')
    #             ret = super().move(_pos, **kwargs)
    #     return ret
    #
    # def set(self, *args, wait=True, **kwargs):
    #     return super().set(*args, wait=wait, **kwargs)

johann_emission = JohannEmission(name='johann_emission')


# johann_emission.energy._limits=(8004, 8068)


_johann_motor_dictionary = {
'auxxy_x':                  {'name': auxxy.x.name,                                     'description': 'Johann Crystal Assy X',        'keyword': 'Crystal Assy X',            'object': auxxy.x,                                  'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
'auxxy_y':                  {'name': auxxy.y.name,                                     'description': 'Johann Detector X',            'keyword': 'Detector X',                'object': auxxy.y,                                  'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
'johann_cr_main_roll':      {'name': johann_main_crystal.motor_cr_main_roll.name,      'description': 'Johann Main Crystal Roll',     'keyword': 'Main Roll',                 'object': johann_main_crystal.motor_cr_main_roll,           'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
'johann_cr_main_yaw':       {'name': johann_main_crystal.motor_cr_main_yaw.name,       'description': 'Johann Main Crystal Yaw',      'keyword': 'Main Yaw',                  'object': johann_main_crystal.motor_cr_main_yaw,            'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
'johann_cr_aux2_roll':      {'name': johann_aux2_crystal.motor_cr_aux2_roll.name,      'description': 'Johann Aux2 Crystal Roll',     'keyword': 'Aux2 Roll',                 'object': johann_aux2_crystal.motor_cr_aux2_roll,           'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
'johann_cr_aux2_yaw':       {'name': johann_aux2_crystal.motor_cr_aux2_yaw.name,       'description': 'Johann Aux2 Crystal Yaw',      'keyword': 'Aux2 Yaw',                  'object': johann_aux2_crystal.motor_cr_aux2_yaw,            'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
'johann_cr_aux2_x':         {'name': johann_aux2_crystal.motor_cr_aux2_x.name,         'description': 'Johann Aux2 Crystal X',        'keyword': 'Aux2 X',                    'object': johann_aux2_crystal.motor_cr_aux2_x,              'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2500},
'johann_cr_aux2_y':         {'name': johann_aux2_crystal.motor_cr_aux2_y.name,         'description': 'Johann Aux2 Crystal Y',        'keyword': 'Aux2 Y',                    'object': johann_aux2_crystal.motor_cr_aux2_y,              'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 1000},
'johann_cr_aux3_roll':      {'name': johann_aux3_crystal.motor_cr_aux3_roll.name,      'description': 'Johann Aux3 Crystal Roll',     'keyword': 'Aux3 roll',                 'object': johann_aux3_crystal.motor_cr_aux3_roll,           'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
'johann_cr_aux3_yaw':       {'name': johann_aux3_crystal.motor_cr_aux3_yaw.name,       'description': 'Johann Aux3 Crystal Yaw',      'keyword': 'Aux3 Yaw',                  'object': johann_aux3_crystal.motor_cr_aux3_yaw,            'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
'johann_cr_aux3_x':         {'name': johann_aux3_crystal.motor_cr_aux3_x.name,         'description': 'Johann Aux3 Crystal X',        'keyword': 'Aux3 X',                    'object': johann_aux3_crystal.motor_cr_aux3_x,              'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2500},
'johann_cr_aux3_y':         {'name': johann_aux3_crystal.motor_cr_aux3_y.name,         'description': 'Johann Aux3 Crystal Y',        'keyword': 'Aux3 Y',                    'object': johann_aux3_crystal.motor_cr_aux3_y,              'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 1000},
'johann_cr_main_bragg':     {'name': johann_main_crystal.bragg.name,                   'description': 'Johann Main Crystal Bragg',    'keyword': 'Main Bragg',                'object': johann_main_crystal.bragg,                        'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_cr_aux2_bragg':     {'name': johann_aux2_crystal.bragg.name,                   'description': 'Johann Aux2 Crystal Bragg',    'keyword': 'Aux2 Bragg',                'object': johann_aux2_crystal.bragg,                        'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_cr_aux3_bragg':     {'name': johann_aux3_crystal.bragg.name,                   'description': 'Johann Aux3 Crystal Bragg',    'keyword': 'Aux3 Bragg',                'object': johann_aux3_crystal.bragg,                        'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_det_focus':         {'name': johann_det_arm.det_focus.name,                    'description': 'Johann Detector Focus',        'keyword': 'Detector Focus',            'object': johann_det_arm.det_focus,                 'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 5},
'johann_x':                 {'name': johann_spectrometer_x.x.name,                     'description': 'Johann Spectrometer X',        'keyword': 'Spectrometer X',            'object': johann_spectrometer_x.x,                  'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
'johann_bragg_angle':       {'name': johann_spectrometer.bragg.name,                   'description': 'Johann Global Bragg Angle',    'keyword': 'Global Bragg Angle',        'object': johann_spectrometer.bragg,                'group': 'spectrometer',  'user': True,  'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_energy':            {'name': johann_emission.energy.name,                      'description': 'Johann Emission Energy',       'keyword': 'Emission Energy',           'object': johann_emission.energy,                   'group': 'spectrometer',  'user': True,  'spectrometer_kind': 'johann', 'typical_step': 1},
}

motor_dictionary = {**motor_dictionary, **_johann_motor_dictionary}
