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


johann_spectrometer_motor = JohannSpectrometerMotor(name='motor_emission')

motor_emission_key = 'motor_emission'

motor_emission_dict = {'name': johann_spectrometer_motor.name, 'description' : 'Emission energy', 'object': johann_spectrometer_motor, 'group': 'spectrometer'}
motor_dictionary['motor_emission'] = motor_emission_dict

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

    def __init__(self, R=1000, det_dR=0, src_x=0, src_y=0):
        self.R = R
        self.det_dR = det_dR
        self.x_src = src_x
        self.y_src = src_y

    def compute_geometry(self, ba_deg):
        ba = np.deg2rad(ba_deg)

        self.y_cr = 0 + self.x_src
        self.x_cr = -self.R * np.cos(np.pi / 2 - ba) + self.y_src

        self.x_det = +2 * self.x_cr * np.cos(ba) * np.cos(ba) - self.det_dR * np.cos(np.pi - 2 * ba) + self.x_src
        self.y_det = -2 * self.x_cr * np.cos(ba) * np.sin(ba) - self.det_dR * np.sin(np.pi - 2 * ba) + self.y_src

    @property
    def crystal_coords(self):
        return (self.x_cr, self.y_cr)

    @property
    def detector_coords(self):
        return (self.x_det, self.y_det)
    #
    def plot_full_range(self):

        ba_deg = np.linspace(65, 89, 101)
        plt.figure(1)
        plt.clf()
        plt.plot(self.x_src, self.y_src, 'ko')

        for each_ba_deg in ba_deg:
            self.compute_geometry(each_ba_deg)
            x_cr, y_cr = self.crystal_coords
            x_det, y_det = self.detector_coords

            plt.plot(x_cr, y_cr, 'bo')
            plt.plot(x_det, y_det, 'ro')
            plt.axis('square')





row_circle = RowlandCircle()
row_circle.plot_full_range()

# class DetectorArm(Device):
class DetectorArm(PseudoPositioner):

    L1 = 550  # length of the big arm
    L2 = 81  # distance between the second gon and the sensetive surface of the detector

    x = Cpt(EpicsMotor, 'XF:08IDB-OP{Stage:Aux1-Ax:Y}Mtr')
    th1 = Cpt(EpicsMotor, 'XF:08IDB-OP{Misc:2-Ax:8}Mtr') # give better names
    th2 = Cpt(EpicsMotor, 'XF:08IDB-OP{Misc:2-Ax:6}Mtr')

    ba = Cpt(PseudoSingle, name='ba')
    x_det = Cpt(PseudoSingle, name='x_det')
    y_det = Cpt(PseudoSingle, name='y_det')

    # _real = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._real = [x.name, th1.name, th2.name]
        self.restore_parking_pos()


    def set_parking_pos(self):
        self.th1_0 = self.th1.position
        self.th2_0 = self.th2.position
        self.h = self.L1 * np.sin(np.deg2rad(self.th1_0))
        self.x_0 = self.x.position
        self.dx = self.L1 * np.cos(np.deg2rad(self.th1_0)) - self.L2

    def restore_parking_pos(self):
        '''
        Read parking positions from previous records
        '''
        self.x_0 = -204.5
        self.th1_0 = 62
        self.th2_0 = -62
        self.dx = 177.21
        self.h = 485.6211760724097


    def _forward(self, pseudo_pos):
        # print(pseudo_pos)
        ba, x_det, y_det = pseudo_pos.ba, pseudo_pos.x_det, pseudo_pos.y_det
        # print(f'{}, {}, {}')
        # print(f'{ba_deg=}, {x_det=}, {y_det=}')
        ba_rad = np.deg2rad(ba)
        phi = np.pi - 2 * ba_rad
        # print(f'{phi=}')
        sin_th1 = (self.h - self.L2 * np.sin(phi) - y_det) / self.L1
        # print(f'{sin_th1=}')
        th1 = np.arcsin(sin_th1)
        th2 = phi + th1
        x = self.x_0 - self.dx + self.L1 * np.cos(th1) - self.L2 * np.cos(phi) - x_det

        # print('I am at the end of forward')
        # kwargs = {f'{self.name}_x': ba, f'{self.name}_th1': np.rad2deg(th1), f'{self.name}_th2': -np.rad2deg(th2)}
        # return self.RealPosition(**kwargs)
        return self.RealPosition(x, np.rad2deg(th1), -np.rad2deg(th2))

    def _inverse(self, real_pos):
        # print(real_pos)
        x, th1, th2 = real_pos.x, real_pos.th1, real_pos.th2
        th2 *= -1
        ba = (180 - (th2 - th1)) / 2
        x_det = self.x_0 - self.dx + self.L1 * np.cos(np.deg2rad(th1)) - self.L2 * np.cos(np.deg2rad(th2 - th1)) - x
        y_det = self.h - self.L1 * np.sin(np.deg2rad(th1)) - self.L2 * np.sin(np.deg2rad(th2 - th1))
        # print('I am at the end of inverse')
        # kwargs = {f'{self.name}_ba': ba, f'{self.name}_x_det': x_det, f'{self.name}_y_det': y_det}
        # return self.PseudoPosition(**kwargs)
        return self.PseudoPosition(ba, x_det, y_det)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        return self._forward(pseudo_pos)

    @real_position_argument
    def inverse(self, real_pos):
        return self._inverse(real_pos)


