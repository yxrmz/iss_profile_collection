import matplotlib.pyplot as plt


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

# bla = []
# DELTA = []
# extrapolate_linearly([3, 4], bla, DELTA)


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

        self.init_from_settings()
        self.compute_trajectories()

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
        self.config['bragg_registration']['bragg'] = {k : [] for k in _johann_spectrometer_motor_keys}
            #
            #
            #
            #
            # self.converter_nom2act = {}
            # for motor_key in _johann_spectrometer_motor_keys:
            #     # _c_nom2act = Nominal2ActualConverterWithLinearInterpolation()
            #     pos_nom = config['bragg_registration']['pos_nom'][motor_key]
            #     pos_act = config['bragg_registration']['pos_act'][motor_key]
            #     for _pos_nom, _pos_act in zip(pos_nom, pos_act):
            #         _c_nom2act.append_point(_pos_nom, _pos_act)
            #     self.converter_nom2act[motor_key] = _c_nom2act

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
        self.compute_trajectories()

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
            self.det_focus = det_focus
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


# johann_emission.energy._limits=(8004, 8068)


# _johann_motor_dictionary = {
# 'auxxy_x':                  {'name': auxxy.x.name,                                     'description': 'Johann Crystal Assy X',        'object': auxxy.x,                                  'keyword': 'Crystal Assy X',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
# 'auxxy_y':                  {'name': auxxy.y.name,                                     'description': 'Johann Detector X',            'object': auxxy.y,                                  'keyword': 'Detector X',           'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
# 'johann_cr_main_roll':      {'name': johann_main_crystal.motor_cr_main_roll.name,      'description': 'Johann Main Crystal Roll',     'object': johann_main_crystal.motor_cr_main_roll,   'keyword': 'Main Crystal Roll',    'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
# 'johann_cr_main_yaw':       {'name': johann_main_crystal.motor_cr_main_yaw.name,       'description': 'Johann Main Crystal Yaw',      'object': johann_main_crystal.motor_cr_main_yaw,    'keyword': 'Main Crystal Yaw',     'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
# 'johann_cr_aux2_roll':      {'name': johann_aux2_crystal.motor_cr_aux2_roll.name,      'description': 'Johann Aux2 Crystal Roll',     'object': johann_aux2_crystal.motor_cr_aux2_roll,   'keyword': 'Aux2 Crystal Roll',    'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
# 'johann_cr_aux2_yaw':       {'name': johann_aux2_crystal.motor_cr_aux2_yaw.name,       'description': 'Johann Aux2 Crystal Yaw',      'object': johann_aux2_crystal.motor_cr_aux2_yaw,    'keyword': 'Aux2 Crystal Yaw',     'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
# 'johann_cr_aux2_x':         {'name': johann_aux2_crystal.motor_cr_aux2_x.name,         'description': 'Johann Aux2 Crystal X',        'object': johann_aux2_crystal.motor_cr_aux2_x,      'keyword': 'Aux2 Crystal X',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2500},
# 'johann_cr_aux2_y':         {'name': johann_aux2_crystal.motor_cr_aux2_y.name,         'description': 'Johann Aux2 Crystal Y',        'object': johann_aux2_crystal.motor_cr_aux2_y,      'keyword': 'Aux2 Crystal Y',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 1000},
# 'johann_cr_aux3_roll':      {'name': johann_aux3_crystal.motor_cr_aux3_roll.name,      'description': 'Johann Aux3 Crystal roll',     'object': johann_aux3_crystal.motor_cr_aux3_roll,   'keyword': 'Aux3 Crystal roll',    'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 100},
# 'johann_cr_aux3_yaw':       {'name': johann_aux3_crystal.motor_cr_aux3_yaw.name,       'description': 'Johann Aux3 Crystal Yaw',      'object': johann_aux3_crystal.motor_cr_aux3_yaw,    'keyword': 'Aux3 Crystal Yaw',     'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 50},
# 'johann_cr_aux3_x':         {'name': johann_aux3_crystal.motor_cr_aux3_x.name,         'description': 'Johann Aux3 Crystal X',        'object': johann_aux3_crystal.motor_cr_aux3_x,      'keyword': 'Aux3 Crystal X',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2500},
# 'johann_cr_aux3_y':         {'name': johann_aux3_crystal.motor_cr_aux3_y.name,         'description': 'Johann Aux3 Crystal Y',        'object': johann_aux3_crystal.motor_cr_aux3_y,      'keyword': 'Aux3 Crystal Y',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 1000},
# 'johann_cr_main_bragg':     {'name': johann_main_crystal.bragg.name,                   'description': 'Johann Main Crystal Bragg',    'object': johann_main_crystal.bragg,                'keyword': 'Main Crystal Bragg',   'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
# 'johann_cr_aux2_bragg':     {'name': johann_aux2_crystal.bragg.name,                   'description': 'Johann Aux2 Crystal Bragg',    'object': johann_aux2_crystal.bragg,                'keyword': 'Aux2 Crystal Bragg',   'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
# 'johann_cr_aux3_bragg':     {'name': johann_aux3_crystal.bragg.name,                   'description': 'Johann Aux3 Crystal Bragg',    'object': johann_aux3_crystal.bragg,                'keyword': 'Aux3 Crystal Bragg',   'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 0.05},
# 'johann_det_focus':         {'name': johann_det_arm.det_focus.name,                    'description': 'Johann Detector Focus',        'object': johann_det_arm.det_focus,                 'keyword': 'Detector Focus',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 5},
# 'johann_x':                 {'name': johann_spectrometer_x.x.name,                     'description': 'Johann Spectrometer X',        'object': johann_spectrometer_x.x,                  'keyword': 'Spectrometer X',       'group': 'spectrometer',  'user': False, 'spectrometer_kind': 'johann', 'typical_step': 2.5},
# 'johann_bragg_angle':       {'name': johann_spectrometer.bragg.name,                   'description': 'Johann Global Bragg Angle',    'object': johann_spectrometer.bragg,                'keyword': 'Global Bragg Angle',   'group': 'spectrometer',  'user': True,  'spectrometer_kind': 'johann', 'typical_step': 0.05},
# 'johann_energy':            {'name': johann_emission.energy.name,                      'description': 'Johann Emission Energy',       'object': johann_emission.energy,                   'keyword': 'Emission Energy',      'group': 'spectrometer',  'user': True,  'spectrometer_kind': 'johann', 'typical_step': 1},
# }
#
# motor_dictionary = {**motor_dictionary, **_johann_motor_dictionary}


centroid_y = EpicsSignal('XF:08IDB-BI{BPM:SP-2}Stats1:CentroidY_RBV', name='centroid_y')
intensity = EpicsSignal('XF:08IDB-BI{BPM:SP-2}Stats1:Total_RBV', name='intensity')

centroid_y_data = {'value': [], 'timestamp': []}
intensity_data =  {'value': [], 'timestamp': []}

def cb_add_data(value, **kwargs):
    # print_to_gui(f"{value = }", add_timestamp=True)
    if len(centroid_y_data) >=10000:
        centroid_y_data['value'].pop(0)
        centroid_y_data['timestamp'].pop(0)
    centroid_y_data['value'].append(value)
    centroid_y_data['timestamp'].append(kwargs['timestamp'])

centroid_y.subscribe(cb_add_data)

def cb_add_data_int(value, **kwargs):
    # print_to_gui(f"{value = }", add_timestamp=True)
    if len(intensity_data) >=10000:
        intensity_data['value'].pop(0)
        intensity_data['timestamp'].pop(0)
    intensity_data['value'].append(value)
    intensity_data['timestamp'].append(kwargs['timestamp'])

intensity.subscribe(cb_add_data_int)


def get_fft(t, s):
    freq = np.fft.fftfreq(t.size, d=t[1] - t[0])
    s_fft = np.abs(np.fft.fft(s))[np.argsort(freq)]
    freq = freq[np.argsort(freq)]
    return freq[freq>0], s_fft[freq>0]

def plot_fft(t, s, *args, **kwargs):
    f, s_fft = get_fft(np.array(t), np.array(s))
    plt.plot(f, s_fft, *args, **kwargs)

def plot_trace_info(data_dict, fignum=1, clear=True):
    t = np.linspace(data_dict['timestamp'][0], data_dict['timestamp'][-1], len(data_dict['timestamp']))
    v = np.interp(t, data_dict['timestamp'], data_dict['value'])

    # t = np.linspace(intensity_data['timestamp'][0], intensity_data['timestamp'][-1], len(intensity_data['timestamp']))
    # v = np.interp(t, intensity_data['timestamp'], intensity_data['value'])

    freq, centroid_fft = get_fft(t, v)
    # freq = np.fft.fftfreq(v.size, d=t[1] - t[0])
    # centroid_fft = np.abs(np.fft.fft(v))[np.argsort(freq)]
    # freq = freq[np.argsort(freq)]

    plt.figure(fignum, clear=clear)
    plt.subplot(221)
    plt.plot(data_dict['timestamp'], data_dict['value'] - np.mean(data_dict['value']))

    plt.subplot(222)
    plt.hist(data_dict['value'] - np.mean(data_dict['value']), 100, density=True);

    plt.subplot(223)
    plt.semilogy(freq, centroid_fft)
    plt.xlim(0.1, 15)
    # plt.ylim(1e2, 1e6)
# plt.semilogy(centroid_fft)


plot_trace_info(centroid_y_data, )
plot_trace_info(intensity_data, fignum=2)

centroid_y_data_85_3 = copy.deepcopy(centroid_y_data)
intensity_data_85_3 = copy.deepcopy(intensity_data)

plot_trace_info(centroid_y_data_85, clear=True, fignum=1)
plot_trace_info(centroid_y_data_65, clear=False, fignum=1)

plot_trace_info(intensity_data_85, fignum=2)

plot_trace_info(centroid_y_data_85_2, clear=True, fignum=1)
plot_trace_info(centroid_y_data_85_3, clear=False, fignum=1)

plot_trace_info(intensity_data_85_2, clear=True, fignum=2)
plot_trace_info(intensity_data_85_3, clear=False, fignum=2)


apb_ave.set_exposure_time(10)
RE(bp.count([apb_ave]))

t = db[-1].table()

# gain was set to 5
t_all_connected_no_scope = db['af703640-8980-4dcd-9545-4c8f0fce4046'].table()
t_all_connected_no_scope_ir_it = db['4d156431-bb99-47e0-af71-c1f1b8b3c0ec'].table()

t_no_amplifier_no_scope = db['ced4d069-6d30-443f-913c-704afa08b5a2'].table()
t_all_conneced_no_scope_with_dominik = db['1c8eaaf9-8d6a-4b86-8255-8559be5d9591'].table()

t_all_connected_no_scope_manual_gain = db['abc456fc-2014-4fab-b55c-6420c7a11e79'].table()
t_all_connected_no_scope_manual_gain_10MHz = db['676abda3-cb15-4612-a6a7-3c88d3be874e'].table()
t_all_connected_no_scope_manual_gain_FB = db['d44ce8d5-0fb3-4af6-985e-346dc98c3d93'].table()
t_all_connected_no_scope_direct_cable = db['aa5c3275-e63f-453a-847d-3d54cce0b015'].table()
t_all_connected_no_scope_direct_cable_with_grounding = db['6869fdc4-1fc9-4057-88ed-53c636bfed4a'].table()

