print(ttime.ctime() + ' >>>> ' + __file__)
def elastic_scan_plan(DE=5, dE=0.1):
    npt = np.round(DE/dE + 1)
    name = 'elastic spectrometer scan'
    plan = bp.relative_scan([pil100k, apb_ave], hhm.energy, -DE/2, DE/2, npt, md={'plan_name': 'elastic_scan ' + motor.name, 'name' : name})
    yield from plan


def johann_calibration_scan_plan(energies=None, DE=5, dE=0.1):
    for energy in energies:
        yield from bps.mv(hhm.energy, energy)
        # yield from move_emission_energy_plan(energy)
        yield from bps.mv(johann_emission.energy, energy)
        yield from elastic_scan_plan(DE=DE, dE=dE)



def plot_radiation_damage_scan_data(db, uid):
    t = db[uid].table()
    plt.figure()
    plt.plot(t['time'], t['pil100k_stats1_total']/np.abs(t['apb_ave_ch1_mean']))



# def move_johann_spectrometer_energy(energy=-1):
#     current_energy = johann_emission.energy.position
#     energy = float(energy)
#     energy_arr = np.linspace(current_energy, energy, int(np.abs(energy - current_energy)/5) + 2)[1:]
#     for _energy in energy_arr:
#         print_to_gui(f'Moving spectrometer to {_energy}')
#         yield from bps.mv(johann_emission, _energy, wait=True)
#         # yield from move_motor_plan(motor_attr=johann_emission.energy.name, based_on='object_name', position=float(_energy))

def move_johann_spectrometer_energy(energy : float=-1):
    current_energy = johann_emission.energy.position
    energy = float(energy)

    current_bragg = rowland_circle.e2bragg(current_energy)
    bragg = rowland_circle.e2bragg(energy)

    bragg_arr = np.linspace(current_bragg, bragg, int(np.abs(bragg - current_bragg)/0.25) + 2)[1:]
    energy_arr = rowland_circle.bragg2e(bragg_arr)
    for _bragg, _energy in zip(bragg_arr, energy_arr):
        print_to_gui(f'Moving spectrometer to {_energy}')
        yield from bps.mv(johann_spectrometer, _bragg, wait=True)
        # yield from move_motor_plan(motor_attr=johann_emission.energy.name, based_on='object_name', position=float(_energy))


def prepare_johann_scan_plan(detectors, spectrometer_energy, spectrometer_config_uid):
    ensure_pilatus_is_in_detector_list(detectors)
    if spectrometer_config_uid is not None:
        johann_spectrometer_manager.set_config_by_uid(spectrometer_config_uid)
    yield from move_johann_spectrometer_energy(spectrometer_energy)
    # yield from bps.mv(johann_emission, spectrometer_energy)

def prepare_johann_metadata_and_kwargs(**kwargs):
    metadata = kwargs.pop('metadata')
    j_metadata = {'spectrometer': 'johann',
                  'spectrometer_config': rowland_circle.config,}
    if 'spectrometer_energy' in kwargs.keys():
        spectrometer_energy = kwargs.pop('spectrometer_energy')
        j_metadata['spectrometer_energy'] = spectrometer_energy
    if 'spectrometer_config_uid' in kwargs.keys():
        j_metadata['spectrometer_config_uid'] = kwargs.pop('spectrometer_config_uid')
    return {**j_metadata, **metadata}, kwargs


def collect_n_exposures_johann_plan(**kwargs):
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'], kwargs['spectrometer_config_uid'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    metadata['spectrometer_config']['scan_type'] = 'constant energy'
    yield from collect_n_exposures_plan(metadata=metadata, **kwargs)


def step_scan_johann_herfd_plan(**kwargs):
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'], kwargs['spectrometer_config_uid'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    metadata['spectrometer_config']['scan_type'] = 'constant energy'
    yield from step_scan_plan(metadata=metadata, **kwargs)

def fly_scan_johann_herfd_plan(**kwargs):
    # rixs_file_name = kwargs.pop('rixs_file_name')
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'], kwargs['spectrometer_config_uid'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    metadata['spectrometer_config']['scan_type'] = 'constant energy'
    yield from fly_scan_plan(metadata=metadata, **kwargs)


def get_johann_xes_step_scan_md(name, comment, detectors_dict, emission_energy_list, emission_time_list, element, e0, line, spectrometer_config_uid, metadata):
    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element
    md_general = get_scan_md(name, comment, detectors_dict, '.dat')

    md_scan = {'experiment': 'step_scan',
               'spectrometer': 'johann',
               'spectrometer_config': rowland_circle.config,
               'spectrometer_config_uid': spectrometer_config_uid,
               'spectrometer_energy_steps': emission_energy_list,
               'spectrometer_time_steps': emission_time_list,
               'element': element,
               'element_full': full_element_name,
               'line': line,
               'e0': e0,}
    return {**md_scan, **md_general, **metadata}