det_arm = DetectorArm(name='det_arm')
ttime.sleep(0.1)
# det_arm.set_parking_pos()

dffddfdfgdfdfg

# #######
# from ophyd import SoftPositioner
# class SPseudo3x3(PseudoPositioner):
#     """
#     Interface to three positioners in a coordinate system that flips the sign.
#     """
#     pseudo1 = Cpt(PseudoSingle, limits=(-10, 10), egu='a')
#     pseudo2 = Cpt(PseudoSingle, limits=(-10, 10), egu='b')
#     pseudo3 = Cpt(PseudoSingle, limits=None, egu='c')
#
#     real1 = Cpt(SoftPositioner, init_pos=10.)
#     real2 = Cpt(SoftPositioner, init_pos=10.)
#     real3 = Cpt(SoftPositioner, init_pos=10.)
#
#     @pseudo_position_argument
#     def forward(self, pseudo_pos):
#         "Given a position in the psuedo coordinate system, transform to the real coordinate system."
#         return self.RealPosition(
#             real1=-pseudo_pos.pseudo1,
#             real2=-pseudo_pos.pseudo2,
#             real3=-pseudo_pos.pseudo3
#         )
#
#     @real_position_argument
#     def inverse(self, real_pos):
#         "Given a position in the real coordinate system, transform to the pseudo coordinate system."
#         return self.PseudoPosition(
#             pseudo1=-real_pos.real1,
#             pseudo2=-real_pos.real2,
#             pseudo3=-real_pos.real3
#         )
#
# bla = SPseudo3x3(name='bla')
#
# ######
# # def forward(pseudo_pos, h=det_arm.h, L1=det_arm.L1, L2=det_arm.L2, x_0=det_arm.x_0, dx=det_arm.dx):
# #     ba_deg, x_det, y_det = pseudo_pos
# #     # print(f'{}, {}, {}')
# #     print(f'{ba_deg=}, {x_det=}, {y_det=}')
# #     ba = np.deg2rad(ba_deg)
# #     phi = np.pi - 2 * ba
# #     print(f'{phi=}')
# #     sin_th1 = (h - L2 * np.sin(phi) - y_det) / L1
# #     print(f'{sin_th1=}')
# #     th1 = np.arcsin(sin_th1)
# #     th2 = phi + th1
# #     x = x_0 - dx + L1 * np.cos(th1) - L2 * np.cos(phi) - x_det
# #
# #     return x, np.rad2deg(th1), -np.rad2deg(th2)
#
# ba_set = 89
# row_circle.compute_geometry(ba_set)
# ccs = det_arm.forward((ba_set, *row_circle.detector_coords))
# print(ccs)
#
# det_arm.inverse((det_arm.x.position, det_arm.th1.position, det_arm.th2.position))
#
# det_arm.x.move(ccs[0], wait=False)
# det_arm.th1.move(ccs[1], wait=False)
# det_arm.th2.move(ccs[2], wait=False)
#
# plt.figure(2, clear=True)
# for ba_set in np.arange(65, 91):
#     row_circle.compute_geometry(ba_set)
#     ccs = forward((ba_set, *row_circle.detector_coords))
#     plt.plot(ba_set, ccs[0], 'k.')
#     plt.plot(ba_set, ccs[1], 'm.')
#     plt.plot(ba_set, ccs[2], 'b.')
# # # det_arm.forward((90, 0, 0))