# t_all_connected_no_scope_direct_cable_keithley = db['e0e2ef0e-796a-49d3-aad4-f8929762fe12'].table()
t_all_connected_no_scope_direct_cable_keithley = db['0d265f78-2950-4035-a5b8-60a148af1f19'].table()

t_all_connected_no_scope_direct_cable_ir_held_in_air = db['51f7ed41-e51d-4a5c-a45f-6f1db556ddd1'].table()

t_hv_on = db['62165c00-4b05-4883-850c-fa1510fcad8d'].table()
t_i0_hv_off = db['ae9987b5-7abf-4802-bf72-9067047480ea'].table()
t_all_hv_off = db['964d21f1-0d25-4ffa-91f7-10bd2c5e29b8'].table()

t_apb_only = db['a363016d-8f62-475b-b95c-20ac01172f91'].table()

def _plot_traces(_time, _v, *args, **kwargs):
    plt.subplot(221)
    plt.plot(_time, _v - np.mean(_v), *args, **kwargs)

    plt.subplot(222)
    plt.hist(_v - np.mean(_v), 50, alpha=0.5);

    plt.subplot(223)
    plot_fft(_time, _v, *args, **kwargs)

def plot_traces(t, *args, ch=1, **kwargs):
    _time = np.array(t[f'apb_ave_time_wf'][1])
    _v = np.array(t[f'apb_ave_ch{ch}_wf'][1])
    _plot_traces(_time, _v, *args, **kwargs)


plt.figure()
# plot_traces(t_hv_on, label='HV ON')
# plot_traces(t_i0_hv_off, label='I0 HV OFF')
# plot_traces(t_all_hv_off, label='ALL HV OFF')
plot_traces(t_apb_only, ch=1, label='APB only I0')
plot_traces(t_apb_only, ch=2, label='APB only It')
# plot_traces(t_apb_only, ch=3, label='APB only Ir')
# plot_traces(t_apb_only, ch=4, label='APB only If')



plt.legend()
plt.yscale('log')


bla1 = np.array(t_hv_on['apb_ave_ch1_wf'][1])
bla2 = np.array(t_hv_on['apb_ave_ch2_wf'][1])
bla3 = np.array(t_hv_on['apb_ave_ch3_wf'][1])
bla4 = np.array(t_hv_on['apb_ave_ch4_wf'][1])

bla = np.vstack((bla1, bla2, bla3, bla4))

plt.figure()
plt.plot(bla2, bla3, 'k.')
plt.axis('square')

plt.figure()
plt.imshow(np.corrcoef(bla))
# plot_traces(t_all_connected_no_scope, label='no scope')
# plot_traces(t_all_connected_no_scope_direct_cable, label='FEMTO direct cable no scope')
# plot_traces(t_all_connected_no_scope_direct_cable_keithley, label='KEITHLEY direct cable no scope')

# plot_traces(t_all_connected_no_scope_direct_cable_with_grounding, label='direct cable and grounding no scope')

# plot_traces(t_all_conneced_no_scope_with_dominik, label='dominik no scope')
# plot_traces(t_all_connected_no_scope_manual_gain, label='1 MHzmanual gain no scope')
# plot_traces(t_all_connected_no_scope_manual_gain_10MHz, label='10 Mhz manual gain no scope')
# plot_traces(t_all_connected_no_scope_manual_gain_FB, label='FB manual gain no scope')
plot_traces(t_no_amplifier_no_scope, label='no amplifier no scope')

plt.legend()
plt.yscale('log')



plt.figure()
plot_traces(t_all_connected_no_scope_ir_it, label='no scope IR', ch=3)
plot_traces(t_all_connected_no_scope_direct_cable_ir_held_in_air, label='no scope IR in air', ch=3)

# plot_traces(t_all_connected_no_scope_ir_it, label='with scope Ir', ch=2)
# plot_traces(t_all_connected_no_scope_ir_it, label='with scope It', ch=3)
# plot_traces(t_all_connected_no_scope_ir_it, label='no scope Ir', ch=3)
# plot_traces(t_all_conneced_no_scope_with_dominik, label='dominik no scope')
# plot_traces(t_all_connected_no_scope_manual_gain, label='manual gain no scope')
# plot_traces(t_all_connected_no_scope_manual_gain_10MHz, label='10 Mhz no scope')
# plot_traces(t_all_connected_no_scope_manual_gain_FB, label='FB no scope')
# plot_traces(t_no_amplifier_no_scope, label='no amplifier no scope')

plt.figure()
_plot_traces(t_all_connected_no_scope[f'apb_ave_time_wf'][1],
             np.array(t_all_connected_no_scope['apb_ave_ch2_wf'][1]) / np.array(t_all_connected_no_scope['apb_ave_ch1_wf'][1]))



RE(bp.count([apb_ave]))


t_85 = db['668a4f77-567e-4516-ba8e-a861740298ae'].table()
t_65 = db['d69716cf-454b-4f9d-b567-d5f9ea18b6be'].table()

# no expansion tank
t_85_2 = db['d8828258-96d6-4b0e-96d1-da68c099afb7'].table()

# with expansion tank
t_85_3 = db['b33a284e-a12f-4762-a57d-9a280e874b0f'].table()

t_5000 = db['280aec42-a42c-44fd-9862-bbc3f7339d65'].table()

t_2021 = db_archive['65eb5b76-4598-43f0-bde0-233df7a3a5db'].table()

plt.figure()
# plt.plot(t_2021.apb_ave_time_wf[1], np.array(t_2021.apb_ave_ch1_wf[1])/ 1560 * 930)
# plt.plot(t_5000.apb_ave_time_wf[1], t_5000.apb_ave_ch1_wf[1])
# plt.plot(t_85.apb_ave_time_wf[1], t_85.apb_ave_ch1_wf[1])
# plt.plot(t_65.apb_ave_time_wf[1], t_65.apb_ave_ch1_wf[1])

# plot_traces(t_85, label='85 Hz')
plot_traces(t_85_2, label='85 Hz no expansion tank')
plot_traces(t_85_3, label='85 Hz with expansion tank')
# plot_traces(t_65, label='65 Hz')
plt.legend()
plt.yscale('log')

# plt.hist(t_2021.apb_ave_ch1_wf[1]/np.mean(t_2021.apb_ave_ch1_wf[1]), 100, density=True, alpha=0.5);
# plt.hist(t_85.apb_ave_ch1_wf[1]/np.mean(t_85.apb_ave_ch1_wf[1]), 100, density=True, alpha=0.5);
# plt.xlabel('intensity')
# plt.ylabel('')

hdr = db[-1]
_t = hdr.table(stream_name='apb_stream', fill=True)['apb_stream'][1]
t_apb = hdr.table(stream_name='apb_stream', fill=True)['apb_stream'][1]
# _t = hdr.table(stream_name='pb9_enc1', fill=True)['pb9_enc1'][1]
# t_enc = hdr.table(stream_name='pb9_enc1', fill=True)['pb9_enc1'][1]

# plt.figure(); plt.plot(t_enc[:, 0] + t_enc[:, 1]*1e-9, t_enc[:, 2])
plt.plot(t_apb[:, 0], t_apb[:, 1])



img = bpm_es.get_image_array_data_reshaped()




# dark_image = picam.image.array_data.get().reshape(2048, 2048)
xray_image = picam.image.array_data.get().reshape(2048, 2048)


VMIN, VMAX = 0, 6000
plt.figure(1, clear=True)
plt.subplot(131)
plt.imshow(dark_image, vmin=VMIN, vmax=VMAX)
plt.title(f'Dark ({VMIN}-{VMAX})')

plt.subplot(132)
plt.imshow(xray_image, vmin=VMIN, vmax=VMAX)
plt.title(f'Bright ({VMIN}-{VMAX})')

plt.subplot(133)
# plt.imshow(xray_image - dark_image, vmin=VMIN, vmax=VMAX)
plt.imshow(xray_image - dark_image, vmin=0, vmax=100)
plt.title(f'Difference ({VMIN}-{VMAX})')


##
t = db[-1].table()
energy = t.hhm_energy.values
intensity = t.picam_stats1_total.values
intensity = normalize_peak(intensity)
Ecen0, fwhm0 = estimate_center_and_width_of_peak(energy, intensity)
Ecen, fwhm, intensity_cor, intensity_fit, intensity_fit_raw = fit_gaussian(energy, intensity, Ecen0, fwhm0)


##########

RE(bp.count([picam], 6))

uid_xray = '95e43edc-9507-44f1-966f-db923b7338f4'
uid_dark = 'fc298c99-fd12-4ff6-b915-294e9efadf91'


def _get_images(uids):
    if type(uids) == str:
        uids = [uids]

    imgs = []
    for uid in uids:
        t = db[uid].table(fill=True)
        for i in range(2, t.picam_image.size + 1):
            imgs.append(t.picam_image[i].squeeze())
    return np.array(imgs)

def get_image(uid):
    imgs = _get_images(uid)
    return np.mean(imgs, axis=0)

def get_spectrum(uid, nx1=410, nx2=460, ny1=1100, ny2=2000):
    image = get_image(uid)
    # spectrum = np.mean(image[510:560, 535:1000], axis=0)
    # nx1=510, nx2=560, ny1=535, ny2=1000
    spectrum = np.mean(image[nx1:nx2, ny1:ny2], axis=0)
    return spectrum

from scipy.signal import medfilt2d, medfilt

def get_spectrum_std(uid):
    images = _get_images(uid)
    spectra = np.mean(images[:, 510:560, 535:1000], axis=1)
    spectrum_std = np.std(spectra, axis=0)
    return spectrum_std

def get_diff_spectrum(uid_xray, uid_dark, **kwargs):
    spectrum_xray = get_spectrum(uid_xray, **kwargs)
    spectrum_dark = get_spectrum(uid_dark, **kwargs)
    return spectrum_xray - spectrum_dark

# xes_CaO = get_diff_spectrum('95e43edc-9507-44f1-966f-db923b7338f4', 'fc298c99-fd12-4ff6-b915-294e9efadf91')

# energy is 8000
xes_S = get_diff_spectrum('8e5dba0f-ac99-4ed5-bf1b-002638f807b0', 'fa05d9f4-8f17-4203-8074-8fba416829c0')
xes_NiS = get_diff_spectrum('ce9e1afe-e4d2-4d44-9aca-ee36137921c7', '001c7a48-a31d-4d31-ba10-9b087c9b0c20')
xes_CuSO4 = get_diff_spectrum('3091b648-593e-445c-b52f-928b26653493', 'c0919773-7097-42b8-a928-46a8cf4a8ca6')


# hopefully better statistics
xes_S = get_diff_spectrum('ed6d26af-4021-4948-bf34-37e9f83c67e4', 'dad47f8b-fb76-4750-8ed7-22b037562930')
xes_NiS = get_diff_spectrum('fdb767cc-352d-48df-bf6c-d481df424c0b', '1a3fe82d-9b93-4af0-b38a-fef11b94444a')

# energy is 6900

# xes_S = get_diff_spectrum('2b693ada-98da-43c0-84f7-94fe60f8f821', 'fa05d9f4-8f17-4203-8074-8fba416829c0')
# xes_CuSO4 = get_diff_spectrum('3bf4ae34-21b1-49d3-97eb-d18a1039c9cf', 'c0919773-7097-42b8-a928-46a8cf4a8ca6')


