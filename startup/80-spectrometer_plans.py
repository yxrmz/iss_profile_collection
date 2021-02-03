from xas.spectrometer import Crystal, analyze_many_elastic_scans
import copy


# from ophyd import (PseudoPositioner, PseudoSingle)
# from ophyd import (Component as Cpt)
#
# class SpectrometerEnergy(PseudoPositioner):
#     # pseudo motor
#     energy = Cpt(PseudoSingle)
#
#     # real motors
#     crystal_x = auxxy.x
#     crystal_y = auxxy.y
#     det_y0 = huber_stage.z




class EmissionEnergyMotor:

    def __init__(self, energy0, cr_x0, cr_y0, det_y0, kind, hkl):
        self.energy0 = energy0
        self.cr_x0 = cr_x0
        self.cr_y0 = cr_y0
        self.det_y0 = det_y0

        self.crystal = Crystal(1000, 50, hkl, kind)
        self.crystal.place_E(energy0)
        self.cr_x0_nom = copy.copy(self.crystal.x)
        self.cry_0_nom = copy.copy(self.crystal.y)
        self.det_y0_nom = copy.copy(self.crystal.d_y)


    def _get_postion_for_energy(self, energy):

        # print(self.cr_x0_nom, self.crystal.x)
        self.crystal.place_E(energy)
        # print(self.cr_x0_nom, self.crystal.x)
        dcr_x = self.crystal.x - self.cr_x0_nom
        dcr_y = self.crystal.y - self.cry_0_nom
        ddet_y = self.crystal.d_y - self.det_y0_nom
        return (self.cr_x0 - dcr_x), (self.cr_y0 + dcr_y), (self.det_y0 - ddet_y)

    def get_positions_for_energies(self, energy_list):
        crystal_x_list = []
        crystal_y_list = []
        detector_y_list = []
        for energy in energy_list:
            crystal_x, crystal_y, detector_y = self._get_postion_for_energy(energy)
            crystal_x_list.append(crystal_x)
            crystal_y_list.append(crystal_y)
            detector_y_list.append(detector_y)
        return crystal_x_list, crystal_y_list, detector_y_list


def define_spectrometer_motor(kind, hkl):
    energy = hhm.energy.user_readback.get()
    cr_x0 = auxxy.x.user_readback.get()
    cr_y0 = auxxy.y.user_readback.get()
    det_y0 = huber_stage.z.user_readback.get()
    eem = EmissionEnergyMotor(energy, cr_x0, cr_y0, det_y0, kind, hkl)
    return eem

# eem_calculator = define_spectrometer_motor('Ge', [4, 4, 4])


def move_emission_energy_plan(energy):
    cr_x, cr_y, det_y = eem_calculator._get_postion_for_energy(energy)
    # print(cr_x, cr_y, det_y)

    yield from bps.mv(auxxy.x, cr_x)
    yield from bps.mv(auxxy.y, cr_y)
    yield from bps.mv(huber_stage.z, det_y)


# energies = np.linspace(7625, 7730, npt)
#RE(emission_scan_plan(energies))

def emission_scan_plan(energies):
    crystal_x_list, crystal_y_list, detector_y_list = eem_calculator.get_positions_for_energies(energies)
    plan = bp.list_scan([pil100k, apb_ave],
                            auxxy.x, crystal_x_list,
                            auxxy.y, crystal_y_list,
                            huber_stage.z, detector_y_list, md={'plan_name' : 'johann_emission_scan'})
    yield from move_emission_energy_plan(energies[0])
    yield from shutter.open_plan()
    uid = (yield from plan)
    yield from shutter.close_plan()
    # return energies

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

start_position_idx = 21
for i in range(4):
   idx1 = i*energies_emission.size + start_position_idx
   idx2 = (i+1) * energies_emission.size + start_position_idx
   print(idx1, idx2)
   rixs_scan_from_mara_at_each_new_point(energies_emission, positions_co3mno4[idx1:idx2], energies_kbeta)
   print(f'last position used was {idx2}')

#positions_co3mno4[0] = [-26.502437515, -29.168950962, -23.0959375]
#positions_co3mno4 = get_snake_trajectory(3.5, 4, 0.15)



def elastic_scan_plan(DE=5, dE=0.1):
    npt = np.round(DE/dE + 1)
    name = 'elastic spectrometer scan'
    plan = bp.relative_scan([pil100k, apb_ave], hhm.energy, -DE/2, DE/2, npt, md={'plan_name': 'elastic_scan ' + motor.name, 'name' : name})
    yield from plan


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





energies_herfd = db['5bcffa42-fa10-48cb-a8ea-f77172456976'].table()['hhm_energy'].values
this_herfd_plan = herfd_scan_in_pieces_plan(energies_herfd, positions, 21, n=4, exp_time=1)
RE(this_herfd_plan)

def calibration_scan_plan(energies):
    # uids = []
    for energy in energies:
        yield from bps.mv(hhm.energy, energy)
        yield from move_emission_energy_plan(energy)
        yield from elastic_scan_plan()
        # uid = (yield from elastic_scan_plan())
    #     if type(uid) == tuple:
    #         uid = uid[0]
    #     uids.append(uid)
    #
    # energy_converter = analyze_many_elastic_scans(db, uids, energies, plotting=True)
    # return energy_converter


# energies_calibration = np.array([7625,7650,7675,7700,7725])
# uids = RE(calibration_scan_plan(energies_calibration))
#EC = analyze_many_elastic_scans(db, uids, energies_calibration, plotting=True)



def plot_radiation_damage_scan_data(db, uid):
    t = db[uid].table()
    plt.figure()
    plt.plot(t['time'], t['pil100k_stats1_total']/np.abs(t['apb_ave_ch1_mean']))


def n_exposures_plan(n):
    yield from shutter.open_plan()
    yield from bp.count([pil100k, apb_ave], n)
    yield from shutter.close_plan()


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



energies_vtc_cubanes = np.hstack((np.arange(7670, 7684+2, 2),
                                  np.arange(7685, 7712+0.5, 0.5),
                                  np.arange(7714, 7725+2, 2)))[::-1]
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