# class JohannMultiCrystalSpectrometer(Device):
# # class JohannMultiCrystalSpectrometer(PseudoPositioner):
#
#     # crystal0 = Cpt(JohannCrystal, ':0', leading=True)
#     # crystal1 = Cpt(JohannCrystal, name='crystal1')
#     det_arm = Cpt(DetectorArm, name='det_arm')
#
#
#
#     # _real = ['motor_crystal_x',
#     #          'motor_crystal_y',
#     #          'motor_detector_y']
# # PseudoPositioner
#
# johann_spectrometer = JohannMultiCrystalSpectrometer(name='johann_spectrometer')

# class JohannMultiCrystalSpectrometer(PseudoPositioner, JohannMotorCollection):
#
#     energy = Cpt(PseudoSingle, name='emission_energy')
#
#     x0 = Cpt(EpicsMotor, '')
#     y0 = Cpt(EpicsMotor, '')
#     pitch0 = Cpt(EpicsMotor, '')
#     yaw0 = Cpt(EpicsMotor, '')
#
#     det_gon0






    # y_all = Cpt(EpicsMotor, '-Ax:P}Mtr')
    # x_all = Cpt(EpicsMotor, '-Ax:P}Mtr')
    # motor_crystal_x = auxxy.x
    # motor_crystal_y = auxxy.y
    # motor_detector_y = huber_stage.z
    # _real = ['x0', 'y0', 'pitch0', 'yaw0']
    #
    # # def __init__(self):
    # #





import h5py
class RIXSLogger:
    scanned_emission_energies = np.array([])
    normalized_points = np.array([])
    herfd_list = []

    def __init__(self, filepath, resume_flag=False):
        self.filepath = filepath
        if resume_flag:
            self._find_scanned_emission_energies()
        else:
            try:
                f = h5py.File(self.filepath, 'w-')
                f.close()
            except OSError:
                raise OSError('rixs log file with this name already exists')



    def _find_scanned_emission_energies(self):
        f = h5py.File(self.filepath, 'r')
        self.herfd_list = list(f.keys())
        for uid in self.herfd_list:
            ee = f[f'{uid}/emission_energy'][()]
            # self.scanned_emission_energies.append(ee)
            self.scanned_emission_energies = np.append(self.scanned_emission_energies, ee)
            # print(ee)
            if 'uid_norm' in f[f'{uid}'].keys():
                # self.normalized_points.append(True)
                self.normalized_points = np.append(self.normalized_points, True)
            else:
                self.normalized_points = np.append(self.normalized_points, False)
        f.close()
        self.scanned_emission_energies = np.array(self.scanned_emission_energies)
        self.normalized_points = np.array(self.normalized_points)

    def energy_was_measured(self, emission_energy, threshold=1e-3):
        if len(self.scanned_emission_energies) == 0:
            return False
        d = np.min(np.abs(self.scanned_emission_energies - emission_energy))
        return d < threshold

    def point_was_normalized(self, herfd_uid_to_check):
        for i, herfd_uid in enumerate(self.herfd_list):
            if herfd_uid_to_check == herfd_uid:
                return self.normalized_points[i]
        return

    def set_point_as_normalized(self, herfd_uid_to_check):
        for i, herfd_uid in enumerate(self.herfd_list):
            if herfd_uid_to_check == herfd_uid:
                self.normalized_points[i] = True

    def write_uid_herfd(self, uid_herfd, emission_energy):
        f = h5py.File(self.filepath, 'r+')
        f.create_group(uid_herfd)
        f[uid_herfd]['emission_energy'] = emission_energy
        f.close()
        self.herfd_list.append(uid_herfd)
        self.scanned_emission_energies = np.array(self.scanned_emission_energies.tolist() + [emission_energy])
        self.normalized_points = np.array(self.normalized_points.tolist() + [False])

    def write_herfd_pos(self, uid_herfd, x_nom, y_nom, z_nom, x_act, y_act, z_act):
        f = h5py.File(self.filepath, 'r+')
        f[uid_herfd]['x_nom'] = x_nom
        f[uid_herfd]['y_nom'] = y_nom
        f[uid_herfd]['z_nom'] = z_nom
        f[uid_herfd]['x_act'] = x_act
        f[uid_herfd]['y_act'] = y_act
        f[uid_herfd]['z_act'] = z_act
        f.close()

    def write_uid_norm(self, uid_herfd, uid_norm, energy_in_norm, energy_out_norm,
                       x_norm_nom, y_norm_nom, z_norm_nom,
                       x_norm_act, y_norm_act, z_norm_act):
        f = h5py.File(self.filepath, 'r+')
        f[uid_herfd]['uid_norm'] = uid_norm
        f[uid_herfd]['x_norm_nom'] = x_norm_nom
        f[uid_herfd]['y_norm_nom'] = y_norm_nom
        f[uid_herfd]['z_norm_nom'] = z_norm_nom
        f[uid_herfd]['x_norm_act'] = x_norm_act
        f[uid_herfd]['y_norm_act'] = y_norm_act
        f[uid_herfd]['z_norm_act'] = z_norm_act
        f[uid_herfd]['energy_in_norm'] = energy_in_norm
        f[uid_herfd]['energy_out_norm'] = energy_out_norm
        f.close()
        self.set_point_as_normalized(uid_herfd)