# plt.figure(); plt.imshow(get_image('3bf4ae34-21b1-49d3-97eb-d18a1039c9cf'))


def norm_y(y, n1=0, n2=10):
    # return (y - np.mean(y[80:100])) / (np.percentile(y, 98) - np.mean(y[:10]))
    return (y - np.mean(y[n1:n2])) / (np.max(y) - np.mean(y[n1:n2]))

plt.figure(2, clear=True)
plt.plot(norm_y(xes_S), label='S$^0$')
plt.plot(norm_y(xes_NiS), label='S$^{2-}$')
plt.plot(norm_y(xes_CuSO4), label='S$^{6+}$')
plt.legend()

# plt.plot(spectrum_dark)

data = [{'label': 'Low 4 MHz', 'spectrum': get_diff_spectrum(       'ed6d26af-4021-4948-bf34-37e9f83c67e4', 'dad47f8b-fb76-4750-8ed7-22b037562930')},
        {'label': 'Low 1 MHz', 'spectrum': get_diff_spectrum(       '3348b8eb-cc6e-497a-9b4e-3956baf9d930', '3db3d8d8-e6ff-4637-9cf2-61798c92a604')},
        {'label': 'Medium 4 MHz', 'spectrum': get_diff_spectrum(    '2bc9f5d0-9b7f-4028-adf7-ed4dc524e0d6', 'da240c40-1dc5-406d-ae3b-034923161309' )},
        {'label': 'Medium 1 MHz', 'spectrum': get_diff_spectrum(    '59b4c491-17c8-486c-b720-960c83a8369f', '76f75e5c-4fc8-41be-a8e1-7b2034298223')},
        {'label': 'High 4 MHz', 'spectrum': get_diff_spectrum(      'a0dc124c-213d-4400-8b2c-77be35067cbc','e6abc2c2-1099-4b5c-974f-87227d7c48b0')},
        {'label': 'High 1 MHz', 'spectrum': get_diff_spectrum(      '35846bb3-122d-487b-8c50-82f5e4bd7662', '23c569b4-a79c-4847-aba2-97d9c3baf421')}]

plt.figure(1, clear=True)
for d in data:
    plt.plot(norm_y(d['spectrum']), label=d['label'])
plt.legend()


uids_xray = ['ed6d26af-4021-4948-bf34-37e9f83c67e4',
'3348b8eb-cc6e-497a-9b4e-3956baf9d930',
'2bc9f5d0-9b7f-4028-adf7-ed4dc524e0d6',
'59b4c491-17c8-486c-b720-960c83a8369f',
'a0dc124c-213d-4400-8b2c-77be35067cbc',
'35846bb3-122d-487b-8c50-82f5e4bd7662',]

plt.figure(2, clear=True)
for uid, d in zip(uids_xray, data):
    _s = get_spectrum(uid)
    _s_std = get_spectrum_std(uid)

    # spectrum_std = get_spectrum_std(uid)
    plt.plot(_s_std/_s,label = d['label'])
plt.legend()



xes_CuSO4_200ms_x50 = get_diff_spectrum('26dec81f-d05e-41d0-b6cb-2399d13f8061', '5b0153b5-4800-4b82-8c52-db9e46932641')
xes_CuSO4_1s_x10 = get_diff_spectrum('bc9ab44d-f7ff-482e-add7-3ea9aae30f50', '4fec3cc0-852d-40d1-a129-a1fcb9df1422')
xes_CuSO4_10s_x1 = get_diff_spectrum('ba97a231-b4b9-4543-9fe8-3c287ded1e52', 'ac14d1c3-04b7-4068-b165-fce49795c269')

plt.figure(1, clear=True)
plt.plot(norm_y(xes_CuSO4_200ms_x50), label='200ms x50')
plt.plot(norm_y(xes_CuSO4_1s_x10)-0.5, label='1s x10')
plt.plot(norm_y(xes_CuSO4_10s_x1)-1.0, label='10s x1')
plt.legend()


plt.figure(2, clear=True)
plt.semilogx([0.2, 1, 10], [np.std(norm_y(xes_CuSO4_200ms_x50)[80:180]),
          np.std(norm_y(xes_CuSO4_1s_x10)[80:180]),
          np.std(norm_y(xes_CuSO4_10s_x1)[80:180])], 'ks-')
plt.xticks([0.2, 1, 10], ['0.2', '1', '10'])
plt.xlabel('exposure time')
plt.ylabel('readout noise')


xes_CuSO4_10s = get_diff_spectrum('02673265-b344-4895-bcee-b5aa4e204b62', 'ac14d1c3-04b7-4068-b165-fce49795c269', nx1=510, nx2=560, ny1=535, ny2=1000)
# xes_NiS_10s = get_diff_spectrum('8737790c-b258-46ee-8717-08d7117cdbd6', 'ac14d1c3-04b7-4068-b165-fce49795c269')
xes_NiS_10s = get_diff_spectrum('8d212734-0e0d-4974-97a6-a24d34b23daa', 'ac14d1c3-04b7-4068-b165-fce49795c269', nx1=510, nx2=560, ny1=535, ny2=1000)
xes_S_10s = get_diff_spectrum('a345643c-2ac3-48b2-9d68-f53153769736', 'ac14d1c3-04b7-4068-b165-fce49795c269', nx1=510, nx2=560, ny1=535, ny2=1000)


from scipy.interpolate import interp1d
energy_interp = interp1d([28.5, 265.5], [6900/3, 2308], fill_value='extrapolate')

plt.figure(1, clear=True)
plt.plot(energy_interp(np.arange(xes_CuSO4_10s.size)), norm_y(xes_CuSO4_10s, n1=60, n2=80), label='S$^{6+}$ (CuSO4)')
plt.plot(energy_interp(np.arange(xes_S_10s.size) + 2.5), norm_y(xes_S_10s, n1=60, n2=80), label='S$^{0}$ (S)')
plt.plot(energy_interp(np.arange(xes_NiS_10s.size) + 1), norm_y(xes_NiS_10s, n1=60, n2=80), label='S$^{2-}$ (NiS)')
# plt.plot(norm_y(xes_CuSO4_1s_x10)-0.5, label='1s x10')
# plt.plot(norm_y(xes_CuSO4_10s_x1)-1.0, label='10s x1')
plt.legend()

plt.xlim(2302, 2314)

plt.figure(2, clear=True)
plt.plot(np.arange(70), norm_y(xes_CuSO4_10s)[:70] / norm_y(xes_CuSO4_10s)[:70].max(), label='CuSO4')
plt.plot(np.arange(70)+2.5, norm_y(xes_S_10s)[:70] / norm_y(xes_S_10s)[:70].max(), label='S')
plt.plot(np.arange(70)+1, norm_y(xes_NiS_10s)[:70] / norm_y(xes_NiS_10s)[:70].max(), label='NiS')
# plt.plot(norm_y(xes_CuSO4_1s_x10)-0.5, label='1s x10')
# plt.plot(norm_y(xes_CuSO4_10s_x1)-1.0, label='10s x1')
plt.legend()

# visualizing S images
VMIN=20000
VMAX=30000
plt.figure(2, clear=True)
plt.subplot(131)
plt.imshow(get_image('a345643c-2ac3-48b2-9d68-f53153769736')[500:560, 685:900], vmin=VMIN, vmax=VMAX)
plt.title('X-rays ON')
plt.colorbar()

plt.subplot(132)
plt.imshow(get_image('ac14d1c3-04b7-4068-b165-fce49795c269')[500:560, 685:900], vmin=VMIN, vmax=VMAX)
plt.title('Dark')
plt.colorbar()

plt.subplot(133)
plt.imshow(get_image('a345643c-2ac3-48b2-9d68-f53153769736')[500:560, 685:900] -
           get_image('ac14d1c3-04b7-4068-b165-fce49795c269')[500:560, 685:900], vmin=0, vmax=8000)
plt.title('Difference')
plt.colorbar()
plt.tight_layout()
xray_image = picam.image.array_data.get().reshape(1024, 2048)
xray_image2 = picam.image.array_data.get().reshape(1024, 2048)
dark_image = picam.image.array_data.get().reshape(1024, 2048)

plt.figure(); plt.imshow(xray_image + xray_image2 - 2*dark_image, vmin=0, vmax=2000)


xes_Ag = get_diff_spectrum('97d5ec49-1012-4181-9d70-ff7bc5914bba', '6be5c7da-1bb1-406b-a198-c4b35ffcd939')

# xes_PdO = get_diff_spectrum('f5abe7c0-8665-4b56-88d6-fd3b4ae0f8c7', '88c05f17-1f3f-483e-9d98-ff2877997b08')
xes_PdO = get_diff_spectrum('4ce40b1b-34af-42ce-a8c1-09590c248ebe', 'a9e5b448-bcbc-4bf6-970e-e7c879dce3da')
xes_Pd = get_diff_spectrum('602a4a09-c573-4ca5-a6df-2179c247b99c', '561198a8-c738-494f-b298-84cc6fe7c8e5')
#Pd elastic scans: 6670 - '10587276-105a-413f-b021-64a58a2639f6', 6640 - '056c3a42-b10c-48bf-a63f-7c71dc86852c'

xes_PdCl2 = get_diff_spectrum('566a26db-7d27-4d9c-8e46-5cab8c788bb1', 'a35794f5-25e2-46b7-a137-462fe7ac0448')
xes_12Z23IE = get_diff_spectrum('4a480d33-efb0-4538-9dcd-c9024d0c0eee', '127ea31d-c1fd-4a95-889b-511c75990576')


plt.figure(2, clear=True)
# plt.plot(xes_Ag)

plt.plot(norm_y(xes_Pd), label='Pd')
plt.plot(norm_y(xes_PdO), label='PdO')
# plt.plot(norm_y(xes_PdCl2), label='PdCl2')
plt.plot(norm_y(xes_12Z23IE), label='Z23IE')
plt.legend()



daq_dict = [{'sample_name': 'PdCl2', 'position':{'x': -12.520,
                                                'y': -42.992,
                                                'z': -12.604}},
            {'sample_name': 'Pd(NH3)4', 'position': {'x': -12.220,
                                                     'y': -58.532,
                                                     'z': -9.504}},

            {'sample_name': 'Pd2', 'position': {'x': -12.220,
                                                'y': -71.342,
                                                'z': -9.804}},

            {'sample_name': 'Pd3', 'position': {'x': -12.220,
                                                'y': -86.592,
                                                'z': -11.304}},

            ]

while True:
    for sample in daq_dict:
        RE(move_sample_stage_plan(sample['position']))
        md = {**sample}



        md['image'] = 'dark'
        RE(bp.count([picam], 6, md=md))

        shutter.open()

        md['image'] = 'data'
        RE(move_mono_energy(7000))
        RE(bp.count([picam], 11, md=md))

        md['image'] = '6640'
        RE(move_mono_energy(6640))
        RE(bp.count([picam], 2, md=md))

        md['image'] = '6670'
        RE(move_mono_energy(6670))
        RE(bp.count([picam], 2, md=md))

        shutter.close()



# visualizing  images
VMIN=10000
VMAX=20000