def step_scan_johann_xes_plan(name=None, comment=None, detectors=[],
                              mono_energy=None, mono_angle_offset=None,
                              emission_energy_list=None, emission_time_list=None,
                              element='', line='', e0=None,
                              spectrometer_config_uid=None,
                              metadata={}):

    default_detectors = [apb_ave, hhm_encoder]
    # default_detectors = []
    aux_detectors = get_detector_device_list(detectors, flying=False)
    all_detectors = default_detectors + aux_detectors
    detectors_dict = {k: {'device': v} for k, v in zip(detectors, aux_detectors)}

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    yield from bps.mv(hhm.energy, mono_energy)
    yield from prepare_johann_scan_plan(detectors, emission_energy_list[0], spectrometer_config_uid)

    md = get_johann_xes_step_scan_md(name, comment, detectors_dict, emission_energy_list, emission_time_list, element,
                                     e0, line, spectrometer_config_uid, metadata)
    yield from general_energy_step_scan(all_detectors, johann_emission, emission_energy_list, emission_time_list, md=md)



def deal_with_sample_coordinates_for_rixs(sample_coordinates, emission_energy_list, name):
    if type(sample_coordinates) == list:
        assert len(sample_coordinates) == len(emission_energy_list), 'number of positions on the sample must match the number of energy points on emission grid'
    else:
        sample_coordinates = [sample_coordinates] * len(emission_energy_list)

    if type(name) == list:
        assert len(name) == len(emission_energy_list), 'number of positions on the sample must match the number of energy points on emission grid'
    else:
        name = [name] * len(emission_energy_list)

    return sample_coordinates, name


def get_johann_rixs_md(name, element_line, line, e0_line, metadata):
    # metadata['rixs_file_name'] = create_interp_file_name(name, '.rixs')
    metadata['element_line'] = element_line
    metadata['line'] = line
    metadata['e0_line'] = e0_line
    return metadata


def johann_rixs_plan_bundle(plan_name, name=None, comment=None, detectors=[],
                            trajectory_filename=None, mono_angle_offset=None,
                            emission_energy_list=None, sample_coordinates=None,
                            element='', edge='', e0=None, element_line='', line='', e0_line=None,
                            rixs_kwargs={}, spectrometer_config_uid=None, metadata={}):
    sample_coordinates, names = deal_with_sample_coordinates_for_rixs(sample_coordinates, emission_energy_list, name)
    metadata = get_johann_rixs_md(name, element_line, line, e0_line, metadata)
    plans = []
    for emission_energy, sample_position, name in zip(emission_energy_list, sample_coordinates, names):

        if sample_position is not None:
            plans.append({'plan_name': 'move_sample_stage_plan',
                          'plan_kwargs': {'sample_coordinates': sample_position}})

        plans.append({'plan_name': plan_name,
                      'plan_kwargs': {'name': f'{name} {emission_energy:0.2f}',
                                      'comment': comment,
                                      'detectors': detectors,
                                      'trajectory_filename': trajectory_filename,
                                      'element': element,
                                      'edge': edge,
                                      'e0': e0,
                                      'spectrometer_energy': emission_energy,
                                      'spectrometer_config_uid': spectrometer_config_uid,
                                      'mono_angle_offset': mono_angle_offset,
                                      'metadata': metadata}})
        # deal with rixs_kwargs
    return plans

def fly_scan_johann_rixs_plan_bundle(**kwargs):
    return johann_rixs_plan_bundle('fly_scan_johann_herfd_plan', **kwargs)

def step_scan_johann_rixs_plan_bundle(**kwargs):
    return johann_rixs_plan_bundle('step_scan_johann_herfd_plan', **kwargs)


from xas.spectrometer import analyze_elastic_fly_scan

def obtain_spectrometer_resolution_plan(rois=None, plot_func=None, liveplot_kwargs=None, attempts=5, sleep=5, alignment_data=None):
    for i in range(attempts):
        try:
            print_to_gui(f'Analyzing resolution scan: attempt {i+1}', tag='Spectrometer', add_timestamp=True)
            fwhm = analyze_elastic_fly_scan(db, -1, rois=rois, plot_func=plot_func)
            if alignment_data is not None:
                start = db[-1].start
                uid = start.uid
                _dict = {'uid': uid,
                         'fwhm': fwhm,
                         'tweak_motor_description': start['tweak_motor_description'],
                         'tweak_motor_position': start['tweak_motor_position']}
                alignment_data.append(_dict)
            yield from bps.null()
            break
        except Exception as e:
            yield from bps.sleep(sleep)



