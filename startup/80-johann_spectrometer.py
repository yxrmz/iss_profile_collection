import numpy as np
import pandas as pd
from xas.spectrometer import Crystal, analyze_many_elastic_scans
import copy



from ophyd import (PseudoPositioner, PseudoSingle)
from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)


def move_crystal_plan(x, y):
    yield from bps.mv(auxxy.x, x)
    yield from bps.mv(auxxy.y, y)



class JohannSpectrometerMotor(PseudoPositioner):
    energy = Cpt(PseudoSingle, name='emission_energy')
    motor_crystal_x = auxxy.x
    motor_crystal_y = auxxy.y
    motor_detector_y = huber_stage.z
    _real = ['motor_crystal_x',
             'motor_crystal_y',
             'motor_detector_y']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.energy0 = None
        self.cr_x0 = None
        self.cr_x0=None
        self.cr_y0=None
        self.det_y0=None
        self.spectrometer_root_path = f"{ROOT_PATH}/{USER_PATH}"
        self._initialized = False


    def define_motor_coordinates(self, energy0, R, kind, hkl,
                                  cr_x0=None, cr_y0=None, det_y0=None,
                 energy_limits=None):

        self.energy0 = energy0
        if cr_x0 is None:
            self.cr_x0 = self.motor_crystal_x.user_readback.get()
        else:
            self.cr_x0 = cr_x0
        if cr_y0 is None:
            self.cr_y0 = self.motor_crystal_y.user_readback.get()
        else:
            self.cr_y0 = cr_y0
        if det_y0 is None:
            self.det_y0 = self.motor_detector_y.user_readback.get()
        else:
            self.det_y0 = det_y0
        self.crystal = Crystal(R, 50, hkl, kind)
        self.crystal.place_E(energy0)
        self.cr_x0_nom = copy.copy(self.crystal.x)
        self.cry_0_nom = copy.copy(self.crystal.y)
        self.det_y0_nom = copy.copy(self.crystal.d_y)

        if energy_limits is not None:
            condition = ((type(energy_limits) == tuple) and (len(energy_limits)==2))
            assert condition, 'Invalid limits for emission energy motor'
            self.energy._limits = energy_limits
        self.energy_converter = None
        self._initialized = True

    def append_energy_converter(self, ec):
        self.energy_converter = ec

    @pseudo_position_argument
    def forward(self, energy_input_object):
        energy = energy_input_object.energy
        if self.energy_converter is not None:
            energy = self.energy_converter.act2nom(energy)
        self.crystal.place_E(energy)
        dcr_x = self.crystal.x - self.cr_x0_nom
        dcr_y = self.crystal.y - self.cry_0_nom
        ddet_y = self.crystal.d_y - self.det_y0_nom

        position_detector_y = self.det_y0 - ddet_y
        position_crystal_y = self.cr_y0 + dcr_y
        position_crystal_x = self.cr_x0 - dcr_x

        return self.RealPosition(motor_detector_y = position_detector_y,
                                 motor_crystal_y = position_crystal_y,
                                 motor_crystal_x = position_crystal_x)

    @real_position_argument
    def inverse(self, real_pos):
        x = self.cr_x0 + self.cr_x0_nom  - real_pos.motor_crystal_x
        y = self.cry_0_nom - self.cr_y0 + real_pos.motor_crystal_y
        d_y = self.det_y0 + self.det_y0_nom - real_pos.motor_detector_y
        energy = self.crystal.compute_energy_from_positions(x, y, d_y)
        if self.energy_converter is not None:
            energy = self.energy_converter.nom2act(energy)
        return [energy]


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

