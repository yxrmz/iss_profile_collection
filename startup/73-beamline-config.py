from xas.trajectory import TrajectoryCreator



def tabulate_hhmy_position_plan(stdout=sys.stdout):
    _energies = [13000, 15000, 17500, 20000, 22500, 25000, 27500, 30000]  # np.arange(5000, 11000, 1000)
    data_df = pd.DataFrame(columns=['energy', 'hhmy', 'hhrmy', 'uid'])

    for energy in _energies:
        # enable_fb_in_the_end = energy>13000

        yield from optimize_beamline_plan(energy, tune_elements=tune_elements_ext, force_prepare=True, enable_fb_in_the_end=False)
        uid = db[-3].start['uid']
        data_df = data_df.append({'energy' : energy,
                                  'hhmy' : hhm.y.user_readback.get(),
                                  'hhrmy' : hhrm.y.user_readback.get(),
                                  'uid' : uid},
                                   ignore_index=True)
        data_df.to_json('/nsls2/xf08id/Sandbox/Beamline_components/2021_09_09_beamline_tabulation/beamline_hhmy_hhrmy_tabulation_high_energies.json')





def gen_trajectory(element, edge):
    trajectory_creator = TrajectoryCreator(servocycle=hhm.servocycle, pulses_per_deg=hhm.pulses_per_deg)
    E0 = xraydb.xray_edge(element, edge).energy

    trajectory_creator.define(edge_energy=E0,
                              dsine_preedge_duration=4,
                              dsine_edge_duration=6,
                              dsine_postedge_duration=20,
                              dsine_preedge_frac=0.5,
                              dsine_postedge_frac=0.3,
                              trajectory_type='Double Sine/Constant Edge',
                              pad_time=0.5)
    trajectory_creator.elem = f'{element}'
    trajectory_creator.edge = f'{edge}'
    trajectory_creator.e0 = E0
    trajectory_creator.interpolate()
    trajectory_creator.revert()
    trajectory_creator.tile(reps=1,
                            single_direction=True)
    trajectory_creator.e2encoder(hhm.angle_offset.value)
    filename = f'{element}-{edge}.txt'
    filepath = trajectory_manager.trajectory_path + filename
    np.savetxt(filepath,
               trajectory_creator.energy_grid, fmt='%.6f',
               header=f'element: {trajectory_creator.elem}, edge: {trajectory_creator.edge}, E0: {trajectory_creator.e0}')  # , scan_direction: {self.traj_creator.direction}')
    trajectory_manager.load(filename, 1, is_energy=True, offset=hhm.angle_offset.value)
    trajectory_manager.init(1)



class BeamlineConfig:

    def __init__(self):
        self.filepath = '/nsls2/xf08id/Sandbox/Beamline_components/beamline_config/config.json'
        try:
            self.data = pd.read_json(self.filepath)
        except:
            self.data = pd.DataFrame(columns=['timestamp', 'energy', 'hhm_pitch', 'hhm_y', 'hhrm_y',
                                              'hhm_angle_offset', 'hhm_fb_center', 'hhm_fb_line'])


    def save_current_config(self):

        timestamp = ttime.ctime()
        energy = hhm.energy.position
        hhm_pitch = hhm.pitch.position
        hhm_y =hhm.y.position
        hhrm_y = hhrm.y.position
        hhm_angle_offset = hhm.angle_offset.value
        hhm_fb_center = hhm.fb_center.value
        hhm_fb_line = hhm.fb_line.value


        self.data = self.data.append({'timestamp' : timestamp,
                                      'energy' : energy,
                                      'hhm_pitch' : hhm_pitch,
                                      'hhm_y' : hhm_y,
                                      'hhrm_y' : hhrm_y,
                                      'hhm_angle_offset' : hhm_angle_offset,
                                      'hhm_fb_center' : hhm_fb_center,
                                      'hhm_fb_line' : hhm_fb_line},
                                      ignore_index=True)

        self.data.to_json(self.filepath)

beamline_config = BeamlineConfig()



def prepare_tune_calibrate_plan(element, edge):
    if validate_element_edge_in_db_proc(element):
        energy = xraydb.xray_edge(element, edge).energy

        yield from optimize_beamline_plan(energy, tune_elements=tune_elements, force_prepare=True,
                                          enable_fb_in_the_end=True)

        gen_trajectory(element, edge)

        # yield from adjust_ic_gains()
        # yield from adjust_ic_gains()
        yield from calibrate_energy_plan(element, edge, dE=35, plot_fun=None)
        yield from bps.mv(hhm.energy, energy)
        beamline_config.save_current_config()
    else:
        pass

# foil_list = [('Ti', 'K'),
#              ('V' , 'K'),
#              ('Cr', 'K'),
#              ('Mn', 'K'),
#              ('Fe', 'K'),
#              ('Co', 'K'),
#              ('Ni', 'K'),
#              ('Cu', 'K'),
#              ('Zn', 'K'),
#              ('Ta', 'L3'),
#              ('Re', 'L3'),
#              ('Ir', 'L3'),
#              ('Pt', 'L3'),
#              ('Au', 'L3'),
#              ('Pb', 'L3'),
#              ('Se', 'K'),
#              ('Zr', 'K'),
#              ('Nb', 'K'),
#              ('Mo', 'K'),
#              ('Ru', 'K'),
#              ('Rh', 'K'),
#              ('Pd', 'K'),
#              ('Ag', 'K'),
#              ('Cd', 'K'),
#              ('In', 'K'),
#              ('Sn', 'K')]


def go_over_foils(_foil_list):
    for foil in _foil_list:
        element, edge = foil
        yield from prepare_tune_calibrate_plan(element, edge)

foil_list = [('Cr', 'K'),
             ('Mn', 'K'),
             ('Fe', 'K'),
             ('Co', 'K'),
             ('Ni', 'K'),
             ('Cu', 'K'),
             ('Zn', 'K'),
             ('Ta', 'L3'),
             ('Pt', 'L3'),
             ('Au', 'L3'),
             ('Zr', 'K'),
             ('Nb', 'K'),
             ('Mo', 'K'),
             # ('Rh', 'K'),
             # ('Pd', 'K'),
             # ('Ag', 'K'),
             # ('Cd', 'K'),
             # ('Sn', 'K'),
            ]

# foil_list = [('Ni', 'K')]
# RE(go_over_foils(foil_list))