def johann_resolution_scan_plan_bundle(e_cen=8000.0, e_width=10.0, e_velocity=2.0, rois=None, motor_info='', plan_gui_services=None, liveplot_kwargs=None, md=None, alignment_data=None):
    plans = []
    trajectory_filename = scan_manager.quick_linear_trajectory_filename(e_cen, e_width, e_velocity)
    if md is None: md = {}

    name = f'Resolution scan {e_cen} {motor_info}'
    scan_kwargs = {'name': name, 'comment': '',
                   'trajectory_filename': trajectory_filename,
                   'detectors': ['Pilatus 100k'],
                   'element': '', 'e0': e_cen, 'edge': '',
                   'metadata': md}

    plans.append({'plan_name': 'fly_scan_plan',
                  'plan_kwargs': {**scan_kwargs}})
    plans.append({'plan_name': 'obtain_spectrometer_resolution_plan',
                  'plan_kwargs': {'rois' : rois, 'liveplot_kwargs': liveplot_kwargs, 'alignment_data': alignment_data},
                  'plan_gui_services': plan_gui_services})

    return plans



def quick_crystal_motor_scan(motor_description=None, scan_range=None, velocity=None, pil100k_exosure_time=0.1, plot_func=None, liveplot_kwargs=None, md=None):
    motor_device = get_motor_device(motor_description, based_on='description')
    detectors = [apb.ch1, pil100k.stats1.total, pil100k.stats2.total, pil100k.stats3.total, pil100k.stats4.total, ]

    print_to_gui(f'Quick scanning motor {motor_description}', tag='Spectrometer')

    num_images = (scan_range / velocity  + 1) / pil100k_exosure_time
    print(num_images)
    pil100k_init_exposure_time = pil100k.cam.acquire_period.get()
    pil100k_init_num_images = pil100k.cam.num_images.get()
    pil100k_init_image_mode = pil100k.cam.image_mode.get()

    pil100k.set_exposure_time(pil100k_exosure_time)
    pil100k.set_num_images(num_images)

    pil100k.cam.image_mode.set(1).wait()

    start_acquiring_plan = bps.mv(pil100k.cam.acquire, 1)
    yield from ramp_motor_scan(motor_device, detectors, scan_range, velocity=velocity, return_motor_to_initial_position=True, start_acquiring_plan=start_acquiring_plan, md=md)

    pil100k.set_exposure_time(pil100k_init_exposure_time)
    pil100k.set_num_images(pil100k_init_num_images)
    pil100k.cam.image_mode.set(pil100k_init_image_mode).wait()



# RE(quick_crystal_motor_scan(motor_description='Johann Main Crystal Roll',
#                            scan_range=800,
#                            velocity=25))

# def _estimate_width_of_the_peak
# from numpy.polynomial import Polynomial

from scipy.signal import savgol_filter
def estimate_center_and_width_of_peak(E, I):
    E_cen = E[np.argmax(np.abs(I))]
    e_low = E < E_cen
    e_high = E > E_cen
    x1 = np.interp(0.5, I[e_low], E[e_low])
    x2 = np.interp(0.5, I[e_high][np.argsort(I[e_high])], E[e_high][np.argsort(I[e_high])])
    fwhm = np.abs(x1 - x2)
    return E_cen, fwhm, x1, x2

def smooth_any_peak(x, y, n=4):
    y_fit = savgol_filter(y, 5, 3)
    return x, y, y_fit

def _estimate_peak_properties(x, y, plotting=False, fignum=None, clear=False):
    y_smooth = savgol_filter(y, 5, 3)
    # y_smooth_bkg = np.mean(y_smooth[y_smooth<=np.percentile(y_smooth[1:-1], 3 / y.size * 100)])
    # y_smooth_bkg = np.mean(y_smooth[5:20])
    y_smooth_bkg = np.mean(y_smooth[:3])
    # y_smooth_max = y_smooth.max()
    y_smooth_max = np.mean(np.sort(y_smooth)[-3:])
    y_smooth = (y_smooth - y_smooth_bkg) / (y_smooth_max - y_smooth_bkg)
    x_cen, x_fwhm, x1, x2 = estimate_center_and_width_of_peak(x, y_smooth)
    x_com = np.sum(x * y_smooth) / np.sum(y_smooth)
    x_mask = (x >= x1) & (x <= x2)
    y12_int = np.trapz(y_smooth[x_mask], x[x_mask])
    if plotting:
        plt.figure(fignum, clear=clear)
        plt.plot(x - x_com, (y - y_smooth_bkg) / (y_smooth_max - y_smooth_bkg), 'k.')
        plotted_lines = plt.plot(x - x_com, y_smooth, '-')
        color = plotted_lines[0].get_color()
        plt.vlines([x1 - x_com, x2 - x_com], 0, 1, colors=color)
        plt.hlines([0.5], x1 - x_com, x2 - x_com, colors=color)
    return x_cen, x_fwhm, x1, x2, y12_int