class RowlandCircle:

    def __init__(self, R=1000, x_src=0, y_src=0):
        self.R = R
        self.x_src = x_src
        self.y_src = y_src

    def compute_geometry(self, bragg_deg, det_dR=0):
        bragg = np.deg2rad(bragg_deg)

        self.y_cr = 0 + self.x_src
        self.x_cr = -self.R * np.cos(np.pi / 2 - bragg) + self.y_src

        self.x_det = +2 * self.x_cr * np.cos(bragg) * np.cos(bragg) - det_dR * np.cos(np.pi - 2 * bragg) + self.x_src
        self.y_det = -2 * self.x_cr * np.cos(bragg) * np.sin(bragg) - det_dR * np.sin(np.pi - 2 * bragg) + self.y_src

    @property
    def crystal_coords(self):
        return (self.x_cr, self.y_cr)

    @property
    def detector_coords(self):
        return (self.x_det, self.y_det)
    #
    def plot_full_range(self):

        bragg_deg = np.linspace(65, 89, 101)
        plt.figure(1)
        plt.clf()
        plt.plot(self.x_src, self.y_src, 'ko')

        for each_bragg_deg in bragg_deg:
            self.compute_geometry(each_bragg_deg)
            x_cr, y_cr = self.crystal_coords
            x_det, y_det = self.detector_coords

            plt.plot(x_cr, y_cr, 'bo')
            plt.plot(x_det, y_det, 'ro')
            plt.axis('square')


def compute_rowland_circle_geometry(x_src, y_src, R, bragg_deg, det_dR):
    bragg = np.deg2rad(bragg_deg)

    x_cr = -R * np.cos(np.pi / 2 - bragg)
    y_cr = 0

    x_det = +2 * x_cr * np.cos(bragg) * np.cos(bragg) - det_dR * np.cos(np.pi - 2 * bragg)
    y_det = -2 * x_cr * np.cos(bragg) * np.sin(bragg) - det_dR * np.sin(np.pi - 2 * bragg)

    return (x_cr + x_src), (y_cr + y_src), (x_det + x_src), (y_det + y_src)



#
row_circle = RowlandCircle()
# row_circle.plot_full_range()

# class DetectorArm(Device):

class ISSPseudoPositioner(PseudoPositioner):

    def __init__(self, *args, special_pseudo='bragg', **kwargs):
        self.pseudo_keys = [k for k, _ in self._get_pseudo_positioners()]
        self.real_keys = [k for k, _ in self._get_real_positioners()]
        self.motor_keys = self.pseudo_keys + self.real_keys
        super().__init__(*args, **kwargs)

        # self.special_pseudo = special_pseudo
        # self.reset_correction()
        # self.reset_calibration_data()
        # self.apply_correction = True

    # def reset_correction(self):
    #     self.correction_dict = {'act2nom': {k: [0] for k in self.pseudo_keys},
    #                             'nom2act': {k: [0] for k in self.pseudo_keys}}
    #
    # def reset_calibration_data(self):
    #     self.calibration_data = {'actual': {k: [] for k in self.pseudo_keys},
    #                              'nominal': {k: [] for k in self.pseudo_keys}}
    #
    # def register_calibration_point(self, special_pseudo_pos):
    #     pseudo_dict = self.pseudo_pos2dict(self.position)
    #     actual_dict = copy.deepcopy(pseudo_dict)
    #     actual_dict[self.special_pseudo] = special_pseudo_pos
    #     nominal_dict = self.pseudo_pos2dict(self.inverse(self.forward(**{self.special_pseudo : pseudo_dict[self.special_pseudo]})))
    #     for k in self.pseudo_keys:
    #         self.calibration_data['actual'][k].append(actual_dict[k])
    #         self.calibration_data['nominal'][k].append(nominal_dict[k])
    #
    #     # real_dict = self.real_pos2dict(self.real_position)
    #     # actual_dict = copy.deepcopy(real_dict)
    #     # actual_dict[self.special_pseudo] = special_pseudo_pos
    #     # nominal_dict = self.pseudo_pos2dict(
    #     #     self.inverse(self.forward(**{self.special_pseudo: pseudo_dict[self.special_pseudo]})))
    #     # for k in self.pseudo_keys:
    #     #     self.calibration_data['actual'][k].append(actual_dict[k])
    #     #     self.calibration_data['nominal'][k].append(nominal_dict[k])
    #
    # def process_calibration(self, npoly=None):
    #     if npoly is None:
    #         npoly = len(self.calibration_data['nominal'][self.special_pseudo]) - 1
    #     for key in self.pseudo_keys:
    #         x_nom = np.array(self.calibration_data['nominal'][key])
    #         x_act = np.array(self.calibration_data['actual'][key])
    #         self.correction_dict['nom2act'][key] = np.polyfit(x_nom, x_act - x_nom, npoly)
    #         self.correction_dict['act2nom'][key] = np.polyfit(x_act, x_nom - x_act, npoly)
    #
    # def correct(self, pseudo_dict, way='act2nom'):
    #     if self.apply_correction:
    #         for k in pseudo_dict.keys():
    #             delta = np.polyval(self.correction_dict[way][k], pseudo_dict[k])
    #             pseudo_dict[k] += delta
    #     return pseudo_dict

    def pseudo_pos2dict(self, pseudo_pos):
        ret = {k : getattr(pseudo_pos, k) for k in self.pseudo_keys}
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
        # pseudo_dict = self.correct(pseudo_dict, way='act2nom')
        real_dict = self._forward(pseudo_dict)
        # real_dict = self._forward(pseudo_pos)
        return self.RealPosition(**real_dict)

    @real_position_argument
    def inverse(self, real_pos):
        real_dict = self.real_pos2dict(real_pos)
        pseudo_dict = self._inverse(real_dict)
        # pseudo_dict = self.correct(pseudo_dict, way='nom2act')
        return self.PseudoPosition(**pseudo_dict)


    @property
    def position_dict(self):
        return self.pseudo_pos2dict(self.position)

    @property
    def real_position_dict(self):
        return self.real_pos2dict(self.real_position)


