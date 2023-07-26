from xas.spectrometer import ingest_epics_motor_fly_scan, analyze_elastic_fly_scan, analyze_linewidth_fly_scan, get_optimal_crystal_alignment_position

ALIGNMENT_SAMPLE_NAME = 'alignment sample'
ALIGNMENT_SAMPLE_UID = 'alignment'

def step_scan_simple_johann_piezo_plan(crystal=None, axis=None, scan_range=None, step_size=None, exposure_time=0.5, plot_func=None, liveplot_kwargs=None, md=None):
    motor_description = _crystal_alignment_dict[crystal][axis]
    rel_start, rel_stop, num_steps = convert_range_to_start_stop(scan_range, step_size)
    yield from general_scan(detectors=['Pilatus 100k'], motor=motor_description, rel_start=rel_start, rel_stop=rel_stop,
                            num_steps=num_steps, exposure_time=exposure_time, liveplot_kwargs={}, md=md)

def fly_epics_scan_simple_johann_piezo_plan(crystal, axis, scan_range, duration, plot_func=None, liveplot_kwargs=None, md=None):
    crystals = [crystal]
    detectors = ['Pilatus 100k']
    relative_trajectory = {'positions': [-scan_range/2, scan_range/2],
                           'durations': [duration]}
    yield from fly_epics_scan_custom_johann_piezo_plan(crystals=crystals, axis=axis, detectors=detectors,
                                                       relative_trajectory=relative_trajectory, md=md)

def simple_johann_piezo_plan(scan_kind=None, **kwargs):
    if scan_kind == 'step':
        yield from step_scan_simple_johann_piezo_plan(**kwargs)
    elif scan_kind == 'fly':
        yield from fly_epics_scan_simple_johann_piezo_plan(**kwargs)

def tune_johann_piezo_plan(property='com', pil100k_roi_num=None, scan_kind=None, **kwargs):
    yield from simple_johann_piezo_plan(scan_kind, **kwargs)
    if scan_kind == 'step':
        t = db[-1].table()
    elif scan_kind == 'fly':
        t = ingest_epics_motor_fly_scan(db, -1)

    motor_description = _crystal_alignment_dict[kwargs['crystal']][kwargs['axis']]
    motor_object = get_motor_device(motor_description, based_on='description')
    x = t[motor_object.name].values
    y = t[f'pil100k_stats{pil100k_roi_num}_total'].values

    if property == 'com':
        new_position = np.sum((y - y.min()) * x) / np.sum((y - y.min()))
    else:
        raise ValueError('not implemented')

    yield from move_motor_plan(motor_attr=motor_description, based_on='description', position=new_position)


def _johann_analyze_alignment_scan(alignemnt_plan, rois=None, plot_func=None, liveplot_kwargs=None, alignment_data=None, fom=None):
    if alignemnt_plan == 'fly_scan_johann_elastic_alignment_plan_bundle':
        fom_value = analyze_elastic_fly_scan(db, -1, rois=rois, plot_func=plot_func)
    elif alignemnt_plan == 'epics_fly_scan_johann_emission_alignment_plan_bundle':
        pass
    elif alignemnt_plan == 'fly_scan_johann_herfd_alignment_plan_bundle':
        pass

    if alignment_data is not None:
        start = db[-1].start
        uid = start.uid
        _dict = {'uid': uid,
                 fom: fom_value,
                 'tweak_motor_description': start['tweak_motor_description'],
                 'tweak_motor_position': start['tweak_motor_position']}
        alignment_data.append(_dict)

def johann_analyze_alignment_scan(attempts=5, sleep=3, **kwargs):
    for i in range(attempts):
        try:
            print_to_gui(f'Analyzing spectrometer alignment scan: attempt {i+1}', tag='Spectrometer', add_timestamp=True)
            _johann_analyze_alignment_scan(**kwargs)
            yield from bps.null()
            break
        except Exception as e:
            yield from bps.sleep(sleep)

def fly_scan_johann_elastic_alignment_plan_bundle(crystal=None, e_cen=8000.0, scan_range=10.0, duration=2.0, motor_info='', md=None):
    e_velocity = scan_range / duration
    trajectory_filename = scan_manager.quick_linear_trajectory_filename(e_cen, scan_range, e_velocity)
    if md is None: md = {}

    md = {'sample_name': ALIGNMENT_SAMPLE_NAME,
          'sample_uid': ALIGNMENT_SAMPLE_UID,
          'plan_name': 'fly_scan_johann_elastic_alignment_plan',
          **md}

    name = f'{crystal} elastic scan at {e_cen: 0.1f} {motor_info}'
    scan_kwargs = {'name': name, 'comment': '',
                   'trajectory_filename': trajectory_filename,
                   'detectors': ['Pilatus 100k'],
                   'element': '', 'e0': e_cen, 'edge': '',
                   'metadata': md}
    return [{'plan_name': 'fly_scan_plan',
                  'plan_kwargs': {**scan_kwargs}}]