def _estimate_peak_fwhm(x, y, **kwargs):
    _, x_fwhm, _, _, y12_int = _estimate_peak_properties(x, y, **kwargs)
    return x_fwhm, y12_int

def _estimate_peak_fwhm_from_roll_scan(df, x_col, y_col, **kwargs):
    x = df[x_col].values
    y = df[y_col].values
    return _estimate_peak_fwhm(x, y, **kwargs)

# _estimate_peak_fwhm_from_roll_scan(t, 'johann_main_crystal_motor_cr_main_roll', 'pil100k_stats1_total', plotting=True, clear=True)

def estimate_peak_fwhm_from_roll_scan(db, uid, x_col='johann_main_crystal_motor_cr_main_roll', y_col='pil100k_stats1_total', **kwargs):
    df = process_monitor_scan(db, uid, det_for_time_base='pil100k')
    df = df[3 : df.shape[0]-3]
    return _estimate_peak_fwhm_from_roll_scan(df, x_col, y_col, **kwargs)[0]

def estimate_peak_intensity_from_roll_scan(db, uid, x_col='johann_main_crystal_motor_cr_main_roll', y_col='pil100k_stats1_total', **kwargs):
    df = process_monitor_scan(db, uid, det_for_time_base='pil100k')
    df = df[3 : df.shape[0]-3]
    return _estimate_peak_fwhm_from_roll_scan(df, x_col, y_col, **kwargs)[1]

def plot_roll_scan(db, uid, x_col='johann_main_crystal_motor_cr_main_roll', y_col='pil100k_stats1_total', **kwargs):
    df = process_monitor_scan(db, uid, det_for_time_base='pil100k')
    df = df[3 : df.shape[0]-3]
    plt.plot(df[x_col], df[y_col])



# RE(general_scan(detectors=['Pilatus 100k'], motor='Johann Main Crystal Roll',
#              rel_start=-400, rel_stop=400, num_steps=81, exposure_time=0.1, liveplot_kwargs={}))

# _estimate_peak_fwhm_from_roll_scan(db[-1].table(), 'johann_main_crystal_motor_cr_main_roll', 'pil100k_stats1_total', plotting=True)

def run_alignment_scans_for_crystal(motor=None, rel_start=None, rel_stop=None, num_steps=None, exposure_time=None,
                                    tweak_motor=None, tweak_motor_rel_start=None, tweak_motor_rel_stop=None, tweak_motor_num_steps=None):
    tweak_motor_pos = tweak_motor.position + np.linspace(tweak_motor_rel_start, tweak_motor_rel_stop, tweak_motor_num_steps)
    uids = []
    for i, _pos in enumerate(tweak_motor_pos):
        print_to_gui(f'Aligning motor {tweak_motor.name} (step {i + 1}, position={_pos})', add_timestamp=True, tag='Spectrometer')
        yield from bps.mv(tweak_motor, _pos)
        md = {tweak_motor.name: tweak_motor.position}
        # print_to_gui(f'motor {motor} position before scanning {johann_main_crystal.motor_cr_main_roll.position}', add_timestamp=True,
        #              tag='Spectrometer')
        uid = yield from general_scan(detectors=['Pilatus 100k'], motor=motor, rel_start=rel_start, rel_stop=rel_stop, num_steps=num_steps, exposure_time=exposure_time, liveplot_kwargs={}, md=md)
        uids.append(uid)

    return uids


def run_quick_alignment_scan_for_crystal_at_tweak_pos(motor_description=None, scan_range=None, velocity=None,
                                    tweak_motor=None, tweak_motor_pos=None):
    yield from bps.mv(tweak_motor, tweak_motor_pos)
    md = {tweak_motor.name: tweak_motor.position}
    return (yield from quick_crystal_motor_scan(motor_description=motor_description, scan_range=scan_range,
                                              velocity=velocity, md=md))


