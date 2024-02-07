import pandas as pd
from xas.spectrometer import analyze_elastic_fly_scan, analyze_linewidth_fly_scan, get_optimal_crystal_alignment_position
from xas.process import get_processed_df_from_uid_for_epics_fly_scan


ALIGNMENT_SAMPLE_NAME = 'alignment sample'
ALIGNMENT_SAMPLE_UID = 'alignment'

# JOHANN_DEFAULT_DETECTOR_KEY = 'Pilatus 100k'
JOHANN_DEFAULT_DETECTOR_KEY = 'Pilatus 100k New'
JOHANN_DEFAULT_DETECTOR_DICT = detector_dictionary[JOHANN_DEFAULT_DETECTOR_KEY]


def step_scan_simple_johann_piezo_plan(crystal=None, axis=None, scan_range=None, step_size=None, exposure_time=0.5, md=None):
    motor_description = _crystal_alignment_dict[crystal][axis]
    rel_start, rel_stop, num_steps = convert_range_to_start_stop(scan_range, step_size)
    yield from general_scan(detectors=[JOHANN_DEFAULT_DETECTOR_KEY], motor=motor_description, rel_start=rel_start, rel_stop=rel_stop,
                            num_steps=num_steps, exposure_time=exposure_time, liveplot_kwargs={}, md=md)

def fly_epics_scan_simple_johann_piezo_plan(crystal=None, axis=None, scan_range=None, duration=None, md=None):
    crystals = [crystal]
    detectors = [JOHANN_DEFAULT_DETECTOR_DICT['flying_device']]
    relative_trajectory = {'positions': [-scan_range/2, scan_range/2],
                           'durations': [duration]}
    if md is None: md = {}
    yield from epics_fly_scan_custom_johann_piezo_plan(crystals=crystals, axis=axis, detectors=detectors,
                                                       relative_trajectory=relative_trajectory, md=md)


#
# plan = epics_fly_scan_custom_johann_piezo_plan(#crystals=['main', 'aux4', 'aux2'],
#                                                crystals=['main', 'aux2', 'aux3', 'aux4', 'aux5'],
#                                                 axis='roll',
#                                                 detectors=[pil100k_stream, apb_stream],
#                                                 relative_trajectory={'positions': [-400, -395, 395, 400],
#                                                                      'durations': [0.1, 30, 0.1]},
#                                                 md={'experiment': 'epics_fly_scan'})
# RE(plan)

def simple_johann_piezo_plan(scan_kind=None, **kwargs):
    if scan_kind == 'step':
        yield from step_scan_simple_johann_piezo_plan(**kwargs)
    elif scan_kind == 'fly':
        yield from fly_epics_scan_simple_johann_piezo_plan(**kwargs)

def tune_johann_piezo_plan(property='com', pil100k_roi_num=None, scan_kind=None, plot_func=None,
                           liveplot_kwargs=None, plan_gui_services=None, **kwargs):
    yield from simple_johann_piezo_plan(scan_kind, **kwargs)
    if scan_kind == 'step':
        t = db[-1].table()
        y = t[f'{JOHANN_DEFAULT_DETECTOR_DICT["device"].name}_stats{pil100k_roi_num}_total'].values
    elif scan_kind == 'fly':
        t = get_processed_df_from_uid_for_epics_fly_scan(db, -1)
        y = t[f'{JOHANN_DEFAULT_DETECTOR_DICT["device"].name}_roi{pil100k_roi_num}'].values

    motor_description = _crystal_alignment_dict[kwargs['crystal']][kwargs['axis']]
    motor_object = get_motor_device(motor_description, based_on='description')
    x = t[motor_object.name].values

    if property == 'com':
        # new_position = np.sum((y - y.min()) * x) / np.sum((y - y.min()))
        _y = y - y.min()
        _y_half = _y >= np.percentile(_y, 50)
        x_use = x[_y_half]
        y_use = _y[_y_half]
        new_position = np.sum(y_use * x_use) / np.sum(y_use)
    elif property == 'max':
        new_position = x[np.argmax(y)]
    else:
        raise ValueError('not implemented')
    if np.isnan(new_position):
        print_to_gui(f'New motor position is not defined', tag='spectrometer',
                     add_timestamp=True)
    else:
        print_to_gui(f'Moving motor {motor_description} to position {new_position}', tag='spectrometer', add_timestamp=True)
        yield from move_motor_plan(motor_attr=motor_description, based_on='description', position=new_position)


    # print_to_gui(f'{plot_func=}', tag='DEBUG', add_timestamp=True)
    if plot_func is not None:
        # print_to_gui('actually plotting epics data', tag='DEBUG', add_timestamp=True)
        plot_func(x, _y, x_fit=x_use, y_fit=y_use, x_peak=new_position, y_peak=y.max(), x_label=motor_description, scan_motor_description=motor_description)
        # print_to_gui('actually done plotting epics data', tag='DEBUG', add_timestamp=True)

def fly_scan_johann_elastic_alignment_plan_bundle(crystal=None, e_cen=8000.0, scan_range=10.0, duration=5.0, motor_info='', md=None):
    e_velocity = scan_range / duration
    trajectory_filename = scan_manager.quick_linear_trajectory_filename(e_cen, scan_range, e_velocity)
    if md is None: md = {'scan_tag': ''}

    md = {'sample_name': ALIGNMENT_SAMPLE_NAME,
          'sample_uid': ALIGNMENT_SAMPLE_UID,
          'spectrometer_current_crystal': crystal,
          **md}

    name = f'{crystal}{md["scan_tag"]} elastic scan at {e_cen: 0.1f} {motor_info}'
    scan_kwargs = {'name': name, 'comment': '',
                   'trajectory_filename': trajectory_filename,
                   'detectors': [JOHANN_DEFAULT_DETECTOR_KEY],
                   'element': '', 'e0': e_cen, 'edge': '',
                   'metadata': md}
    return [{'plan_name': 'fly_scan_plan',
                  'plan_kwargs': {**scan_kwargs}}]

# plans = fly_scan_johann_elastic_alignment_plan_bundle(crystal='aux5', e_cen=8046, scan_range=12, duration=20, motor_info='Cu foil spot2', md={})
# plan_processor.add_plans(plans)

def epics_fly_scan_johann_emission_alignment_plan_bundle(crystal=None, mono_energy=None, scan_range=None, duration=None, motor_info='', md=None):
    if md is None: md = {'scan_tag': ''}
    md = {'sample_name': ALIGNMENT_SAMPLE_NAME,
          'sample_uid': ALIGNMENT_SAMPLE_UID,
          'plan_name': 'epics_fly_scan_johann_emission_alignment_plan',
          **md}

    name = f'{crystal}{md["scan_tag"]} roll scan at {motor_info}'
    scan_kwargs = {'name': name, 'comment': '', 'detectors': [JOHANN_DEFAULT_DETECTOR_KEY],
                   'mono_energy': mono_energy,
                   'spectrometer_central_energy': None,
                   'relative_trajectory': {'positions' : [-scan_range/2, scan_range/2], 'durations': [duration]},
                   'crystal_selection': crystal,
                   'element': '', 'e0': None, 'line': '',
                   'metadata': md}

    return [{'plan_name': 'epics_fly_scan_johann_xes_plan',
             'plan_kwargs': scan_kwargs}]

# plans = epics_fly_scan_johann_emission_alignment_plan_bundle(crystal='aux2', mono_energy=11570, scan_range=1000, duration=10, motor_info='test', md={})
# plan_processor.add_plans(plans)


def fly_scan_johann_herfd_alignment_plan_bundle(crystal=None, element=None, edge=None, duration=None, scan_range=None, motor_info='', md=None):
    trajectory_filename = scan_manager.quick_herfd_trajectory_filename(element, edge, duration, scan_range)
    e0 = xraydb.xray_edge(element, edge).energy
    if md is None: md = {'scan_tag': ''}

    md = {'sample_name': ALIGNMENT_SAMPLE_NAME,
          'sample_uid': ALIGNMENT_SAMPLE_UID,
          'spectrometer_current_crystal': crystal,
          **md}

    name = f'{crystal}{md["scan_tag"]} herfd scan at {element}-{edge} {motor_info}'
    scan_kwargs = {'name': name, 'comment': '',
                   'trajectory_filename': trajectory_filename,
                   'detectors': [JOHANN_DEFAULT_DETECTOR_KEY],
                   'element': element, 'e0': e0, 'edge': edge,
                   'metadata': md}
    return [{'plan_name': 'fly_scan_plan',
             'plan_kwargs': scan_kwargs}]

# plans = fly_scan_johann_herfd_alignment_plan_bundle(crystal='main', element='Cu', edge='K', duration=10, motor_info='test', md={})
# plan_processor.add_plans(plans*3)