from xas.xray import bragg2e, e2bragg
from xas.fitting import Nominal2ActualConverter
class JohannMultiCrystalSpectrometerAlt(ISSPseudoPositioner): #(PseudoPositioner):
    motor_cr_assy_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
    motor_cr_assy_y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')

    motor_cr_main_roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
    motor_cr_main_yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')

    cr_main_roll_offset = Cpt(SoftPositioner, init_pos=0)  # software representation of the angular offset on the crystal stage

    motor_det_x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
    motor_det_th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta1}Mtr')  # give better names
    motor_det_th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Det:Gon:Theta2}Mtr')

    cr_assy_x = Cpt(PseudoSingle, name='cr_x')
    cr_assy_y = Cpt(PseudoSingle, name='cr_y')

    cr_main_bragg = Cpt(PseudoSingle, name='cr_bragg')
    cr_main_yaw = Cpt(PseudoSingle, name='cr_bragg')

    det_bragg = Cpt(PseudoSingle, name='det_bragg')
    det_x = Cpt(PseudoSingle, name='det_x')
    det_y = Cpt(PseudoSingle, name='det_y')

    bragg = Cpt(PseudoSingle, name='bragg')
    # bragg_act = Cpt(PseudoSingle, name='bragg_act')
    x = Cpt(PseudoSingle, name='x')
    det_focus = Cpt(PseudoSingle, name='det_focus')
    energy = Cpt(PseudoSingle, name='energy')

    _real = ['motor_cr_assy_x', 'motor_cr_assy_y', 'motor_cr_main_roll', 'motor_cr_main_yaw',
             'motor_det_x', 'motor_det_th1', 'motor_det_th2']
    _pseudo_precision = {'cr_assy_x' : 5e-3,
                         'cr_assy_y' : 5e-3,
                         'cr_main_bragg' : 5e-6,
                         'cr_main_yaw' : 5e-6,
                         'det_bragg' : 5e-6,
                         'det_x' : 5e-3,
                         'det_y' : 5e-3,
                         'bragg' : 5e-6,
                         'x' : 5e-3,
                         'det_focus' : 1e-2,
                         'energy' : 1e-3}
    _pseudo = list(_pseudo_precision.keys())

    det_L1 = 550  # length of the big arm
    det_L2 = 91  # distance between the second gon and the sensitive surface of the detector

    def __init__(self, *args, auto_target=False, **kwargs):
        self.json_path = f'{ROOT_PATH_SHARED}/settings/json/johann_config.json'
        self.init_from_settings()
        super().__init__(*args, auto_target=auto_target, **kwargs)
        self.set_cr_main_roll_offset_from_settings()
        self.operation_mode = 'nominal'
        self.reset_offset_data()
        self._initialized = False
        self.energy_converter = None
        self._print_inverse = False

    def load_config(self, file):
        with open(file, 'r') as f:
            config = json.loads(f.read())
        return config

    def save_current_spectrometer_config(self, file):
        config = self.get_spectrometer_config()
        with open(file, 'w') as f:
            json.dump(config, f)

    def save_current_spectrometer_config_to_settings(self):
        self.save_current_spectrometer_config(self.json_path)

    def init_from_settings(self):
        try:
            config = self.load_config(self.json_path)
            self.set_spectrometer_config(config)
        except Exception as e:
            config = {'crystal' : 'Si',
                      'hkl' : (6, 2, 0),
                      'R': 1000,
                      'x_src': 0,
                      'y_src': 0,
                      'motor_cr_assy_x0': 992.9999570365,
                      'motor_cr_assy_y0': 7.481774249999999,
                      'motor_cr_main_roll0': 8.1324,
                      'motor_cr_main_yaw0' : 0.85,
                      'cr_main_roll_offset': 17.125,
                      'motor_det_x0': -10,  # high limit of this motor should be at 529 mm
                      'motor_det_th10': 69,
                      'motor_det_th20': -69}
            self.set_spectrometer_config(config)

    def set_spectrometer_config(self, config):
        self.crystal = config['crystal']
        self.hkl = config['hkl']
        self.R = config['R']
        self.x_src = config['x_src']
        self.y_src = config['y_src']

        self.motor_cr_assy_x0 = config['motor_cr_assy_x0']
        self.motor_cr_assy_y0 = config['motor_cr_assy_y0']
        self.motor_cr_main_roll0 = config['motor_cr_main_roll0']
        self.motor_cr_main_yaw0 = config['motor_cr_main_yaw0']
        self.__cr_main_roll_offset = config['cr_main_roll_offset']

        self.motor_det_x0 = config['motor_det_x0']
        self.motor_det_th10 = config['motor_det_th10']
        self.motor_det_th20 = config['motor_det_th20']

    def get_spectrometer_config(self):
        config = {'crystal' : self.crystal,
                  'hkl' : self.hkl,
                  'R': self.R,
                  'x_src': self.x_src,
                  'y_src': self.y_src,
                  'motor_cr_assy_x0': self.motor_cr_assy_x0,
                  'motor_cr_assy_y0': self.motor_cr_assy_y0,
                  'motor_cr_main_roll0': self.motor_cr_main_roll0,
                  'motor_cr_main_yaw0' : self.motor_cr_main_yaw0,
                  'cr_main_roll_offset': self.cr_main_roll_offset.position,
                  'motor_det_x0': self.motor_det_x0,
                  'motor_det_th10': self.motor_det_th10,
                  'motor_det_th20': self.motor_det_th20}
        return config

    def set_cr_main_roll_offset_from_settings(self):
        self.cr_main_roll_offset.set(self.__cr_main_roll_offset)
        # self.__cr_main_roll_offset = None

    def update_johann_parameters(self, crystal='Si', hkl=(7, 3, 3), R=1000, x_src=0, y_src=0):
        self.crystal = crystal
        self.hkl = hkl
        self.R = R
        self.x_src = x_src
        self.y_src = y_src

    def set_det_parking(self):
        self.motor_det_x0 = self.motor_det_x.position
        self.motor_det_th10 = self.motor_det_th1.position
        self.motor_det_th20 = self.motor_det_th2.position

    def set_main_crystal_parking(self):
        self.motor_cr_assy_x0 = self.motor_cr_assy_x.position
        self.motor_cr_assy_y0 = self.motor_cr_assy_y.position
        self.motor_cr_main_roll0 = self.motor_cr_main_roll.position / 1000
        self.motor_cr_main_yaw0 = self.motor_cr_main_yaw.position / 1000

    @property
    def det_dx(self):
        return self.det_L1 * np.cos(np.deg2rad(self.motor_det_th10)) - self.det_L2

    @property
    def det_h(self):
        return self.det_L1 * np.sin(np.deg2rad(self.motor_det_th10))

    def reset_offset_data(self):
        self.offset_data = {'nominal': {k: [] for k in self.pseudo_keys},
                            'actual': {k: [] for k in self.pseudo_keys}}
        self.motor_offset_registry = []

    @property
    def n_offset_points(self):
        return len(self.offset_data['nominal']['bragg'])

    def register_energy(self, energy, energy_limits=None):
        bragg_act = e2bragg(energy, self.crystal, self.hkl)
        bragg = self.bragg.position
        cr_main_roll_offset_value = self.cr_main_roll_offset.position
        self.cr_main_roll_offset.set(cr_main_roll_offset_value + (bragg - bragg_act))
        self.motor_offset_registry.append(self.position_dict)
        if energy_limits is not None:
            self.energy._limits = energy_limits
        self._initialized = True
        self.save_current_spectrometer_config_to_settings()

    def update_motor_pos_for_energy(self, new_pos_dict):
        if len(self.motor_offset_registry) == 0:
            pass
        elif len(self.motor_offset_registry) == 1:
            new_pos_dict['cr_main_yaw'] = self.motor_offset_registry[0]['cr_main_yaw']
            new_pos_dict['x'] = self.motor_offset_registry[0]['x']
            new_pos_dict['det_focus'] = self.motor_offset_registry[0]['det_focus']
            new_pos_dict['det_bragg'] += self.motor_offset_registry[0]['det_bragg'] - self.motor_offset_registry[0]['bragg']
            self._move_det_arm_only(new_pos_dict)

    def append_energy_converter(self, ec):
        self.energy_converter = ec

    def which_motor_moves(self, new_pos_dict):
        try:
            old_pos_dict = self.pseudo_pos2dict(self.position)
        except Exception as e:
            print(e)
            old_pos_dict = self._inverse(self.real_pos2dict(self.real_position))
        moving_motors = []
        moving_motors_delta = []
        # print('###########')
        # print(f'\t old_pos \t new_pos \t motor_name')
        for motor_name in old_pos_dict.keys():
            # print(f'{old_pos_dict[motor_name] : .4f} \t {new_pos_dict[motor_name] : .4f} \t - {motor_name}')
            if not np.isclose(old_pos_dict[motor_name], new_pos_dict[motor_name], atol=self._pseudo_precision[motor_name]):
                moving_motors.append(motor_name)
                moving_motors_delta.append(new_pos_dict[motor_name] - old_pos_dict[motor_name])
        if len(moving_motors) == 0:
            return None
        elif len(moving_motors) == 1:
            return moving_motors[0]
        elif len(moving_motors) > 1:
            dd = {m : d for m, d in zip(moving_motors, moving_motors_delta)}
            print_to_gui(f'Info: Multiple Johann spetrometer pseudo motors are being moved. {dd}', tag='Spectrometer')
            return moving_motors[0]

    def _move_crystal_only(self, new_pos_dict):
        cr_assy_x, _, _, _ = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, new_pos_dict['cr_main_bragg'], 0)
        cr_assy_x += self.R
        # print(f'Updating cr_assy_x: old_pos={new_pos_dict["cr_assy_x"]}, new_pos={cr_assy_x}')
        new_pos_dict['cr_assy_x'] = cr_assy_x

    def _move_det_arm_only(self, new_pos_dict):
        _, _, det_x, det_y = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, new_pos_dict['det_bragg'],
                                                             new_pos_dict['det_focus'])
        det_x += new_pos_dict['x']
        # print(f'Updating det_x: old_pos={new_pos_dict["det_x"]}, new_pos={det_x}')
        new_pos_dict['det_x'] = det_x
        # print(f'Updating det_y: old_pos={new_pos_dict["det_y"]}, new_pos={det_y}')
        new_pos_dict['det_y'] = det_y

    def _move_all_components(self, new_pos_dict):
        new_pos_dict['cr_main_bragg'] = new_pos_dict['bragg']
        new_pos_dict['det_bragg'] = new_pos_dict['bragg']
        self._move_crystal_only(new_pos_dict)
        self._move_det_arm_only(new_pos_dict)

    # def _move_all_components_with_correction(self, new_pos_dict):
    #     if self.n_offset_points == 0:
    #         new_pos_dict['bragg'] = new_pos_dict['bragg_act']
    #         self._move_all_components(new_pos_dict)
    #
    #     elif self.n_offset_points == 1:
    #         new_pos_dict['bragg'] = self.decorrect_bragg(new_pos_dict['bragg_act'])
    #         # new_pos_dict['bragg'] -= (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
    #         # pos_nom = {k: self.offset_data['nominal'][k][0] for k in self.pseudo_keys}
    #         # pos_nom['bragg'] = bragg
    #         self._move_all_components(new_pos_dict)
    #         # sdfs
    #         for k in self.pseudo_keys:
    #             if (k != 'bragg') and (k != 'bragg_act'):
    #                 new_pos_dict[k] += (self.offset_data['actual'][k][0] - self.offset_data['nominal'][k][0])
    #
    #     elif self.n_offset_points == 2:
    #         new_pos_dict['bragg'] = self.decorrect_bragg(new_pos_dict['bragg_act'])
    #         # new_pos_dict['bragg'] -= (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
    #         # pos_nom = {k: self.offset_data['nominal'][k][0] for k in self.pseudo_keys}
    #         # pos_nom['bragg'] = bragg
    #         self._move_all_components(new_pos_dict)
    #         # sdfs
    #         for k in self.pseudo_keys:
    #             if (k != 'bragg') and (k != 'bragg_act'):
    #                 p = np.polyfit(np.array(self.offset_data['actual']['bragg']),
    #                                np.array(self.offset_data['actual'][k]) -
    #                                np.array(self.offset_data['nominal'][k]), 1)
    #                 delta = np.polyval(p, new_pos_dict['bragg_act'])
    #
    #                 new_pos_dict[k] += delta
    #
    # def correct_bragg(self, bragg):
    #     if self.n_offset_points == 0:
    #         return bragg
    #     elif self.n_offset_points == 1:
    #         return bragg + (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
    #     elif self.n_offset_points == 2:
    #         p = np.polyfit(np.array(self.offset_data['nominal']['bragg']),
    #                        np.array(self.offset_data['actual']['bragg']) -
    #                        np.array(self.offset_data['nominal']['bragg']), 1)
    #         delta = np.polyval(p, bragg)
    #         return bragg + delta
    #
    # def decorrect_bragg(self, bragg_act):
    #     if self.n_offset_points == 0:
    #         return bragg_act
    #     elif self.n_offset_points == 1:
    #         return bragg_act - (self.offset_data['actual']['bragg'][0] - self.offset_data['nominal']['bragg'][0])
    #     elif self.n_offset_points == 2:
    #         p = np.polyfit(np.array(self.offset_data['actual']['bragg']),
    #                        np.array(self.offset_data['actual']['bragg']) -
    #                        np.array(self.offset_data['nominal']['bragg']), 1)
    #         delta = np.polyval(p, bragg_act)
    #         return bragg_act - delta

    def handle_pseudo_input(self, new_pos_dict):
        moving_motor = self.which_motor_moves(new_pos_dict)
        # print(f'Motor moving: {moving_motor}')

        if moving_motor == 'cr_main_bragg':
            self._move_crystal_only(new_pos_dict)

        elif (moving_motor == 'det_bragg') or (moving_motor == 'det_focus'):
            self._move_det_arm_only(new_pos_dict)

        elif (moving_motor == 'bragg'):
            self._move_all_components(new_pos_dict)

        elif (moving_motor == 'energy'):
            if self.energy_converter is not None:
                new_pos_dict['energy'] = self.energy_converter.act2nom(new_pos_dict['energy'])
            new_pos_dict['bragg'] = e2bragg(new_pos_dict['energy'], self.crystal, self.hkl)
            self._move_all_components(new_pos_dict)
            self.update_motor_pos_for_energy(new_pos_dict)
        #     # print('moving_motor is bragg_act')
        #     self._move_all_components_with_correction(new_pos_dict)

    def _forward(self, pseudo_pos_dict):
        self.handle_pseudo_input(pseudo_pos_dict)
        cr_assy_x, cr_assy_y, cr_main_bragg, cr_main_yaw = pseudo_pos_dict['cr_assy_x'],\
                                                           pseudo_pos_dict['cr_assy_y'],\
                                                           pseudo_pos_dict['cr_main_bragg'],\
                                                           pseudo_pos_dict['cr_main_yaw']

        det_bragg, det_x, det_y = pseudo_pos_dict['det_bragg'],\
                                  pseudo_pos_dict['det_x'],\
                                  pseudo_pos_dict['det_y']

        x = pseudo_pos_dict['x']

        motor_cr_assy_x = x - cr_assy_x + self.motor_cr_assy_x0
        motor_cr_assy_y = cr_assy_y + self.motor_cr_assy_y0
        motor_cr_main_roll = (cr_main_bragg + self.cr_main_roll_offset.position + self.motor_cr_main_roll0 - 90) * 1000
        motor_cr_main_yaw = cr_main_yaw * 1000

        _det_bragg_rad = np.deg2rad(det_bragg)
        _phi = np.pi - 2 * _det_bragg_rad
        _sin_th1 = (self.det_h - self.det_L2 * np.sin(_phi) - det_y) / self.det_L1
        motor_det_th1 = np.arcsin(_sin_th1)
        motor_det_th2 = _phi + motor_det_th1
        motor_det_x = self.motor_det_x0 - self.det_dx + self.det_L1 * np.cos(motor_det_th1) - self.det_L2 * np.cos(_phi) - det_x + x
        motor_det_th1 = np.rad2deg(motor_det_th1)
        motor_det_th2 = -np.rad2deg(motor_det_th2)

        output = {'motor_cr_assy_x'   : motor_cr_assy_x,
                  'motor_cr_assy_y'   : motor_cr_assy_y,
                  'motor_cr_main_roll': motor_cr_main_roll,
                  'motor_cr_main_yaw' : motor_cr_main_yaw,
                  'motor_det_x'  : motor_det_x,
                  'motor_det_th1': motor_det_th1,
                  'motor_det_th2': motor_det_th2}
        # print(output)

        return output


    def _inverse(self, real_pos_dict):
        if self._print_inverse: print('INVERSE INVOKED')
        motor_cr_assy_x, motor_cr_assy_y, motor_cr_main_roll, motor_cr_main_yaw, motor_det_x, motor_det_th1, motor_det_th2 = \
            real_pos_dict['motor_cr_assy_x'], \
            real_pos_dict['motor_cr_assy_y'], \
            real_pos_dict['motor_cr_main_roll'], \
            real_pos_dict['motor_cr_main_yaw'], \
            real_pos_dict['motor_det_x'], \
            real_pos_dict['motor_det_th1'], \
            real_pos_dict['motor_det_th2']

        cr_main_bragg = 90 + motor_cr_main_roll / 1000 - self.cr_main_roll_offset.position - self.motor_cr_main_roll0
        cr_main_yaw = motor_cr_main_yaw / 1000
        cr_assy_x, _, _, _ = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, cr_main_bragg, 0)
        cr_assy_x += self.R
        cr_assy_y = motor_cr_assy_y - self.motor_cr_assy_y0
        x = cr_assy_x + (motor_cr_assy_x - self.motor_cr_assy_x0)

        motor_det_th2 *= -1
        det_bragg = (180 - (motor_det_th2 - motor_det_th1)) / 2

        det_x = self.motor_det_x0 - self.det_dx + self.det_L1 * np.cos(np.deg2rad(motor_det_th1)) - self.det_L2 * np.cos(np.deg2rad(motor_det_th2 - motor_det_th1)) - motor_det_x + x
        det_y = self.det_h - self.det_L1 * np.sin(np.deg2rad(motor_det_th1)) - self.det_L2 * np.sin(np.deg2rad(motor_det_th2 - motor_det_th1))

        _, _, det_x_ref, det_y_ref = compute_rowland_circle_geometry(self.x_src, self.y_src, self.R, det_bragg, 0)
        det_x_ref += x
        det_focus = np.sqrt((det_x - det_x_ref) ** 2 + (det_y - det_y_ref) ** 2) * np.sign(det_y_ref - det_y)
        bragg = cr_main_bragg
        energy = bragg2e(bragg, self.crystal, self.hkl)
        if self.energy_converter is not None:
            energy = self.energy_converter.nom2act(energy)

        return {'cr_assy_x' : cr_assy_x,
                'cr_assy_y' : cr_assy_y,
                'cr_main_bragg' : cr_main_bragg,
                'cr_main_yaw' : cr_main_yaw,
                'det_bragg' : det_bragg,
                'det_x' : det_x,
                'det_y' : det_y,
                'bragg' : bragg,
                'x' : x,
                'det_focus' : det_focus,
                'energy' : energy}