def epics_fly_scan_johann_emission_alignment_plan_bundle(crystal=None, mono_energy=None, scan_range=None, duration=None, motor_info='', md=None):
    if md is None: md = {}
    md = {'sample_name': ALIGNMENT_SAMPLE_NAME,
          'sample_uid': ALIGNMENT_SAMPLE_UID,
          'plan_name': 'epics_fly_scan_johann_emission_alignment_plan',
          **md}

    name = f'{crystal} emission scan at {motor_info}'
    scan_kwargs = {'name': name, 'comment': '', 'detectors': ['Pilatus 100k'],
                   'mono_energy': mono_energy,
                   'spectrometer_central_energy': None,
                   'relative_trajectory': {'positions' : [-scan_range/2, scan_range/2], 'durations': [duration]},
                   'crystal_selection': crystal,
                   'element': '', 'e0': None, 'line': '',
                   'metadata': md}

    return [{'plan_name': 'epics_fly_scan_johann_xes_plan',
             'plan_kwargs': scan_kwargs}]

def fly_scan_johann_herfd_alignment_plan_bundle(crystal=None, element=None, edge=None, duration=None, motor_info='', md=None):
    trajectory_filename = scan_manager.quick_herfd_trajectory_filename(element, edge, duration)
    e0 = xraydb.xray_edge(element, edge).energy
    if md is None: md = {}

    md = {'sample_name': ALIGNMENT_SAMPLE_NAME,
          'sample_uid': ALIGNMENT_SAMPLE_UID,
          'plan_name': 'fly_scan_johann_herfd_alignment_plan',
          **md}

    name = f'{crystal} herfd scan at {element}-{edge} {motor_info}'
    scan_kwargs = {'name': name, 'comment': '',
                   'trajectory_filename': trajectory_filename,
                   'detectors': ['Pilatus 100k'],
                   'element': element, 'e0': e0, 'edge': edge,
                   'metadata': md}
    return [{'plan_name': 'fly_scan_plan',
             'plan_kwargs': scan_kwargs}]

def johann_alignment_scan_plan_bundle(alignemnt_plan=None, rois=None, liveplot_kwargs=None, alignment_data=None, fom=None, plan_gui_services=None, **scan_kwargs):
    plans = []
    plans.append({'plan_name': alignemnt_plan,
                  'plan_kwargs': {**scan_kwargs}})
    plans.append({'plan_name': 'johann_analyze_alignment_scan',
                  'plan_kwargs': {'alignemnt_plan': alignemnt_plan, 'rois': rois, 'liveplot_kwargs': liveplot_kwargs,
                                  'alignment_data': alignment_data, 'fom': fom},
                  'plan_gui_services': plan_gui_services})
    return plans


def johann_focus_on_one_crystal_plan(crystal, yaw_shift=800):
    print_to_gui(f'Focus on {crystal} crystal. Moving other crystals from the field of view.',
                 add_timestamp=True, tag='spectrometer')

    enabled_crystals = [_c for _c, _e in johann_emission.enabled_crystals.items() if _e]
    unwanted_crystals = [c for c in enabled_crystals if c != crystal]
    for cr in unwanted_crystals:
        yaw_direction = 1 if cr in ['aux3', 'aux5'] else -1
        yield from move_relative_motor_plan(motor_attr=_crystal_alignment_dict[cr]['yaw'],
                                            based_on='description',
                                            rel_position=yaw_shift * yaw_direction)


def undo_johann_focus_on_one_crystal_plan(crystal, yaw_shift=800):
    print_to_gui(f'Focus was on {crystal} crystal. Moving other crystals back into the field of view.',
                 add_timestamp=True, tag='spectrometer')
    yield from johann_focus_on_one_crystal_plan(crystal, yaw_shift=-yaw_shift)


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



def move_to_optimal_crystal_alignment_position_plan(alignment_data=None, fom=None, polarity='pos', plot_func=None):
    multiplier = 1 if polarity == 'pos' else -1
    x = [v['tweak_motor_position'] for v in alignment_data if fom in v.keys()]
    y = [v[fom]*multiplier for v in alignment_data if fom in v.keys()]
    position = get_optimal_crystal_alignment_position(x, y, plot_func=plot_func)
    tweak_motor_description = alignment_data[0]['tweak_motor_description']
    print_to_gui(f'Best position for {tweak_motor_description} was found to be {position}', add_timestamp=True, tag='Spectrometer')
    yield from move_motor_plan(motor_attr=tweak_motor_description, based_on='description', position=position)