def johann_alignment_scan_plan_bundle(alignment_plan=None, rois=None,  alignment_data=None,
                                      liveplot_kwargs=None, plan_gui_services=None, **scan_kwargs):
    plans = []
    plans.append({'plan_name': alignment_plan,
                  'plan_kwargs': {**scan_kwargs}})
    plans.append({'plan_name': 'johann_add_scan_to_alignment_data_plan',
                  'plan_kwargs': {'alignment_data': alignment_data,
                                  'alignment_plan': alignment_plan,
                                  '_uid': -1,
                                  'rois': rois}})
    return plans


def johann_add_scan_to_alignment_data_plan(alignment_data=None, alignment_plan='', _uid=-1, rois=None):
    if alignment_data is not None:
        start = db[_uid].start
        uid = start.uid
        alignment_data.append({
            'crystal': start['alignment_crystal'],
            'tweak_motor_description': start['tweak_motor_description'],
            'tweak_motor_position': start['tweak_motor_position'],
            'scan_scope': start['scan_scope'],
            'alignment_plan': alignment_plan,
            'rois': rois,
            'uid': uid, })
        if alignment_data is johann_emission.alignment_data:
            johann_emission.save_alignment_data_to_settings()

    yield from bps.null()



# def _johann_analyze_alignment_data(alignment_data, scan_scope='alignment', force_analysis=False, plot_func=None):
def _johann_analyze_alignment_data_entry(entry):
    if entry['alignment_plan'] == 'fly_scan_johann_elastic_alignment_plan_bundle':
        # fwhm_value, max_value, max_loc, com_loc = analyze_elastic_fly_scan(db, entry['uid'],
        #                                                                    rois=entry['rois'])
        fwhm_value, max_value, max_loc, com_loc = analyze_linewidth_fly_scan(db, entry['uid'],
                                                                             x_key='energy',
                                                                             rois=entry['rois'])
    elif entry['alignment_plan'] == 'epics_fly_scan_johann_emission_alignment_plan_bundle':
        x_key = db[entry['uid']].start['motor_stream_names'][0].replace('_monitor', '')
        fwhm_value, max_value, max_loc, com_loc = analyze_linewidth_fly_scan(db, entry['uid'],
                                                                             x_key=x_key,
                                                                             rois=entry['rois'])
    elif entry['alignment_plan'] == 'fly_scan_johann_herfd_alignment_plan_bundle':
        pass

    else:
        raise NotImplementedError('This is not yet implemented')
    entry['fwhm_value'] = fwhm_value
    entry['max_value'] = max_value
    entry['max_loc'] = max_loc
    entry['com_loc'] = com_loc

def johann_analyze_alignment_data_entry(entry, attempts=5, sleep=3):
    for i in range(attempts):
        try:
            _johann_analyze_alignment_data_entry(entry)
            break
        except Exception as e:
            print(e)
            ttime.sleep(sleep)

def update_entries_for_herfd_calibration_data(alignment_data=None, alignment_plan=None):
    entries_ref = get_relevant_entries_from_alignment_data(alignment_data=alignment_data,
                                                           scan_scope='calibration_reference',
                                                           alignment_plan=alignment_plan)
    uid_calibration_ref = entries_ref[-1]['uid']
    entries = get_relevant_entries_from_alignment_data(alignment_data=alignment_data,
                                                       scan_scope='calibration',
                                                       alignment_plan=alignment_plan)
    for entry in entries:
        if 'uid_calibration_ref' not in entry:
            entry['uid_calibration_ref'] = uid_calibration_ref


def johann_analyze_alignment_data(alignment_data=None, scan_scope=None, alignment_plan=None, crystal=None, force_analysis=False, plot_func=None, ):
    if alignment_data is not None:

        if (alignment_plan == 'fly_scan_johann_herfd_alignment_plan_bundle') and (scan_scope == 'calibration'):
            update_entries_for_herfd_calibration_data(alignment_data=alignment_data, alignment_plan=alignment_plan)

        for entry in alignment_data:
            if ((entry['scan_scope'] == scan_scope) and
                ((crystal is None) or (entry['crystal']==crystal)) and
                ((alignment_plan is None) or (entry['alignment_plan'] == alignment_plan))):
                if force_analysis or any(k not in entry.keys() for k in ['fwhm_value', 'max_value', 'max_loc', 'com_loc']):
                    johann_analyze_alignment_data_entry(entry)
        if alignment_data is johann_emission.alignment_data:
            johann_emission.save_alignment_data_to_settings()
def johann_analyze_alignment_data_plan(**kwargs):
    johann_analyze_alignment_data(**kwargs)
    yield from bps.null()

def get_relevant_entries_from_alignment_data(alignment_data=None, scan_scope=None, alignment_plan=None, crystal=None, tweak_motor_description=None):
    key_checklist = {'scan_scope': scan_scope}
    if alignment_plan is not None: key_checklist['alignment_plan'] = alignment_plan
    if crystal is not None: key_checklist['crystal'] = crystal
    if tweak_motor_description is not None: key_checklist['tweak_motor_description'] = tweak_motor_description
    return [entry for entry in alignment_data if all(entry[k] == v for k, v in key_checklist.items())]


def find_optimal_crystal_alignment_position(alignment_data=None, scan_scope=None, alignment_plan=None, crystal=None, tweak_motor_description=None, fom: str='fwhm_value', plot_func=None):
    relevant_entries = get_relevant_entries_from_alignment_data(alignment_data=alignment_data, scan_scope=scan_scope, alignment_plan=alignment_plan, crystal=crystal, tweak_motor_description=tweak_motor_description)

    if tweak_motor_description is None:
        tweak_motor_descriptions = [entry['tweak_motor_description'] for entry in relevant_entries]
        if len(set(tweak_motor_descriptions)) == 1:
            tweak_motor_description = tweak_motor_descriptions[0]
        else:
            print_to_gui('Multiple tweak motors found in alignment data. Will use the latest one.', add_timestamp=True, tag='Spectrometer')
            tweak_motor_description = tweak_motor_descriptions[-1]

    multiplier = -1 if fom == 'max_value' else 1
    x = [entry['tweak_motor_position'] for entry in relevant_entries]
    y = [entry[fom] * multiplier for entry in relevant_entries]
    position = get_optimal_crystal_alignment_position(x, y, plot_func=plot_func)
    return position, tweak_motor_description

def move_motor_to_position_from_latest_scan_plan(motor_description=None, fom=None, alignment_data=None, scan_scope=None, alignment_plan=None, crystal=None):
    relevant_entries = get_relevant_entries_from_alignment_data(alignment_data=alignment_data, scan_scope=scan_scope,
                                                                alignment_plan=alignment_plan, crystal=crystal)
    entry = relevant_entries[-1] # use the latest one
    position = entry[fom]
    print_to_gui(f'Moving the motor {motor_description} to {position}', tag='Spectrometer', add_timestamp=True)
    yield from move_motor_plan(motor_attr=motor_description, based_on='description', position=position)

def move_to_optimal_crystal_alignment_position_plan(**kwargs):
    position, tweak_motor_description = find_optimal_crystal_alignment_position(**kwargs)
    print_to_gui(f'Best position for {tweak_motor_description} was found to be {position}', add_timestamp=True, tag='Spectrometer')
    print_to_gui(f'Moving the motor {tweak_motor_description} to {position}', tag='Spectrometer', add_timestamp=True)
    yield from move_motor_plan(motor_attr=tweak_motor_description, based_on='description', position=position)

def move_to_optimal_rowland_circle_radius_plan(crystals: list=None, energy: float=None, **kwargs):
    positions = []
    for crystal in crystals:
        position, _ = find_optimal_crystal_alignment_position(crystal=crystal, **kwargs)
        positions.append(position)
    best_position = np.mean(positions)
    print_to_gui(f'Best position for {kwargs["tweak_motor_description"]} was found to be {best_position}', add_timestamp=True,
                 tag='Spectrometer')
    yield from move_rowland_circle_R_plan(new_R=best_position, energy=energy)

def johann_report_spectrometer_resolution_plan(crystals=None, alignment_data=None, alignment_plan=None):
    resolutions = []
    for crystal in crystals:
        relevant_entries = get_relevant_entries_from_alignment_data(alignment_data=alignment_data,
                                                                    scan_scope='resolution',
                                                                    alignment_plan=alignment_plan, crystal=crystal)
        resolution = relevant_entries[-1]['fwhm_value']
        resolutions.append(resolution)
        print_to_gui(f'Resolution of {crystal} crystal: {resolution}', tag='Spectrometer', add_timestamp=True)

    print_to_gui(f'Average resolution: {np.mean(resolutions)}')
    yield from bps.null()


def johann_report_bender_results_plan(crystal=None, alignment_data=None, alignment_plan=None):
    relevant_entries = get_relevant_entries_from_alignment_data(alignment_data=alignment_data,
                                                                scan_scope='bender_scan',
                                                                alignment_plan=alignment_plan, crystal=crystal)
    for entry in relevant_entries:
        print_to_gui(f'Bender at {entry["tweak_motor_description"]}: fwhm={entry["fwhm_value"]} eV', tag='Spectrometer', add_timestamp=True)

    yield from bps.null()

