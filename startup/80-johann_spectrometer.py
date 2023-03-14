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


from xas.xray import bragg2e, e2bragg, crystal_reflectivity
from xas.spectrometer import compute_rowland_circle_geometry, _compute_rotated_rowland_circle_geometry

_BIG_DETECTOR_ARM_LENGTH = 550 # length of the big arm
_SMALL_DETECTOR_ARM_LENGTH = 91 # distance between the second gon and the sensitive surface of the detector

_johann_det_arm_motor_keys = ['motor_det_x', 'motor_det_th1', 'motor_det_th2']
_johann_cr_assy_motor_keys = ['motor_cr_assy_x', 'motor_cr_assy_y']
_johann_cr_main_motor_keys = ['motor_cr_main_roll', 'motor_cr_main_yaw']
_johann_cr_aux2_motor_keys = ['motor_cr_aux2_x', 'motor_cr_aux2_y', 'motor_cr_aux2_roll', 'motor_cr_aux2_yaw']
_johann_cr_aux3_motor_keys = ['motor_cr_aux3_x', 'motor_cr_aux3_y', 'motor_cr_aux3_roll', 'motor_cr_aux3_yaw']

_johann_spectrometer_motor_keys = (_johann_det_arm_motor_keys +
                                   _johann_cr_assy_motor_keys +
                                   _johann_cr_main_motor_keys +
                                   _johann_cr_aux2_motor_keys +
                                   _johann_cr_aux3_motor_keys)

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

        self.init_from_settings()

        self.compute_nominal_trajectory()
        self.update_nominal_trajectory_for_detector(self.det_focus, force_update=True)

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
            config = { 'initialized': True,
                       'R' : 1000,
                       'crystal' : 'Si',
                       'hkl' : [6, 2, 0],
                       'enabled_crystals': {'main': True, 'aux2': True, 'aux3': True},
                       'parking': { 'motor_det_x': -10.0,  # high limit of this motor should be at 529 mm
                                    'motor_det_th1': 0.0,
                                    'motor_det_th2': 0.0,
                                    'motor_cr_assy_x': 0.000,
                                    'motor_cr_assy_y': 5.682,
                                    'motor_cr_main_roll': -100.0,
                                    'motor_cr_main_yaw': 560.0,
                                    'motor_cr_aux2_x': 0,
                                    'motor_cr_aux2_y': -9420.0,
                                    'motor_cr_aux2_roll': -330,
                                    'motor_cr_aux2_yaw': -790.0,
                                    'motor_cr_aux3_x': 0,
                                    'motor_cr_aux3_y': -3100.0,
                                    'motor_cr_aux3_roll': -350,
                                    'motor_cr_aux3_yaw': 1320,
                                    },
                       'roll_offset' : 3.00,
                       'det_offsets': { 'motor_det_th1': 69.0,
                                        'motor_det_th2': -69.0},
                       'det_focus' : 10.0,
                       'bragg_registration' : {'pos_nom' : {k : [] for k in _johann_spectrometer_motor_keys},
                                               'pos_act' : {k : [] for k in _johann_spectrometer_motor_keys}},
                       'energy_calibration' : {'x_nom': [],
                                               'x_act': [],
                                               'n_poly': 2},
                       }
        self.set_spectrometer_config(config)

    def set_spectrometer_config(self, config):
        # config needs a validation may be
        self.config = config

        if 'bragg_registration' in config.keys():
            self.converter_nom2act = {}
            for motor_key in _johann_spectrometer_motor_keys:
                _c_nom2act = Nominal2ActualConverterWithLinearInterpolation()
                pos_nom = config['bragg_registration']['pos_nom'][motor_key]
                pos_act = config['bragg_registration']['pos_act'][motor_key]
                for _pos_nom, _pos_act in zip(pos_nom, pos_act):
                    _c_nom2act.append_point(_pos_nom, _pos_act)
                self.converter_nom2act[motor_key] = _c_nom2act

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
        return self.config['det_focus']

    @det_focus.setter
    def det_focus(self, value):
        self.config['det_focus'] = value

    @property
    def R(self):
        return self.config['R']

    @R.setter
    def R(self, value):
        self.config['parking']['motor_cr_assy_x'] += (self.config['R'] - value)
        self.config['R'] = value

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
        self.compute_nominal_trajectory()
        self.update_nominal_trajectory_for_detector(self.det_focus, force_update=True)
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

        return {'bragg' :               braggs,
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
                'motor_cr_aux3_yaw':    motor_cr_aux3_yaw}

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
            self.det_focus = det_focus
            motor_det_x, motor_det_th1, motor_det_th2 = self._compute_trajectory_for_detector(self.traj['bragg'],
                                                                                              self.traj['det_x'],
                                                                                              self.traj['det_y'],
                                                                                              det_focus=det_focus)
            self.traj['motor_det_x'] = motor_det_x
            self.traj['motor_det_th1'] = motor_det_th1
            self.traj['motor_det_th2'] = motor_det_th2


    def compute_nominal_trajectory(self, npt=250):
        self.traj = self._compute_nominal_trajectory(npt=npt)

    def _convert_motor_pos_nom2act(self, motor_key, pos):
        if motor_key in self.converter_nom2act.keys():
            pos = self.converter_nom2act[motor_key].nom2act(pos)
        return pos

    def _convert_motor_pos_act2nom(self, motor_key, pos):
        if motor_key in self.converter_nom2act.keys():
            pos = self.converter_nom2act[motor_key].act2nom(pos)
        return pos

    def register_bragg(self, bragg_act, motor_pos_dict):
        pos_nom = {}
        for motor_key in motor_pos_dict.keys():
            pos_nom[motor_key] = self.compute_motor_position(motor_key, bragg_act, nom2act=False)
        pos_act = {**motor_pos_dict}
        for motor_key in pos_act.keys():
            self.converter_nom2act[motor_key].append_point(pos_nom[motor_key], pos_act[motor_key])
            self.config['bragg_registration']['pos_nom'][motor_key].append(pos_nom[motor_key])
            self.config['bragg_registration']['pos_act'][motor_key].append(pos_act[motor_key])
        self.save_current_spectrometer_config_to_settings()

    def register_energy(self, energy_act, motor_pos_dict):
        bragg_act = self.e2bragg(energy_act)
        self.register_bragg(bragg_act, motor_pos_dict)

    def reset_bragg_registration(self):
        self.config['bragg_registration'] = {'pos_nom': {k: [] for k in _johann_spectrometer_motor_keys},
                                             'pos_act': {k: [] for k in _johann_spectrometer_motor_keys}}
        for motor_key in _johann_spectrometer_motor_keys:
            self.converter_nom2act[motor_key] = Nominal2ActualConverterWithLinearInterpolation()

    def plot_motor_pos_vs_bragg(self, motor_key, fignum=1):
        bragg = self.traj['bragg']
        pos = self.compute_motor_position(motor_key, bragg)
        plt.figure(fignum, clear=True)
        plt.plot(bragg, pos)

    def _compute_motor_position(self, motor_key, bragg, nom2act=True):
        pos =  np.interp(bragg, self.traj['bragg'], self.traj[motor_key])
        if motor_key in self.config['parking'].keys():
            pos0 = self.config['parking'][motor_key]
        else:
            pos0 = 0
        pos += pos0
        if nom2act:
            # pos = self.converter_nom2act[motor_key].nom2act(pos)
            pos = self._convert_motor_pos_nom2act(motor_key, pos)
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
        if nom2act:
            # pos = self.converter_nom2act[motor_key].act2nom(pos)
            pos = self._convert_motor_pos_act2nom(motor_key, pos)
        pos0 = self.config['parking'][motor_key]
        vs = self.traj[motor_key]
        bs = self.traj['bragg']
        bragg = np.interp(pos - pos0, vs[bs <= 90],  bs[bs <= 90])

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
        self.rowland_circle.update_nominal_trajectory_for_detector(det_focus)
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

    cr_aux2_roll_home = Cpt(EpicsSignal, '2:Yaw}Mtr.HOMF')
    cr_aux2_yaw_home = Cpt(EpicsSignal, '2:Yaw}Mtr.HOMF')
    cr_aux2_x_home = Cpt(EpicsSignal, '2:X}Mtr.HOMF')
    cr_aux2_y_home = Cpt(EpicsSignal, '2:Y}Mtr.HOMF')

    cr_aux3_roll_home = Cpt(EpicsSignal, '3:Yaw}Mtr.HOMF')
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

    def set_spectrometer_calibration(self, x_nom, x_act, n_poly=2):
        self.rowland_circle.set_spectrometer_calibration(x_nom, x_act, n_poly=n_poly)

    def set_energy_limits(self, e_lo, e_hi):
        self.energy._limits = (e_lo, e_hi)

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


# johann_emission.energy._limits=(6469.9, 6542)