# Pd
# dark_uids = '602a4a09-c573-4ca5-a6df-2179c247b99c'
# bright_uids = '561198a8-c738-494f-b298-84cc6fe7c8e5'

# PdO
# dark_uids = 'a9e5b448-bcbc-4bf6-970e-e7c879dce3da'
# bright_uids = '4ce40b1b-34af-42ce-a8c1-09590c248ebe'

# Pd_6640
# bright_uids = '056c3a42-b10c-48bf-a63f-7c71dc86852c'
# dark_uids = 'a9e5b448-bcbc-4bf6-970e-e7c879dce3da'

# PdCl2
# bright_uids = '566a26db-7d27-4d9c-8e46-5cab8c788bb1'
# dark_uids = 'a35794f5-25e2-46b7-a137-462fe7ac0448'

# bright_uids = ['566a26db-7d27-4d9c-8e46-5cab8c788bb1',
#                '7347de44-6f96-4951-9e02-9f8356f1cca9',
#                '8fa81c46-b454-48a4-9053-ce4c0aab978c',
#                '054b9406-5236-407e-bee5-3cef1736c06f',
#                'b8a09724-2bb3-49d2-a33b-33c4287d3f2e',
#                '50b91bbe-fd17-4c93-a3e9-6a655a733520',
#                '45341693-e724-4693-80b7-23f122857bcc',
#                '2648a34d-416c-495d-9f92-b86eba976a69',
#                '77a1d220-c711-4eb5-bba2-e1037d44d7bd']
#
#
# dark_uids = ['a35794f5-25e2-46b7-a137-462fe7ac0448',
#              '3fad56fd-b17f-4733-b08a-28333c33b4ae',
#              'b9aca12a-309c-4cba-882b-62080026d483',
#              '55c02ae4-af9e-4997-8722-f1dec2cbb2f7',
#              'bb1505e6-d740-4d40-b50e-91c1347018ae',
#              'ac87f9e2-1fbf-4a2f-bf49-493266d2f5e2',
#              '90c7e76a-835c-42d1-bf86-26230b8f618a',
#              'bbcad194-f9ae-445c-8afd-a16125b96b81',
#              '22b18e71-b6e4-4a27-a00f-d4bbbcf6878f',
#              '89ae0563-0833-4bfb-a5a0-952cd52b42b8']

# PdCl2 elastic
# bright_uids = ['1992dd7b-7986-42cd-a563-6b8e9f319e9a',
#  '67ae327a-81fc-4e0a-8d50-3e17736b6fec',
#  '5ba41985-4ae8-4553-95bb-c28119edb8c7',
#  '4d7422f9-f982-46df-ad1d-8c73cbc81cbf',
#  '35b78814-f7a4-4c7b-ba0e-2dc3a2001cd2',
#  '06d0826d-a0ad-4b87-b397-1701230979f8',
#  'aaea69f8-0e22-47bb-b43e-8d65d9655fd3',
#  '08fdf135-7cb8-4dfb-b88f-7e621b4820f2',
#  'ab20c160-2d36-42d9-8353-7fe9e3ec0721']
#
#
# dark_uids = ['4832393a-4c90-4216-a336-afe2baaae22f',
#  '851579b3-79db-4927-a770-d8c472ae813d',
#  'e2301d15-0466-4beb-b1ab-b531ef131288',
#  'f3fcf316-fb5d-4158-8cfd-9448afbaed99',
#  'b4dcde49-d414-4bee-9ddd-e1441238d52f',
#  'f81cdac0-af65-4a91-b3aa-2871ff8880ea',
#  'a53c7d82-4421-46cf-bafb-ccd60de17771',
#  '17110bfe-b73a-48d0-9ca0-0a998f7c717d',
#  '71d650b4-2ac8-48c1-9361-f433826102f8']

# Pd(NH3)4
# bright_uids = ['c3dfdff3-bf39-4732-a973-522a24f4e6a2',
#  'e5f0157b-0239-41a0-8197-15e83d0c7b75',
#  'd0651960-1cd9-4dd7-b8a2-81c058c1085f',
#  '39470b7c-c7c7-42d4-8d92-b8be21517323',
#  'c3f8e77d-5b0d-41fb-aac4-0e1a97529878',
#  '47f756cd-413c-4d8a-9e6c-3fed1e8b7c83',
#  '08d0def3-2239-4ad5-946d-c9a2281ac474',
#  '3a874c4b-b724-44aa-94ac-806bdff9a024',
#  '155e8363-8b42-4b1d-ba14-264a043fc61f']
#
# dark_uids=['9173c023-843d-4fdf-b36a-46b7ba65a53b',
#  'e96e70be-eb75-4711-a655-faf67fca8890',
#  '0677f1e9-05f3-4ddb-a330-de0264701438',
#  '326a8be0-82c3-4ea2-ac9d-96bba75df16f',
#  'ca7be1b8-e532-4273-8d17-05921efafc8b',
#  '78082826-de89-4692-8504-ee28c66117b2',
#  'dd31c57c-1e55-4cd4-999c-90227dc53826',
#  'e004037d-e7ec-4a9d-884a-6ba7536aff72',
#  '1e9292b6-9005-42f7-b3f2-a9d49ee05e72']

# # Pd(NH3)4 elastic
# bright_uids = ['35ab3f72-4091-4560-83e2-5b4b2f6effb1',
#  '9b639407-be56-4c43-8dba-fdaa954745c4',
#  '928a95ca-6555-41dc-b203-d4d75d2bfa3d',
#  '6bf5a9cd-2e8c-401d-92a3-d3bed6172a8b',
#  '604b68c2-3230-46ad-a91a-80662240e818',
#  '7ca5d3ad-d151-40f8-abeb-8e3318a4ac8e',
#  '69ac54c3-d2f9-42a1-95ff-df988e34b1d1',
#  '3afca479-7be2-40bf-abad-e760edd64dfe',
#  '6ca9689e-e403-4c26-bfb9-fe918a0da0e1']
#
# dark_uids=['4f9862e5-7814-43d7-a7a1-3367e04c7901',
#  'ab6fb0b4-0e24-4d28-aa1f-aef9024ed19c',
#  '20319d5e-63d8-486d-a2fb-88b1efc21ac1',
#  '514cba99-4588-457e-a829-bbf9a11454f5',
#  'a5b9e34b-0b15-4cc2-8bcb-3f0a9f81a4a5',
#  'aefe2c4d-7215-45c4-bf86-47032b15a502',
#  'd1477acb-a64f-4f58-8b01-0bde7790271e',
#  'adb891d5-cff6-4462-b8e2-5e9b933bc030',
#  '3e92c745-8b99-47ea-b3af-cc89661e8a23']

# Pd2
# bright_uids =['e14aa64c-27f5-4ff1-b1fd-5f7ba50ec7e7',
#  'db4fb6f6-1b3e-4bd7-9607-2d26b8597adc',
#  '6f2ecf29-aa8c-4a39-a646-161e4ee8ed67',
#  '4b8ef676-7ed2-4ec1-8f86-2ae335b6d8c2',
#  '8d675274-b0e0-4eb5-98b3-abf653328c6c',
#  '526aaab2-5e0f-4753-ad0e-846bdd3bdfcd',
#  '5d9f02cf-6981-4ead-828b-77556204c58e',
#  '31a40963-83a7-4999-bc0a-6ee1672d3e83',
#  'dfc54abc-d3e9-440f-bb73-80223dcf499a']
#
#
# dark_uids =['d65afa97-4908-4bd3-a898-b0b500ea2da9',
#  'e8c5cc0d-e648-4413-b003-590ab5f7bd66',
#  'a45e9b96-c746-4702-b832-8bc700cca72f',
#  '617ede9d-cc22-4862-9f94-6430de1ab957',
#  '8c5deba6-7ab7-490d-87b1-96621310da21',
#  'ac0c1bd8-a7fc-4e4e-92f6-c05d11e37b61',
#  '9fd5e67a-c493-400d-aef4-ac90a21c3e0f',
#  '75b5ebf8-37e7-412c-a61b-817a9dd56882',
#  'ca84c094-cf61-449c-9a03-09c08de242df']


# # Pd2 elastic
# bright_uids =['57ac501c-fbc9-489a-9fe4-cf985b5ce88d',
#  '9dd11765-4e27-4c1e-bb36-692a278b5b94',
#  'c54e71b7-9457-4933-9d16-9c6770ecd5b0',
#  '5bd922e2-3027-4a30-8d90-64a9075707c0',
#  '31df1441-6ae2-4e10-847e-5f3a356163ca',
#  'd1b88cb4-355c-43db-9520-7b64c2072cd2',
#  '9ea26ba2-84b3-4227-af3a-b9745f41c80d',
#  '30833947-cabb-4f8d-af2b-5e359fb19933',
#  '48a69ad7-76b6-4061-a6f3-d0668a01477a']
#
# dark_uids =['f48972b5-f829-4342-a8ba-8a1a1ac53ed5',
#  'c5131f36-eb40-4738-bd52-366ff94e8135',
#  'cec03d1a-5649-41bc-86ae-2a58f56b86fd',
#  '4ee97ba0-cc40-4170-a5ce-b2549df0b6ea',
#  'ea645434-b7d2-44c4-b6f2-372332e126ba',
#  '24a00ecf-2722-42df-b687-9ff51f1fb78c',
#  'b8204e28-040a-4139-aa63-839327fd0d00',
#  '3b675eb1-2571-45b6-a8d8-cb5d0fa27df9',
#  'd14f0abd-f016-4b15-a376-18f20b502166']


# Pd3
bright_uids =['6b128517-bfe4-40d0-94cf-def3ae979ea1',
 '34906393-827a-43f1-9863-9ee8525d09ee',
 '916917fa-6277-466d-b8ac-14f490ec5b30',
 '94128351-f342-41ef-a93d-081f6d5c670f',
 'd038ee63-e076-4d07-a870-6876d511d124',
 'dac0c16b-32e9-487c-964a-9d089227e6ca',
 '578bc61c-7c1d-4966-8b70-803360cee9fc',
 'fdc035a2-a090-47f1-8afd-f022ca8d1c34',
 '34a7b9be-0717-45ba-84ea-f02baa3d7294']

dark_uids =['187f522c-f9ff-42c1-bd8a-21f2d03f1af2',
 'd4d1e822-6c7b-4b6f-874b-d10bcb8888f7',
 '235eefc2-2011-48e3-90fa-260e49ca7445',
 '524e87d2-4b83-41c8-b8e3-02cc65768275',
 '578ee294-79df-4772-b981-d3df2b6be59d',
 'ef7462ed-4ac3-470f-b7d4-63188e846bc7',
 '3352a16a-534e-4821-89c1-74a5441bffcb',
 '3e73d638-f16b-430e-8875-84e8dd201795',
 '7b2d99b6-d35c-4ab5-a3d9-063835407664']