def get_johann_crystal_axis_motor_pos(crystal, axis):
    motor_description = _crystal_alignment_dict[crystal][axis]
    motor_obj = get_motor_device(motor_description, based_on='description')
    return motor_obj.position

def get_tweak_motor_positions_for_crystal(crystal, tweak_motor_axis, motor_range_mm, motor_num_steps):
    motor_description = _crystal_alignment_dict[crystal][tweak_motor_axis]
    motor_obj = get_motor_device(motor_description, based_on='description')
    motor_pos_init = motor_obj.position

    motor_pos_start = motor_pos_init - motor_range_mm / 2
    motor_pos_stop = motor_pos_init + motor_range_mm / 2

    motor_pos_steps = np.linspace(motor_pos_start, motor_pos_stop, motor_num_steps)

    motor_low_lim = motor_obj.low_limit # check this
    motor_high_lim = motor_obj.high_limit  # check this
    motor_pos_steps = motor_pos_steps[(motor_pos_steps >= motor_low_lim) & (motor_pos_steps <= motor_high_lim)]
    return motor_pos_init, motor_pos_steps, motor_description


_alignment_strategy_to_plan_dict = {'emission': {'fly': 'epics_fly_scan_johann_emission_alignment_plan_bundle'},
                                    'elastic': {'fly': 'fly_scan_johann_elastic_alignment_plan_bundle'},
                                    'herfd': {'fly': 'fly_scan_johann_herfd_alignment_plan_bundle'}}


def johann_tweak_crystal_and_scan_plan_bundle(crystal=None, scan_range_alignment_multiplier=None,
                                              alignment_data=None,
                                              motor_info=None,
                                              mono_energy=None,
                                              tweak_motor_axis=None, tweak_motor_range=None, tweak_motor_num_steps=None,
                                              alignment_strategy=None, scan_kind=None,
                                              pil100k_roi_num=None,
                                              yaw_tune=True, yaw_tune_range=800, yaw_tune_duration=10, yaw_tune_step=10,
                                              yaw_tune_exposure=0.25,
                                              roll_tune=False, roll_tune_range=800, roll_tune_duration=10,
                                              roll_tune_step=10,
                                              roll_tune_exposure=0.25,
                                              scan_range=800, scan_duration=10, scan_step=10, scan_exposure=0.25,
                                              herfd_scan_element='', herfd_scan_edge='', md=None,
                                              plot_func=None, liveplot_kwargs=None,
                                              extended_msg_printing=True):
    plans = []

    plans.append({'plan_name': 'johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

    if alignment_data is None:
        alignment_data = []

    if md is None:
        md = {}

    if scan_range_alignment_multiplier is None:
        _tweak_motor_range = tweak_motor_range
    else:
        _tweak_motor_range = tweak_motor_range * scan_range_alignment_multiplier
    tweak_motor_init_pos, tweak_motor_pos, tweak_motor_description = get_tweak_motor_positions_for_crystal(crystal,
                                                                                                           tweak_motor_axis,
                                                                                                           _tweak_motor_range,
                                                                                                           tweak_motor_num_steps)
    if liveplot_kwargs is None:
        liveplot_kwargs = {}
    if mono_energy is None: mono_energy = hhm.energy.position
    yaw_init_position = get_johann_crystal_axis_motor_pos(crystal, 'yaw')

    for i, _pos in enumerate(tweak_motor_pos):
        if extended_msg_printing:
            plans.append({'plan_name': 'print_message_plan',
                          'plan_kwargs': {
                              'msg': f'Motor {tweak_motor_description} in position={_pos}) (step {i + 1}/{len(tweak_motor_pos)}',
                              'add_timestamp': True,
                              'tag': 'Spectrometer'}})
        plans.append({'plan_name': 'move_motor_plan',
                      'plan_kwargs': {'motor_attr': tweak_motor_description,
                                      'based_on': 'description',
                                      'position': _pos}})

        plans.append({'plan_name': 'move_motor_plan',
                      'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
                                      'based_on': 'description',
                                      'position': mono_energy}})

        # pretune yaw
        if (crystal != 'main') and yaw_tune:
            yaw_tune_params = {'scan_range': yaw_tune_range}
            if scan_kind == 'fly':
                yaw_tune_params['duration'] = yaw_tune_duration
            elif scan_kind == 'step':
                yaw_tune_params['step_size'] = yaw_tune_step
                yaw_tune_params['exposure_time'] = yaw_tune_exposure

            plans.append({'plan_name': 'tune_johann_piezo_plan',
                          'plan_kwargs': {'property': 'com',
                                          'pil100k_roi_num': pil100k_roi_num,
                                          'scan_kind': scan_kind,
                                          'crystal': crystal,
                                          'axis': 'yaw',
                                          **yaw_tune_params,
                                          'plot_func': plot_func,
                                          'liveplot_kwargs': liveplot_kwargs}})

        # pretune roll
        if roll_tune:
            roll_tune_params = {'scan_range': roll_tune_range}
            if scan_kind == 'fly':
                roll_tune_params['duration'] = roll_tune_duration
            elif scan_kind == 'step':
                roll_tune_params['step_size'] = roll_tune_step
                roll_tune_params['exposure_time'] = roll_tune_exposure
            plans.append({'plan_name': 'tune_johann_piezo_plan',
                          'plan_kwargs': {'property': 'com',
                                          'pil100k_roi_num': pil100k_roi_num,
                                          'scan_kind': scan_kind,
                                          'crystal': crystal,
                                          'axis': 'roll',
                                          **roll_tune_params,
                                          'plot_func': plot_func,
                                          'liveplot_kwargs': liveplot_kwargs}})

        _md = {**md}
        if ('tweak_motor_description' not in _md.keys()) and ('tweak_motor_position' not in _md.keys()):
            _md = {'tweak_motor_description': tweak_motor_description,
                   'tweak_motor_position': _pos,
                   **_md}
        if ('alignment_crystal' not in _md.keys()):
            _md = {'alignment_crystal': crystal,
                   **_md}

        alignment_plan_kwargs = {'scan_range': scan_range}
        if scan_kind == 'fly':
            alignment_plan_kwargs['duration'] = scan_duration
        elif scan_kind == 'step':
            alignment_plan_kwargs['step_size'] = scan_step
            alignment_plan_kwargs['exposure_time'] = scan_exposure

        if alignment_strategy == 'emission':
            alignment_plan_kwargs['mono_energy'] = mono_energy

        elif alignment_strategy == 'elastic':
            alignment_plan_kwargs['e_cen'] = mono_energy

        elif alignment_strategy == 'herfd':
            alignment_plan_kwargs['element'] = herfd_scan_element
            alignment_plan_kwargs['edge'] = herfd_scan_edge

        if motor_info is None:
            motor_info = f'{tweak_motor_description}={_pos: 0.2f}'
        plans.append({'plan_name': 'johann_alignment_scan_plan_bundle',
                      'plan_kwargs': {'rois': [pil100k_roi_num],
                                      'liveplot_kwargs': liveplot_kwargs,
                                      'alignment_data': alignment_data,
                                      'md': _md,
                                      'motor_info': motor_info,
                                      'alignment_plan': _alignment_strategy_to_plan_dict[alignment_strategy][scan_kind],
                                      'crystal': crystal,
                                      **alignment_plan_kwargs}})

    plans.append({'plan_name': 'undo_johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})
    if extended_msg_printing:
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {
                          'msg': f'Returning motor {tweak_motor_description} to initial position={tweak_motor_init_pos})',
                          'add_timestamp': True,
                          'tag': 'Spectrometer'}})
    plans.append({'plan_name': 'move_motor_plan',
                  'plan_kwargs': {'motor_attr': tweak_motor_description,
                                  'based_on': 'description',
                                  'position': tweak_motor_init_pos}})
    plans.append({'plan_name': 'move_motor_plan',
                  'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
                                  'based_on': 'description',
                                  'position': mono_energy}})
    if crystal != 'main':
        plans.append({'plan_name': 'move_motor_plan',
                      'plan_kwargs': {'motor_attr': _crystal_alignment_dict[crystal]['yaw'],
                                      'based_on': 'description',
                                      'position': yaw_init_position}})

    return plans