def run_quick_alignment_scans_for_crystal(motor_description=None, scan_range=None, velocity=None,
                                    tweak_motor=None, tweak_motor_rel_start=None, tweak_motor_rel_stop=None, tweak_motor_num_steps=None):
    tweak_motor_init_pos = tweak_motor.position
    tweak_motor_pos = tweak_motor_init_pos + np.linspace(tweak_motor_rel_start, tweak_motor_rel_stop, tweak_motor_num_steps)
    uids = []
    for i, _pos in enumerate(tweak_motor_pos):
        print_to_gui(f'Aligning motor {tweak_motor.name} (step {i + 1}, position={_pos})', add_timestamp=True,
                     tag='Spectrometer')
        uid = yield from run_quick_alignment_scan_for_crystal_at_tweak_pos(motor_description=motor_description, scan_range=scan_range, velocity=velocity,
                                                                           tweak_motor=tweak_motor, tweak_motor_pos=_pos)
        uids.append(uid)
    yield from bps.mv(tweak_motor, tweak_motor_init_pos)
    return uids



def bragg_scan_for_individual_crystals(rel_start=None, rel_stop=None, num_steps=None, exposure_time=None, yaw_offset=None):

    bragg_motors = ['Johann Main Crystal Bragg']

    uids = []
    for i, _pos in enumerate(tweak_motor_pos):
        print_to_gui(f'Aligning motor {tweak_motor.name} (step {i + 1}, position={_pos})', add_timestamp=True, tag='Spectrometer')
        yield from bps.mv(tweak_motor, _pos)
        md = {tweak_motor.name: tweak_motor.position}
        # print_to_gui(f'motor {motor} position before scanning {johann_main_crystal.motor_cr_main_roll.position}', add_timestamp=True,
        #              tag='Spectrometer')
    uid = yield from general_scan(detectors=['Pilatus 100k'], motor=motor, rel_start=rel_start, rel_stop=rel_stop, num_steps=num_steps, exposure_time=exposure_time, liveplot_kwargs={}, md=md)
    uids.append(uid)

    return uids



# RE(run_alignment_scans_for_crystal(motor='Johann Main Crystal Roll', rel_start=-400, rel_stop=400, num_steps=81, exposure_time=0.5,
#                                 tweak_motor=johann_spectrometer_x, tweak_motor_rel_start=-10, tweak_motor_rel_stop=10, tweak_motor_num_steps=3))
# RE(run_alignment_scans_for_crystal(motor='Johann Aux2 Crystal Roll', rel_start=-400, rel_stop=400, num_steps=81, exposure_time=0.5,
#                                 tweak_motor=johann_aux2_crystal.motor_cr_aux2_x, tweak_motor_rel_start=-10000, tweak_motor_rel_stop=10000, tweak_motor_num_steps=9))
# RE(run_alignment_scans_for_crystal(motor='Johann Aux3 Crystal Roll', rel_start=-400, rel_stop=400, num_steps=81, exposure_time=0.5,
#                                 tweak_motor=johann_aux3_crystal.motor_cr_aux3_x, tweak_motor_rel_start=-10000, tweak_motor_rel_stop=10000, tweak_motor_num_steps=3))

# RE(run_quick_alignment_scans_for_crystal(motor_description='Johann Main Crystal Roll', scan_range=800, velocity=25, tweak_motor=johann_spectrometer_x, tweak_motor_rel_start=-10, tweak_motor_rel_stop=10, tweak_motor_num_steps=9))
# RE(run_quick_alignment_scans_for_crystal(motor_description='Johann Aux2 Crystal Roll', scan_range=800, velocity=25, tweak_motor=johann_aux2_crystal.motor_cr_aux2_x, tweak_motor_rel_start=-10000, tweak_motor_rel_stop=10000, tweak_motor_num_steps=9))
# RE(run_quick_alignment_scans_for_crystal(motor_description='Johann Aux3 Crystal Roll', scan_range=800, velocity=25, tweak_motor=johann_aux3_crystal.motor_cr_aux3_x, tweak_motor_rel_start=-10000, tweak_motor_rel_stop=10000, tweak_motor_num_steps=11))


# RE(run_quick_alignment_scan_for_crystal_at_tweak_pos(motor_description='Johann Aux2 Crystal Roll', scan_range=800, velocity=25, tweak_motor=johann_aux2_crystal.motor_cr_aux2_x, tweak_motor_pos=12400))