johann_emission = JohannMultiCrystalSpectrometerAlt(name='johann_emission')
# johann_emission.register_energy(7470)


motor_dictionary['johann_bragg_angle'] = {'name': johann_emission.bragg.name,
                                          'description' : 'Johann Bragg Angle',
                                          'object': johann_emission.bragg,
                                          'group': 'spectrometer'}

motor_dictionary['johann_det_focus'] =   {'name': johann_emission.det_focus.name,
                                          'description' : 'Johann Detector Focus',
                                          'object': johann_emission.det_focus,
                                          'group': 'spectrometer'}

motor_dictionary['johann_x'] =           {'name': johann_emission.x.name,
                                          'description' : 'Johann X',
                                          'object': johann_emission.x,
                                          'group': 'spectrometer'}

motor_dictionary['johann_energy'] =      {'name': johann_emission.energy.name,
                                          'description' : 'Johann Energy',
                                          'object': johann_emission.energy,
                                          'group': 'spectrometer'}




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
# class MainJohannCrystal(ISSPseudoPositioner):
#     x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:X}Mtr')
#     y = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Ana:Assy:Y}Mtr')
#     roll = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Roll}Mtr')
#     yaw = Cpt(EpicsMotor, 'XF:08IDB-OP{HRS:1-Stk:1:Yaw}Mtr')
#
#     roll_offset = Cpt(SoftPositioner, init_pos=0.0) # software representation of the angular offset on the crystal stage
#
#     x_cr = Cpt(PseudoSingle, name='x_cr')
#     y_cr = Cpt(PseudoSingle, name='y_cr')
#     bragg = Cpt(PseudoSingle, name='bragg')
#     yaw_cr = Cpt(PseudoSingle, name='yaw_cr')
#
#
#     _real = ['x', 'y', 'roll', 'yaw']
#     _pseudo = ['x_cr', 'y_cr', 'bragg', 'yaw_cr']
#
#     def __init__(self, *args, config=None, **kwargs):
#         self.restore_parking(config)
#         super().__init__(*args, **kwargs)
#         self.restore_roll_offset(config)
#
#     def set_parking(self):
#         self.x0 = self.x.position
#         self.y0 = self.y.position
#         self.roll0 = self.roll.position / 1000
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
#         self.y0 = 4.438
#         self.roll0 = 5.750
#         self.yaw0 = 0.170
#
#     def restore_roll_offset(self, config):
#         if config is not None:
#             self.roll_offset.set(config['main_johann_crystal_roll_offset0'])
#         else:
#             self.roll_offset.set(0)
#
#     def set_roll_offset(self, value):
#         self.roll_offset.set(value)
#
#     def read_current_config(self):
#         return {'main_johann_crystal_x0': self.x0,
#                 'main_johann_crystal_y0': self.y0,
#                 'main_johann_crystal_roll0': self.roll0,
#                 'main_johann_crystal_yaw0': self.yaw0,
#                 'main_johann_crystal_roll_offset0': self.roll_offset.position}
#
#     # def _forward(self, pseudo_pos):
#     #     bragg, x_cr, y, yaw = pseudo_pos.bragg, pseudo_pos.x_cr, pseudo_pos.y, pseudo_pos.yaw
#
#     def _forward(self, pseudo_dict):
#         # bragg, x_cr, y, yaw = pseudo_dict['bragg'], pseudo_dict['x_cr'], pseudo_dict['y'], pseudo_dict['yaw']
#         x_cr, y_cr, bragg, yaw_cr = pseudo_dict['x_cr'], pseudo_dict['y_cr'], pseudo_dict['bragg'], pseudo_dict['yaw_cr']
#         roll = -(90 - bragg - self.roll_offset.position - self.roll0) * 1000
#         x = self.x0 - x_cr
#         return {'x' : x, 'roll' : roll, 'y' : y_cr, 'yaw' : yaw_cr}
#         # return self.RealPosition(x=x, roll=roll, y=y, yaw=yaw)
#
#     # def _inverse(self, real_pos):
#     #     x, roll, y, yaw = real_pos.x, real_pos.roll, real_pos.y, real_pos.yaw
#
#     def _inverse(self, real_dict):
#         x, roll, y, yaw = real_dict['x'], real_dict['roll'], real_dict['y'], real_dict['yaw'],
#         bragg = 90 + roll / 1000 - self.roll_offset.position - self.roll0
#         x_cr = self.x0 - x
#         return {'x_cr' : x_cr, 'y_cr' : y, 'bragg' : bragg, 'yaw_cr' : yaw}
#         # return self.PseudoPosition(bragg=bragg, x_cr=x_cr, y=y, yaw=yaw)
#


    # @pseudo_position_argument
    # def forward(self, pseudo_pos):
    #     return self._forward(pseudo_pos)
    #
    # @real_position_argument
    # def inverse(self, real_pos):
    #     return self._inverse(real_pos)

# j_cr = MainJohannCrystal(name='j_cr')

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