def johann_spectrometer_run_alignment_scans_vs_R_plans(
        crystals: list,
        alignment_data: list,
        R_range: float, R_num_steps: int, spectrometer_nominal_energy: float,
        mono_energy: float,
        automatic_mode: bool,
        automatic_fom: str,
        scan_tag: str='',
        **kwargs):
    plans = []

    R_init = rowland_circle.R
    Rs = np.linspace(R_init - R_range / 2, R_init + R_range / 2, R_num_steps)

    for j, _R in enumerate(Rs):
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {'msg': f'Aligning for R={_R} (step {j + 1}/{R_num_steps})',
                                      'add_timestamp': True,
                                      'tag': 'Spectrometer'}})

        plans.append({'plan_name': 'move_rowland_circle_R_plan',
                      'plan_kwargs': {'new_R': _R,
                                      'energy': spectrometer_nominal_energy}})


        for i, crystal in enumerate(crystals):

            plans.append({'plan_name': 'print_message_plan',
                          'plan_kwargs': {'msg': f'Aligning {crystal} crystal (step {i + 1}/{len(crystals)}).',
                                          'add_timestamp': True,
                                          'tag': 'Spectrometer'}})

            plans.append({'plan_name': 'johann_tweak_crystal_and_scan_plan_bundle',
                          'plan_kwargs': {'crystal': crystal,
                                          'scan_range_alignment_multiplier': None,
                                          'alignment_data': alignment_data,
                                          'motor_info': f'R={_R: 0.2f}',
                                          'mono_energy': mono_energy,
                                          'tweak_motor_axis': 'x',
                                          'tweak_motor_range': 0,
                                          'tweak_motor_num_steps': 1,
                                          'md': {'tweak_motor_description': 'Rowland Circle Radius',
                                                 'tweak_motor_position': _R,
                                                 'scan_scope': 'alignment',
                                                 'scan_tag': scan_tag},
                                          'extended_msg_printing': False,
                                          **kwargs}})

    if automatic_mode:
        _alignment_plan = _alignment_strategy_to_plan_dict[kwargs['alignment_strategy']][kwargs['scan_kind']]
        analysis_kwargs = {'alignment_data': alignment_data,
                           'scan_scope': 'alignment',
                           'alignment_plan': _alignment_plan,
                           'crystal': None}
        plans.append({'plan_name': 'johann_analyze_alignment_data_plan',
                      'plan_kwargs': analysis_kwargs})
        plans.append({'plan_name': 'move_to_optimal_rowland_circle_radius_plan',
                      'plan_kwargs': {**analysis_kwargs,
                                      'crystals': crystals,
                                      'energy': spectrometer_nominal_energy,
                                      'tweak_motor_description': 'Rowland Circle Radius',
                                      'fom': automatic_fom}})

    else:
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {'msg': f'Returning R to initial position={R_init})',
                                      'add_timestamp': True,
                                      'tag': 'Spectrometer'}})
        plans.append({'plan_name': 'move_rowland_circle_R_plan',
                      'plan_kwargs': {'new_R': R_init,
                                      'energy': spectrometer_nominal_energy}})

    return plans


# ALIGNMENT_DATA = {}
# plans = johann_spectrometer_run_alignment_scans_vs_R_plans(
#                                               alignment_data=ALIGNMENT_DATA,
#                                               spectrometer_energy=9989, R_range=0, R_num_steps=1,
#                                               alignment_by='elastic', scan_kind='fly',
#                                               pil100k_roi_num=1,
#                                               exposure_time=0.5,
#                                               scan_range_yaw=1000, scan_step_yaw=10, scan_duration_yaw=10,
#                                               scan_range_roll=1000, scan_step_roll=None, scan_duration_roll=10,
#                                               scan_range_mono=12, scan_step_mono=None, scan_duration_mono=10,
#                                               herfd_element=None, herfd_edge=None, scan_duration_herfd=None,
#                                               plot_func=None, liveplot_kwargs=None)
# plan_processor.add_plans(plans)

def johann_spectrometer_run_alignment_scans_vs_x_plans(
        crystals: list,
        alignment_data: list,
        x_range: float, x_num_steps: int,
        mono_energy: float,
        automatic_mode: bool,
        automatic_fom: str,
        scan_tag: str='',
        **kwargs):

    plans = []
    for crystal in crystals:
        multiplier = 1 if crystal == 'main' else 1000
        plans.append({'plan_name': 'johann_tweak_crystal_and_scan_plan_bundle',
                      'plan_kwargs': {'crystal': crystal,
                                      'scan_range_alignment_multiplier': multiplier,
                                      'alignment_data': alignment_data,
                                      'mono_energy': mono_energy,
                                      'tweak_motor_axis': 'x',
                                      'tweak_motor_range': x_range,
                                      'tweak_motor_num_steps': x_num_steps,
                                      'md': {'scan_scope': 'alignment', 'scan_tag': scan_tag},
                                      **kwargs}})

        # in automatic mode it is important that if main crystal is enabled, it should be optimized first
        # that is currently enforced in the parent plans calling this one
        if automatic_mode:
            _alignment_plan = _alignment_strategy_to_plan_dict[kwargs['alignment_strategy']][kwargs['scan_kind']]
            analysis_kwargs = {'alignment_data': alignment_data,
                               'scan_scope': 'alignment',
                               'alignment_plan': _alignment_plan,
                               'crystal': crystal}
            plans.append({'plan_name': 'johann_analyze_alignment_data_plan',
                          'plan_kwargs': analysis_kwargs})
            plans.append({'plan_name': 'move_to_optimal_crystal_alignment_position_plan',
                          'plan_kwargs': {**analysis_kwargs,
                                          'tweak_motor_description': _crystal_alignment_dict[crystal]['x'],
                                          'fom': automatic_fom}})


    return plans


# ALIGNMENT_DATA = {}
# plans = johann_crystal_alignment_plan_bundle(crystal='aux3', scan_range_alignment_multiplier=1000,
#                                          alignment_data=ALIGNMENT_DATA,
#                                          tweak_motor_axis='x', tweak_motor_range=10, tweak_motor_num_steps=5,
#                                          alignment_by='elastic', scan_kind='fly',
#                                          pil100k_roi_num=1,
#                                          exposure_time=0.25,
#                                          scan_range_yaw=1000, scan_step_yaw=10, scan_duration_yaw=10,
#                                          scan_range_roll=1000, scan_step_roll=None, scan_duration_roll=10,
#                                          scan_range_mono=25, scan_step_mono=None, scan_duration_mono=60,
#                                          herfd_element='U', herfd_edge='L3', scan_duration_herfd=45,
#                                          plot_func=None, liveplot_kwargs=None)
# plan_processor.add_plans(plans)

def johann_spectrometer_alignment_plan_bundle(
        crystals=None,
        alignment_data=None,
        alignment_motor=None,
        motor_range=None, motor_num_steps=None,
        spectrometer_nominal_energy=None,
        automatic_mode=False,
        automatic_fom='max',
        post_tuning=True,
        **kwargs):

    plans = []

    if alignment_data is None:
        alignment_data = johann_emission.alignment_data

    if crystals is None:
        crystals = johann_emission.enabled_crystals_list

    mono_energy = hhm.energy.position

    plans.append({'plan_name': 'print_message_plan',
                  'plan_kwargs': {
                      'msg': f'Starting the spectrometer alignment.',
                      'add_timestamp': True,
                      'tag': 'Spectrometer'}})

    if alignment_motor == 'R':
        _plans = johann_spectrometer_run_alignment_scans_vs_R_plans(
            crystals=crystals,
            alignment_data=alignment_data,
            R_range=motor_range, R_num_steps=motor_num_steps, spectrometer_nominal_energy=spectrometer_nominal_energy,
            mono_energy=mono_energy,
            automatic_mode=automatic_mode,
            automatic_fom=automatic_fom,
            **kwargs)

    elif alignment_motor == 'X':
        _plans = johann_spectrometer_run_alignment_scans_vs_x_plans(
            crystals=crystals,
            alignment_data=alignment_data,
            x_range=motor_range, x_num_steps=motor_num_steps,
            mono_energy=mono_energy,
            automatic_mode=automatic_mode,
            automatic_fom=automatic_fom,
            **kwargs)
    else:
        raise NotImplementedError('Alignment can be performed only by X and R!')

    plans.extend(_plans)

    if post_tuning:
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {
                          'msg': f'Performing post-alignment yaw motor tuning)',
                          'add_timestamp': True,
                          'tag': 'Spectrometer'}})

        for crystal in crystals:
            if (crystal != 'main') and kwargs['yaw_tune']:
                yaw_tune_params = {'scan_range': kwargs['yaw_tune_range']}
                if kwargs['scan_kind'] == 'fly':
                    yaw_tune_params['duration'] = kwargs['yaw_tune_duration']
                elif kwargs['scan_kind'] == 'step':
                    yaw_tune_params['step_size'] = kwargs['yaw_tune_step']
                    yaw_tune_params['exposure_time'] = kwargs['yaw_tune_exposure']

                if 'plot_func' in kwargs:
                    plot_func = kwargs['plot_func']
                else:
                    plot_func = None

                if 'liveplot_kwargs' in kwargs:
                    liveplot_kwargs = kwargs['liveplot_kwargs']
                else:
                    liveplot_kwargs = {}

                plans.append({'plan_name': 'tune_johann_piezo_plan',
                              'plan_kwargs': {'property': 'com',
                                              'pil100k_roi_num': kwargs['pil100k_roi_num'],
                                              'scan_kind': kwargs['scan_kind'],
                                              'crystal': crystal,
                                              'axis': 'yaw',
                                              **yaw_tune_params,
                                              'plot_func': plot_func,
                                              'liveplot_kwargs': liveplot_kwargs}})

    plans.append({'plan_name': 'print_message_plan',
                  'plan_kwargs': {
                      'msg': f'Spectrometer alignment is complete.',
                      'add_timestamp': True,
                      'tag': 'Spectrometer'}})

    return plans