_crystal_alignment_dict = {'main': {'roll': 'Johann Main Crystal Roll',
                                    'yaw':  'Johann Main Crystal Yaw',
                                    'x':    'Johann Crystal Assy X'},
                           'aux2': {'roll': 'Johann Aux2 Crystal Roll',
                                    'yaw':  'Johann Aux2 Crystal Yaw',
                                    'x':    'Johann Aux2 Crystal X'},
                           'aux3': {'roll': 'Johann Aux3 Crystal Roll',
                                    'yaw':  'Johann Aux3 Crystal Yaw',
                                    'x':    'Johann Aux3 Crystal X'},
                           'aux4': {'roll': 'Johann Aux4 Crystal Roll',
                                    'yaw':  'Johann Aux4 Crystal Yaw',
                                    'x':    'Johann Aux4 Crystal X'},
                           'aux5': {'roll': 'Johann Aux5 Crystal Roll',
                                    'yaw':  'Johann Aux5 Crystal Yaw',
                                    'x':    'Johann Aux5 Crystal X'}
                           }



def crystal_piezo_scan(crystal=None, axis=None, scan_range=None, step_size=None, exposure_time=0.5, plot_func=None, liveplot_kwargs=None, md=None):
    motor_description = _crystal_alignment_dict[crystal][axis]
    rel_start, rel_stop, num_steps = convert_range_to_start_stop(scan_range, step_size)
    yield from general_scan(detectors=['Pilatus 100k'], motor=motor_description, rel_start=rel_start, rel_stop=rel_stop,
                            num_steps=num_steps, exposure_time=exposure_time, liveplot_kwargs={}, md=md)

def johann_hhm_resolution_scan(scan_range=None, step_size=None, exposure_time=0.5, plot_func=None, liveplot_kwargs=None, md=None):
    motor_description = 'A Monochromator Energy'
    rel_start, rel_stop, num_steps = convert_range_to_start_stop(scan_range, step_size)
    yield from general_scan(detectors=['Pilatus 100k'], motor=motor_description, rel_start=rel_start, rel_stop=rel_stop,
                            num_steps=num_steps, exposure_time=exposure_time, liveplot_kwargs={}, md=md)

# RE(johann_hhm_resolution_scan(scan_range=10, step_size=0.5, exposure_time=0.5))

# RE(crystal_piezo_scan(crystal='main', axis='roll', scan_range=800, step_size=10, exposure_time=0.5, plot_func=None, liveplot_kwargs=None, md=None))
def crystal_piezo_tune(property='com', pil100k_roi_num=None, **kwargs):
    yield from crystal_piezo_scan(**kwargs)
    t = db[-1].table()

    motor_description = _crystal_alignment_dict[kwargs['crystal']][kwargs['axis']]
    motor_object = get_motor_device(motor_description, based_on='description')
    x = t[motor_object.name].values
    y = t[f'pil100k_stats{pil100k_roi_num}_total'].values

    if property == 'com':
        new_position = np.sum((y - y.min()) * x) / np.sum((y - y.min()))
    else:
        raise ValueError('not implemented')

    yield from move_motor_plan(motor_attr=motor_description, based_on='description', position=new_position)

# RE(crystal_piezo_tune(property='com', roi_num=1, crystal='main', axis='yaw', rel_start=-400, rel_stop=400, num_steps=25, exposure_time=0.5, plot_func=None, liveplot_kwargs=None, md=None))

def estimate_peak_fwhm_from_roll_scan(uid, crystal, pil100k_roi_num=1,plotting=False, fignum=None, clear=True):
    motor_description = _crystal_alignment_dict[crystal]['roll']
    motor_object = get_motor_device(motor_description, based_on='description')
    x_col = motor_object.name
    y_col = f'pil100k_stats{pil100k_roi_num}_total'

    df = db[uid].table()
    return _estimate_peak_fwhm_from_roll_scan(df, x_col, y_col, plotting=plotting, fignum=fignum, clear=clear)[0]

def estimate_peak_fwhm_from_elastic_step_scan(uid, pil100k_roi_num=1,plotting=False, fignum=None, clear=True):
    x_col = 'hhm_energy'
    y_col = f'pil100k_stats{pil100k_roi_num}_total'

    df = db[uid].table()
    return _estimate_peak_fwhm_from_roll_scan(df, x_col, y_col, plotting=plotting, fignum=fignum, clear=clear)[0]

def process_crystal_piezo_roll_scan(crystal=None, pil100k_roi_num=None, alignment_data=None, plot_func=None, uid=-1):
    fwhm = estimate_peak_fwhm_from_roll_scan(uid, crystal, pil100k_roi_num=pil100k_roi_num)
    hdr = db[uid]
    start = hdr.start
    uid = start.uid
    print(uid)
    _dict = {'uid': uid,
             'fwhm': fwhm,
             'tweak_motor_description': start['tweak_motor_description'],
             'tweak_motor_position': start['tweak_motor_position']}
    alignment_data.append(_dict)
    yield from bps.null()