# # # Pd3 elastic
bright_uids =['127ea31d-c1fd-4a95-889b-511c75990576',
 '4a480d33-efb0-4538-9dcd-c9024d0c0eee',
 'd28dd5f7-72d6-4f2b-b28d-a412ee1b8a56',
 '07479908-d619-4bbf-a1ff-53d73e938f5b',
 'a5d210fe-fa1d-4be2-ade4-7dfdbc21c288',
 '5ae0fca2-8eda-42ef-9f13-67c92884d50b',
 '4eb1c088-5109-4abb-acd7-2a706ea21e5d',
 '94a322fc-db1a-40e6-a35d-a62b372e1348',
 '7f0637d9-449a-4406-a331-d442fa5586b9',
 'e068e24f-af07-48ac-acec-8c5988ba003f',
 'd0d902cd-0939-487e-8fae-856d72526812',
 '85f83507-a243-4507-918a-c54cbaa34e34',
 'cb6ddfc5-2ada-4310-ac3b-5b2bb559807a',
 'c6a6d288-7a62-41a1-a1b3-dd16328210c2']


dark_uids =['578d23ff-f35d-45af-8fe9-1f7f18bdefb9',
 '82604fd3-bd12-4366-aeb4-dae245bb6b55',
 '2e4e71c1-7ee9-47f0-858e-e95e8a513f4d',
 'f11a57de-b661-46a4-8c6b-3477704c55f4',
 '93c16531-0a2b-458c-9dc5-38d6445b0cc3',
 '9b37d3fb-bdad-4eba-acbe-d87f0606dada',
 '435fa16d-5378-441a-8041-7a0f0419d772',
 'd91d47f4-f222-40be-ad92-39fd218d48b9']


image_bright = get_image(bright_uids)
image_dark = get_image(dark_uids)
nx1, nx2 = 1, 1024
ny1, ny2 = 1, 2048

# nx1, nx2 = 380, 480
# ny1, ny2 = 600, 2048


plt.figure(2, clear=True)
plt.subplot(311)

plt.imshow(image_bright[nx1:nx2, ny1:ny2], vmin=VMIN, vmax=VMAX)
plt.title('X-rays ON')
# plt.colorbar()

plt.subplot(312)
plt.imshow(image_dark[nx1:nx2, ny1:ny2], vmin=VMIN, vmax=VMAX)
# plt.imshow(medfilt2d(get_image(dark_uids)[nx1:nx2, ny1:ny2]), vmin=VMIN, vmax=VMAX)
plt.title('Dark')
# plt.colorbar()

plt.subplot(313)
plt.imshow(image_bright[nx1:nx2, ny1:ny2] -
           image_dark[nx1:nx2, ny1:ny2], vmin=-2000, vmax=2000)
plt.title('Difference')
# plt.colorbar()
# plt.tight_layout()



xes_PdO = get_diff_spectrum('4ce40b1b-34af-42ce-a8c1-09590c248ebe', 'a9e5b448-bcbc-4bf6-970e-e7c879dce3da', nx1=380, nx2=480, ny1=500, ny2=2048)
xes_Pd = get_diff_spectrum('602a4a09-c573-4ca5-a6df-2179c247b99c', '561198a8-c738-494f-b298-84cc6fe7c8e5', nx1=380, nx2=480, ny1=500, ny2=2048)
# xes_PdCl2 = get_diff_spectrum('566a26db-7d27-4d9c-8e46-5cab8c788bb1', 'a35794f5-25e2-46b7-a137-462fe7ac0448', nx1=380, nx2=480, ny1=500, ny2=2048)
xes_PdCl2 = get_diff_spectrum(['566a26db-7d27-4d9c-8e46-5cab8c788bb1',
                               '7347de44-6f96-4951-9e02-9f8356f1cca9',
                               '8fa81c46-b454-48a4-9053-ce4c0aab978c',
                               '054b9406-5236-407e-bee5-3cef1736c06f',
                               'b8a09724-2bb3-49d2-a33b-33c4287d3f2e',
                               '50b91bbe-fd17-4c93-a3e9-6a655a733520',
                               '45341693-e724-4693-80b7-23f122857bcc',
                               '2648a34d-416c-495d-9f92-b86eba976a69',
                               '77a1d220-c711-4eb5-bba2-e1037d44d7bd'],
                              ['a35794f5-25e2-46b7-a137-462fe7ac0448',
                               '3fad56fd-b17f-4733-b08a-28333c33b4ae',
                               'b9aca12a-309c-4cba-882b-62080026d483',
                               '55c02ae4-af9e-4997-8722-f1dec2cbb2f7',
                               'bb1505e6-d740-4d40-b50e-91c1347018ae',
                               'ac87f9e2-1fbf-4a2f-bf49-493266d2f5e2',
                               '90c7e76a-835c-42d1-bf86-26230b8f618a',
                               'bbcad194-f9ae-445c-8afd-a16125b96b81',
                               '22b18e71-b6e4-4a27-a00f-d4bbbcf6878f',
                               '89ae0563-0833-4bfb-a5a0-952cd52b42b8'],
                              nx1=380, nx2=480, ny1=500, ny2=2048)
xes_PdNH34 = get_diff_spectrum(['c3dfdff3-bf39-4732-a973-522a24f4e6a2',
                                'e5f0157b-0239-41a0-8197-15e83d0c7b75',
                                'd0651960-1cd9-4dd7-b8a2-81c058c1085f',
                                '39470b7c-c7c7-42d4-8d92-b8be21517323',
                                'c3f8e77d-5b0d-41fb-aac4-0e1a97529878',
                                '47f756cd-413c-4d8a-9e6c-3fed1e8b7c83',
                                '08d0def3-2239-4ad5-946d-c9a2281ac474',
                                '3a874c4b-b724-44aa-94ac-806bdff9a024',
                                '155e8363-8b42-4b1d-ba14-264a043fc61f'],
                               ['9173c023-843d-4fdf-b36a-46b7ba65a53b',
                                'e96e70be-eb75-4711-a655-faf67fca8890',
                                '0677f1e9-05f3-4ddb-a330-de0264701438',
                                '326a8be0-82c3-4ea2-ac9d-96bba75df16f',
                                'ca7be1b8-e532-4273-8d17-05921efafc8b',
                                '78082826-de89-4692-8504-ee28c66117b2',
                                'dd31c57c-1e55-4cd4-999c-90227dc53826',
                                'e004037d-e7ec-4a9d-884a-6ba7536aff72',
                                '1e9292b6-9005-42f7-b3f2-a9d49ee05e72'],
                              nx1=380, nx2=480, ny1=500, ny2=2048)

xes_Pd2 = get_diff_spectrum(['e14aa64c-27f5-4ff1-b1fd-5f7ba50ec7e7',
 'db4fb6f6-1b3e-4bd7-9607-2d26b8597adc',
 '6f2ecf29-aa8c-4a39-a646-161e4ee8ed67',
 '4b8ef676-7ed2-4ec1-8f86-2ae335b6d8c2',
 '8d675274-b0e0-4eb5-98b3-abf653328c6c',
 '526aaab2-5e0f-4753-ad0e-846bdd3bdfcd',
 '5d9f02cf-6981-4ead-828b-77556204c58e',
 '31a40963-83a7-4999-bc0a-6ee1672d3e83',
 'dfc54abc-d3e9-440f-bb73-80223dcf499a'],
                            ['d65afa97-4908-4bd3-a898-b0b500ea2da9',
                             'e8c5cc0d-e648-4413-b003-590ab5f7bd66',
                             'a45e9b96-c746-4702-b832-8bc700cca72f',
                             '617ede9d-cc22-4862-9f94-6430de1ab957',
                             '8c5deba6-7ab7-490d-87b1-96621310da21',
                             'ac0c1bd8-a7fc-4e4e-92f6-c05d11e37b61',
                             '9fd5e67a-c493-400d-aef4-ac90a21c3e0f',
                             '75b5ebf8-37e7-412c-a61b-817a9dd56882',
                             'ca84c094-cf61-449c-9a03-09c08de242df'],
                              nx1=380, nx2=480, ny1=500, ny2=2048)

xes_Pd3 = get_diff_spectrum(['6b128517-bfe4-40d0-94cf-def3ae979ea1',
 '34906393-827a-43f1-9863-9ee8525d09ee',
 '916917fa-6277-466d-b8ac-14f490ec5b30',
 '94128351-f342-41ef-a93d-081f6d5c670f',
 'd038ee63-e076-4d07-a870-6876d511d124',
 'dac0c16b-32e9-487c-964a-9d089227e6ca',
 '578bc61c-7c1d-4966-8b70-803360cee9fc',
 'fdc035a2-a090-47f1-8afd-f022ca8d1c34',
 '34a7b9be-0717-45ba-84ea-f02baa3d7294'],
                            ['187f522c-f9ff-42c1-bd8a-21f2d03f1af2',
                             'd4d1e822-6c7b-4b6f-874b-d10bcb8888f7',
                             '235eefc2-2011-48e3-90fa-260e49ca7445',
                             '524e87d2-4b83-41c8-b8e3-02cc65768275',
                             '578ee294-79df-4772-b981-d3df2b6be59d',
                             'ef7462ed-4ac3-470f-b7d4-63188e846bc7',
                             '3352a16a-534e-4821-89c1-74a5441bffcb',
                             '3e73d638-f16b-430e-8875-84e8dd201795',
                             '7b2d99b6-d35c-4ab5-a3d9-063835407664'],
                              nx1=380, nx2=480, ny1=500, ny2=2048)




#Pd elastic scans: 6670 - '10587276-105a-413f-b021-64a58a2639f6', 6640 - '056c3a42-b10c-48bf-a63f-7c71dc86852c'
xes_Pd_elastic = get_diff_spectrum('056c3a42-b10c-48bf-a63f-7c71dc86852c', '10587276-105a-413f-b021-64a58a2639f6', nx1=380, nx2=480, ny1=500, ny2=2048)
# xes_Pd_6670 = get_diff_spectrum(, '561198a8-c738-494f-b298-84cc6fe7c8e5', nx1=380, nx2=480, ny1=500, ny2=2048)
xes_PdCl2_elastic = get_diff_spectrum(['1992dd7b-7986-42cd-a563-6b8e9f319e9a',
                                       '67ae327a-81fc-4e0a-8d50-3e17736b6fec',
                                       '5ba41985-4ae8-4553-95bb-c28119edb8c7',
                                       '4d7422f9-f982-46df-ad1d-8c73cbc81cbf',
                                       '35b78814-f7a4-4c7b-ba0e-2dc3a2001cd2',
                                       '06d0826d-a0ad-4b87-b397-1701230979f8',
                                       'aaea69f8-0e22-47bb-b43e-8d65d9655fd3',
                                       '08fdf135-7cb8-4dfb-b88f-7e621b4820f2',
                                       'ab20c160-2d36-42d9-8353-7fe9e3ec0721'],
                                      ['4832393a-4c90-4216-a336-afe2baaae22f',
                                       '851579b3-79db-4927-a770-d8c472ae813d',
                                       'e2301d15-0466-4beb-b1ab-b531ef131288',
                                       'f3fcf316-fb5d-4158-8cfd-9448afbaed99',
                                       'b4dcde49-d414-4bee-9ddd-e1441238d52f',
                                       'f81cdac0-af65-4a91-b3aa-2871ff8880ea',
                                       'a53c7d82-4421-46cf-bafb-ccd60de17771',
                                       '17110bfe-b73a-48d0-9ca0-0a998f7c717d',
                                       '71d650b4-2ac8-48c1-9361-f433826102f8'], nx1=380, nx2=480, ny1=500, ny2=2048)