def johann_spectrometer_calibration_plan_bundle(
    crystals: list=None,
    alignment_data=None,
    mono_energy=None,
    fom=None,
    tweak_roll_range=None, tweak_roll_num_steps=None,
    calibration_strategy=None, scan_kind=None,
    pil100k_roi_num=None,
    scan_range=800, scan_duration=10, scan_step=10, scan_exposure=0.25,
    herfd_scan_element='', herfd_scan_edge='', md=None,
    plot_func=None, liveplot_kwargs=None):

    plans = []

    if alignment_data is None:
        alignment_data = johann_emission.alignment_data

    if crystals is None:
        crystals = johann_emission.enabled_crystals_list

    if mono_energy is None: mono_energy = hhm.energy.position

    if md is None:
        md = {}
    md = {**md, 'scan_scope': 'calibration'}

    if calibration_strategy == 'roll':

        plans.append({'plan_name': 'move_motor_plan',
                      'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
                                      'based_on': 'description',
                                      'position': mono_energy}})

        for crystal in crystals:
            plans.append({'plan_name': 'johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

            alignment_plan_kwargs = {'scan_range': scan_range}

            if scan_kind == 'fly':
                alignment_plan_kwargs['duration'] = scan_duration
            elif scan_kind == 'step':
                alignment_plan_kwargs['step_size'] = scan_step
                alignment_plan_kwargs['exposure_time'] = scan_exposure

            alignment_plan_kwargs['mono_energy'] = mono_energy
            motor_info = 'calibration'

            plans.append({'plan_name': 'johann_alignment_scan_plan_bundle',
                          'plan_kwargs': {'rois': [pil100k_roi_num],
                                          'liveplot_kwargs': liveplot_kwargs,
                                          'alignment_data': alignment_data,
                                          'md': md,
                                          'motor_info': motor_info,
                                          'alignment_plan': _alignment_strategy_to_plan_dict['emission'][scan_kind],
                                          'crystal': crystal,
                                          **alignment_plan_kwargs}})

            plans.append({'plan_name': 'undo_johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

        _alignment_plan = _alignment_strategy_to_plan_dict['emission'][scan_kind]
        analysis_kwargs = {'alignment_data': alignment_data,
                           'scan_scope': 'calibration',
                           'alignment_plan': _alignment_plan,
                           'crystal': None}
        plans.append({'plan_name': 'johann_analyze_alignment_data_plan',
                      'plan_kwargs': analysis_kwargs})

        for crystal in crystals:
            motor_description = _crystal_alignment_dict[crystal]['roll']
            plans.append({'plan_name': 'move_motor_to_position_from_latest_scan_plan',
                          'plan_kwargs': {'motor_description': motor_description,
                                          'fom': fom,
                                          'alignment_data': alignment_data,
                                          'scan_scope': 'calibration',
                                          'alignment_plan': _alignment_strategy_to_plan_dict['emission'][scan_kind],
                                          'crystal':crystal}})

    elif calibration_strategy == 'herfd':
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {'msg': f'Calibrating {crystals[0]} crystal (step {1}/{len(crystals)}).',
                                      'add_timestamp': True,
                                      'tag': 'Spectrometer'}})
        _plans = johann_spectrometer_calibration_plan_bundle(crystals=crystals[:1],
                                                             alignment_data=alignment_data,
                                                             mono_energy=mono_energy,
                                                             fom=fom,
                                                             tweak_roll_range=None, tweak_roll_num_steps=None,
                                                             calibration_strategy='roll', scan_kind=scan_kind,
                                                             pil100k_roi_num=pil100k_roi_num,
                                                             scan_range=scan_range, scan_duration=scan_duration,
                                                             scan_step=scan_step, scan_exposure=scan_exposure,
                                                             md=None, plot_func=None, liveplot_kwargs=None)
        plans.extend(_plans)

        plans.append({'plan_name': 'johann_tweak_crystal_and_scan_plan_bundle',
                      'plan_kwargs': {'crystal': crystals[0],
                                      'scan_range_alignment_multiplier': None,
                                      'alignment_data': alignment_data,
                                      'motor_info': f'calibration_ref',
                                      'mono_energy': mono_energy,
                                      'tweak_motor_axis': 'roll',
                                      'tweak_motor_range': 0,
                                      'tweak_motor_num_steps': 1,
                                      'alignment_strategy': 'herfd', 'scan_kind': scan_kind,
                                      'pil100k_roi_num': pil100k_roi_num,
                                      'yaw_tune': False,
                                      'roll_tune': False,
                                      'scan_range': scan_range, 'scan_duration': scan_duration,
                                      'scan_step': scan_step, 'scan_exposure': scan_exposure,
                                      'md': {'scan_scope': 'calibration_reference',
                                             'scan_tag': ''},
                                      'herfd_scan_element': herfd_scan_element,
                                      'herfd_scan_edge': herfd_scan_edge,
                                      'extended_msg_printing': False}})


    for i, crystal in enumerate(crystals[1:]):
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {'msg': f'Calibrating {crystal} crystal (step {i + 2}/{len(crystals)}).',
                                      'add_timestamp': True,
                                      'tag': 'Spectrometer'}})

        plans.append({'plan_name': 'johann_tweak_crystal_and_scan_plan_bundle',
                      'plan_kwargs': {'crystal': crystal,
                                      'scan_range_alignment_multiplier': 1,
                                      'alignment_data': alignment_data,
                                      'motor_info': f'calibration',
                                      'mono_energy': mono_energy,
                                      'tweak_motor_axis': 'roll',
                                      'tweak_motor_range': tweak_roll_range,
                                      'tweak_motor_num_steps': tweak_roll_num_steps,
                                      'alignment_strategy': 'herfd', 'scan_kind': scan_kind,
                                      'pil100k_roi_num': pil100k_roi_num,
                                      'yaw_tune': False,
                                      'roll_tune': False,
                                      'scan_range': scan_range, 'scan_duration': scan_duration,
                                      'scan_step': scan_step, 'scan_exposure': scan_exposure,
                                      'md': {'scan_scope': 'calibration',
                                             'scan_tag': ''},
                                      'herfd_scan_element': herfd_scan_element,
                                      'herfd_scan_edge': herfd_scan_edge,
                                      'extended_msg_printing': False}})

    _alignment_plan = _alignment_strategy_to_plan_dict['herfd'][scan_kind]
    analysis_kwargs = {'alignment_data': alignment_data,
                       'scan_scope': 'calibration',
                       'alignment_plan': _alignment_plan}
    plans.append({'plan_name': 'johann_analyze_alignment_data_plan',
                  'plan_kwargs': {**analysis_kwargs, 'crystal': None}})

    for i, crystal in enumerate(crystals[1:]):
        plans.append({'plan_name': 'move_to_optimal_crystal_alignment_position_plan',
                      'plan_kwargs': {**analysis_kwargs,
                                      'crystal': crystal,
                                      'tweak_motor_description': _crystal_alignment_dict[crystal]['roll'],
                                      'fom': 'chisq'}})

    return plans


def johann_spectrometer_resolution_plan_bundle(
    crystals: list=None,
    alignment_data=None,
    mono_energy=None,
    scan_kind=None,
    pil100k_roi_num=None,
    scan_range=15, scan_duration=10, scan_step=0.1, scan_exposure=0.25,
    md=None,
    plot_func=None, liveplot_kwargs=None):

    plans = []

    if alignment_data is None:
        alignment_data = johann_emission.alignment_data

    if crystals is None:
        crystals = johann_emission.enabled_crystals_list

    if mono_energy is None: mono_energy = hhm.energy.position

    if md is None:
        md = {}
    md = {**md, 'scan_scope': 'resolution'}

    for crystal in crystals:
        plans.append({'plan_name': 'johann_tweak_crystal_and_scan_plan_bundle',
                      'plan_kwargs': {'crystal': crystal,
                                      'scan_range_alignment_multiplier': None,
                                      'alignment_data': alignment_data,
                                      'motor_info': f'resolution',
                                      'mono_energy': mono_energy,
                                      'tweak_motor_axis': 'roll',
                                      'tweak_motor_range': 0,
                                      'tweak_motor_num_steps': 1,
                                      'alignment_strategy': 'elastic', 'scan_kind': scan_kind,
                                      'pil100k_roi_num': pil100k_roi_num,
                                      'yaw_tune': False,
                                      'roll_tune': False,
                                      'scan_range': scan_range, 'scan_duration': scan_duration,
                                      'scan_step': scan_step, 'scan_exposure': scan_exposure,
                                      'md': {'tweak_motor_description': 'E',
                                             'tweak_motor_position': f'{mono_energy}',
                                             **md},
                                      'extended_msg_printing': False}})

    _alignment_plan = _alignment_strategy_to_plan_dict['elastic'][scan_kind]
    analysis_kwargs = {'alignment_data': alignment_data,
                       'scan_scope': 'resolution',
                       'alignment_plan': _alignment_plan,
                       'crystal': None}
    plans.append({'plan_name': 'johann_analyze_alignment_data_plan',
                  'plan_kwargs': analysis_kwargs})

    plans.append({'plan_name': 'johann_report_spectrometer_resolution_plan',
                  'plan_kwargs': {'crystals': crystals,
                                  'alignment_data': alignment_data,
                                  'alignment_plan': _alignment_plan}})
    return plans