def process_elastic_step_scan(pil100k_roi_num=None, alignment_data=None, plot_func=None, uid=-1):
    fwhm = estimate_peak_fwhm_from_elastic_step_scan(uid, pil100k_roi_num=pil100k_roi_num)
    hdr = db[uid]
    start = hdr.start
    uid = start.uid
    print(uid)
    _dict = {'uid': uid,
             'fwhm': fwhm,
             'tweak_motor_description': start['tweak_motor_description'],
             'tweak_motor_position': start['tweak_motor_position']}
    alignment_data.append(_dict)
    yield from bps.null()

# process_crystal_piezo_roll_scan(crystal='main', pil100k_roi_num=1, alignment_data=[])


def quick_crystal_piezo_scan(crystal=None, axis=None, scan_range=None, velocity=None, pil100k_exosure_time=0.1, plot_func=None, liveplot_kwargs=None, md=None):
    motor_description = _crystal_alignment_dict[crystal][axis]
    motor_device = get_motor_device(motor_description, based_on='description')
    detectors = [apb.ch1, pil100k.stats1.total, pil100k.stats2.total, pil100k.stats3.total, pil100k.stats4.total, ]

    print_to_gui(f'Quick scanning motor {motor_description}', tag='Spectrometer')

    num_images = (scan_range / velocity  + 1) / pil100k_exosure_time
    print(num_images)
    pil100k_init_exposure_time = pil100k.cam.acquire_period.get()
    pil100k_init_num_images = pil100k.cam.num_images.get()
    pil100k_init_image_mode = pil100k.cam.image_mode.get()

    pil100k.set_exposure_time(pil100k_exosure_time)
    pil100k.set_num_images(num_images)

    pil100k.cam.image_mode.set(1).wait()

    start_acquiring_plan = bps.mv(pil100k.cam.acquire, 1)
    yield from ramp_motor_scan(motor_device, detectors, scan_range, velocity=velocity, return_motor_to_initial_position=True, start_acquiring_plan=start_acquiring_plan, md=md)

    pil100k.set_exposure_time(pil100k_init_exposure_time)
    pil100k.set_num_images(pil100k_init_num_images)
    pil100k.cam.image_mode.set(pil100k_init_image_mode).wait()


def quick_crystal_piezo_tune(**kwargs):
    yield from quick_crystal_piezo_scan(**kwargs)
    com = obtain_ramp_scan_com_plan(db, -1)
    motor_description = _crystal_alignment_dict[kwargs['crystal']][kwargs['axis']]
    yield from move_motor_plan(motor_attr=motor_description, based_on='description', position=com)


def get_tweak_motor_positions_for_crystal(crystal, motor_range_mm, motor_num_steps):
    motor_description = _crystal_alignment_dict[crystal]['x']
    motor_obj = get_motor_device(motor_description, based_on='description')
    motor_pos_init = motor_obj.position

    motor_pos_start = motor_pos_init - motor_range_mm / 2
    motor_pos_stop = motor_pos_init + motor_range_mm / 2

    motor_pos_steps = np.linspace(motor_pos_start, motor_pos_stop, motor_num_steps)

    motor_low_lim = motor_obj.low_limit # check this
    motor_high_lim = motor_obj.high_limit  # check this
    motor_pos_steps = motor_pos_steps[(motor_pos_steps >= motor_low_lim) & (motor_pos_steps <= motor_high_lim)]
    return motor_pos_init, motor_pos_steps, motor_description