def johann_crystal_alignment_plan_bundle(crystal=None, scan_range_alignment_multiplier=None,
                                         alignment_by=None, scan_kind=None,
                                         pil100k_roi_num=None,
                                         alignment_data=None,
                                         scan_range_yaw=None, scan_step_yaw=10, scan_duration_yaw=10,
                                         scan_range_roll=None, scan_step_roll=None, scan_duration_roll=None,
                                         scan_range_mono=None, scan_step_mono=None, scan_duration_mono=None,
                                         exposure_time=None,
                                         herfd_element=None, herfd_edge=None, scan_duration_herfd=None,
                                         tweak_motor_range=None, tweak_motor_num_steps=None,
                                         plot_func=None, liveplot_kwargs=None):
    plans = []
    if alignment_data is None:
        alignment_data = []

    if scan_range_alignment_multiplier is None:
        _tweak_motor_range = tweak_motor_range
    else:
        _tweak_motor_range = tweak_motor_range * scan_range_alignment_multiplier

    tweak_motor_init_pos, tweak_motor_pos, tweak_motor_description = get_tweak_motor_positions_for_crystal(crystal, _tweak_motor_range, tweak_motor_num_steps)

    mono_energy = hhm.energy.position

    plans.append({'plan_name': 'print_message_plan',
                  'plan_kwargs': {'msg': f'Aligning {crystal} crystal.',
                                  'add_timestamp': True,
                                  'tag': 'Spectrometer'}})

    plans.append({'plan_name': 'johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

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
            # pretune yaw
            plans.append({'plan_name': 'move_motor_plan',
                          'plan_kwargs': {'motor_attr': 'A Monochromator Energy',
                                          'based_on': 'description',
                                          'position': mono_energy}})
            yaw_scan_params = {'scan_range': scan_range_yaw, 'exposure_time': exposure_time}
            if scan_kind == 'fly':
                yaw_scan_params['duration'] = scan_duration_yaw
            elif scan_kind == 'step':
                yaw_scan_params['step_size'] = scan_step_yaw

            plans.append({'plan_name': 'tune_johann_piezo_plan',
                          'plan_kwargs': {'property': 'com',
                                          'pil100k_roi_num': pil100k_roi_num,
                                          'scan_kind': scan_kind,
                                          'crystal': crystal,
                                          'axis': 'yaw',
                                          'scan_range': scan_range_yaw,
                                          **yaw_scan_params,
                                          'plot_func': plot_func,
                                          'liveplot_kwargs': liveplot_kwargs}})

        md = {'tweak_motor_description': tweak_motor_description,
              'tweak_motor_position': _pos}

        if alignment_by == 'emission':
            fom, polarity = 'emission_line_fwhm', 'pos'
            if scan_kind == 'fly':
                alignment_plan_kwargs = {'alignment_plan': 'epics_fly_scan_johann_emission_alignment_plan_bundle',
                                         'crystal': crystal,
                                         'mono_energy': mono_energy,
                                         'scan_range': scan_range_roll,
                                         'duration': scan_duration_roll}
        elif alignment_by == 'elastic':
            fom, polarity = 'elastic_line_fwhm', 'pos'
            if scan_kind == 'fly':
                alignment_plan_kwargs = {'alignment_plan': 'fly_scan_johann_elastic_alignment_plan_bundle',
                                         'crystal': crystal,
                                         'e_cen': mono_energy,
                                         'scan_range': scan_range_mono,
                                         'duration': scan_duration_mono}
        elif alignment_by == 'herfd':
            fom, polarity = 'herfd_fom', 'pos'
            if scan_kind == 'fly':
                alignment_plan_kwargs = {'alignment_plan': 'fly_scan_johann_herfd_alignment_plan_bundle',
                                         'crystal': crystal,
                                         'element': herfd_element,
                                         'edge': herfd_edge,
                                         'duration': scan_duration_herfd}

        plans.append({'plan_name': 'johann_alignment_scan_plan_bundle',
                      'plan_kwargs': {'rois': [pil100k_roi_num],
                                      'liveplot_kwargs': liveplot_kwargs,
                                      'alignment_data': alignment_data,
                                      'md': md,
                                      'fom': fom,
                                      'motor_info': f'{tweak_motor_description}={_pos: 0.2f}',
                                      **alignment_plan_kwargs}})

    plans.append({'plan_name': 'move_to_optimal_crystal_alignment_position_plan',
                  'plan_kwargs': {'alignment_data': alignment_data,
                                  'fom': fom,
                                  'polarity': polarity}})

    plans.append({'plan_name': 'undo_johann_focus_on_one_crystal_plan', 'plan_kwargs': {'crystal': crystal}})

    return plans


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



def johann_spectrometer_alignment_plan_bundle(**kwargs):
    plans = []

    alignment_data = johann_emission.alignment_data

    enabled_crystals = [_c for _c, _e in johann_emission.enabled_crystals.items() if _e]

    # enforce that the main crystal is aligned first
    if 'main' in enabled_crystals:
        enabled_crystals.pop(enabled_crystals.index('main'))
        enabled_crystals = ['main'] + enabled_crystals

    for crystal in enabled_crystals:
        if crystal not in alignment_data.keys():
            alignment_data[crystal] = []

        multiplier = 1 if crystal == 'main' else 1000
        plans.append({'plan_name': 'run_alignment_scans_for_crystal_bundle',
                      'plan_kwargs': {'crystal': crystal,
                                      'scan_range_alignment_multiplier': multiplier,
                                      **kwargs}})

    return plans


def johann_spectrometer_calibration_plan_bundle(**kwargs):
    pass