def johann_bender_scan_plan_bundle(
    alignment_data=None,
    crystal=None,
    mono_energy=None,
    scan_kind=None,
    pil100k_roi_num=None,
    scan_range=15, scan_duration=10, scan_step=0.1, scan_exposure=0.25,
    bender_tweak_range=None, bender_tweak_n_steps=None,
    md=None, liveplot_kwargs=None):

    plans = []

    if alignment_data is None:
        alignment_data = johann_emission.alignment_data

    if crystal is None:
        crystal = johann_emission.enabled_crystals_list[0]

    if md is None:
        md = {}
    md = {**md, 'scan_scope': 'bender_scan'}

    alignment_plan_kwargs = {'scan_range': scan_range}

    if scan_kind == 'fly':
        alignment_plan_kwargs['duration'] = scan_duration
    elif scan_kind == 'step':
        alignment_plan_kwargs['step_size'] = scan_step
        alignment_plan_kwargs['exposure_time'] = scan_exposure

    alignment_plan_kwargs['e_cen'] = mono_energy


    bender_current_position = bender.pos.user_readback.get()
    bender_positions = bender_current_position + np.linspace(-bender_tweak_range / 2, +bender_tweak_range / 2, bender_tweak_n_steps)

    plans.append({'plan_name': 'johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

    for bender_position in bender_positions:
        plans.append({'plan_name': 'move_motor_plan',
                      'plan_kwargs': {'motor_attr': bender.name,
                                      'based_on': 'object_name',
                                      'position': bender_position}})
        plans.append({'plan_name': 'sleep',
                      'plan_kwargs': {'delay': 3}})
        motor_info = f'bender={bender_position}'
        plans.append({'plan_name': 'johann_alignment_scan_plan_bundle',
                      'plan_kwargs': {'rois': [pil100k_roi_num],
                                      'liveplot_kwargs': liveplot_kwargs,
                                      'alignment_data': alignment_data,
                                      'md': {**md,
                                             'tweak_motor_description': 'Bender',
                                             'tweak_motor_position': bender_position},
                                      'motor_info': motor_info,
                                      'alignment_plan': _alignment_strategy_to_plan_dict['elastic'][scan_kind],
                                      'crystal': crystal,
                                      **alignment_plan_kwargs}})

    plans.append({'plan_name': 'undo_johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

    plans.append({'plan_name': 'move_motor_plan',
                  'plan_kwargs': {'motor_attr': bender.name,
                                  'based_on': 'object_name',
                                  'position': bender_current_position}})

    _alignment_plan = _alignment_strategy_to_plan_dict[kwargs['alignment_strategy']][kwargs['scan_kind']]
    analysis_kwargs = {'alignment_data': alignment_data,
                       'scan_scope': 'alignment',
                       'alignment_plan': _alignment_plan,
                       'crystal': None}

    plans.append({'plan_name': 'johann_analyze_alignment_data_plan',
                  'plan_kwargs': analysis_kwargs})

    plans.append({'plan_name': 'johann_report_bender_results_plan',
                  'plan_kwargs': {'crystal': crystal,
                                  'alignment_data': alignment_data,
                                  'alignment_plan': _alignment_plan}})

    return plans


'''
_motors = [johann_aux2_crystal.motor_cr_aux2_roll,
           johann_aux3_crystal.motor_cr_aux3_roll,
           johann_aux4_crystal.motor_cr_aux4_roll,
           johann_aux5_crystal.motor_cr_aux5_roll]
_zero_positions = [495.84000000000003,
                  1030.998,
                  1736.188,
                  426.14300000000003]
for _motor, _zero_position in zip(_motors, _zero_positions):
    SHIFT = 3
    _motor.move(_zero_position + SHIFT)
    # print(_motor.position)
_scan_tag = f'_roll={SHIFT}'
'''

'''
ALIGNMENT_DATA = []
plans = johann_spectrometer_alignment_plan_bundle(
        alignment_data=ALIGNMENT_DATA,
        alignment_motor='R',
        motor_range=12, motor_num_steps=4,
        spectrometer_nominal_energy=9989,
        post_tuning=False,
        alignment_strategy='elastic', scan_kind='fly',
        pil100k_roi_num=1,
        yaw_tune=True, yaw_tune_range=800, yaw_tune_duration=5,
        roll_tune=False, roll_tune_range=800, roll_tune_duration=10,
        scan_range=15, scan_duration=10,
        herfd_scan_element='', herfd_scan_edge='')
plan_processor.add_plans(plans)
'''

    #     # plans.append({'plan_name': 'move_to_optimal_crystal_alignment_position_plan',
    #     #               'plan_kwargs': {'alignment_data': alignment_data[crystal],
    #     #                               'fom': _scan_fom_dict[kwargs['alignment_by']]['alignment']['fom'],
    #     #                               'polarity': _scan_fom_dict[kwargs['alignment_by']]['alignment']['polarity']}})
    #

    #
    # scan_range_yaw = kwargs['scan_range_yaw']
    # scan_duration_yaw = kwargs['scan_duration_yaw']
    # scan_step_yaw = kwargs['scan_step_yaw']
    # exposure_time = kwargs['exposure_time']
    # pil100k_roi_num = kwargs['pil100k_roi_num']
    # scan_kind = kwargs['scan_kind']
    # plot_func = kwargs['plot_func']
    # liveplot_kwargs = kwargs['liveplot_kwargs']
    #
    # for crystal in enabled_crystals:
    #     if crystal != 'main':
    #         # pretune yaw
    #         plans.append({'plan_name': 'move_motor_plan',
    #                       'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
    #                                       'based_on': 'description',
    #                                       'position': mono_energy}})
    #         yaw_scan_params = {'scan_range': scan_range_yaw}
    #         if scan_kind == 'fly':
    #             yaw_scan_params['duration'] = scan_duration_yaw
    #         elif scan_kind == 'step':
    #             yaw_scan_params['step_size'] = scan_step_yaw
    #             yaw_scan_params['exposure_time'] = exposure_time
    #
    #         plans.append({'plan_name': 'tune_johann_piezo_plan',
    #                       'plan_kwargs': {'property': 'com',
    #                                       'pil100k_roi_num': pil100k_roi_num,
    #                                       'scan_kind': scan_kind,
    #                                       'crystal': crystal,
    #                                       'axis': 'yaw',
    #                                       'scan_range': scan_range_yaw,
    #                                       **yaw_scan_params,
    #                                       'plot_func': plot_func,
    #                                       'liveplot_kwargs': liveplot_kwargs}})
    #
    # plans.append({'plan_name': 'print_message_plan',
    #               'plan_kwargs': {
    #                   'msg': f'Spectrometer alignment is complete.',
    #                   'add_timestamp': True,
    #                   'tag': 'Spectrometer'}})




# ALIGNMENT_DATA = []
#
# plans = []
# plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#               'plan_kwargs': {'crystal': 'aux5', 'scan_range_alignment_multiplier': 1000,
#                               'alignment_data': ALIGNMENT_DATA,
#                               'tweak_motor_axis': 'x', 'tweak_motor_range': 30, 'tweak_motor_num_steps': 11,
#                               'alignment_by': 'emission', 'scan_kind': 'fly',
#                               'pil100k_roi_num': 1,
#                               'exposure_time': None,
#                               'scan_range_yaw': 1000, 'scan_step_yaw': 20, 'scan_duration_yaw': 10,
#                               'scan_range_roll': 1000, 'scan_step_roll': None, 'scan_duration_roll': 10,
#                               'scan_range_mono': 15, 'scan_step_mono': 0.1, 'scan_duration_mono': 10,
#                               'herfd_element': 'Cu', 'herfd_edge': 'K', 'scan_duration_herfd': 10,
#                               'plot_func': None, 'liveplot_kwargs': None}})
# ALIGNMENT_DATA = {}
#
# plans = []
# for crystal in ['aux3', 'aux4', 'aux5']:
#     ALIGNMENT_DATA[crystal] = []
#     plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                   'plan_kwargs': {'crystal': crystal, 'scan_range_alignment_multiplier': 1000,
#                                                  'alignment_data': ALIGNMENT_DATA[crystal],
#                                                  'tweak_motor_axis': 'x', 'tweak_motor_range': 30, 'tweak_motor_num_steps': 15,
#                                                  'alignment_by': 'emission', 'scan_kind': 'fly',
#                                                  'pil100k_roi_num': 1,
#                                                  'exposure_time': None,
#                                                  'scan_range_yaw': 500, 'scan_step_yaw': 20, 'scan_duration_yaw': 10,
#                                                  'scan_range_roll': 1000, 'scan_step_roll': None, 'scan_duration_roll': 10,
#                                                  'scan_range_mono': 15, 'scan_step_mono': 0.1, 'scan_duration_mono': 10,
#                                                  'herfd_element': 'Cu', 'herfd_edge': 'K', 'scan_duration_herfd': 10,
#                                                  'plot_func': None, 'liveplot_kwargs': None}})
# plan_processor.add_plans(plans)

# ALIGNMENT_DATA = []
# plans = []
#
# plans.append({'plan_name': 'move_sample_stage_plan', # Cu foil
#    'plan_kwargs': {'sample_coordinates': {'x': 23.309,
#      'y': -45.664,
#      'z': 7.0,
#      'th': 80.364}},
#    'plan_description': 'move_sample_stage_plan'})
#
# for alignment_by in ['emission', 'herfd']:
#
#     plans.append({'plan_name': 'move_motor_plan',
#                   'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
#                                   'based_on': 'description',
#                                   'position': 9000}})
#     plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                   'plan_kwargs': {'crystal': 'main', 'scan_range_alignment_multiplier': 1,
#                                                  'alignment_data': ALIGNMENT_DATA,
#                                                  'tweak_motor_axis': 'x', 'tweak_motor_range': 25, 'tweak_motor_num_steps': 25,
#                                                  'alignment_by': alignment_by, 'scan_kind': 'fly',
#                                                  'pil100k_roi_num': 1,
#                                                  'exposure_time': None,
#                                                  'scan_range_yaw': 1000, 'scan_step_yaw': 20, 'scan_duration_yaw': 10,
#                                                  'scan_range_roll': 1000, 'scan_step_roll': None, 'scan_duration_roll': 10,
#                                                  'scan_range_mono': 15, 'scan_step_mono': 0.1, 'scan_duration_mono': 10,
#                                                  'herfd_element': 'Cu', 'herfd_edge': 'K', 'scan_duration_herfd': 10,
#                                                  'plot_func': None, 'liveplot_kwargs': None}})
#
#
#     for i in range(2, 6):
#         plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                       'plan_kwargs': {'crystal': f'aux{i}', 'scan_range_alignment_multiplier': 1000,
#                                       'alignment_data': ALIGNMENT_DATA,
#                                       'tweak_motor_axis': 'x', 'tweak_motor_range': 30, 'tweak_motor_num_steps': 30,
#                                       'alignment_by': alignment_by, 'scan_kind': 'fly',
#                                       'pil100k_roi_num': 1,
#                                       'exposure_time': None,
#                                       'scan_range_yaw': 1000, 'scan_step_yaw': 20, 'scan_duration_yaw': 10,
#                                       'scan_range_roll': 1000, 'scan_step_roll': None, 'scan_duration_roll': 10,
#                                       'scan_range_mono': 15, 'scan_step_mono': 0.1, 'scan_duration_mono': 10,
#                                       'herfd_element': 'Cu', 'herfd_edge': 'K', 'scan_duration_herfd': 10,
#                                       'plot_func': None, 'liveplot_kwargs': None}})
#
#
# plans.append({'plan_name': 'move_motor_plan',
#                       'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
#                                       'based_on': 'description',
#                                       'position': 8046}})
#
#
# sample_move_plans = \
# [{'plan_name': 'move_sample_stage_plan', # Cu foil
#    'plan_kwargs': {'sample_coordinates': {'x': 23.309,
#      'y': -45.664,
#      'z': 7.0,
#      'th': 80.364}},
#    'plan_description': 'move_sample_stage_plan'},
#
#  {'plan_name': 'move_sample_stage_plan', # w foil
#    'plan_kwargs': {'sample_coordinates': {'x': 28.316,
#      'y': -71.268,
#      'z': 7.0,
#      'th': 80.364}},
#    'plan_description': 'move_sample_stage_plan'},
#
#  {'plan_name': 'move_sample_stage_plan', # water
#    'plan_kwargs': {'sample_coordinates': {'x': -21.519,
#      'y': -63.759,
#      'z': 6.38,
#      'th': 80.364}},
#    'plan_description': 'move_sample_stage_plan'},
#
#  {'plan_name': 'move_sample_stage_plan', # zeolite
#    'plan_kwargs': {'sample_coordinates': {'x': -26.11,
#      'y': -63.759,
#      'z': 7.31,
#      'th': 80.364}},
#    'plan_description': 'move_sample_stage_plan'},
#
#  {'plan_name': 'move_sample_stage_plan', # plastic
#    'plan_kwargs': {'sample_coordinates': {'x': -14.021,
#      'y': -63.976,
#      'z': 6.38,
#      'th': 80.364}},
#    'plan_description': 'move_sample_stage_plan'},
#  ]
#
# for sample_move_plan in sample_move_plans:
#     plans.append(sample_move_plan)
#
#     plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                   'plan_kwargs': {'crystal': 'main', 'scan_range_alignment_multiplier': 1,
#                                   'alignment_data': ALIGNMENT_DATA,
#                                   'tweak_motor_axis': 'x', 'tweak_motor_range': 25, 'tweak_motor_num_steps': 25,
#                                   'alignment_by': 'elastic', 'scan_kind': 'fly',
#                                   'pil100k_roi_num': 1,
#                                   'exposure_time': None,
#                                   'scan_range_yaw': 1000, 'scan_step_yaw': 20, 'scan_duration_yaw': 10,
#                                   'scan_range_roll': 1000, 'scan_step_roll': None, 'scan_duration_roll': 10,
#                                   'scan_range_mono': 15, 'scan_step_mono': 0.1, 'scan_duration_mono': 10,
#                                   'herfd_element': 'Cu', 'herfd_edge': 'K', 'scan_duration_herfd': 10,
#                                   'plot_func': None, 'liveplot_kwargs': None}})
#
#     for i in range(2, 6):
#         plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                       'plan_kwargs': {'crystal': f'aux{i}', 'scan_range_alignment_multiplier': 1000,
#                                       'alignment_data': ALIGNMENT_DATA,
#                                       'tweak_motor_axis': 'x', 'tweak_motor_range': 30, 'tweak_motor_num_steps': 30,
#                                       'alignment_by': 'elastic', 'scan_kind': 'fly',
#                                       'pil100k_roi_num': 1,
#                                       'exposure_time': None,
#                                       'scan_range_yaw': 1000, 'scan_step_yaw': 20, 'scan_duration_yaw': 10,
#                                       'scan_range_roll': 1000, 'scan_step_roll': None, 'scan_duration_roll': 10,
#                                       'scan_range_mono': 15, 'scan_step_mono': 0.1, 'scan_duration_mono': 10,
#                                       'herfd_element': 'Cu', 'herfd_edge': 'K', 'scan_duration_herfd': 10,
#                                       'plot_func': None, 'liveplot_kwargs': None}})
#
#
#
# plan_processor.add_plans(plans)

# ALIGNMENT_DATA = []
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

# plans = run_alignment_scans_for_crystal_bundle(crystal='main', alignment_by='emission', pil100k_roi_num=1,
#                                                alignment_data=ALIGNMENT_DATA,
#                                                scan_range_roll=800, scan_range_yaw=400, step_size=10,
#                                                exposure_time = 0.3,
#                                                tweak_motor_range=15, tweak_motor_num_steps=7,
#                                                plot_func=None, liveplot_kwargs=None)

# plans = run_alignment_scans_for_crystal_bundle(crystal='aux5', alignment_by='emission', pil100k_roi_num=1,
#                                            alignment_data=ALIGNMENT_DATA,
#                                            scan_range_roll=800, scan_range_yaw=600, step_size=10,
#                                            exposure_time = 0.3,
#                                            tweak_motor_range=10000, tweak_motor_num_steps=5,
#                                            plot_func=None, liveplot_kwargs=None)


#
# def johann_spectrometer_alignment_plan_bundle(**kwargs):
#     plans = []
#
#     alignment_data = johann_emission.alignment_data
#     enabled_crystals = johann_emission.enabled_crystals_list
#
#     mono_energy = hhm.energy.position
#
#     plans.append({'plan_name': 'print_message_plan',
#                   'plan_kwargs': {
#                       'msg': f'Starting the spectrometer alignment.',
#                       'add_timestamp': True,
#                       'tag': 'Spectrometer'}})
#
#     for crystal in enabled_crystals:
#         if crystal not in alignment_data.keys():
#             alignment_data[crystal] = []
#
#         plans.append({'plan_name': 'print_message_plan',
#                       'plan_kwargs': {'msg': f'Aligning {crystal} crystal.',
#                                       'add_timestamp': True,
#                                       'tag': 'Spectrometer'}})
#
#         multiplier = 1 if crystal == 'main' else 1000
#         plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                       'plan_kwargs': {'crystal': crystal,
#                                       'scan_range_alignment_multiplier': multiplier,
#                                       'alignment_data': alignment_data[crystal],
#                                       'tweak_motor_axis': 'x',
#                                       **kwargs}})
#         plans.append({'plan_name': 'move_to_optimal_crystal_alignment_position_plan',
#                       'plan_kwargs': {'alignment_data': alignment_data[crystal],
#                                       'fom': _scan_fom_dict[kwargs['alignment_by']]['alignment']['fom'],
#                                       'polarity': _scan_fom_dict[kwargs['alignment_by']]['alignment']['polarity']}})
#
#     plans.append({'plan_name': 'print_message_plan',
#                   'plan_kwargs': {
#                       'msg': f'Performing post-alignment yaw motor tuning)',
#                       'add_timestamp': True,
#                       'tag': 'Spectrometer'}})
#
#     scan_range_yaw = kwargs['scan_range_yaw']
#     scan_duration_yaw = kwargs['scan_duration_yaw']
#     scan_step_yaw = kwargs['scan_step_yaw']
#     exposure_time = kwargs['exposure_time']
#     pil100k_roi_num = kwargs['pil100k_roi_num']
#     scan_kind = kwargs['scan_kind']
#     plot_func = kwargs['plot_func']
#     liveplot_kwargs = kwargs['liveplot_kwargs']
#
#     for crystal in enabled_crystals:
#         if crystal != 'main':
#             # pretune yaw
#             plans.append({'plan_name': 'move_motor_plan',
#                           'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
#                                           'based_on': 'description',
#                                           'position': mono_energy}})
#             yaw_scan_params = {'scan_range': scan_range_yaw}
#             if scan_kind == 'fly':
#                 yaw_scan_params['duration'] = scan_duration_yaw
#             elif scan_kind == 'step':
#                 yaw_scan_params['step_size'] = scan_step_yaw
#                 yaw_scan_params['exposure_time'] = exposure_time
#
#             plans.append({'plan_name': 'tune_johann_piezo_plan',
#                           'plan_kwargs': {'property': 'com',
#                                           'pil100k_roi_num': pil100k_roi_num,
#                                           'scan_kind': scan_kind,
#                                           'crystal': crystal,
#                                           'axis': 'yaw',
#                                           'scan_range': scan_range_yaw,
#                                           **yaw_scan_params,
#                                           'plot_func': plot_func,
#                                           'liveplot_kwargs': liveplot_kwargs}})
#
#     plans.append({'plan_name': 'print_message_plan',
#                   'plan_kwargs': {
#                       'msg': f'Spectrometer alignment is complete.',
#                       'add_timestamp': True,
#                       'tag': 'Spectrometer'}})
#
#     return plans
#
# #consider having short
# def johann_spectrometer_calibration_plan_bundle(calibrate_by=None, scan_kind=None,
#                                                 pil100k_roi_num=None,
#                                                 calibration_data=None,
#                                                 exposure_time=None,
#                                                 scan_range_roll=None, scan_step_roll=None, scan_duration_roll=None, # scan range roll better be small for this
#                                                 herfd_element=None, herfd_edge=None, scan_duration_herfd=None,
#                                                 liveplot_kwargs=None):
#
#     enabled_crystals = johann_emission.enabled_crystals_list
#
#     if calibration_data is None:
#         calibration_data = {}
#
#     plans = []
#
#     plans.append({'plan_name': 'print_message_plan',
#                   'plan_kwargs': {
#                       'msg': f'Starting the spectrometer calibration.',
#                       'add_timestamp': True,
#                       'tag': 'Spectrometer'}})
#
#     if calibrate_by == 'roll':
#         for crystal in enabled_crystals:
#             scan_params = {'scan_range': scan_range_roll}
#             if scan_kind == 'fly':
#                 scan_params['duration'] = scan_duration_roll
#             elif scan_kind == 'step':
#                 scan_params['step_size'] = scan_step_roll
#                 scan_params['exposure_time'] = exposure_time
#
#             plans.append({'plan_name': 'tune_johann_piezo_plan',
#                           'plan_kwargs': {'scan_kind': scan_kind,
#                                           'crystal': crystal,
#                                           'axis': 'roll',
#                                           'liveplot_kwargs': liveplot_kwargs,
#                                           'pil100k_roi_num': pil100k_roi_num,
#                                           **scan_params}})
#
#     elif calibrate_by == 'herfd':
#         scan_kwargs = {'scan_range_alignment_multiplier': 1,
#                        'tweak_motor_axis': 'roll',
#                        'alignment_by': 'herfd',
#                        'scan_kind': scan_kind,
#                        'pil100k_roi_num': pil100k_roi_num,
#                        'exposure_time': exposure_time,
#                        'herfd_element': herfd_element,
#                        'herfd_edge': herfd_edge,
#                        'scan_duration_herfd': scan_duration_herfd,
#                        'liveplot_kwargs': liveplot_kwargs}
#
#         calibration_data[enabled_crystals[0]] = []
#         plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                       'plan_kwargs': {'crystal': enabled_crystals[0],
#                                       'tweak_motor_range': 0,
#                                       'tweak_motor_num_steps': 1,
#                                       'alignment_data': calibration_data[enabled_crystals[0]],
#                                       **scan_kwargs}})
#
#         for crystal in enabled_crystals[1:]:
#             plans.append({'plan_name': 'johann_crystal_alignment_plan_bundle',
#                           'plan_kwargs': {'crystal': crystal,
#                                           'tweak_motor_range': scan_range_roll,
#                                           'tweak_motor_num_steps': int(scan_range_roll / scan_step_roll) + 1,
#                                           **scan_kwargs}})
#
#             # perform analysis on the calibration data
#             plans.append({'plan_name': 'johann_analyze_herfd_calibration_data_plan',
#                           'plan_kwargs': {'calibration_data': calibration_data, 'liveplot_kwargs': liveplot_kwargs}})
#
#             plans.append({'plan_name': 'move_to_optimal_crystal_alignment_position_plan',
#                           'plan_kwargs': {'alignment_data': calibration_data[crystal],
#                                           'fom': _scan_fom_dict['herfd']['calibration']['fom'],
#                                           'polarity': _scan_fom_dict['herfd']['calibration']['polarity']}})
#
#     plans.append({'plan_name': 'print_message_plan',
#                   'plan_kwargs': {
#                       'msg': f'Spectrometer calibration is complete.',
#                       'add_timestamp': True,
#                       'tag': 'Spectrometer'}})
#
#     return plans
#
#
# def johann_analyze_spectrometer_resolution_plan(resolution_data=None, fom=None):
#     fwhms = []
#     print_to_gui('')
#     for crystal, scan_result in resolution_data.items():
#         print_to_gui(f'Resolution for {crystal} crystal is {scan_result[fom]}')
#         fwhms.append(scan_result[fom])
#     print_to_gui('')
#     print_to_gui(f'The average spectrometer resolution is {np.mean(fwhms): 0.2f} eV.')
#     print_to_gui('')
#     yield from bps.null()
#
# def johann_measure_spectrometer_resolution_plan_bundle(**kwargs):
#     plans = []
#     resolution_data = {}
#     fom = _scan_fom_dict['elastic']['alignment']
#
#     enabled_crystals = johann_emission.enabled_crystals_list
#     for crystal in enabled_crystals:
#         plans.append({'plan_name': 'johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})
#         plans.append({'plan_name': 'johann_alignment_scan_plan_bundle',
#                       'plan_kwargs': {'crystal': crystal,
#                                       'alignment_plan': 'fly_scan_johann_elastic_alignment_plan_bundle',
#                                       'fom': fom,
#                                       'alignment_data': resolution_data,
#                                       **kwargs}})
#
#         plans.append({'plan_name': 'undo_johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})
#
#     plans.append({'plan_name': 'estimate_spectrometer_resolution_plan',
#                   'plan_kwargs': {'resolution_data': resolution_data,
#                                   'fom': fom}})
#
#     return plans


# plans = []
# plans.extend(johann_measure_spectrometer_resolution_plan_bundle(e_cen=8340, scan_range=12, duration=20, motor_info='resolution', md={}))
# plan_processor.add_plans(plans)
#
# bla=[]
# plans = []
# # plans.append({'plan_name': 'johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': 'aux5'}})
# plans.append({'plan_name': 'johann_alignment_scan_plan_bundle',
#               'plan_kwargs': {'crystal': 'main',
#                               'alignment_plan': 'fly_scan_johann_elastic_alignment_plan_bundle',
#                               'fom': _scan_fom_dict['elastic']['alignment'],
#                               'alignment_data': bla,
#                               'e_cen': 8340, 'scan_range': 12, 'duration': 20, 'motor_info': 'main try2', 'md': {}}})
#
# plan_processor.add_plans(plans)
# plans = []
# plans.extend(johann_spectrometer_calibration_plan_bundle(calibrate_by='roll', scan_kind='fly', pil100k_roi_num=1, scan_range_roll=1000, scan_duration_roll=10))
# plan_processor.add_plans(plans)