xes_PdNH34_elastic = get_diff_spectrum(['35ab3f72-4091-4560-83e2-5b4b2f6effb1',
                                        '9b639407-be56-4c43-8dba-fdaa954745c4',
                                        '928a95ca-6555-41dc-b203-d4d75d2bfa3d',
                                        '6bf5a9cd-2e8c-401d-92a3-d3bed6172a8b',
                                        '604b68c2-3230-46ad-a91a-80662240e818',
                                        '7ca5d3ad-d151-40f8-abeb-8e3318a4ac8e',
                                        '69ac54c3-d2f9-42a1-95ff-df988e34b1d1',
                                        '3afca479-7be2-40bf-abad-e760edd64dfe',
                                        '6ca9689e-e403-4c26-bfb9-fe918a0da0e1'],
                                       ['4f9862e5-7814-43d7-a7a1-3367e04c7901',
                                        'ab6fb0b4-0e24-4d28-aa1f-aef9024ed19c',
                                        '20319d5e-63d8-486d-a2fb-88b1efc21ac1',
                                        '514cba99-4588-457e-a829-bbf9a11454f5',
                                        'a5b9e34b-0b15-4cc2-8bcb-3f0a9f81a4a5',
                                        'aefe2c4d-7215-45c4-bf86-47032b15a502',
                                        'd1477acb-a64f-4f58-8b01-0bde7790271e',
                                        'adb891d5-cff6-4462-b8e2-5e9b933bc030',
                                        '3e92c745-8b99-47ea-b3af-cc89661e8a23'], nx1=380, nx2=480, ny1=500, ny2=2048)

xes_Pd2_elastic = get_diff_spectrum(['57ac501c-fbc9-489a-9fe4-cf985b5ce88d',
 '9dd11765-4e27-4c1e-bb36-692a278b5b94',
 'c54e71b7-9457-4933-9d16-9c6770ecd5b0',
 '5bd922e2-3027-4a30-8d90-64a9075707c0',
 '31df1441-6ae2-4e10-847e-5f3a356163ca',
 'd1b88cb4-355c-43db-9520-7b64c2072cd2',
 '9ea26ba2-84b3-4227-af3a-b9745f41c80d',
 '30833947-cabb-4f8d-af2b-5e359fb19933',
 '48a69ad7-76b6-4061-a6f3-d0668a01477a'],
                                    ['f48972b5-f829-4342-a8ba-8a1a1ac53ed5',
                                     'c5131f36-eb40-4738-bd52-366ff94e8135',
                                     'cec03d1a-5649-41bc-86ae-2a58f56b86fd',
                                     '4ee97ba0-cc40-4170-a5ce-b2549df0b6ea',
                                     'ea645434-b7d2-44c4-b6f2-372332e126ba',
                                     '24a00ecf-2722-42df-b687-9ff51f1fb78c',
                                     'b8204e28-040a-4139-aa63-839327fd0d00',
                                     '3b675eb1-2571-45b6-a8d8-cb5d0fa27df9',
                                     'd14f0abd-f016-4b15-a376-18f20b502166'], nx1=380, nx2=480, ny1=500, ny2=2048)

xes_Pd3_elastic = get_diff_spectrum(['127ea31d-c1fd-4a95-889b-511c75990576',
 '4a480d33-efb0-4538-9dcd-c9024d0c0eee',
 'd28dd5f7-72d6-4f2b-b28d-a412ee1b8a56',
 '07479908-d619-4bbf-a1ff-53d73e938f5b',
 'a5d210fe-fa1d-4be2-ade4-7dfdbc21c288',
 '5ae0fca2-8eda-42ef-9f13-67c92884d50b',
 '4eb1c088-5109-4abb-acd7-2a706ea21e5d',
 '94a322fc-db1a-40e6-a35d-a62b372e1348',
 '7f0637d9-449a-4406-a331-d442fa5586b9',
 'e068e24f-af07-48ac-acec-8c5988ba003f',
 'd0d902cd-0939-487e-8fae-856d72526812',
 '85f83507-a243-4507-918a-c54cbaa34e34',
 'cb6ddfc5-2ada-4310-ac3b-5b2bb559807a',
 'c6a6d288-7a62-41a1-a1b3-dd16328210c2'],
                                    ['578d23ff-f35d-45af-8fe9-1f7f18bdefb9',
                                     '82604fd3-bd12-4366-aeb4-dae245bb6b55',
                                     '2e4e71c1-7ee9-47f0-858e-e95e8a513f4d',
                                     'f11a57de-b661-46a4-8c6b-3477704c55f4',
                                     '93c16531-0a2b-458c-9dc5-38d6445b0cc3',
                                     '9b37d3fb-bdad-4eba-acbe-d87f0606dada',
                                     '435fa16d-5378-441a-8041-7a0f0419d772',
                                     'd91d47f4-f222-40be-ad92-39fd218d48b9'], nx1=380, nx2=480, ny1=500, ny2=2048)


# xes_PdCl2 = get_diff_spectrum('566a26db-7d27-4d9c-8e46-5cab8c788bb1', 'a35794f5-25e2-46b7-a137-462fe7ac0448')
# xes_12Z23IE = get_diff_spectrum('4a480d33-efb0-4538-9dcd-c9024d0c0eee', '127ea31d-c1fd-4a95-889b-511c75990576')


def norm_bkg_y(_y, n1=10, n2=20, do_medfilt=True):
    if do_medfilt:
        y = medfilt(_y, 3)
    else:
        y = _y.copy()
    # return (y - np.mean(y[80:100])) / (np.percentile(y, 98) - np.mean(y[:10]))
    x = np.arange(y.size)
    x1, x2 = np.mean(x[:n1]), np.mean(x[-n2:])
    y1, y2 = np.mean(y[:n1]), np.mean(y[-n2:])
    p = np.polyfit([x1, x2], [y1, y2], 1)
    y_bkg = np.polyval(p, x)
    return (y - y_bkg) / (np.max(y) - y_bkg)

energy_interp = interp1d([703, 1338], [6640/2, 6670/2], fill_value='extrapolate')


# plt.plot(energy_interp(np.arange(xes_CuSO4_10s.size)), norm_y(xes_CuSO4_10s, n1=60, n2=80), label='S$^{6+}$ (CuSO4)')


plt.figure(2, clear=True)
# plt.plot(xes_Ag)

plt.plot(energy_interp(np.arange(xes_Pd.size)), norm_bkg_y(xes_Pd), label='Pd')
plt.plot(energy_interp(np.arange(xes_PdO.size)), norm_bkg_y(xes_PdO), label='PdO')
# plt.plot(energy_interp(np.arange(xes_PdCl2.size)+11), norm_bkg_y(xes_PdCl2), label='PdCl2')
plt.plot(energy_interp(np.arange(xes_PdNH34.size)+6), norm_bkg_y(xes_PdNH34), label='Pd(NH3)4')
# plt.plot(energy_interp(np.arange(xes_Pd2.size)+5), norm_bkg_y(xes_Pd2), label='Pd2')
# plt.plot(energy_interp(np.arange(xes_Pd3.size)+1), norm_bkg_y(xes_Pd3), label='Pd3')

# plt.plot(energy_interp(np.arange(xes_Pd_elastic.size)), norm_bkg_y(np.abs(xes_Pd_elastic)), label='Pd elastic')
# plt.plot(energy_interp(np.arange(xes_PdCl2_elastic.size)+11), norm_bkg_y(np.abs(xes_PdCl2_elastic)), label='PdCL2 elastic')
# plt.plot(energy_interp(np.arange(xes_PdNH34_elastic.size)+6), norm_bkg_y(np.abs(xes_PdNH34_elastic)), label='Pd(NH3)4 elastic')
# plt.plot(energy_interp(np.arange(xes_Pd2_elastic.size)+5), norm_bkg_y(np.abs(xes_Pd2_elastic)), label='Pd2 elastic')
# plt.plot(energy_interp(np.arange(xes_Pd3_elastic.size)+1), norm_bkg_y(np.abs(xes_Pd3_elastic)), label='Pd3 elastic')
# plt.plot(xes_Pd_6670, label='6670')
plt.xlim(3320, 3335)

plt.legend()
plt.xlabel('Emission energy, eV')
plt.ylabel('Intensity, a.u.')
plt.title('incident energy 7000 eV')





##################

from ophyd import EpicsMotor as _EpicsMotor
from ophyd import (Device, Kind, Component as Cpt,
                   EpicsSignal, EpicsSignalRO, Kind,
                   PseudoPositioner, PseudoSingle, SoftPositioner, Signal, SignalRO)
from ophyd.status import SubscriptionStatus, DeviceStatus

class EpicsMotorWithTweaking(_EpicsMotor):
    # set does not work in this class; use put!
    twv = Cpt(EpicsSignal, '.TWV', kind='omitted')
    twr = Cpt(EpicsSignal, '.TWR', kind='omitted')
    twf = Cpt(EpicsSignal, '.TWF', kind='omitted')

EpicsMotor = EpicsMotorWithTweaking

##
import threading
motor_cr_main_roll = EpicsMotor('XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr', name='motor_cr_main_roll')
motor_cr_aux2_roll = EpicsMotor('XF:08IDB-OP{HRS:1-Stk:2:Roll}Mtr', name='motor_cr_aux2_roll')
motor_cr_aux3_roll = EpicsMotor('XF:08IDB-OP{HRS:1-Stk:3:Roll}Mtr', name='motor_cr_aux3_roll')

apb_timestamp_s = EpicsSignal('XF:08IDB-CT{PBA:1}:EVR:TS:Sec-I', name='apb_timestamp_s')
apb_timestamp_ns = EpicsSignal('XF:08IDB-CT{PBA:1}:EVR:TS:NSec-I', name='apb_timestamp_ns')