def function_for_measuing_samples():
    sample_1_x, sample_1_y, sample_1_z = -25.586,  1.613, -20.301
    sample_2_x, sample_2_y, sample_2_z = -25.741,-15.287, -20.401
    sample_3_x, sample_3_y, sample_3_z = -25.146, -29.887, -21.301
    RE(move_sample(sample_1_x, sample_1_y, sample_1_z))
    xlive_gui.widget_run.parameter_values[0].setText(f'FeTiO3 HERFD')
    xlive_gui.widget_run.run_scan()
    for i in range(3):
        RE(move_sample(sample_2_x, sample_2_y, sample_2_z))
        xlive_gui.widget_run.parameter_values[0].setText(f'LiTi2O3 HERFD')
        xlive_gui.widget_run.run_scan()

        RE(move_sample(sample_3_x, sample_3_y, sample_3_z))
        xlive_gui.widget_run.parameter_values[0].setText(f'CaTiO3 HERFD')
        xlive_gui.widget_run.run_scan()



def rixs_scan_plan(energies_in, energies_out):
    for energy_in in energies_in:
        yield from bps.mv(hhm.energy, energy_in)
        yield from emission_scan_plan(energies_out)


###########
def rixs_scan_RE(energies_out):
    for energy_out in energies_out:

        widget_run.run_scan()




###########


def move_sample(x, y, z):
    yield from bps.mv(giantxy.x, x)
    yield from bps.mv(giantxy.y, y)
    yield from bps.mv(usermotor2.pos, z)

# def move_sample_back(dx, dy, dz):
#     sdsdfsd
#     yield from bps.mv(giantxy.x, -dx)
#     yield from bps.mv(giantxy.y, -dy)
#     yield from bps.mvr(usermotor2.pos, -dz)


def get_snake_trajectory(x, y, step=0.2):
    x0 = giantxy.x.user_readback.get()
    y0 = giantxy.y.user_readback.get()
    z0 = usermotor2.pos.user_readback.get()

    _dxs = np.arange(0, x+step, step) / np.cos(np.deg2rad(30))
    _dys = np.arange(0, y+step, step)
    _dzs = -_dxs/np.cos(np.deg2rad(30))
    position_list = []
    for dx, dz in zip(_dxs, _dzs):
        for dy in _dys:
            position_list.append([x0 + dx, y0+dy, z0+dz])
    return position_list


#positions = get_snake_trajectory(3, 3, 0.2)
# widget_run = xlive_gui.widget_run

def rixs_scan_from_mara_at_each_new_point(energies_out, positions, energies_kbeta):
    filename = f'/nsls2/xf08id/users/2021/1/308190/rixs_Co3MnO4_uids_{new_uid()[:6]}.txt'
    print(f'Uids will be stored under  {filename}')
    for energy_out, position in zip(energies_out, positions):
        print(f'Emission energy {energy_out}' )
        print('Starting Move Energy...')
        RE(move_emission_energy_plan(energy_out))
        print('Move Energy Complete')
        print('Starting Move Sample...')
        RE(move_sample(*position))
        print('Move Sample Complete')
        print('Starting HERFD Scan...')
        widget_run.run_scan()
        print('HERFD Scan complete...')
        uid_herfd = db[-1].start['uid']


        while np.abs(hhm.energy.user_readback.get() - 8000) > 1:
            try:
                print('attempting to move energy to 8000')
                RE(bps.mv(hhm.energy, 8000, timeout=30))
            except:
                print('the motion timed out. Stopping the motor.')
                hhm.energy.stop()

        print('Starting Emission Scan...')
        uid_xes = RE(emission_scan_plan(energies_kbeta))
        print('Emission Scan complete...')
        with open(filename, "a") as text_file:
            text_file.write(ttime.ctime() + ' ' + uid_herfd + ' ' + uid_xes[0] + '\n')

