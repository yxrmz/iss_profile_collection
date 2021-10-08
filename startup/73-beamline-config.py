from xas.trajectory import TrajectoryCreator


def gen_trajectory(element, edge):
    trajectory_creator = TrajectoryCreator(servocycle=hhm.servocycle, pulses_per_deg=hhm.pulses_per_deg)
    E0 = xraydb.xray_edge(element, edge).energy

    trajectory_creator.define(edge_energy=E0,
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
    filename = trajectory_manager.trajectory_path + 'test_traj.txt'
    np.savetxt(filename,
               trajectory_creator.energy_grid, fmt='%.6f',
               header=f'element: {trajectory_creator.elem}, edge: {trajectory_creator.edge}, E0: {trajectory_creator.e0}')  # , scan_direction: {self.traj_creator.direction}')



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








def prepare_tune_calibrate_plan(element, edge):
    energy = xraydb.xray_edge(element, edge).energy

    yield from optimize_beamline_plan(energy, tune_elements=tune_elements, force_prepare=True,
                                      enable_fb_in_the_end=False)


    yield from calibrate_energy_plan(element, edge, dE=35, plot_fun=None)



class BeamlineConfig:

    def __iter__(self):
        self.filepath = ''
        self.data = pd.DataFrame(columns=['timestamp', 'energy', 'hhm_pitch', 'hhm_y', 'hhrm_y', 'hhm_angle_offset'])



        pass

    def save_current_config(self):
        timestamp = ttime.ctime()
        energy = hhm.energy.position
        hhm_pitch = hhm.pitch.position
        hhm_y =hhm.y.position
        hhrm_y = hhrm.y.position
        hhm_angle_offset = hhm.angle_offset.position

        self.data = self.data.append({'energy': energy,
                                      'hhmy': hhm.y.user_readback.get(),
                                      'hhrmy': hhrm.y.user_readback.get(),
                                      'uid': uid},
                                      ignore_index=True)