def run_alignment_scans_for_crystal_bundle(crystal=None, alignment_by=None, pil100k_roi_num=None,
                                           alignment_data=None,
                                           scan_range_roll=None, scan_range_yaw=None, step_size=None,
                                           exposure_time = None,
                                           tweak_motor_range=None, tweak_motor_num_steps=None,
                                           plot_func=None, liveplot_kwargs=None):
    if alignment_data is None:
        alignment_data = []
    tweak_motor_init_pos, tweak_motor_pos, tweak_motor_description = get_tweak_motor_positions_for_crystal(crystal, tweak_motor_range, tweak_motor_num_steps)

    plans = []

    for i, _pos in enumerate(tweak_motor_pos):
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {'msg': f'Aligning motor {tweak_motor_description} (step {i + 1}, position={_pos})',
                                      'add_timestamp': True,
                                      'tag': 'Spectrometer'}})
        plans.append({'plan_name': 'move_motor_plan',
                      'plan_kwargs': {'motor_attr': tweak_motor_description,
                                      'based_on': 'description',
                                      'position': _pos}})
        if crystal != 'main':
            plans.append({'plan_name': 'crystal_piezo_tune',
                          'plan_kwargs': {'property': 'com',
                                          'pil100k_roi_num': pil100k_roi_num,
                                          'crystal': crystal,
                                          'axis': 'yaw',
                                          'scan_range': scan_range_yaw,
                                          'step_size': 25, # step_size
                                          'exposure_time': exposure_time,
                                          'plot_func': plot_func,
                                          'liveplot_kwargs': liveplot_kwargs}})

        md = {'tweak_motor_description': tweak_motor_description,
              'tweak_motor_position': _pos}

        if alignment_by == 'emission':
            plans.append({'plan_name': 'crystal_piezo_scan',
                          'plan_kwargs': {'crystal': crystal,
                                          'axis': 'roll',
                                          'scan_range': scan_range_roll,
                                          'step_size': step_size,
                                          'exposure_time': exposure_time,
                                          'plot_func': plot_func,
                                          'liveplot_kwargs': liveplot_kwargs,
                                          'md': md}})
            plans.append({'plan_name': 'process_crystal_piezo_roll_scan',
                          'plan_kwargs': {'crystal': crystal,
                                          'pil100k_roi_num': pil100k_roi_num,
                                          'alignment_data': alignment_data}})


        elif alignment_by == 'elastic':
            e_cen = hhm.energy.position
            plans.append({'plan_name': 'johann_hhm_resolution_scan',
                          'plan_kwargs': {'scan_range': scan_range_roll,
                                          'step_size': 0.1,
                                          'exposure_time': exposure_time,
                                          'plot_func': plot_func,
                                          'liveplot_kwargs': liveplot_kwargs,
                                          'md': md}})
            plans.append({'plan_name': 'process_elastic_step_scan',
                          'plan_kwargs': {'pil100k_roi_num': pil100k_roi_num,
                                          'alignment_data': alignment_data}})

            # plans.append({'plan_name': 'move_mono_energy',
            #               'plan_kwargs': {'energy': e_cen}})


    plans.append({'plan_name': 'move_motor_plan',
                  'plan_kwargs': {'motor_attr': tweak_motor_description,
                                  'based_on': 'description',
                                  'position': tweak_motor_init_pos}})

    return plans

ALIGNMENT_DATA = []
# plans = run_alignment_scans_for_crystal_bundle(crystal='main', alignment_by='elastic', pil100k_roi_num=1,
#                                            alignment_data=ALIGNMENT_DATA,
#                                            scan_range_roll=12, scan_range_yaw=400, step_size=10,
#                                            exposure_time = 0.5,
#                                            tweak_motor_range=20, tweak_motor_num_steps=9,
#                                            plot_func=None, liveplot_kwargs=None)

# plans = run_alignment_scans_for_crystal_bundle(crystal='aux2', alignment_by='elastic', pil100k_roi_num=1,
#                                            alignment_data=ALIGNMENT_DATA,
#                                            scan_range_roll=12, scan_range_yaw=600, step_size=20,
#                                            exposure_time = 0.3,
#                                            tweak_motor_range=24000, tweak_motor_num_steps=11,
#                                            plot_func=None, liveplot_kwargs=None)

plans = run_alignment_scans_for_crystal_bundle(crystal='main', alignment_by='emission', pil100k_roi_num=1,
                                               alignment_data=ALIGNMENT_DATA,
                                               scan_range_roll=800, scan_range_yaw=400, step_size=10,
                                               exposure_time = 0.3,
                                               tweak_motor_range=15, tweak_motor_num_steps=7,
                                               plot_func=None, liveplot_kwargs=None)

# plans = run_alignment_scans_for_crystal_bundle(crystal='aux5', alignment_by='emission', pil100k_roi_num=1,
#                                            alignment_data=ALIGNMENT_DATA,
#                                            scan_range_roll=800, scan_range_yaw=600, step_size=10,
#                                            exposure_time = 0.3,
#                                            tweak_motor_range=10000, tweak_motor_num_steps=5,
#                                            plot_func=None, liveplot_kwargs=None)
#
# # # # for uid in df.uid[[0, 5, 8]]:
# for uid in df.uid:
#     estimate_peak_fwhm_from_roll_scan(uid, 'aux4', pil100k_roi_num=1,plotting=True, fignum=1, clear=False)
#     # estimate_peak_fwhm_from_elastic_step_scan(uid, pil100k_roi_num=1, plotting=True, fignum=1, clear=False)