#rixs_scan_from_mara_at_each_new_point(energies_emission,
#                                      positions[:energies_emission.size],
#                                      energies_kbeta)

# start_position_idx = 21
# for i in range(4):
#    idx1 = i*energies_emission.size + start_position_idx
#    idx2 = (i+1) * energies_emission.size + start_position_idx
#    print(idx1, idx2)
#    rixs_scan_from_mara_at_each_new_point(energies_emission, positions_co3mno4[idx1:idx2], energies_kbeta)
#    print(f'last position used was {idx2}')

#positions_co3mno4[0] = [-26.502437515, -29.168950962, -23.0959375]
#positions_co3mno4 = get_snake_trajectory(3.5, 4, 0.15)




def herfd_scan_in_pieces_plan(energies_herfd, positions, pos_start_index, n=4, exp_time=0.5):
    idx_e = np.round(np.linspace(0, energies_herfd.size-1, n+1))
    for i in range(idx_e.size-1):
        idx1 = int( np.max([idx_e[i]-1, 0]) )
        idx2 = int( np.min([idx_e[i+1]+1, energies_herfd.size-1]) )
        print(f'the scan will be performed between {energies_herfd[idx1]} and {energies_herfd[idx2]}')
        energy_steps = energies_herfd[idx1:idx2]
        time_steps = np.ones(energy_steps.shape) * exp_time
        yield from move_sample(*positions[pos_start_index+i])
        partial_herfd_plan = step_scan_plan('Co3MnO4 long HERFD scan',
                                            '',
                                            energy_steps, time_steps, [pil100k, apb_ave], element='Co', e0=7709, edge='K')
        yield from shutter.open_plan()
        yield from partial_herfd_plan
        yield from shutter.close_plan()





# energies_herfd = db['5bcffa42-fa10-48cb-a8ea-f77172456976'].table()['hhm_energy'].values
# this_herfd_plan = herfd_scan_in_pieces_plan(energies_herfd, positions, 21, n=4, exp_time=1)
# RE(this_herfd_plan)



# energies_calibration = np.array([7625,7650,7675,7700,7725])
# uids = RE(calibration_scan_plan(energies_calibration))
#EC = analyze_many_elastic_scans(db, uids, energies_calibration, plotting=True)








# def test():
#     eem = define_spectrometer_motor('Ge', [4,4,4])
#     print(eem._get_postion_for_energy(7649))
#     print(eem._get_postion_for_energy(7639))
#     print(eem._get_postion_for_energy(7629))

#
# test()

######


# spectrometer_calibration_dict = {}

# Energy      CrX         CrY         DetY
# 7649.2     -129.570     16.285       331.731
# 7639.2     -132.144

def move_to_7649():
    yield from bps.mv(auxxy.x,-129.570 )
    yield from bps.mv(auxxy.y, 16.285)
    yield from bps.mv(huber_stage.z,331.731)
    yield from bps.mv(hhm.energy,7649.2)

#######
def define_energy_range():
    # for CoO
   # energies_kbeta = np.linspace(7625, 7665, 41)
   # energies_emission = np.arange(7641, 7659+0.25, 0.25)
    # for Co4O
    energies_kbeta = np.linspace(7649, 7650, 2)
    energies_emission = np.arange(7627, 7659+0.25, 0.25)
    return energies_kbeta, energies_emission



# energies_vtc_cubanes = np.hstack((np.arange(7670, 7684+2, 2),
#                                   np.arange(7685, 7712+0.5, 0.5),
#                                   np.arange(7714, 7725+2, 2)))[::-1]
def scan_vtc_plan(energies_vtc, positions, start_index):
    idx = start_index + 0

    while True:
        print(f'moving to sample index {idx} at {positions[idx]}')
        yield from move_sample(*positions[idx])
        yield from emission_scan_plan(energies_vtc)
        idx += 1





# energies_vtc_cubanes = np.arange(7670, 7725+0.25, 0.25)
# energies_vtc_cubanes = np.hstack((np.arange(7670, 7684+2, 2), np.arange(7685, 7712+0.5, 0.5), np.arange(7714, 7725+2, 2)))
# RE(move_to_7649())
# eem_calculator = define_spectrometer_motor('Ge', [4, 4, 4])
# energies_kbeta, energies_emission = define_energy_range()
# RE(move_sample(*[-24.7386537495, -15.568973257, -22.495625]))
# positions = get_snake_trajectory(2.5, 4.2, 0.15)
# widget_run = xlive_gui.widget_run
#energies_kbeta_fine = np.linspace(7625, 7665, 51)