_johann_motor_dictionary = {
'auxxy_x':                  {'name': auxxy.x.name,                                     'description': 'Johann Crystal Assy X',        'object': auxxy.x,                                  'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
'auxxy_y':                  {'name': auxxy.y.name,                                     'description': 'Johann Detector X',            'object': auxxy.y,                                  'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
'johann_cr_main_roll':      {'name': johann_main_crystal.motor_cr_main_roll.name,      'description': 'Johann Main Crystal Roll',     'object': johann_main_crystal.motor_cr_main_roll,   'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
'johann_cr_main_yaw':       {'name': johann_main_crystal.motor_cr_main_yaw.name,       'description': 'Johann Main Crystal Yaw',      'object': johann_main_crystal.motor_cr_main_yaw,    'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
'johann_cr_aux2_roll':      {'name': johann_aux2_crystal.motor_cr_aux2_roll.name,      'description': 'Johann Aux2 Crystal Roll',     'object': johann_aux2_crystal.motor_cr_aux2_roll,   'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
'johann_cr_aux2_yaw':       {'name': johann_aux2_crystal.motor_cr_aux2_yaw.name,       'description': 'Johann Aux2 Crystal Yaw',      'object': johann_aux2_crystal.motor_cr_aux2_yaw,    'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
'johann_cr_aux2_x':         {'name': johann_aux2_crystal.motor_cr_aux2_x.name,         'description': 'Johann Aux2 Crystal X',        'object': johann_aux2_crystal.motor_cr_aux2_x,      'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2500},
'johann_cr_aux2_y':         {'name': johann_aux2_crystal.motor_cr_aux2_y.name,         'description': 'Johann Aux2 Crystal Y',        'object': johann_aux2_crystal.motor_cr_aux2_y,      'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 1000},
'johann_cr_aux3_roll':      {'name': johann_aux3_crystal.motor_cr_aux3_roll.name,      'description': 'Johann Aux3 Crystal roll',     'object': johann_aux3_crystal.motor_cr_aux3_roll,   'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
'johann_cr_aux3_yaw':       {'name': johann_aux3_crystal.motor_cr_aux3_yaw.name,       'description': 'Johann Aux3 Crystal Yaw',      'object': johann_aux3_crystal.motor_cr_aux3_yaw,    'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
'johann_cr_aux3_x':         {'name': johann_aux3_crystal.motor_cr_aux3_x.name,         'description': 'Johann Aux3 Crystal X',        'object': johann_aux3_crystal.motor_cr_aux3_x,      'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2500},
'johann_cr_aux3_y':         {'name': johann_aux3_crystal.motor_cr_aux3_y.name,         'description': 'Johann Aux3 Crystal Y',        'object': johann_aux3_crystal.motor_cr_aux3_y,      'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 1000},
'johann_cr_main_bragg':     {'name': johann_main_crystal.bragg.name,                   'description': 'Johann Main Crystal Bragg',    'object': johann_main_crystal.bragg,                'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_cr_aux2_bragg':     {'name': johann_aux2_crystal.bragg.name,                   'description': 'Johann Aux2 Crystal Bragg',    'object': johann_aux2_crystal.bragg,                'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_cr_aux3_bragg':     {'name': johann_aux3_crystal.bragg.name,                   'description': 'Johann Aux3 Crystal Bragg',    'object': johann_aux3_crystal.bragg,                'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_det_focus':         {'name': johann_det_arm.det_focus.name,                    'description': 'Johann Detector Focus',        'object': johann_det_arm.det_focus,                 'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 5},
'johann_x':                 {'name': johann_spectrometer_x.x.name,                     'description': 'Johann Spectrometer X',        'object': johann_spectrometer_x.x,                  'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
'johann_bragg_angle':       {'name': johann_spectrometer.bragg.name,                   'description': 'Johann Global Bragg Angle',    'object': johann_spectrometer.bragg,                'group': 'spectrometer',  'user': True,  'spectrometer_kind': 'johann', 'typical_step': 0.05},
'johann_energy':            {'name': johann_emission.energy.name,                      'description': 'Johann Emission Energy',       'object': johann_emission.energy,                   'group': 'spectrometer',  'user': True,  'spectrometer_kind': 'johann', 'typical_step': 1},
}

motor_dictionary = {**motor_dictionary, **_johann_motor_dictionary}



# df = []
#
# for _energy in np.linspace(6470, 6540, 101):
#     pos_dict = copy.deepcopy(johann_emission._forward({'energy': _energy}))
#     pos_dict['energy'] = _energy
#     df.append(pos_dict)
#
# df = pd.DataFrame(df)


# johann_crystal_homing = JohannCrystalHoming('XF:08IDB-OP{HRS:1-Stk:', name='johann_crystal_homing')
# johann_crystal_homing.home_all_axes()

# bla = EpicsSignal('XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr.HOMF', name='bla')
# bla.put(1)

# rowland_circle.config['parking']['motor_cr_assy_y'] = 7.682
# johann_spectrometer_x.move(x=-10)
#
#
# johann_spectrometer_x.move(x=10)

# rowland_circle.config['parking']['motor_cr_main_roll'] = -20
# johann_main_crystal.move(bragg=81.73)
#
# rowland_circle.config['parking']['motor_cr_aux2_x'] = -10000
# rowland_circle.config['parking']['motor_cr_aux2_yaw'] = 7150
# rowland_circle.config['parking']['motor_cr_aux2_roll'] = 450
# johann_aux2_crystal.move(bragg=81.73)
#
# rowland_circle.config['parking']['motor_cr_aux3_x'] = -8000
# rowland_circle.config['parking']['motor_cr_aux3_yaw'] = -6750
# rowland_circle.config['parking']['motor_cr_aux3_roll'] = 1000
# johann_aux3_crystal.move(bragg=81.73)

# rowland_circle.config['roll_offset'] = 12.00916586506561# - (82.20916586506561 - 81.70)
# rowland_circle.compute_nominal_trajectory()
# rowland_circle.update_nominal_trajectory_for_detector(-7.992103369546962, force_update=True)

# def compute_rowland_circle_geometry(x_src, y_src, R, bragg_deg, det_dR):
#     bragg = np.deg2rad(bragg_deg)
#
#     x_cr = -R * np.cos(np.pi / 2 - bragg)
#     y_cr = 0
#
#     x_det = +2 * x_cr * np.cos(bragg) * np.cos(bragg) - det_dR * np.cos(np.pi - 2 * bragg)
#     y_det = -2 * x_cr * np.cos(bragg) * np.sin(bragg) - det_dR * np.sin(np.pi - 2 * bragg)
#
#     return (x_cr + x_src), (y_cr + y_src), (x_det + x_src), (y_det + y_src)
#
#
# from scipy.spatial.transform import Rotation
# from scipy.optimize import fsolve
# def compute_rotated_rowland_circle_geometry(x_cr_main, y_cr_main, x_det, y_det, bragg_deg, dz, ax=None, ax2=None):
#     bragg = np.deg2rad(bragg_deg)
#
#     _phi = np.linspace(0, 2*np.pi, 361)
#     _x_o = R/2 * np.cos(_phi) - R/2 * np.sin(bragg)
#     _y_o = R / 2 * np.sin(_phi) + R / 2 * np.cos(bragg)
#     _z_o = np.zeros(_phi.size)
#
#     # rmat_z = Rotation.from_euler('z', -(90 - bragg_deg), degrees=True).as_matrix()
#     # _xyz_o_rot1 = rmat_z @ np.vstack((_x_o, _y_o, _z_o))
#     #
#     # rmat_y = Rotation.from_euler('y', 10, degrees=True).as_matrix()
#     # _xyz_o_rot2 = rmat_y @ _xyz_o_rot1
#     #
#     # rmat_z2 = Rotation.from_euler('z', +(90 - bragg_deg), degrees=True).as_matrix()
#     # _xyz_o_rot3 = rmat_z2 @ _xyz_o_rot2
#
#     def rotate_xyz(xyz, omega):
#         rmat = Rotation.from_euler('zyz', [-(90 - bragg_deg), omega, (90 - bragg_deg)], degrees=True).as_matrix()
#         return rmat @ xyz
#
#     def z_cr_rot_from_rotate_xyz(omega):
#         _, _, z_cr_rot = rotate_xyz(np.array([x_main_cr, y_main_cr, 0]), omega)
#         return z_cr_rot
#
#     def solve_omega_func(omega):
#         z_cr_rot = z_cr_rot_from_rotate_xyz(omega)
#         return z_cr_rot - dz
#
#     omega0 = fsolve(solve_omega_func, dz / 10)
#     print(solve_omega_func(omega0))
#     omega = omega0
#     _xyz_o_rot = rotate_xyz(np.vstack((_x_o, _y_o, _z_o)), omega)
#     x_cr_rot, y_cr_rot, z_cr_rot = rotate_xyz(np.array([x_main_cr, y_main_cr, 0]), omega)
#     x_det_rot, y_det_rot, z_det_rot = rotate_xyz(np.array([x_det, y_det, 0]), omega)
#     # rmat @
#
#     omegas = np.linspace(-90, 90, 181*3)
#     zzs = np.array([z_cr_rot_from_rotate_xyz(v) for v in omegas])
#
#     # x_cr_rot, y_cr_rot, z_cr_rot = rmat @ np.hstack((x_main_cr, y_main_cr, 0))
#     # x_det_rot, y_det_rot, z_det_rot = rmat @ np.hstack((x_det, y_det, 0))
#
#
#     # ax.scatter(_x_o, _y_o, _z_o, marker='.', color='k')
#     # ax.scatter(_xyz_o_rot1[0, :], _xyz_o_rot1[1, :], _xyz_o_rot1[2, :], color='k', marker='.')
#     # ax.scatter(_xyz_o_rot2[0, :], _xyz_o_rot2[1, :], _xyz_o_rot2[2, :], color='k', marker='.')
#     # ax.scatter(_xyz_o_rot3[0, :], _xyz_o_rot3[1, :], _xyz_o_rot3[2, :], color='k', marker='.')
#     # ax.scatter(_xyz_o_rot[0, :], _xyz_o_rot[1, :], _xyz_o_rot[2, :], color='g', marker='.')
#     _s = 50
#     ax.scatter(0, 0, marker='o', color='k', s=_s)
#     ax.scatter(x_cr_main, y_cr_main, 0, marker='o', color='b', s=_s)
#     ax.scatter(x_det, y_det, 0, marker='o', color='r', s=_s)
#
#     ax.scatter(x_cr_rot, y_cr_rot, z_cr_rot,  marker='*', color='b', s=_s)
#     ax.scatter(x_det_rot, y_det_rot, z_det_rot,  marker='*', color='r', s=_s)
#
#     ax.set_xlim(-1000, 400)
#     ax.set_ylim(-600, 800)
#     ax.set_zlim(-700, 700)
#
#
#     ax2.plot(omegas, zzs)
#     ax2.plot(omega0, dz, 'r*')
#
#     # ax.axis('equal')
#     # # x_cr = -R * np.cos(np.pi / 2 - bragg)
#     # # y_cr = 0
#     # #
#     # # x_det = +2 * x_cr * np.cos(bragg) * np.cos(bragg) - det_dR * np.cos(np.pi - 2 * bragg)
#     # # y_det = -2 * x_cr * np.cos(bragg) * np.sin(bragg) - det_dR * np.sin(np.pi - 2 * bragg)
#     # #
#     # return (x_cr + x_src), (y_cr + y_src), (x_det + x_src), (y_det + y_src)
#
# fig = plt.figure(1, clear=True)
# ax = fig.add_subplot(projection='3d')
#
# fig2 = plt.figure(2, clear=True)
# ax2 = fig2.add_subplot()
#
# bragg = 80
# R = 1000
# det_dR = 0
#
# for bragg in np.linspace(65, 88, 3):
#     x_main_cr, y_main_cr, x_det, y_det = compute_rowland_circle_geometry(0, 0, R, bragg, det_dR)
#     compute_rotated_rowland_circle_geometry(x_main_cr, y_main_cr, x_det, y_det, bragg, 139.5, ax=ax, ax2=ax2)




#
# row_circle = RowlandCircle()
# # row_circle.plot_full_range()

# class DetectorArm(Device):
###################
# from xas.spectrometer import compute_rowland_circle_geometry, compute_rotated_rowland_circle_geometry
#
#
# class ISSPseudoPositioner(PseudoPositioner):
#
#     def __init__(self, *args, special_pseudo='bragg', **kwargs):
#         self.pseudo_keys = [k for k, _ in self._get_pseudo_positioners()]
#         self.real_keys = [k for k, _ in self._get_real_positioners()]
#         self.motor_keys = self.pseudo_keys + self.real_keys
#         super().__init__(*args, **kwargs)
#
#         # self.special_pseudo = special_pseudo
#         # self.reset_correction()
#         # self.reset_calibration_data()
#         # self.apply_correction = True
#
#     # def reset_correction(self):
#     #     self.correction_dict = {'act2nom': {k: [0] for k in self.pseudo_keys},
#     #                             'nom2act': {k: [0] for k in self.pseudo_keys}}
#     #
#     # def reset_calibration_data(self):
#     #     self.calibration_data = {'actual': {k: [] for k in self.pseudo_keys},
#     #                              'nominal': {k: [] for k in self.pseudo_keys}}
#     #
#     # def register_calibration_point(self, special_pseudo_pos):
#     #     pseudo_dict = self.pseudo_pos2dict(self.position)
#     #     actual_dict = copy.deepcopy(pseudo_dict)
#     #     actual_dict[self.special_pseudo] = special_pseudo_pos
#     #     nominal_dict = self.pseudo_pos2dict(self.inverse(self.forward(**{self.special_pseudo : pseudo_dict[self.special_pseudo]})))
#     #     for k in self.pseudo_keys:
#     #         self.calibration_data['actual'][k].append(actual_dict[k])
#     #         self.calibration_data['nominal'][k].append(nominal_dict[k])
#     #
#     #     # real_dict = self.real_pos2dict(self.real_position)
#     #     # actual_dict = copy.deepcopy(real_dict)
#     #     # actual_dict[self.special_pseudo] = special_pseudo_pos
#     #     # nominal_dict = self.pseudo_pos2dict(
#     #     #     self.inverse(self.forward(**{self.special_pseudo: pseudo_dict[self.special_pseudo]})))
#     #     # for k in self.pseudo_keys:
#     #     #     self.calibration_data['actual'][k].append(actual_dict[k])
#     #     #     self.calibration_data['nominal'][k].append(nominal_dict[k])
#     #
#     # def process_calibration(self, npoly=None):
#     #     if npoly is None:
#     #         npoly = len(self.calibration_data['nominal'][self.special_pseudo]) - 1
#     #     for key in self.pseudo_keys:
#     #         x_nom = np.array(self.calibration_data['nominal'][key])
#     #         x_act = np.array(self.calibration_data['actual'][key])
#     #         self.correction_dict['nom2act'][key] = np.polyfit(x_nom, x_act - x_nom, npoly)
#     #         self.correction_dict['act2nom'][key] = np.polyfit(x_act, x_nom - x_act, npoly)
#     #
#     # def correct(self, pseudo_dict, way='act2nom'):
#     #     if self.apply_correction:
#     #         for k in pseudo_dict.keys():
#     #             delta = np.polyval(self.correction_dict[way][k], pseudo_dict[k])
#     #             pseudo_dict[k] += delta
#     #     return pseudo_dict
#
#     def pseudo_pos2dict(self, pseudo_pos):
#         ret = {k : getattr(pseudo_pos, k) for k in self.pseudo_keys}
#         for k in ret.keys():
#             if ret[k] is None:
#                 try:
#                     ret[k] = getattr(self, k).position
#                 except:
#                     ttime.sleep(1)
#                     ret[k] = getattr(self, k).position
#         return ret
#
#     def real_pos2dict(self, real_pos):
#         ret = {k: getattr(real_pos, k) for k in self.real_keys}
#         for k in ret.keys():
#             if ret[k] is None:
#                 try:
#                     ret[k] = getattr(self, k).position
#                 except:
#                     ttime.sleep(1)
#                     ret[k] = getattr(self, k).position
#         return ret
#
#     @pseudo_position_argument
#     def forward(self, pseudo_pos):
#         pseudo_dict = self.pseudo_pos2dict(pseudo_pos)
#         # pseudo_dict = self.correct(pseudo_dict, way='act2nom')
#         real_dict = self._forward(pseudo_dict)
#         # real_dict = self._forward(pseudo_pos)
#         return self.RealPosition(**real_dict)
#
#     @real_position_argument
#     def inverse(self, real_pos):
#         real_dict = self.real_pos2dict(real_pos)
#         pseudo_dict = self._inverse(real_dict)
#         # pseudo_dict = self.correct(pseudo_dict, way='nom2act')
#         return self.PseudoPosition(**pseudo_dict)
#
#
#     @property
#     def position_dict(self):
#         return self.pseudo_pos2dict(self.position)
#
#     @property
#     def real_position_dict(self):
#         return self.real_pos2dict(self.real_position)
#
#
# from xas.xray import bragg2e, e2bragg
# from xas.fitting import Nominal2ActualConverter
#
# class JohannMultiCrystalSpectrometerAlt(ISSPseudoPositioner): #(PseudoPositioner):
#     motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
#     motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
#
#     motor_cr_main_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
#     motor_cr_main_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')
#
#     cr_main_roll_offset = Cpt(SoftPositioner, init_pos=0)  # software representation of the angular offset on the crystal stage
#
#     # motor_cr_aux2_x =  Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:X}Mtr')
#     # motor_cr_aux2_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Y}Mtr')
#     # motor_cr_aux2_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Roll}Mtr')
#     # motor_cr_aux2_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:2:Yaw}Mtr')
#
#     motor_det_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
#     motor_det_th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta1}Mtr')  # give better names
#     motor_det_th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta2}Mtr')
#
#     cr_assy_x = Cpt(PseudoSingle, name='cr_assy_x')
#     cr_assy_y = Cpt(PseudoSingle, name='cr_assy_y')
#
#     cr_main_bragg = Cpt(PseudoSingle, name='cr_main_bragg')
#     cr_main_yaw = Cpt(PseudoSingle, name='cr_main_yaw')
#
#     # cr_aux2_x = Cpt(PseudoSingle, name='cr_aux2_x')
#     # cr_aux2_y = Cpt(PseudoSingle, name='cr_aux2_y')
#     # cr_aux2_bragg = Cpt(PseudoSingle, name='cr_aux2_bragg')
#     # cr_aux2_yaw = Cpt(PseudoSingle, name='cr_aux2_yaw')
#
#     det_bragg = Cpt(PseudoSingle, name='det_bragg')
#     det_x = Cpt(PseudoSingle, name='det_x')
#     det_y = Cpt(PseudoSingle, name='det_y')
#
#     bragg = Cpt(PseudoSingle, name='bragg')
#     # bragg_act = Cpt(PseudoSingle, name='bragg_act')
#     x = Cpt(PseudoSingle, name='x')
#     det_focus = Cpt(PseudoSingle, name='det_focus')
#     energy = Cpt(PseudoSingle, name='energy')
#
#     _real = ['motor_cr_assy_x', 'motor_cr_assy_y', 'motor_cr_main_roll', 'motor_cr_main_yaw',
#              'motor_det_x', 'motor_det_th1', 'motor_det_th2']
#     _pseudo_precision = {'cr_assy_x' : 5e-3,
#                          'cr_assy_y' : 5e-3,
#                          'cr_main_bragg' : 5e-6,
#                          'cr_main_yaw' : 5e-6,
#                          # 'cr_aux2_x': 5e-3,
#                          # 'cr_aux2_y': 5e-3,
#                          # 'cr_aux2_bragg': 5e-6,
#                          # 'cr_aux2_yaw': 5e-6,
#                          'det_bragg' : 5e-6,
#                          'det_x' : 5e-3,
#                          'det_y' : 5e-3,
#                          'bragg' : 5e-6,
#                          'x' : 5e-3,
#                          'det_focus' : 1e-2,
#                          'energy' : 1e-3}
#     _pseudo = list(_pseudo_precision.keys())
#
#     det_L1 = 550  # length of the big arm
#     det_L2 = 91  # distance between the second gon and the sensitive surface of the detector
#
#     def __init__(self, *args, auto_target=False, **kwargs):
#         self.json_path = f'{ROOT_PATH_SHARED}/settings/json/johann_config.json'
#         self.reset_offset_data()
#         self._initialized = False
#         self.energy_converter = None
#         self.init_from_settings()
#         super().__init__(*args, auto_target=auto_target, **kwargs)
#         self.set_cr_main_roll_offset_from_settings()
#
#         # self.operation_mode = 'nominal'
#
#         # self._print_inverse = False
#
#     def load_config(self, file):
#         with open(file, 'r') as f:
#             config = json.loads(f.read())
#         return config
#
#     def save_current_spectrometer_config(self, file):
#         config = self.get_spectrometer_config()
#         with open(file, 'w') as f:
#             json.dump(config, f)
#
#     def save_current_spectrometer_config_to_settings(self):
#         self.save_current_spectrometer_config(self.json_path)
#
#     def init_from_settings(self):
#         try:
#             config = self.load_config(self.json_path)
#             self.set_spectrometer_config(config)
#         except Exception as e:
#             config = {'crystal' : 'Si',
#                       'hkl' : (6, 2, 0),
#                       'R': 1000,
#                       'x_src': 0,
#                       'y_src': 0,
#                       'motor_cr_assy_x0': 992.9999570365,
#                       'motor_cr_assy_y0': 7.481774249999999,
#                       'motor_cr_main_roll0': 8.1324,
#                       'motor_cr_main_yaw0' : 0.85,
#                       'cr_main_roll_offset': 17.125,
#                       'motor_det_x0': -10,  # high limit of this motor should be at 529 mm
#                       'motor_det_th10': 69,
#                       'motor_det_th20': -69}
#             self.set_spectrometer_config(config)
#
#     def set_spectrometer_config(self, config):
#         self.crystal = config['crystal']
#         self.hkl = config['hkl']
#         self.R = config['R']
#         self.x_src = config['x_src']
#         self.y_src = config['y_src']
#
#         self.motor_cr_assy_x0 = config['motor_cr_assy_x0']
#         self.motor_cr_assy_y0 = config['motor_cr_assy_y0']
#         self.motor_cr_main_roll0 = config['motor_cr_main_roll0']
#         self.motor_cr_main_yaw0 = config['motor_cr_main_yaw0']
#         self.__cr_main_roll_offset = config['cr_main_roll_offset']
#
#         self.motor_det_x0 = config['motor_det_x0']
#         self.motor_det_th10 = config['motor_det_th10']
#         self.motor_det_th20 = config['motor_det_th20']
#         self.motor_offset_registry = config['motor_offset_registry']
#         if len(self.motor_offset_registry) > 0:
#             self._initialized = True
#
#         if 'ec_x_nom' in config.keys():
#             if (len(config['ec_x_nom']) > 0) and (len(config['ec_x_act']) > 0) and (config['ec_n_poly'] > 0):
#                 self.energy_converter = Nominal2ActualConverter(config['ec_x_nom'], config['ec_x_act'], config['ec_n_poly'])
#
#     def get_spectrometer_config(self):
#         config = {'crystal' : self.crystal,
#                   'hkl' : self.hkl,
#                   'R': self.R,
#                   'x_src': self.x_src,
#                   'y_src': self.y_src,
#                   'motor_cr_assy_x0': self.motor_cr_assy_x0,
#                   'motor_cr_assy_y0': self.motor_cr_assy_y0,
#                   'motor_cr_main_roll0': self.motor_cr_main_roll0,
#                   'motor_cr_main_yaw0' : self.motor_cr_main_yaw0,
#                   'cr_main_roll_offset': self.cr_main_roll_offset.position,
#                   'motor_det_x0': self.motor_det_x0,
#                   'motor_det_th10': self.motor_det_th10,
#                   'motor_det_th20': self.motor_det_th20,
#                   'motor_offset_registry': self.motor_offset_registry,
#                   'ec_x_nom' : [],
#                   'ec_x_act': [],
#                   'ec_n_poly': 0}
#
#         if self.energy_converter is not None:
#             config['ec_x_nom'] = [v for v in self.energy_converter.x_nominal]
#             config['ec_x_act'] = [v for v in self.energy_converter.x_actual]
#             config['ec_n_poly'] = int(self.energy_converter.n_poly)
#         return config
#
#     def set_cr_main_roll_offset_from_settings(self):
#         self.cr_main_roll_offset.set(self.__cr_main_roll_offset)
#         # self.__cr_main_roll_offset = None
#
#     def update_johann_parameters(self, crystal='Si', hkl=(7, 3, 3), R=1000, x_src=0, y_src=0):
#         self.crystal = crystal
#         self.hkl = hkl
#         self.R = R
#         self.x_src = x_src
#         self.y_src = y_src
#
#     def set_det_parking(self):
#         self.motor_det_x0 = self.motor_det_x.position
#         self.motor_det_th10 = self.motor_det_th1.position
#         self.motor_det_th20 = self.motor_det_th2.position
#
#     def set_main_crystal_parking(self):
#         self.motor_cr_assy_x0 = self.motor_cr_assy_x.position
#         self.motor_cr_assy_y0 = self.motor_cr_assy_y.position
#         self.motor_cr_main_roll0 = self.motor_cr_main_roll.position / 1000
#         self.motor_cr_main_yaw0 = self.motor_cr_main_yaw.position / 1000
#
#     @property
#     def det_dx(self):
#         return self.det_L1 * np.cos(np.deg2rad(self.motor_det_th10)) - self.det_L2
#
#     @property
#     def det_h(self):
#         return self.det_L1 * np.sin(np.deg2rad(self.motor_det_th10))
#
#     def reset_offset_data(self):
#         # self.offset_data = {'nominal': {k: [] for k in self.pseudo_keys},
#         #                     'actual': {k: [] for k in self.pseudo_keys}}
#         self.motor_offset_registry = []
#
#     # @property
#     # def n_offset_points(self):
#     #     return len(self.offset_data['nominal']['bragg'])
#
#     def register_energy(self, energy, energy_limits=None):
#         bragg_act = e2bragg(energy, self.crystal, self.hkl)
#         bragg = self.bragg.position
#         cr_main_roll_offset_value = self.cr_main_roll_offset.position
#         self.cr_main_roll_offset.set(cr_main_roll_offset_value + (bragg - bragg_act))
#         self.motor_offset_registry.append(self.position_dict)
#         if energy_limits is not None:
#             self.energy._limits = energy_limits
#         self._initialized = True
#         self.save_current_spectrometer_config_to_settings()
#
#     def update_motor_pos_for_energy(self, new_pos_dict):
#         if len(self.motor_offset_registry) == 0:
#             pass
#         elif len(self.motor_offset_registry) == 1:
#             new_pos_dict['cr_main_yaw'] = self.motor_offset_registry[0]['cr_main_yaw']
#             new_pos_dict['x'] = self.motor_offset_registry[0]['x']
#             new_pos_dict['det_focus'] = self.motor_offset_registry[0]['det_focus']
#             new_pos_dict['det_bragg'] += self.motor_offset_registry[0]['det_bragg'] - self.motor_offset_registry[0]['bragg']
#             self._move_det_arm_only(new_pos_dict)
#
#     def append_energy_converter(self, ec):
#         self.energy_converter = ec
#
#     def which_motor_moves(self, new_pos_dict):
#         try:
#             old_pos_dict = self.pseudo_pos2dict(self.position)
#         except Exception as e:
#             print(e)
#             old_pos_dict = self._inverse(self.real_pos2dict(self.real_position))
#         moving_motors = []
#         moving_motors_delta = []
#         # print('###########')
#         # print(f'\t old_pos \t new_pos \t motor_name')
#         for motor_name in old_pos_dict.keys():
#             # print(f'{old_pos_dict[motor_name] : .4f} \t {new_pos_dict[motor_name] : .4f} \t - {motor_name}')
#             if not np.isclose(old_pos_dict[motor_name], new_pos_dict[motor_name], atol=self._pseudo_precision[motor_name]):
#                 moving_motors.append(motor_name)
#                 moving_motors_delta.append(new_pos_dict[motor_name] - old_pos_dict[motor_name])
#         if len(moving_motors) == 0:
#             return None
#         elif len(moving_motors) == 1:
#             return moving_motors[0]
#         elif len(moving_motors) > 1:
#             dd = {m : d for m, d in zip(moving_motors, moving_motors_delta)}
#             print_to_gui(f'Info: Multiple Johann spetrometer pseudo motors are being moved. {dd}', tag='Spectrometer')
#             return moving_motors[0]
#
#     def _move_crystal_only(self, new_pos_dict):
#         cr_assy_x, _, _, _ = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, new_pos_dict['cr_main_bragg'], 0)
#         cr_assy_x += self.R
#         # print(f'Updating cr_assy_x: old_pos={new_pos_dict["cr_assy_x"]}, new_pos={cr_assy_x}')
#         new_pos_dict['cr_assy_x'] = cr_assy_x
#
#     def _move_det_arm_only(self, new_pos_dict):
#         _, _, det_x, det_y = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, new_pos_dict['det_bragg'],
#                                                              new_pos_dict['det_focus'])
#         det_x += new_pos_dict['x']
#         # print(f'Updating det_x: old_pos={new_pos_dict["det_x"]}, new_pos={det_x}')
#         new_pos_dict['det_x'] = det_x
#         # print(f'Updating det_y: old_pos={new_pos_dict["det_y"]}, new_pos={det_y}')
#         new_pos_dict['det_y'] = det_y
#
#     def _move_all_components(self, new_pos_dict):
#         new_pos_dict['cr_main_bragg'] = new_pos_dict['bragg']
#         new_pos_dict['det_bragg'] = new_pos_dict['bragg']
#         self._move_crystal_only(new_pos_dict)
#         self._move_det_arm_only(new_pos_dict)
#
#     # def _move_all_components_with_correction(self, new_pos_dict):
#     #     if self.n_offset_points == 0:
#     #         new_pos_dict['bragg'] = new_pos_dict['bragg_act']
#     #         self._move_all_components(new_pos_dict)
#     #
#     #     elif self.n_offset_points == 1:
#     #         new_pos_dict['bragg'] = self.decorrect_bragg(new_pos_dict['bragg_act'])
#     #         # new_pos_dict['bragg'] -= (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
#     #         # pos_nom = {k: self.offset_data['nominal'][k][0] for k in self.pseudo_keys}
#     #         # pos_nom['bragg'] = bragg
#     #         self._move_all_components(new_pos_dict)
#     #         # sdfs
#     #         for k in self.pseudo_keys:
#     #             if (k != 'bragg') and (k != 'bragg_act'):
#     #                 new_pos_dict[k] += (self.offset_data['actual'][k][0] - self.offset_data['nominal'][k][0])
#     #
#     #     elif self.n_offset_points == 2:
#     #         new_pos_dict['bragg'] = self.decorrect_bragg(new_pos_dict['bragg_act'])
#     #         # new_pos_dict['bragg'] -= (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
#     #         # pos_nom = {k: self.offset_data['nominal'][k][0] for k in self.pseudo_keys}
#     #         # pos_nom['bragg'] = bragg
#     #         self._move_all_components(new_pos_dict)
#     #         # sdfs
#     #         for k in self.pseudo_keys:
#     #             if (k != 'bragg') and (k != 'bragg_act'):
#     #                 p = np.polyfit(np.array(self.offset_data['actual']['bragg']),
#     #                                np.array(self.offset_data['actual'][k]) -
#     #                                np.array(self.offset_data['nominal'][k]), 1)
#     #                 delta = np.polyval(p, new_pos_dict['bragg_act'])
#     #
#     #                 new_pos_dict[k] += delta
#     #
#     # def correct_bragg(self, bragg):
#     #     if self.n_offset_points == 0:
#     #         return bragg
#     #     elif self.n_offset_points == 1:
#     #         return bragg + (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
#     #     elif self.n_offset_points == 2:
#     #         p = np.polyfit(np.array(self.offset_data['nominal']['bragg']),
#     #                        np.array(self.offset_data['actual']['bragg']) -
#     #                        np.array(self.offset_data['nominal']['bragg']), 1)
#     #         delta = np.polyval(p, bragg)
#     #         return bragg + delta
#     #
#     # def decorrect_bragg(self, bragg_act):
#     #     if self.n_offset_points == 0:
#     #         return bragg_act
#     #     elif self.n_offset_points == 1:
#     #         return bragg_act - (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
#     #     elif self.n_offset_points == 2:
#     #         p = np.polyfit(np.array(self.offset_data['actual']['bragg']),
#     #                        np.array(self.offset_data['actual']['bragg']) -
#     #                        np.array(self.offset_data['nominal']['bragg']), 1)
#     #         delta = np.polyval(p, bragg_act)
#     #         return bragg_act - delta
#
#     def handle_pseudo_input(self, new_pos_dict):
#         moving_motor = self.which_motor_moves(new_pos_dict)
#         # print(f'Motor moving: {moving_motor}')
#
#         if moving_motor == 'cr_main_bragg':
#             self._move_crystal_only(new_pos_dict)
#
#         elif (moving_motor == 'det_bragg') or (moving_motor == 'det_focus'):
#             self._move_det_arm_only(new_pos_dict)
#
#         elif (moving_motor == 'bragg'):
#             self._move_all_components(new_pos_dict)
#
#         elif (moving_motor == 'energy'):
#             if self.energy_converter is not None:
#                 new_pos_dict['energy'] = self.energy_converter.act2nom(new_pos_dict['energy'])
#             new_pos_dict['bragg'] = e2bragg(new_pos_dict['energy'], self.crystal, self.hkl)
#             self._move_all_components(new_pos_dict)
#             self.update_motor_pos_for_energy(new_pos_dict)
#         #     # print('moving_motor is bragg_act')
#         #     self._move_all_components_with_correction(new_pos_dict)
#
#     def _forward(self, pseudo_pos_dict):
#         self.handle_pseudo_input(pseudo_pos_dict)
#         cr_assy_x, cr_assy_y, cr_main_bragg, cr_main_yaw = pseudo_pos_dict['cr_assy_x'],\
#                                                            pseudo_pos_dict['cr_assy_y'],\
#                                                            pseudo_pos_dict['cr_main_bragg'],\
#                                                            pseudo_pos_dict['cr_main_yaw']
#
#         det_bragg, det_x, det_y = pseudo_pos_dict['det_bragg'],\
#                                   pseudo_pos_dict['det_x'],\
#                                   pseudo_pos_dict['det_y']
#
#         x = pseudo_pos_dict['x']
#
#         motor_cr_assy_x = x - cr_assy_x + self.motor_cr_assy_x0
#         motor_cr_assy_y = cr_assy_y + self.motor_cr_assy_y0
#         motor_cr_main_roll = (cr_main_bragg + self.cr_main_roll_offset.position + self.motor_cr_main_roll0 - 90) * 1000
#         motor_cr_main_yaw = cr_main_yaw * 1000
#
#         _det_bragg_rad = np.deg2rad(det_bragg)
#         _phi = np.pi - 2 * _det_bragg_rad
#         _sin_th1 = (self.det_h - self.det_L2 * np.sin(_phi) - det_y) / self.det_L1
#         motor_det_th1 = np.arcsin(_sin_th1)
#         motor_det_th2 = _phi + motor_det_th1
#         motor_det_x = self.motor_det_x0 - self.det_dx + self.det_L1 * np.cos(motor_det_th1) - self.det_L2 * np.cos(_phi) - det_x + x
#         motor_det_th1 = np.rad2deg(motor_det_th1)
#         motor_det_th2 = -np.rad2deg(motor_det_th2)
#
#         output = {'motor_cr_assy_x'   : motor_cr_assy_x,
#                   'motor_cr_assy_y'   : motor_cr_assy_y,
#                   'motor_cr_main_roll': motor_cr_main_roll,
#                   'motor_cr_main_yaw' : motor_cr_main_yaw,
#                   'motor_det_x'  : motor_det_x,
#                   'motor_det_th1': motor_det_th1,
#                   'motor_det_th2': motor_det_th2}
#         # print(output)
#
#         return output
#
#
#     def _inverse(self, real_pos_dict):
#         # if self._print_inverse: print('INVERSE INVOKED')
#         motor_cr_assy_x, motor_cr_assy_y, motor_cr_main_roll, motor_cr_main_yaw, motor_det_x, motor_det_th1, motor_det_th2 = \
#             real_pos_dict['motor_cr_assy_x'], \
#             real_pos_dict['motor_cr_assy_y'], \
#             real_pos_dict['motor_cr_main_roll'], \
#             real_pos_dict['motor_cr_main_yaw'], \
#             real_pos_dict['motor_det_x'], \
#             real_pos_dict['motor_det_th1'], \
#             real_pos_dict['motor_det_th2']
#
#         cr_main_bragg = 90 + motor_cr_main_roll / 1000 - self.cr_main_roll_offset.position - self.motor_cr_main_roll0
#         cr_main_yaw = motor_cr_main_yaw / 1000
#         cr_assy_x, _, _, _ = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, cr_main_bragg, 0)
#         cr_assy_x += self.R
#         cr_assy_y = motor_cr_assy_y - self.motor_cr_assy_y0
#         x = cr_assy_x + (motor_cr_assy_x - self.motor_cr_assy_x0)
#
#         motor_det_th2 *= -1
#         det_bragg = (180 - (motor_det_th2 - motor_det_th1)) / 2
#
#         det_x = self.motor_det_x0 - self.det_dx + self.det_L1 * np.cos(np.deg2rad(motor_det_th1)) - self.det_L2 * np.cos(np.deg2rad(motor_det_th2 - motor_det_th1)) - motor_det_x + x
#         det_y = self.det_h - self.det_L1 * np.sin(np.deg2rad(motor_det_th1)) - self.det_L2 * np.sin(np.deg2rad(motor_det_th2 - motor_det_th1))
#
#         _, _, det_x_ref, det_y_ref = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, det_bragg, 0)
#         det_x_ref += x
#         det_focus = np.sqrt((det_x - det_x_ref) ** 2 + (det_y - det_y_ref) ** 2) * np.sign(det_y_ref - det_y)
#         bragg = cr_main_bragg
#         energy = bragg2e(bragg, self.crystal, self.hkl)
#         if self.energy_converter is not None:
#             energy = self.energy_converter.nom2act(energy)
#
#         return {'cr_assy_x' : cr_assy_x,
#                 'cr_assy_y' : cr_assy_y,
#                 'cr_main_bragg' : cr_main_bragg,
#                 'cr_main_yaw' : cr_main_yaw,
#                 'det_bragg' : det_bragg,
#                 'det_x' : det_x,
#                 'det_y' : det_y,
#                 'bragg' : bragg,
#                 'x' : x,
#                 'det_focus' : det_focus,
#                 'energy' : energy}
#
#
# johann_emission = JohannMultiCrystalSpectrometerAlt(name='johann_emission')
# johann_emission.energy._limits=(7420, 7520)
# johann_emission.register_energy(7470)


# motor_dictionary['johann_bragg_angle'] = {'name': johann_emission.bragg.name,
#                                           'description' : 'Johann Bragg Angle',
#                                           'object': johann_emission.bragg,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_det_focus'] =   {'name': johann_emission.det_focus.name,
#                                           'description' : 'Johann Detector Focus',
#                                           'object': johann_emission.det_focus,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_x'] =           {'name': johann_emission.x.name,
#                                           'description' : 'Johann X',
#                                           'object': johann_emission.x,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_energy'] =      {'name': johann_emission.energy.name,
#                                           'description' : 'Johann Energy',
#                                           'object': johann_emission.energy,
#                                           'group': 'spectrometer'}
##############################

#


#

# bla = Nominal2ActualConverterWithLinearInterpolation()
# x_nom = np.array([0.0, 1.0])
# x_act = np.array([0.1, 0.9])
#
# xna = list(zip(x_nom, x_act))[:1]
#
# for xn, xa in xna:
#     bla.append_point(xn, xa)
# # bla.append_point(1, 0.9)
#
# x_grid = np.linspace(-1, 3, 101)
# plt.figure(1, clear=True)
# plt.plot(x_nom[0], x_act[0], 'ro')
# plt.plot(x_nom[1], x_act[1], 'mo')
# plt.plot(x_grid, bla.nom2act(x_grid), '-')
# plt.plot(x_grid, x_grid, 'k-')
#
# plt.axis('equal')

# class TestPositioner(ISSPseudoPositioner):
#     x_act = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
#     x_nom = Cpt(PseudoSingle, name='x_nom')
#
#     _real = ['x_act']
#     _pseudo = ['x_nom']
#
#     def __init__(self, *args, auto_target=False, **kwargs):
#         super().__init__(*args, auto_target=auto_target, **kwargs)
#
#
#     def _forward(self, pseudo_pos_dict):
#         x_nom = pseudo_pos_dict['x_nom']
#         x_act = x_nom
#         return {'x_act' : x_act}
#
#     def _inverse(self, real_pos_dict):
#         x_act = real_pos_dict['x_act']
#         x_nom = x_act
#         return {'x_nom': x_nom}
#
# test_positioner = TestPositioner(name='test_positioner')

# class JohannEmissionMotor(PseudoPositioner):
#     spectrometer = Cpt(JohannMultiCrystalSpectrometerAlt, name='bragg')
#     energy = Cpt(PseudoSingle, name='energy')
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.json_path = f'{ROOT_PATH_SHARED}/settings/json/johann_config.json'
#         self.init_from_settings()
#         # self.calibration_data = {'energy_nominal' : [], 'bragg_nominal' : [], 'bragg_actual' : []}
#         # self.bragg_calibration = None
#         # self.apply_calibration = True
#         self.bragg = self.spectrometer.bragg_act #alias
#
#     #########
#     def load_config(self, file):
#         with open(file, 'r') as f:
#             config = json.loads(f.read())
#         return config
#
#     def save_config(self, file):
#         config = self.get_config()
#         with open(file, 'w') as f:
#             json.dump(config, f)
#
#     def save_to_settings(self):
#         self.save_config(self.json_path)
#
#     def init_from_settings(self):
#         try:
#             config = self.load_config(self.json_path)
#             self.spectrometer.init_from_settings()
#             # self.spectrometer.restore_parking(config)
#             # self.spectrometer.det_arm.restore_parking(config)
#         except FileNotFoundError:
#             print('Could not find Johann spectrometer configuration file. Proceed with caution.')
#             config = {}
#         self.update_johann_parameters(**config)
#
#     def update_johann_parameters(self, crystal='Si', hkl=(7, 3, 3), R=1000, x_src=0, y_src=0, **kwargs):
#         self.crystal = crystal
#         self.hkl = hkl
#         self.spectrometer.R = R
#         self.spectrometer.x_src = x_src
#         self.spectrometer.y_src = y_src
#
#     def get_config(self):
#         config = {'crystal' : self.crystal,
#                 'hkl': self.hkl,
#                 'R': self.spectrometer.R,
#                 'x_src': self.spectrometer.x_src,
#                 'y_src' : self.spectrometer.y_src}
#         spectrometer_config = {}
#         # spectrometer_config = self.spectrometer.read_current_config()
#         # det_arm_config = self.spectrometer.det_arm.read_current_config()
#
#         return {**config, **spectrometer_config}
#
#     # def set_main_crystal_parking(self):
#     #     self.spectrometer.crystal1.set_parking()
#     #     self.save_to_settings()
#     #
#     # def set_det_arm_parking(self):
#     #     self.spectrometer.det_arm.set_parking()
#     #     self.save_to_settings()
#
#     # def register_calibration_point(self, energy):
#     #     self.calibration_data['energy_nominal'].append(energy)
#     #     self.calibration_data['bragg_nominal'].append(e2bragg(energy, self.crystal, self.hkl))
#     #     self.calibration_data['bragg_actual'].append(self.spectrometer.bragg.position)
#     #
#     # def process_calibration(self, n_poly=2):
#     #     self.bragg_calibration = Nominal2ActualConverter(self.calibration_data['bragg_nominal'],
#     #                                                      self.calibration_data['bragg_actual'],
#     #                                                      n_poly=n_poly)
#
#     def _forward(self, pseudo_pos):
#         energy = pseudo_pos.energy
#         bragg = e2bragg(energy, self.crystal, self.hkl)
#         # if (self.bragg_calibration is not None) and (self.apply_calibration):
#         #     bragg = self.bragg_calibration.nom2act(bragg)
#         # det_dR = self.spectrometer.det_dR.position
#         # x_sp = self.spectrometer.x_sp.position
#         pos_dict = self.spectrometer.pseudo_pos2dict(self.spectrometer.position)
#         pos_dict['bragg_act'] = bragg
#         pos = self.spectrometer.PseudoPosition(**pos_dict)
#         return self.RealPosition(spectrometer=pos)
#
#     def _inverse(self, real_pos):
#         bragg = real_pos.spectrometer.bragg_act
#         energy = bragg2e(bragg, self.crystal, self.hkl)
#         return self.PseudoPosition(energy=energy)
#
#     # @pseudo_position_argument
#     def forward(self, pseudo_pos):
#         return self._forward(pseudo_pos)
#
#     # @real_position_argument
#     def inverse(self, real_pos):
#         return self._inverse(real_pos)
#
# johann_emission = JohannEmissionMotor(name='johann_emission')
#
# # johann_emission.spectrometer.offset_data = \
# # {'nominal': {'cr_assy_x': [29.6654660811206, 27.267846810444667],
# #   'cr_assy_y': [0.0, 0.0],
# #   'cr_main_bragg': [76.009194, 76.58919399999999],
# #   'cr_main_yaw': [0.849957, 0.849957],
# #   'det_bragg': [76.009194, 76.58919399999999],
# #   'det_x': [-111.55640935716096, -102.77334615511403],
# #   'det_y': [455.26687918909795, 438.9080447066834],
# #   'bragg': [76.009194, 76.58919399999999],
# #   'bragg_act': [76.009194, 76.009194],
# #   'x': [1.882338408620626, 1.882338408620626],
# #   'det_focus': [0.0055589760942588995, 0.0055589760942588995]},
# #  'actual': {'cr_assy_x': [29.6654660811206, 27.267846810444667],
# #   'cr_assy_y': [0.0, 0.0],
# #   'cr_main_bragg': [76.009194, 76.58919399999999],
# #   'cr_main_yaw': [0.849957, 0.849957],
# #   'det_bragg': [74.819796875, 75.4001875],
# #   'det_x': [-130.46653297345836, -122.58459200449965],
# #   'det_y': [487.7966257311867, 471.2751616484047],
# #   'bragg': [74.82, 75.4],
# #   'bragg_act': [76.009194, 75.39999999999999],
# #   'x': [1.882338408620626, 1.882467896444723],
# #   'det_focus': [0.0055589760942588995, 0]}}
# johann_emission.spectrometer.offset_data = \
# {'nominal': {'cr_assy_x': [29.6654660811206],
#   'cr_assy_y': [0.0],
#   'cr_main_bragg': [76.009194],
#   'cr_main_yaw': [0.849957],
#   'det_bragg': [76.009194],
#   'det_x': [-111.55640935716096],
#   'det_y': [455.26687918909795],
#   'bragg': [76.009194],
#   'bragg_act': [76.009194],
#   'x': [1.882338408620626],
#   'det_focus': [0.0055589760942588995]},
#  'actual': {'cr_assy_x': [29.6654660811206],
#   'cr_assy_y': [0.0],
#   'cr_main_bragg': [76.009194],
#   'cr_main_yaw': [0.849957],
#   'det_bragg': [74.819796875],
#   'det_x': [-130.46653297345836],
#   'det_y': [487.7966257311867],
#   'bragg': [74.82],
#   'bragg_act': [76.009194],
#   'x': [1.882338408620626],
#   'det_focus': [0.0055589760942588995]}}
#
#
# motor_dictionary['johann_bragg_angle'] = {'name': johann_emission.spectrometer.bragg_act.name,
#                                           'description' : 'Johann Bragg Angle',
#                                           'object': johann_emission.spectrometer.bragg_act,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_det_focus'] =   {'name': johann_emission.spectrometer.det_focus.name,
#                                           'description' : 'Johann Detector Focus',
#                                           'object': johann_emission.spectrometer.det_focus,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_x'] =           {'name': johann_emission.spectrometer.x.name,
#                                           'description' : 'Johann X',
#                                           'object': johann_emission.spectrometer.x,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_energy'] =      {'name': johann_emission.energy.name,
#                                           'description' : 'Johann Energy',
#                                           'object': johann_emission.energy,
#                                           'group': 'spectrometer'}



# jsp_alt.register_actual_bragg(74.82)
# jsp_alt.offset_data = \
# {'nominal': {'cr_assy_x': [29.6654660811206, 27.267846810444667],
#   'cr_assy_y': [0.0, 0.0],
#   'cr_main_bragg': [76.009194, 76.58919399999999],
#   'cr_main_yaw': [0.849957, 0.849957],
#   'det_bragg': [76.009194, 76.58919399999999],
#   'det_x': [-111.55640935716096, -102.77334615511403],
#   'det_y': [455.26687918909795, 438.9080447066834],
#   'bragg': [76.009194, 76.58919399999999],
#   'bragg_act': [76.009194, 76.009194],
#   'x': [1.882338408620626, 1.882338408620626],
#   'det_focus': [0.0055589760942588995, 0.0055589760942588995]},
#  'actual': {'cr_assy_x': [29.6654660811206, 27.267846810444667],
#   'cr_assy_y': [0.0, 0.0],
#   'cr_main_bragg': [76.009194, 76.58919399999999],
#   'cr_main_yaw': [0.849957, 0.849957],
#   'det_bragg': [74.819796875, 75.4001875],
#   'det_x': [-130.46653297345836, -122.58459200449965],
#   'det_y': [487.7966257311867, 471.2751616484047],
#   'bragg': [74.82, 75.4],
#   'bragg_act': [76.009194, 75.39999999999999],
#   'x': [1.882338408620626, 1.882467896444723],
#   'det_focus': [0.0055589760942588995, 1.7085024780916698]}}
#
# jsp_alt._forward(
# {'cr_assy_x': 27.267846810444667,
#  'cr_assy_y': 0.0,
#  'cr_main_bragg': 76.58919399999999,
#  'cr_main_yaw': 0.849957,
#  'det_bragg': 75.4001875,
#  'det_x': -122.58466829849965,
#  'det_y': 471.2751616484047,
#  'bragg': 76.58919399999999,
#  'bragg_act': 75.3,
#  'x': 1.8824106759446977,
#  'det_focus': 1.708519174508354}
# )






# motor_dictionary['johann_bragg'] = {'name': jsp_alt.bragg.name,
#                                           'description' : 'Johann Bragg Angle',
#                                           'object': jsp_alt.bragg,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_det_focus'] =   {'name': jsp_alt.det_focus.name,
#                                           'description' : 'Johann Detector Focus',
#                                           'object': jsp_alt.det_focus,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_x'] =           {'name': jsp_alt.x.name,
#                                           'description' : 'Johann X',
#                                           'object': jsp_alt.x,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_energy'] =      {'name': johann_emission.energy.name,
#                                           'description' : 'Johann Energy',
#                                           'object': johann_emission.energy,
#                                           'group': 'spectrometer'}


# jsp_alt._inverse(jsp_alt._forward(
# {'cr_assy_x': 37.782006470714464,
#  'cr_assy_y': 0.0,
#  'cr_main_bragg': 74.2,
#  'cr_main_yaw': 850.0,
#  'det_bragg': 74.5001875,
#  'det_x': -141.02793654090453,
#  'det_y': 491.1571514474454,
#  'bragg': 74.2,
#  'x': 5.1819617407145415,
#  'det_focus': 9.999776182655808}
#
# ))


# bla1 = {'motor_cr_assy_x'   : johann_emission.spectrometer.crystal1.x.position,
#         'motor_cr_assy_y'   : johann_emission.spectrometer.crystal1.y.position,
#         'motor_cr_main_roll': johann_emission.spectrometer.crystal1.roll.position,
#         'motor_cr_main_yaw' : johann_emission.spectrometer.crystal1.yaw.position,
#         'motor_det_x'  : johann_emission.spectrometer.det_arm.x.position,
#         'motor_det_th1': johann_emission.spectrometer.det_arm.th1.position,
#         'motor_det_th2': johann_emission.spectrometer.det_arm.th2.position}
#
# bla2 = jsp_alt._inverse(bla1)
#
# bla3 = jsp_alt._forward(bla2)



# class DetectorArm(ISSPseudoPositioner):
#
#     L1 = 550  # length of the big arm
#     L2 = 91  # distance between the second gon and the sensitive surface of the detector
#
#     x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
#     th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta1}Mtr') # give better names
#     th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta2}Mtr')
#
#     bragg = Cpt(PseudoSingle, name='bragg')
#     x_det = Cpt(PseudoSingle, name='x_det')
#     y_det = Cpt(PseudoSingle, name='y_det')
#
#     def __init__(self, *args, config=None, **kwargs):
#         self.restore_parking(config)
#         super().__init__(*args, **kwargs)
#
#     def set_parking(self):
#         self.x0 = self.x.position
#         self.th10 = self.th1.position
#         self.th20 = self.th2.position
#
#     def restore_parking(self, config):
#         if config is not None:
#             try:
#                 self.x0 = config['johann_det_arm_x0']  # high limit of this motor should be at 592 mm (OR 529???)
#                 self.th10 = config['johann_det_arm_th10']
#                 self.th20 = config['johann_det_arm_th20']
#                 return
#             except:
#                 pass
#         # some default values that are reasonable
#         self.x0 = 0 # high limit of this motor should be at 592 mm (OR 529???)
#         self.th10 = 69
#         self.th20 = -69
#
#     def read_current_config(self):
#         return {'johann_det_arm_x0': self.x0,
#                 'johann_det_arm_th10': self.th10,
#                 'johann_det_arm_th20': self.th20}
#
#     @property
#     def dx(self):
#         return self.L1 * np.cos(np.deg2rad(self.th10)) - self.L2
#
#     @property
#     def h(self):
#         return self.L1 * np.sin(np.deg2rad(self.th10))
#
#
#     def _forward(self, pseudo_dict):
#         bragg, x_det, y_det = pseudo_dict['bragg'], pseudo_dict['x_det'], pseudo_dict['y_det']
#         bragg_rad = np.deg2rad(bragg)
#         phi = np.pi - 2 * bragg_rad
#         sin_th1 = (self.h - self.L2 * np.sin(phi) - y_det) / self.L1
#         th1 = np.arcsin(sin_th1)
#         th2 = phi + th1
#         x = self.x0 - self.dx + self.L1 * np.cos(th1) - self.L2 * np.cos(phi) - x_det
#         return {'x' : x, 'th1' : np.rad2deg(th1), 'th2' : -np.rad2deg(th2)}
#
#     # def _inverse(self, real_pos):
#     #     x, th1, th2 = real_pos.x, real_pos.th1, real_pos.th2
#     def _inverse(self, real_dict):
#         x, th1, th2 = real_dict['x'], real_dict['th1'], real_dict['th2']
#         th2 *= -1
#         bragg = (180 - (th2 - th1)) / 2
#         x_det = self.x0 - self.dx + self.L1 * np.cos(np.deg2rad(th1)) - self.L2 * np.cos(np.deg2rad(th2 - th1)) - x
#         y_det = self.h - self.L1 * np.sin(np.deg2rad(th1)) - self.L2 * np.sin(np.deg2rad(th2 - th1))
#         return {'bragg' : bragg, 'x_det' : x_det, 'y_det' : y_det}
#
#
# det_arm = DetectorArm(name='det_arm')

# class MainJohannCrystal(PseudoPositioner):
# class MainCrystal(ISSPseudoPositioner):
#     x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
#     y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
#     roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
#     yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')
#
#     roll_offset = 0 # software representation of the angular offset on the crystal stage
#
#     x_cr = Cpt(PseudoSingle, name='x_cr')
#     y_cr = Cpt(PseudoSingle, name='y_cr')
#     roll_cr = Cpt(PseudoSingle, name='roll_cr')
#     yaw_cr = Cpt(PseudoSingle, name='yaw_cr')
#
#
#     _real = ['x', 'y', 'roll', 'yaw']
#     _pseudo = ['x_cr', 'y_cr', 'roll_cr', 'yaw_cr']
#
#     def __init__(self, *args, config=None, **kwargs):
#         self.restore_parking(config)
#         super().__init__(*args, **kwargs)
#
#
#     def set_parking(self):
#         assert self.roll_offset == 3.0, 'roll_offset must be 3 deg!'
#         self.x0 = self.x.position
#         self.y0 = self.y.position
#         self.roll0 = self.roll_offset - self.roll.position / 1000
#         self.yaw0 = self.yaw.position / 1000
#         # self.roll_offset0 = self.roll_offset.position
#
#     def restore_parking(self, config):
#         if config is not None:
#             try:
#                 self.x0 = config['main_johann_crystal_x0']
#                 self.y0 = config['main_johann_crystal_y0']
#                 self.roll0 = config['main_johann_crystal_roll0']
#                 self.yaw0 = config['main_johann_crystal_yaw0']
#                 return
#             except:
#                 pass
#         # some default values that are reasonable
#         self.x0 = 1000.000
#         self.y0 = 5.682
#         self.roll0 = 0.1
#         self.yaw0 = 0.620
#         self.roll_offset = 3.0
#
#
#     def set_roll_offset(self, value):
#         self.roll_offset = value
#
#     def read_current_config(self):
#         return {'main_johann_crystal_x0': self.x0,
#                 'main_johann_crystal_y0': self.y0,
#                 'main_johann_crystal_roll0': self.roll0,
#                 'main_johann_crystal_yaw0': self.yaw0,
#                 'main_johann_crystal_roll_offset': self.roll_offset}
#
#     # def _forward(self, pseudo_pos):
#     #     bragg, x_cr, y, yaw = pseudo_pos.bragg, pseudo_pos.x_cr, pseudo_pos.y, pseudo_pos.yaw
#
#     def _forward(self, pseudo_dict):
#         # bragg, x_cr, y, yaw = pseudo_dict['bragg'], pseudo_dict['x_cr'], pseudo_dict['y'], pseudo_dict['yaw']
#         x_cr, y_cr, roll_cr, yaw_cr = pseudo_dict['x_cr'], pseudo_dict['y_cr'], pseudo_dict['roll_cr'], pseudo_dict['yaw_cr']
#
#         x = self.x0 - x_cr
#         y = y_cr + self.y0
#         roll = (roll_cr - 90 - self.roll0 + self.roll_offset) * 1000
#         yaw = (yaw_cr + self.yaw0) * 1000
#         return {'x' : x, 'y' : y, 'roll' : roll, 'yaw' : yaw}
#         # return self.RealPosition(x=x, roll=roll, y=y, yaw=yaw)
#
#     # def _inverse(self, real_pos):
#     #     x, roll, y, yaw = real_pos.x, real_pos.roll, real_pos.y, real_pos.yaw
#
#     def _inverse(self, real_dict):
#         x, y, roll, yaw = real_dict['x'], real_dict['y'], real_dict['roll'], real_dict['yaw']
#         x_cr = self.x0 - x
#         y_cr = y - self.y0
#         roll_cr = 90 + roll / 1000 + self.roll0 - self.roll_offset
#         yaw_cr = yaw / 1000 - self.yaw0
#         return {'x_cr' : x_cr, 'y_cr' : y_cr, 'roll_cr' : roll_cr, 'yaw_cr' : yaw_cr}
#
# _j_cr = MainCrystal(name='j_cr')
#
#
# from xas.spectrometer import compute_rotated_rowland_circle_geometry
# ###
#
# class AuxCrystal(ISSPseudoPositioner):
#     x = Cpt(EpicsMotor, 'X}Mtr')
#     y = Cpt(EpicsMotor, 'Y}Mtr')
#     roll = Cpt(EpicsMotor, 'Roll}Mtr')
#     yaw = Cpt(EpicsMotor, 'Yaw}Mtr')
#
#     roll_offset = 0  # software representation of the angular offset on the crystal stage
#
#     x_cr = Cpt(PseudoSingle, name='x_cr')
#     y_cr = Cpt(PseudoSingle, name='y_cr')
#     roll_cr = Cpt(PseudoSingle, name='roll_cr')
#     yaw_cr = Cpt(PseudoSingle, name='yaw_cr')
#
#     _real = ['x', 'y', 'roll', 'yaw']
#     _pseudo = ['x_cr', 'y_cr', 'roll_cr', 'yaw_cr']
#
#     def __init__(self, *args, config=None, yaw_offset=8.0189144, x_offset=9.77792999999997, **kwargs):
#         self.restore_parking(config)
#         self.yaw_offset = yaw_offset
#         self.x_offset = x_offset
#         super().__init__(*args, **kwargs)
#
#
#     def set_parking(self):
#         self.x0 = self.x.position / 1000
#         self.y0 = self.y.position / 1000
#         self.roll0 = self.roll_offset - self.roll.position / 1000
#         self.yaw0 = self.yaw.position / 1000
#         # self.roll_offset0 = self.roll_offset.position
#
#     def restore_parking(self, config):
#         # if config is not None:
#         #     try:
#         #         self.x0 = config['main_johann_crystal_x0']
#         #         self.y0 = config['main_johann_crystal_y0']
#         #         self.roll0 = config['main_johann_crystal_roll0']
#         #         self.yaw0 = config['main_johann_crystal_yaw0']
#         #         return
#         #     except:
#         #         pass
#         # some default values that are reasonable
#         self.x0 = -14.190
#         self.y0 = -9.425
#         self.roll0 = 0.3160819
#         self.yaw0 = -0.8
#         self.roll_offset = 3.0
#
#     def set_roll_offset(self, value):
#         self.roll_offset = value
#
#     # def read_current_config(self):
#     #     return {'main_johann_crystal_x0': self.x0,
#     #             'main_johann_crystal_y0': self.y0,
#     #             'main_johann_crystal_roll0': self.roll0,
#     #             'main_johann_crystal_yaw0': self.yaw0,
#     #             'main_johann_crystal_roll_offset': self.roll_offset}
#
#     def _forward(self, pseudo_dict):
#         # bragg, x_cr, y, yaw = pseudo_dict['bragg'], pseudo_dict['x_cr'], pseudo_dict['y'], pseudo_dict['yaw']
#         x_cr, y_cr, roll_cr, yaw_cr = pseudo_dict['x_cr'], pseudo_dict['y_cr'], pseudo_dict['roll_cr'], pseudo_dict['yaw_cr']
#
#         x = (self.x0 - x_cr + self.x_offset) * 1000
#         y = (y_cr + self.y0) * 1000
#         roll = (roll_cr - 90 - self.roll0 + self.roll_offset) * 1000
#         yaw = (yaw_cr + self.yaw0 - self.yaw_offset) * 1000
#         return {'x' : x, 'y' : y, 'roll' : roll, 'yaw' : yaw}
#
#     def _inverse(self, real_dict):
#         x, y, roll, yaw = real_dict['x'], real_dict['y'], real_dict['roll'], real_dict['yaw']
#         x_cr = self.x0 - x / 1000 + self.x_offset
#         y_cr = y / 1000 - self.y0
#         roll_cr = 90 + roll / 1000 + self.roll0 - self.roll_offset
#         yaw_cr = yaw / 1000 - self.yaw0 + self.yaw_offset
#         return {'x_cr' : x_cr, 'y_cr' : y_cr, 'roll_cr' : roll_cr, 'yaw_cr' : yaw_cr}
#
# _j_aux_cr = AuxCrystal('XF:08IDB-OP{HRS:1-Stk:2:', name='j_aux_cr')
#
#
#
# class MainJohannCrystal(ISSPseudoPositioner):
#     crystal = Cpt(MainCrystal, name='crystal')
#     bragg = Cpt(PseudoSingle, name='bragg')
#     x = Cpt(PseudoSingle, name='x')
#
#     _real = ['crystal']
#     _pseudo = ['bragg', 'x']
#
#     def __init__(self, *args, R=1000, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.R = R
#
#     def register_bragg(self, bragg_reg):
#         act_pos = self.crystal.pseudo_pos2dict(self._forward({'bragg' : bragg_reg, 'x' : self.x.position})['crystal'])
#         nom_pos = self.crystal.position_dict
#         return act_pos, nom_pos
#
#     def _forward(self, pseudo_dict):
#         bragg, x = pseudo_dict['bragg'], pseudo_dict['x']
#
#         x_cr, y_cr, _, _ = compute_rowland_circle_geometry(0, 0, self.R, bragg, 0)
#         x_cr += self.R + x
#         roll_cr = bragg
#         yaw_cr = 0
#
#         crystal_real_pos = self.crystal.PseudoPosition(x_cr=x_cr,
#                                                        y_cr=y_cr,
#                                                        roll_cr=roll_cr,
#                                                        yaw_cr=yaw_cr)
#         return {'crystal': crystal_real_pos}
#
#     def _inverse(self, _real_dict):
#         real_dict = self.crystal.pseudo_pos2dict(_real_dict['crystal'])
#         bragg = real_dict['roll_cr']
#         x_cr = real_dict['x_cr']
#         x_cr_ref, _, _, _ = compute_rowland_circle_geometry(0, 0, self.R, bragg, 0)
#         x_cr_ref += self.R
#         x =  x_cr - x_cr_ref
#         return {'bragg' : bragg, 'x' : x}
#
# j_cr = MainJohannCrystal(name='j_cr')
#
#
#
# class AuxJohannCrystal(ISSPseudoPositioner):
#     crystal = Cpt(AuxCrystal, name='crystal')
#     bragg = Cpt(PseudoSingle, name='bragg')
#
#     _real = ['crystal']
#     _pseudo = ['bragg']
#
#     def __init__(self, *args, R=1000, cr_index=-1, dz=139.5, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.R = R
#         z = cr_index * dz
#         x_offset, _, _, yaw_offset = compute_rotated_rowland_circle_geometry(0, 0, 1000, 90, z)
#         self.crystal.yaw_offset = yaw_offset
#         self.crystal.x_offset = 1000 - x_offset
#
#     def register_bragg(self, bragg_reg):
#         act_pos = self.crystal.pseudo_pos2dict(self._forward({'bragg' : bragg_reg, 'x' : self.x.position})['crystal'])
#         nom_pos = self.crystal.position_dict
#         return act_pos, nom_pos
#
#     def _forward(self, pseudo_dict):
#         bragg = pseudo_dict['bragg']
#
#         x_cr_main, y_cr_main, x_det, y_det = compute_rowland_circle_geometry(0, 0, self.R, bragg, 0)
#         x_cr_rot, y_cr_rot, roll_cr_rot, yaw_cr_rot = compute_rotated_rowland_circle_geometry(0, 0, self.R, bragg, self.z)
#
#         x_cr = x_cr_rot - x_cr_main
#         y_cr = y_cr_rot - y_cr_main
#         roll_cr = roll_cr_rot
#         yaw_cr = yaw_cr_rot
#
#         crystal_real_pos = self.crystal.PseudoPosition(x_cr=x_cr,
#                                                        y_cr=y_cr,
#                                                        roll_cr=roll_cr,
#                                                        yaw_cr=yaw_cr)
#         return {'crystal': crystal_real_pos}
#
#     def _inverse(self, _real_dict):
#         real_dict = self.crystal.pseudo_pos2dict(_real_dict['crystal'])
#         bragg = real_dict['roll_cr']
#
#
#         x_cr = real_dict['x_cr']
#         x_cr_ref, _, _, _ = compute_rowland_circle_geometry(0, 0, self.R, bragg, 0)
#         x_cr_ref += self.R
#         x =  x_cr - x_cr_ref
#         return {'bragg' : bragg}
#
# j_cr = MainJohannCrystal(name='j_cr')

    # @pseudo_position_argument
    # def forward(self, pseudo_pos):
    #     return self._forward(pseudo_pos)
    #
    # @real_position_argument
    # def inverse(self, real_pos):
    #     return self._inverse(real_pos)

#

# j_cr.calibration_data = {'actual':  {'x_cr': [-1.9267746534999333, 0.35132603950000885],
#                                      'y_cr': [4.4379225, 4.4379225],
#                                      'bragg': [83, 82],
#                                      'yaw_cr': [840.0, 840.0]},
#                          'nominal': {'x_cr': [-1.9267746534999333, 0.35132603950000885],
#                                      'y_cr': [4.4379225, 4.4379225],
#                                      'bragg': [83.10000000000001, 82.05],
#                                      'yaw_cr': [840.0, 840.0]}}

# j_cr.process_calibration()






# class JohannMultiCrystalSpectrometer(ISSPseudoPositioner):
#     det_arm = Cpt(DetectorArm, name='det_arm')
#     crystal1 = Cpt(MainJohannCrystal, name='crystal1')
#
#     bragg = Cpt(PseudoSingle, name='bragg')
#     det_dR = Cpt(PseudoSingle, name='det_dR')
#     x_sp = Cpt(PseudoSingle, name='x_sp')
#
#     def __init__(self, *args, **kwargs):
#         self.restore_config()
#         super().__init__(*args, **kwargs)
#         # self.update_rowland_circle(self.R, self.src_x, self.src_y)
#
#     def restore_config(self):
#         self.R = 1000
#         self.x_src = 0
#         self.y_src = 0
#
#     # def update_rowland_circle(self, R, x_src, y_src):
#     #     self.RC = RowlandCircle(R, x_src=x_src, y_src=y_src)
#
#     def register_calibration_point(self, special_pseudo_pos):
#         super().register_calibration_point(special_pseudo_pos)
#         # _pos = self.calibration_data['nominal'][self.special_pseudo][-1]
#         for key in self.real_keys:
#             getattr(self, key).register_calibration_point(special_pseudo_pos)
#             # _pos = getattr(self, self.special_pseudo).position
#             # getattr(self, key).register_calibration_point(_pos)
#
#     def process_calibration(self, npoly=None):
#         super().process_calibration(npoly=npoly)
#         for key in self.real_keys:
#             getattr(self, key).process_calibration(npoly=npoly)
#
#     def reset_correction(self):
#         super().reset_correction()
#         for key in self.real_keys:
#             getattr(self, key).reset_correction()
#
#     def reset_calibration_data(self):
#         super().reset_calibration_data()
#         for key in self.real_keys:
#             getattr(self, key).reset_calibration_data()
#
#     # def _forward(self, pseudo_pos):
#         # bragg, det_dR, x_sp = pseudo_pos.bragg, pseudo_pos.det_dR, pseudo_pos.x_sp
#     def _forward(self, pseudo_dict):
#         bragg, det_dR, x_sp = pseudo_dict['bragg'], pseudo_dict['det_dR'], pseudo_dict['x_sp']
#
#         x_cr, y_cr, x_det, y_det = compute_rowland_circle_geometry(0, 0, self.R, bragg, det_dR)
#         x_det -= x_sp
#         det_arm_real_pos = self.det_arm.PseudoPosition(bragg=bragg, x_det=x_det, y_det=y_det)
#         x_cr = self.R + x_cr - x_sp
#         y_cr = self.crystal1.y0
#         yaw_cr = self.crystal1.yaw0 * 1000
#         crystal1_real_pos = self.crystal1.PseudoPosition(bragg=bragg, x_cr=x_cr, y_cr=y_cr, yaw_cr=yaw_cr)
#         # return self.RealPosition(det_arm=det_arm_real_pos,
#                                  # crystal1=crystal1_real_pos)
#         return {'det_arm' : det_arm_real_pos, 'crystal1' : crystal1_real_pos}
#
#     # def _inverse(self, real_pos):
#     #     bragg_cr = real_pos.crystal1.bragg
#     #     bragg_det = real_pos.det_arm.bragg
#     def _inverse(self, real_dict):
#         bragg_cr = real_dict['crystal1'].bragg
#         x_cr_ref, y_cr_ref, _, _ = compute_rowland_circle_geometry(0, 0, self.R, bragg_cr, 0)
#         x_cr = real_dict['crystal1'].x_cr - self.R
#         x_sp = x_cr - x_cr_ref
#
#         bragg_det = real_dict['det_arm'].bragg
#         _, _, x_det_ref, y_det_ref = compute_rowland_circle_geometry(x_sp, 0, self.R, bragg_det, 0)
#         x_det, y_det = real_dict['det_arm'].x_det, real_dict['det_arm'].y_det
#         det_dR = np.sqrt((x_det - x_det_ref)**2 + (y_det - y_det_ref)**2) * np.sign(y_det_ref - y_det)
#
#         # return self.PseudoPosition(bragg=bragg_cr, det_dR=det_dR, x_sp=x_sp)
#
#         return {'bragg' : bragg_cr, 'det_dR' : det_dR, 'x_sp' : x_sp}
#
# jsp = JohannMultiCrystalSpectrometer(name='jsp')


# motor_emission_dict = {'name': jsp.bragg.name, 'description' : 'Spectrometer Bragg angle', 'object': jsp.bragg, 'group': 'spectrometer'}
# motor_dictionary['johann_bragg_angle'] = {'name': jsp.bragg.name,
#                                           'description' : 'Johann Bragg Angle',
#                                           'object': jsp.bragg,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_det_focus'] =   {'name': jsp.det_dR.name,
#                                           'description' : 'Johann Detector Focus',
#                                           'object': jsp.det_dR,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_x'] =           {'name': jsp.x_sp.name,
#                                           'description' : 'Johann X',
#                                           'object': jsp.x_sp,
#                                           'group': 'spectrometer'}






# from xas.xray import bragg2e, e2bragg
# from xas.fitting import Nominal2ActualConverter
# class JohannEmissionMotor(PseudoPositioner):
#     spectrometer = Cpt(JohannMultiCrystalSpectrometer, name='bragg')
#     energy = Cpt(PseudoSingle, name='energy')
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.json_path = f'{ROOT_PATH_SHARED}/settings/json/johann_config.json'
#         self.init_from_settings()
#         self.calibration_data = {'energy_nominal' : [], 'bragg_nominal' : [], 'bragg_actual' : []}
#         self.bragg_calibration = None
#         self.apply_calibration = True
#         self.bragg = self.spectrometer.bragg #alias
#
#     #########
#     def load_config(self, file):
#         with open(file, 'r') as f:
#             config = json.loads(f.read())
#         return config
#
#     def save_config(self, file):
#         config = self.get_config()
#         with open(file, 'w') as f:
#             json.dump(config, f)
#
#     def save_to_settings(self):
#         self.save_config(self.json_path)
#
#     def init_from_settings(self):
#         try:
#             config = self.load_config(self.json_path)
#             self.spectrometer.crystal1.restore_parking(config)
#             self.spectrometer.det_arm.restore_parking(config)
#         except FileNotFoundError:
#             print('Could not find Johann spectrometer configuration file. Proceed with caution.')
#             config = {}
#         self.update_johann_parameters(**config)
#
#     def update_johann_parameters(self, crystal='Si', hkl=(7, 3, 3), R=1000, x_src=0, y_src=0, **kwargs):
#         self.crystal = crystal
#         self.hkl = hkl
#         self.spectrometer.R = R
#         self.spectrometer.x_src = x_src
#         self.spectrometer.y_src = y_src
#
#     def get_config(self):
#         config = {'crystal' : self.crystal,
#                 'hkl': self.hkl,
#                 'R': self.spectrometer.R,
#                 'x_src': self.spectrometer.x_src,
#                 'y_src' : self.spectrometer.y_src}
#         crystal1_config = self.spectrometer.crystal1.read_current_config()
#         det_arm_config = self.spectrometer.det_arm.read_current_config()
#
#         return {**config, **crystal1_config, **det_arm_config}
#
#     def set_main_crystal_parking(self):
#         self.spectrometer.crystal1.set_parking()
#         self.save_to_settings()
#
#     def set_det_arm_parking(self):
#         self.spectrometer.det_arm.set_parking()
#         self.save_to_settings()
#
#     def register_calibration_point(self, energy):
#         self.calibration_data['energy_nominal'].append(energy)
#         self.calibration_data['bragg_nominal'].append(e2bragg(energy, self.crystal, self.hkl))
#         self.calibration_data['bragg_actual'].append(self.spectrometer.bragg.position)
#
#     def process_calibration(self, n_poly=2):
#         self.bragg_calibration = Nominal2ActualConverter(self.calibration_data['bragg_nominal'],
#                                                          self.calibration_data['bragg_actual'],
#                                                          n_poly=n_poly)
#
#     def _forward(self, pseudo_pos):
#         energy = pseudo_pos.energy
#         bragg = e2bragg(energy, self.crystal, self.hkl)
#         if (self.bragg_calibration is not None) and (self.apply_calibration):
#             bragg = self.bragg_calibration.nom2act(bragg)
#         det_dR = self.spectrometer.det_dR.position
#         x_sp = self.spectrometer.x_sp.position
#         pos = self.spectrometer.PseudoPosition(bragg=bragg, det_dR=det_dR, x_sp=x_sp)
#         return self.RealPosition(spectrometer=pos)
#
#     def _inverse(self, real_pos):
#         bragg = real_pos.spectrometer.bragg
#         if (self.bragg_calibration is not None) and (self.apply_calibration):
#             bragg = self.bragg_calibration.act2nom(bragg)
#         energy = bragg2e(bragg, self.crystal, self.hkl)
#         return self.PseudoPosition(energy=energy)
#
#     @pseudo_position_argument
#     def forward(self, pseudo_pos):
#         return self._forward(pseudo_pos)
#
#     @real_position_argument
#     def inverse(self, real_pos):
#         return self._inverse(real_pos)
#
# johann_emission = JohannEmissionMotor(name='johann_emission')
#

# motor_dictionary['johann_bragg_angle'] = {'name': johann_emission.spectrometer.bragg.name,
#                                           'description' : 'Johann Bragg Angle',
#                                           'object': johann_emission.spectrometer.bragg,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_det_focus'] =   {'name': johann_emission.spectrometer.det_dR.name,
#                                           'description' : 'Johann Detector Focus',
#                                           'object': johann_emission.spectrometer.det_dR,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_x'] =           {'name': johann_emission.spectrometer.x_sp.name,
#                                           'description' : 'Johann X',
#                                           'object': johann_emission.spectrometer.x_sp,
#                                           'group': 'spectrometer'}
#
# motor_dictionary['johann_energy'] =      {'name': johann_emission.energy.name,
#                                           'description' : 'Johann Energy',
#                                           'object': johann_emission.energy,
#                                           'group': 'spectrometer'}



# def move_det_arm_only(bragg):
#     _, _, x_det, y_det = compute_rowland_circle_geometry(0, 0, 1000, bragg, 0)
#     # print(johann_emission.spectrometer.det_arm.position)
#     johann_emission.spectrometer.det_arm.move(bragg=bragg, x_det=x_det, y_det=y_det)
#
# move_det_arm_only(82)


# ba_set = 75.5
# row_circle.compute_geometry(ba_set)
# coords = row_circle.detector_coords
# jsp.det_arm.move(ba=ba_set, x_det=coords[0], y_det=coords[1])

# ccs_pseudo = (ba_set, *row_circle.detector_coords)
# # ccs_real = det_arm.forward(ba_set, *row_circle.detector_coords)
# # ccs_pseudo = det_arm.inverse(ccs_real)
# # print(ccs_real)
# # print(ccs_pseudo)
# #
# det_arm.move(ba=ccs_pseudo[0], x_det=ccs_pseudo[1], y_det=ccs_pseudo[2])
#
# plt.figure(2, clear=True)
# for ba_set in np.arange(65, 91):
#     row_circle.compute_geometry(ba_set)
#     ccs = det_arm._forward((ba_set, *row_circle.detector_coords))
#     plt.plot(ba_set, ccs[0], 'k.')
#     plt.plot(ba_set, ccs[1], 'm.')
#     plt.plot(ba_set, ccs[2], 'b.')
# # # det_arm.forward((90, 0, 0))


#
#
# import h5py
# class RIXSLogger:
#     scanned_emission_energies = np.array([])
#     normalized_points = np.array([])
#     herfd_list = []
#
#     def __init__(self, filepath, resume_flag=False):
#         self.filepath = filepath
#         if resume_flag:
#             self._find_scanned_emission_energies()
#         else:
#             try:
#                 f = h5py.File(self.filepath, 'w-')
#                 f.close()
#             except OSError:
#                 raise OSError('rixs log file with this name already exists')
#
#
#
#     def _find_scanned_emission_energies(self):
#         f = h5py.File(self.filepath, 'r')
#         self.herfd_list = list(f.keys())
#         for uid in self.herfd_list:
#             ee = f[f'{uid}/emission_energy'][()]
#             # self.scanned_emission_energies.append(ee)
#             self.scanned_emission_energies = np.append(self.scanned_emission_energies, ee)
#             # print(ee)
#             if 'uid_norm' in f[f'{uid}'].keys():
#                 # self.normalized_points.append(True)
#                 self.normalized_points = np.append(self.normalized_points, True)
#             else:
#                 self.normalized_points = np.append(self.normalized_points, False)
#         f.close()
#         self.scanned_emission_energies = np.array(self.scanned_emission_energies)
#         self.normalized_points = np.array(self.normalized_points)
#
#     def energy_was_measured(self, emission_energy, threshold=1e-3):
#         if len(self.scanned_emission_energies) == 0:
#             return False
#         d = np.min(np.abs(self.scanned_emission_energies - emission_energy))
#         return d < threshold
#
#     def point_was_normalized(self, herfd_uid_to_check):
#         for i, herfd_uid in enumerate(self.herfd_list):
#             if herfd_uid_to_check == herfd_uid:
#                 return self.normalized_points[i]
#         return
#
#     def set_point_as_normalized(self, herfd_uid_to_check):
#         for i, herfd_uid in enumerate(self.herfd_list):
#             if herfd_uid_to_check == herfd_uid:
#                 self.normalized_points[i] = True
#
#     def write_uid_herfd(self, uid_herfd, emission_energy):
#         f = h5py.File(self.filepath, 'r+')
#         f.create_group(uid_herfd)
#         f[uid_herfd]['emission_energy'] = emission_energy
#         f.close()
#         self.herfd_list.append(uid_herfd)
#         self.scanned_emission_energies = np.array(self.scanned_emission_energies.tolist() + [emission_energy])
#         self.normalized_points = np.array(self.normalized_points.tolist() + [False])
#
#     def write_herfd_pos(self, uid_herfd, x_nom, y_nom, z_nom, x_act, y_act, z_act):
#         f = h5py.File(self.filepath, 'r+')
#         f[uid_herfd]['x_nom'] = x_nom
#         f[uid_herfd]['y_nom'] = y_nom
#         f[uid_herfd]['z_nom'] = z_nom
#         f[uid_herfd]['x_act'] = x_act
#         f[uid_herfd]['y_act'] = y_act
#         f[uid_herfd]['z_act'] = z_act
#         f.close()
#
#     def write_uid_norm(self, uid_herfd, uid_norm, energy_in_norm, energy_out_norm,
#                        x_norm_nom, y_norm_nom, z_norm_nom,
#                        x_norm_act, y_norm_act, z_norm_act):
#         f = h5py.File(self.filepath, 'r+')
#         f[uid_herfd]['uid_norm'] = uid_norm
#         f[uid_herfd]['x_norm_nom'] = x_norm_nom
#         f[uid_herfd]['y_norm_nom'] = y_norm_nom
#         f[uid_herfd]['z_norm_nom'] = z_norm_nom
#         f[uid_herfd]['x_norm_act'] = x_norm_act
#         f[uid_herfd]['y_norm_act'] = y_norm_act
#         f[uid_herfd]['z_norm_act'] = z_norm_act
#         f[uid_herfd]['energy_in_norm'] = energy_in_norm
#         f[uid_herfd]['energy_out_norm'] = energy_out_norm
#         f.close()
#         self.set_point_as_normalized(uid_herfd)
#
#
#
#
#
#
# def function_for_measuing_samples():
#     sample_1_x, sample_1_y, sample_1_z = -25.586,  1.613, -20.301
#     sample_2_x, sample_2_y, sample_2_z = -25.741,-15.287, -20.401
#     sample_3_x, sample_3_y, sample_3_z = -25.146, -29.887, -21.301
#     RE(move_sample(sample_1_x, sample_1_y, sample_1_z))
#     xlive_gui.widget_run.parameter_values[0].setText(f'FeTiO3 HERFD')
#     xlive_gui.widget_run.run_scan()
#     for i in range(3):
#         RE(move_sample(sample_2_x, sample_2_y, sample_2_z))
#         xlive_gui.widget_run.parameter_values[0].setText(f'LiTi2O3 HERFD')
#         xlive_gui.widget_run.run_scan()
#
#         RE(move_sample(sample_3_x, sample_3_y, sample_3_z))
#         xlive_gui.widget_run.parameter_values[0].setText(f'CaTiO3 HERFD')
#         xlive_gui.widget_run.run_scan()
#
#
#
# def rixs_scan_plan(energies_in, energies_out):
#     for energy_in in energies_in:
#         yield from bps.mv(hhm.energy, energy_in)
#         yield from emission_scan_plan(energies_out)
#
#
# ###########
# def rixs_scan_RE(energies_out):
#     for energy_out in energies_out:
#
#         widget_run.run_scan()
#
#
#
#
# ###########
#
#
# def move_sample(x, y, z):
#     yield from bps.mv(giantxy.x, x)
#     yield from bps.mv(giantxy.y, y)
#     yield from bps.mv(usermotor2.pos, z)
#
# # def move_sample_back(dx, dy, dz):
# #     sdsdfsd
# #     yield from bps.mv(giantxy.x, -dx)
# #     yield from bps.mv(giantxy.y, -dy)
# #     yield from bps.mvr(usermotor2.pos, -dz)
#
#
# def get_snake_trajectory(x, y, step=0.2):
#     x0 = giantxy.x.user_readback.get()
#     y0 = giantxy.y.user_readback.get()
#     z0 = usermotor2.pos.user_readback.get()
#
#     _dxs = np.arange(0, x+step, step) / np.cos(np.deg2rad(30))
#     _dys = np.arange(0, y+step, step)
#     _dzs = -_dxs/np.cos(np.deg2rad(30))
#     position_list = []
#     for dx, dz in zip(_dxs, _dzs):
#         for dy in _dys:
#             position_list.append([x0 + dx, y0+dy, z0+dz])
#     return position_list
#
#
# #positions = get_snake_trajectory(3, 3, 0.2)
# # widget_run = xlive_gui.widget_run
#
# def rixs_scan_from_mara_at_each_new_point(energies_out, positions, energies_kbeta):
#     filename = f'/nsls2/xf08id/users/2021/1/308190/rixs_Co3MnO4_uids_{new_uid()[:6]}.txt'
#     print(f'Uids will be stored under  {filename}')
#     for energy_out, position in zip(energies_out, positions):
#         print(f'Emission energy {energy_out}' )
#         print('Starting Move Energy...')
#         RE(move_emission_energy_plan(energy_out))
#         print('Move Energy Complete')
#         print('Starting Move Sample...')
#         RE(move_sample(*position))
#         print('Move Sample Complete')
#         print('Starting HERFD Scan...')
#         widget_run.run_scan()
#         print('HERFD Scan complete...')
#         uid_herfd = db[-1].start['uid']
#
#
#         while np.abs(hhm.energy.user_readback.get() - 8000) > 1:
#             try:
#                 print('attempting to move energy to 8000')
#                 RE(bps.mv(hhm.energy, 8000, timeout=30))
#             except:
#                 print('the motion timed out. Stopping the motor.')
#                 hhm.energy.stop()
#
#         print('Starting Emission Scan...')
#         uid_xes = RE(emission_scan_plan(energies_kbeta))
#         print('Emission Scan complete...')
#         with open(filename, "a") as text_file:
#             text_file.write(ttime.ctime() + ' ' + uid_herfd + ' ' + uid_xes[0] + '\n')
#
# #rixs_scan_from_mara_at_each_new_point(energies_emission,
# #                                      positions[:energies_emission.size],
# #                                      energies_kbeta)
#
# # start_position_idx = 21
# # for i in range(4):
# #    idx1 = i*energies_emission.size + start_position_idx
# #    idx2 = (i+1) * energies_emission.size + start_position_idx
# #    print(idx1, idx2)
# #    rixs_scan_from_mara_at_each_new_point(energies_emission, positions_co3mno4[idx1:idx2], energies_kbeta)
# #    print(f'last position used was {idx2}')
#
# #positions_co3mno4[0] = [-26.502437515, -29.168950962, -23.0959375]
# #positions_co3mno4 = get_snake_trajectory(3.5, 4, 0.15)
#
#
#
#
# def herfd_scan_in_pieces_plan(energies_herfd, positions, pos_start_index, n=4, exp_time=0.5):
#     idx_e = np.round(np.linspace(0, energies_herfd.size-1, n+1))
#     for i in range(idx_e.size-1):
#         idx1 = int( np.max([idx_e[i]-1, 0]) )
#         idx2 = int( np.min([idx_e[i+1]+1, energies_herfd.size-1]) )
#         print(f'the scan will be performed between {energies_herfd[idx1]} and {energies_herfd[idx2]}')
#         energy_steps = energies_herfd[idx1:idx2]
#         time_steps = np.ones(energy_steps.shape) * exp_time
#         yield from move_sample(*positions[pos_start_index+i])
#         partial_herfd_plan = step_scan_plan('Co3MnO4 long HERFD scan',
#                                             '',
#                                             energy_steps, time_steps, [pil100k, apb_ave], element='Co', e0=7709, edge='K')
#         yield from shutter.open_plan()
#         yield from partial_herfd_plan
#         yield from shutter.close_plan()
#
#
#
#
#
# # energies_herfd = db['5bcffa42-fa10-48cb-a8ea-f77172456976'].table()['hhm_energy'].values
# # this_herfd_plan = herfd_scan_in_pieces_plan(energies_herfd, positions, 21, n=4, exp_time=1)
# # RE(this_herfd_plan)
#
#
#
# # energies_calibration = np.array([7625,7650,7675,7700,7725])
# # uids = RE(calibration_scan_plan(energies_calibration))
# #EC = analyze_many_elastic_scans(db, uids, energies_calibration, plotting=True)
#
#
#
#
#
#
#
#
# # def test():
# #     eem = define_spectrometer_motor('Ge', [4,4,4])
# #     print(eem._get_postion_for_energy(7649))
# #     print(eem._get_postion_for_energy(7639))
# #     print(eem._get_postion_for_energy(7629))
#
# #
# # test()
#
# ######
#
#
# # spectrometer_calibration_dict = {}
#
# # Energy      CrX         CrY         DetY
# # 7649.2     -129.570     16.285       331.731
# # 7639.2     -132.144
#
# def move_to_7649():
#     yield from bps.mv(auxxy.x,-129.570 )
#     yield from bps.mv(auxxy.y, 16.285)
#     yield from bps.mv(huber_stage.z,331.731)
#     yield from bps.mv(hhm.energy,7649.2)
#
# #######
# def define_energy_range():
#     # for CoO
#    # energies_kbeta = np.linspace(7625, 7665, 41)
#    # energies_emission = np.arange(7641, 7659+0.25, 0.25)
#     # for Co4O
#     energies_kbeta = np.linspace(7649, 7650, 2)
#     energies_emission = np.arange(7627, 7659+0.25, 0.25)
#     return energies_kbeta, energies_emission
#
#
#
# # energies_vtc_cubanes = np.hstack((np.arange(7670, 7684+2, 2),
# #                                   np.arange(7685, 7712+0.5, 0.5),
# #                                   np.arange(7714, 7725+2, 2)))[::-1]
# def scan_vtc_plan(energies_vtc, positions, start_index):
#     idx = start_index + 0
#
#     while True:
#         print(f'moving to sample index {idx} at {positions[idx]}')
#         yield from move_sample(*positions[idx])
#         yield from emission_scan_plan(energies_vtc)
#         idx += 1
#
#
#
#
#
# # energies_vtc_cubanes = np.arange(7670, 7725+0.25, 0.25)
# # energies_vtc_cubanes = np.hstack((np.arange(7670, 7684+2, 2), np.arange(7685, 7712+0.5, 0.5), np.arange(7714, 7725+2, 2)))
# # RE(move_to_7649())
# # eem_calculator = define_spectrometer_motor('Ge', [4, 4, 4])
# # energies_kbeta, energies_emission = define_energy_range()
# # RE(move_sample(*[-24.7386537495, -15.568973257, -22.495625]))
# # positions = get_snake_trajectory(2.5, 4.2, 0.15)
# # widget_run = xlive_gui.widget_run
# #energies_kbeta_fine = np.linspace(7625, 7665, 51)
#