class FlyableEpicsMotor(Device):

    def __init__(self, motor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.motor = motor
        self.traj_dict = None
        self.flying_status = None

    def set_trajectory(self, traj_dict):
        # traj_dict = {'positions': [point1, point2, point3, point4],
        #              'velocities': [v1_2, v2_3 ,v3_4]}
        self.traj_dict = traj_dict

    def prepare(self):
        return self.motor.move(self.traj_dict['positions'][0], wait=False)

    def kickoff(self):
        self.flying_status = DeviceStatus(self)
        thread = threading.Thread(target=self.execute_motion, daemon=True)
        thread.start()
        return self.flying_status

    def execute_motion(self):
        self.data = []
        def write_data_callback(value, timestamp, **kwargs):
            self.data.append([timestamp, value])
        cid = self.motor.user_readback.subscribe(write_data_callback)

        pre_fly_velocity = self.motor.velocity.get()
        for prev_position, next_position, duration in zip(self.traj_dict['positions'][:-1],
                                                          self.traj_dict['positions'][1:],
                                                          self.traj_dict['durations']):
            velocity = abs(next_position - prev_position) / duration
            self.motor.velocity.set(velocity).wait()
            self.motor.move(next_position).wait()
        self.flying_status.set_finished()

        self.motor.velocity.set(pre_fly_velocity).wait()
        self.motor.user_readback.unsubscribe(cid)


    def complete(self):
        self.flying_status = None
        self.traj_dict = None

    @property
    def current_trajectory_duration(self):
        return sum(self.traj_dict['durations']) + 5

flying_motor_cr_main_roll = FlyableEpicsMotor(johann_emission.motor_cr_main_roll, name='flying_motor_cr_main_roll')
flying_motor_cr_aux2_roll = FlyableEpicsMotor(johann_emission.motor_cr_aux2_roll, name='flying_motor_cr_aux2_roll')
flying_motor_cr_aux3_roll = FlyableEpicsMotor(johann_emission.motor_cr_aux3_roll, name='flying_motor_cr_aux3_roll')


pos_dict = johann_emission._forward({'energy' : 7085})

traj_dict_main = {'positions': [pos_dict['motor_cr_main_roll'] - 1000,
                                pos_dict['motor_cr_main_roll'] + 1000], 'durations': [30]}
flying_motor_cr_main_roll.set_trajectory(traj_dict_main)
prepare_st1 = flying_motor_cr_main_roll.prepare()

traj_dict_aux2 = {'positions': [pos_dict['motor_cr_aux2_roll'] - 1000 - 100,
                                pos_dict['motor_cr_aux2_roll'] + 1000 - 100], 'durations': [30]}
flying_motor_cr_aux2_roll.set_trajectory(traj_dict_aux2)
prepare_st2 = flying_motor_cr_aux2_roll.prepare()

traj_dict_aux3 = {'positions': [pos_dict['motor_cr_aux3_roll'] - 1000 + 100,
                                pos_dict['motor_cr_aux3_roll'] + 1000 + 100], 'durations': [30]}
flying_motor_cr_aux3_roll.set_trajectory(traj_dict_aux3)
prepare_st3 = flying_motor_cr_aux3_roll.prepare()

combine_status_list([prepare_st1, prepare_st2, prepare_st3]).wait()

st1 = flying_motor_cr_main_roll.kickoff()
st2 = flying_motor_cr_aux2_roll.kickoff()
st3 = flying_motor_cr_aux3_roll.kickoff()

data1 = np.array(flying_motor_cr_main_roll.data)
data2 = np.array(flying_motor_cr_aux2_roll.data)
data3 = np.array(flying_motor_cr_aux3_roll.data)
plt.figure(1, clear=True)
plt.plot(data1[:, 0], data1[:, 1], '.-')
plt.plot(data2[:, 0], data2[:, 1], '.-')
plt.plot(data3[:, 0], data3[:, 1], '.-')
# plt.plot(data[:, 2] - data[0, 2], data[:, 1], 'r.-')
# plt.plot(data[:, 0] - data[:, 2], 'k.-')


###
class FlyerForFlyableEpicsMotor(Device):
    def __init__(self, default_dets, motors, shutter, *args, **kwargs):
        super().__init__(parent=None, *args, **kwargs)

        # apb_stream_idx = dets.index(apb_stream)
        # self.apb_stream = dets[apb_stream_idx]

        self.default_dets = default_dets
        self.aux_dets = []
        self.dets = []
        self.motors = motors
        self.shutter = shutter
        self.complete_status = None

    def set_aux_dets(self, aux_dets):
        self.aux_dets = aux_dets

    def flush_dets(self):
        self.aux_dets = []
        self.dets = []

    def stage(self):
        print_to_gui(f'Preparing mono starting...', add_timestamp=True, tag='Flyer')
        motor_prep_status = combine_status_list([motor.prepare() for motor in self.motors])
        motor_prep_status.wait()
        print_to_gui(f'Preparing mono complete', add_timestamp=True, tag='Flyer')
        self.dets = self.default_dets + self.aux_dets
        print_to_gui(f'Fly scan staging starting...', add_timestamp=True, tag='Flyer')
        staged_list = super().stage()
        scan_duration = max([motor.current_trajectory_duration for motor in self.motors])
            # trajectory_manager.current_trajectory_duration
        for det in self.dets:
            if hasattr(det, 'prepare_to_fly'):
                det.prepare_to_fly(scan_duration)
            print_to_gui(f'{det.name} staging starting', add_timestamp=True, tag='Flyer')
            staged_list += det.stage()
        print_to_gui(f'Fly scan staging complete', add_timestamp=True, tag='Flyer')
        return staged_list

    def unstage(self):
        print_to_gui(f'Fly scan unstaging starting...', add_timestamp=True, tag='Flyer')
        unstaged_list = super().unstage()
        for det in self.dets:
            unstaged_list += det.unstage()
        self.flush_dets()
        print_to_gui(f'Fly scan unstaging complete', add_timestamp=True, tag='Flyer')
        return unstaged_list

    def kickoff(self):
        self.kickoff_status = DeviceStatus(self)
        self.complete_status = DeviceStatus(self)
        thread = threading.Thread(target=self.action_sequence, daemon=True)
        thread.start()
        return self.kickoff_status

    def action_sequence(self):

        print_to_gui(f'Detector kickoff starting...', add_timestamp=True, tag='Flyer')
        self.shutter.open(time_opening=True)
        det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets])
        det_kickoff_status.wait()

        print_to_gui(f'Detector kickoff complete', add_timestamp=True, tag='Flyer')

        print_to_gui(f'Motor trajectory motion starting...', add_timestamp=True, tag='Flyer')

        self.motor_flying_status = combine_status_list([motor.kickoff() for motor in self.motors])
        self.kickoff_status.set_finished()

        self.motor_flying_status.wait()

        print_to_gui(f'Motor trajectory motion complete', add_timestamp=True, tag='Flyer')

        print_to_gui(f'Detector complete starting...', add_timestamp=True, tag='Flyer')
        det_complete_status = combine_status_list([det.complete() for det in self.dets])
        det_complete_status.wait()
        for motor in self.motors:
            motor.complete()
        self.shutter.close()

        print_to_gui(f'Detector complete complete', add_timestamp=True, tag='Flyer')
        self.complete_status.set_finished()

    def complete(self):
        # print(f'{ttime.ctime()} >>> COMPLETE: begin')
        if self.complete_status is None:
            raise RuntimeError("No collection in progress")
        return self.complete_status

    def describe_collect(self):
        return_dict = {}
        for det in self.dets:
            return_dict = {**return_dict, **det.describe_collect()}
        return return_dict

    def collect(self):
        # print_to_gui(f'{ttime.ctime()} Collect starting')
        print_to_gui(f'Collect starting...', add_timestamp=True, tag='Flyer')
        for det in self.dets:
            yield from det.collect()
        # print_to_gui(f'{ttime.ctime()} Collect finished')
        print_to_gui(f'Collect complete', add_timestamp=True, tag='Flyer')

    def collect_asset_docs(self):
        print_to_gui(f'Collect asset docs starting...', add_timestamp=True, tag='Flyer')
        for det in self.dets:
            yield from det.collect_asset_docs()
        print_to_gui(f'Collect asset docs complete', add_timestamp=True, tag='Flyer')


# flyer_apb = FlyerHHM([apb_stream, pb9.enc1, xs_stream], hhm, shutter, name='flyer_apb')
# flyer_apb = FlyerHHM([apb_stream, pb9.enc1], hhm, shutter, name='flyer_apb')
flyer_johann_rolls = FlyerForFlyableEpicsMotor([apb_stream],
                                               [flying_motor_cr_main_roll,
                                                flying_motor_cr_aux2_roll,
                                                flying_motor_cr_aux3_roll],
                                               shutter, name='flyer_apb')

def fly_johann_rolls_plan(name=None, comment=None, trajectory_dictionary=None,
                          element='', e0=0, line='', metadata={}):

    flying_motor_cr_main_roll.set_trajectory(trajectory_dictionary['main'])
    flying_motor_cr_aux2_roll.set_trajectory(trajectory_dictionary['aux2'])
    flying_motor_cr_aux3_roll.set_trajectory(trajectory_dictionary['aux3'])

    detectors = ['Pilatus 100k']
    aux_detectors = get_detector_device_list(detectors, flying=True)
    flyer_johann_rolls.set_aux_dets(aux_detectors)
    detectors_dict = {k :{'device' : v} for k, v in zip(detectors, aux_detectors)}
    md_general = get_scan_md(name, comment, detectors_dict, '.dat')

    md_scan = {'experiment': 'fly_scan',
               'spectrometer': 'johann',
               'spectrometer_config': rowland_circle.config,
               'spectrometer_trajectory_dictionary': trajectory_dictionary,
               'element': element,
               'line': line,
               'e0': e0}
    md = {**md_scan, **md_general, **metadata}

    @bpp.stage_decorator([flyer_johann_rolls])
    def _fly(md):
        plan = bp.fly([flyer_johann_rolls], md=md)
        yield from monitor_during_wrapper(plan, [flying_motor_cr_main_roll.motor.user_readback,
                                                 flying_motor_cr_aux2_roll.motor.user_readback,
                                                 flying_motor_cr_aux3_roll.motor.user_readback])
    yield from _fly(md)


def pseudo_fly_scan_johann_xes_plan(name=None, comment=None, detectors=[],
                              mono_energy=None, mono_angle_offset=None,
                              central_emission_energy=None,
                              trajectory_dictionary=None,
                              element='', line='', e0=None,
                              metadata={}):

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    metadata = {**metadata, **{'spectrometer_central_energy': central_emission_energy}}
    yield from bps.mv(hhm.energy, mono_energy)
    pos_dict = johann_emission._forward({'energy': central_emission_energy})
    johann_emission.motor_cr_main_roll.move(pos_dict['motor_cr_main_roll'])
    johann_emission.motor_cr_aux2_roll.move(pos_dict['motor_cr_aux2_roll'])
    johann_emission.motor_cr_aux3_roll.move(pos_dict['motor_cr_aux3_roll'])
    yield from prepare_johann_scan_plan(detectors, central_emission_energy)
    yield from fly_johann_rolls_plan(name=name, comment=comment, trajectory_dictionary=trajectory_dictionary,
                                     element=element, line=line, e0=e0, metadata=metadata)
    # yield from general_energy_step_scan(all_detectors, johann_emission, emission_energy_list, emission_time_list, md=md)


trajectory_dictionary = {'main': traj_dict_main,
                         'aux2': traj_dict_aux2,
                         'aux3': traj_dict_aux3}

RE(pseudo_fly_scan_johann_xes_plan(name='test', comment='', detectors=['Pilatus 100k'],
                                mono_energy=7200, mono_angle_offset=None,
                                central_emission_energy=7085,
                                trajectory_dictionary=trajectory_dictionary,
                                element='Fe', line='Kb', e0=7059,
                                metadata={}))



for j in range(25):
    RE(bps.mvr(johann_det_arm.motor_det_th1, 3))
    RE(bps.sleep(2))
    RE(bps.mvr(johann_det_arm.motor_det_th1, -3))




#########

# johann_x = [#-8.55,
#             -6.058, -3.55, -1.057, 1.55, 3.944, 6.445]
# uids = [
#    # '4dace7fc-994f-4da4-a2c2-7df3e7f1c233',
#     'cd5ffdf6-6723-45fe-8fd3-39dfdb703f3c',
#     '0f568080-b2a0-4e33-a766-c4ac4638178d',
#     '979a380a-167c-432f-acc6-36bceeea1c6d',
#     'cd067a65-e402-44f1-9bcd-8f10c01c51d2',
#     '96dd4ad7-f178-42b2-90f7-3b37978944b9',
# '32d3bd90-ab2d-40f4-bcb3-62173486c90a'
# ]

johann_x = [-7.5]

uids = ['1c1d309c-9dc2-4d06-8f71-8c74d1575f17', ]


fwhm = []
plt.figure(1, clear=True)
for uid in uids:
    _fwhm = estimate_peak_fwhm_from_roll_scan(db, uid, plotting=True, fignum=1, clear=False)
    fwhm.append(_fwhm)

plt.figure(2, clear=True)
plt.plot(johann_x, fwhm, 'k.-')


##

# uids = ('ed7aeea7-e50d-4f1d-828f-f335383210cc',
#  '5ee2f655-c691-400b-8cc0-8f5e5a57aa71',
#  '40a9f077-7f82-4d40-946f-98a2b1030355',
#  '4f5dac85-bc61-4757-b868-900b221d2dab',
#  '75612f5d-0d25-45c6-ba9f-41c558e8a979',
#  '464e994e-ca73-4ac6-a7a8-52d07872a020',
#  '398398c7-5d44-4e6b-b4d0-3c93cf95bb2d',
#  'd3776097-5a61-457e-9318-a447d17400ff',
#  '0d60c03a-b75b-418f-bb94-02bdfe3f39cb',
# '0e6f37da-8d43-4bf5-935d-8fc348a35bc6',
# 'd8278aa1-21d4-424a-b00b-2223e6c3ac42',
# 'ecacc8a6-ecb7-483d-8cfa-e097839dceae'
#         )
# tweak_motor = johann_spectrometer_x.name
# scan_motor = 'johann_main_crystal_motor_cr_main_roll'
#
# uids = (#'135e21d6-f6bc-439c-8840-64e3c769fab7',
#  'c8b29993-8a05-475d-ab0e-78965ecd4617',
#  'b2257dcc-7433-4445-ab1b-fb494370edee',
#  '775c8aaa-dcac-49eb-bf2a-dc3946423ba4',
#  '38322180-d2c7-469c-83c0-2c6b623f8734',
#  '677d3d31-9808-44b2-8cea-9c9683ead1fd',
#  'fa9b925a-4f39-456f-9b92-fcfec349b13d',
#  '29a90988-23cb-4186-9596-67c184e016cb',
#  '52d54744-d2d2-4a0d-a748-d01ff3b9fc6e')
#
# tweak_motor = johann_aux2_crystal.motor_cr_aux2_x.name
# scan_motor = 'johann_aux2_crystal_motor_cr_aux2_roll'

uids = ('886406a3-b684-4a42-a62b-3a831fcba65e',
 '52643015-84ff-4962-9bd1-0407fbe81830',
 'a8d60e8b-2ed3-4127-9eb9-2d4b43d42f0a',
 '51bf692a-cf50-49e4-9eb9-222ddc678ca4',
 'be00338e-c124-41de-9074-220d80bbda37',
 '5290b704-f7fc-4dcc-a8e0-cf54ec4fdfad',
 'fcf783e6-bea4-48b1-8497-66a250630d2b',
 'db72c465-a47b-44ae-bd84-74c5fd4a59a3',
 '13eee9db-f5a2-4dc3-974a-5c91090a4681')

tweak_motor = johann_aux3_crystal.motor_cr_aux3_x.name
scan_motor = 'johann_aux3_crystal_motor_cr_aux3_roll'

fwhm = []
motor_pos = []
plt.figure(1, clear=True)
for uid in uids:
    hdr = db[uid]
    df = hdr.table()
    _fwhm = _estimate_peak_fwhm_from_roll_scan(df, scan_motor, 'pil100k_stats1_total', plotting=True, fignum=1, clear=False)
    fwhm.append(_fwhm)
    motor_pos.append(hdr.start[tweak_motor])


plt.figure(2, clear=True)
plt.plot(motor_pos, fwhm, 'k.-')



# uids = ['97210e1b-d8e0-436c-97e6-8284d10ce1a4', # main
        # ]

t_main = db['97210e1b-d8e0-436c-97e6-8284d10ce1a4'].table()
t_aux2 = db['4626bc5e-b945-4fca-80e0-af9bda173d7c'].table()
t_aux3 = db['a82eaf26-2281-47e4-b601-815fbd489060'].table()

def plot_plot(t, x_key, y_key):
    x = t[x_key]
    y = t[y_key]
    y_norm = (y - np.mean(y[-5:])) / (y.max() - np.mean(y[-5:]))
    plt.plot(x - np.median(x), y_norm)


plt.figure(1, clear=True)
plot_plot(t_main, 'johann_main_crystal_motor_cr_main_roll', 'pil100k_stats1_total')
plot_plot(t_aux2, 'johann_aux2_crystal_motor_cr_aux2_roll', 'pil100k_stats1_total')
plot_plot(t_aux3, 'johann_aux3_crystal_motor_cr_aux3_roll', 'pil100k_stats1_total')

# plt.plot(t_aux2.johann_aux2_crystal_motor_cr_aux2_roll, t_aux2.pil100k_stats1_total )
# plt.plot(t_aux3.johann_aux3_crystal_motor_cr_aux3_roll, t_aux3.pil100k_stats1_total )

# '68f0f134-fcda-4b15-9053-e47031659a18' # main bragg
 # aux2

def plot_bragg_data(uid, x_key, y_key, n1=0, n2=3):
    t = db[uid].table()
    x = t[x_key]
    y = t[y_key]
    y_norm = (y - np.mean(y[n1:n2])) / (y.max() - np.mean(y[n1:n2]))
    plt.plot(x, y_norm)

plt.figure(1, clear=True)
plot_bragg_data('68f0f134-fcda-4b15-9053-e47031659a18', 'johann_main_crystal_bragg', 'pil100k_stats1_total')
plot_bragg_data('792720f5-89c8-45c7-8b08-e3f1a3b941cf', 'johann_aux2_crystal_bragg', 'pil100k_stats1_total')
plot_bragg_data('20da49aa-5019-4470-9fe8-5d9feeb4ae4c', 'johann_aux3_crystal_bragg', 'pil100k_stats1_total', n1=-3, n2=-1)



# main crystal
uids = \
    ('076e32aa-dc0b-479c-ade9-39e1320a824b',
     '46ba1136-f7f0-4b02-9839-39822b71d629',
     '3d0a01a8-1dfa-4ebd-8f7c-babac5462d6f',
     'a0f89c1f-63ac-4c1d-b038-846c5e596bc6',
     '1142d1eb-c5ee-4758-aa10-f3697f195f05',
     '34145c97-9758-4aa4-9524-df335f128189',
     '6c7843d7-dbe9-4bbf-9fce-55da54557066',
     '78421744-9db2-4950-84ae-e676e209b0f8',
     '5b47e90c-fd45-4372-bcb4-f232d21f19e1')

tweak_motor = johann_spectrometer_x.name
scan_motor = 'johann_main_crystal_motor_cr_main_roll'

uids = \
('a8d4127c-324a-47be-ba81-7c8fa9e10aee',
 'c83ee07c-2775-4c55-88ba-b11b5e7a502c',
 '7af4035d-f82c-4b69-be11-a8f793f79979',
 '2fe6b3e8-b869-4fce-847c-455788e48d80',
 '294e3995-94f3-461a-bd56-72e1f5c19770',
 '9f67596f-5711-4215-8f41-93ff915dc556',
 '704d6542-c46d-4876-bbfb-73eb8daba75a',
 '1401d137-5d07-4393-b111-3e9b3f22cdb6',
 '9f8e362a-ae2c-47e6-8eb3-89d6b4c0a1f3')



tweak_motor = johann_aux2_crystal.motor_cr_aux2_x.name
scan_motor = 'johann_aux2_crystal_motor_cr_aux2_roll'

uids = ('12399c12-6e48-43b5-a26a-491259cbda03',
 '0bab4c15-3fc4-4fc3-84b6-89134479443c',
 '11cd518f-e4ca-43da-b3d4-1ff0b0ff6ed6',
 '1c627016-5a3d-4257-a0c8-5b819abcd2c3',
 'e38b8b31-73d7-4af8-9781-8dcb553e2b35',
 'ebc9f3bc-7c27-49c5-a8d4-5d1da312b950',
 '20ba24b0-b9bf-4f6c-bc75-aaad07def7b5',
 '55510315-d5f9-453c-8074-ab22e380122a',
 '085ac43e-5ffb-437b-88db-5d8fbe4bcf44',
 'b60da7c8-cb01-4d16-937e-99c9ea5d367c',
 '65794f6d-5d85-4b8a-b909-83c20911bf3f')

tweak_motor = johann_aux3_crystal.motor_cr_aux3_x.name
scan_motor = 'johann_aux3_crystal_motor_cr_aux3_roll'


fwhm = []
motor_pos = []
plt.figure(1, clear=True)
for uid in uids:
    # _fwhm = estimate_peak_fwhm_from_roll_scan(db, uid, x_col=scan_motor, y_col='pil100k_stats1_total', plotting=True, fignum=1, clear=False)
    _fwhm = estimate_peak_intensity_from_roll_scan(db, uid, x_col=scan_motor, y_col='pil100k_stats1_total', plotting=True, fignum=1, clear=False)
    fwhm.append(_fwhm)
    hdr = db[uid]
    motor_pos.append(hdr.start[tweak_motor])

plt.figure(2, clear=True)
plt.plot(motor_pos, fwhm, 'k.-')

from xas.db_io import load_apb_dataset_from_db, translate_apb_dataset, load_apb_trig_dataset_from_db, load_pil100k_dataset_from_db


uid = 358337

apb_df, energy_df, energy_offset = load_apb_dataset_from_db(db, uid)
raw_dict = translate_apb_dataset(apb_df, energy_df, energy_offset)

apb_trigger_pil100k_timestamps = load_apb_trig_dataset_from_db(db, uid, use_fall=True,
                                                               stream_name='apb_trigger_pil100k')
pil100k_dict = load_pil100k_dataset_from_db(db, uid, apb_trigger_pil100k_timestamps)
raw_dict = {**raw_dict, **pil100k_dict}

hdr = db[uid]




























{'cycle#33': '2',
 'slack_channel#42': 'C05AF80JYQ5',
 'proposal#36': '312685',
 'PI': 'Kyle Lancaster',
 'beamline_id#44': 'ISS (8-ID)',
 'PI#31': 'Kyle Lancaster',
 'slack_channel#43': 'C05AF80JYQ5',
 'Facility#32': 'NSLS-II',
 'experimenters#34': ['Samantha MacMillan', 'Kyle Lancaster'],
 'saf#41': '311453',
 'Facility#23': 'NSLS-II',
 'saf#42': '311453',
 'proposal_id#25': None,
 'cycle#45': '2',
 'affiliation#37': 'Cornell University',
 'year#35': '2023',
 'affiliation': 'Cornell University',
 'email#40': 'kml236@cornell.edu',
 'experimenters#21': ['Samantha MacMillan', 'Kyle Lancaster'],
 'group#38': 'iss',
 'proposal_id#39': None,
 'scan_id#42': 358216,
 'proposal': '312685',
 'group': 'iss',
 'Facility': 'NSLS-II',
 'beamline_id': 'ISS (8-ID)',
 'proposal_id': None}



