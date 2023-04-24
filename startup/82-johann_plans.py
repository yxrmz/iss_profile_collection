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



def move_johann_spectrometer_energy(energy=-1):
    current_energy = johann_emission.energy.position
    energy = float(energy)
    energy_arr = np.linspace(current_energy, energy, int(np.abs(energy - current_energy)/5) + 2)[1:]
    for _energy in energy_arr:
        print_to_gui(f'Moving spectrometer to {_energy}')
        yield from bps.mv(johann_emission, _energy, wait=True)
        # yield from move_motor_plan(motor_attr=johann_emission.energy.name, based_on='object_name', position=float(_energy))


def prepare_johann_scan_plan(detectors, spectrometer_energy):
    ensure_pilatus_is_in_detector_list(detectors)
    yield from move_johann_spectrometer_energy(spectrometer_energy)
    # yield from bps.mv(johann_emission, spectrometer_energy)

def prepare_johann_metadata_and_kwargs(**kwargs):
    metadata = kwargs.pop('metadata')
    j_metadata = {'spectrometer': 'johann',
                  'spectrometer_config': {},}
    if 'spectrometer_energy' in kwargs.keys():
        spectrometer_energy = kwargs.pop('spectrometer_energy')
        j_metadata['spectrometer_energy'] = spectrometer_energy
    return {**j_metadata, **metadata}, kwargs


def collect_n_exposures_johann_plan(**kwargs):
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    metadata['spectrometer_config']['scan_type'] = 'constant energy'
    yield from collect_n_exposures_plan(metadata=metadata, **kwargs)


def step_scan_johann_herfd_plan(**kwargs):
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    metadata['spectrometer_config']['scan_type'] = 'constant energy'
    yield from step_scan_plan(metadata=metadata, **kwargs)

def fly_scan_johann_herfd_plan(**kwargs):
    # rixs_file_name = kwargs.pop('rixs_file_name')
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata['spectrometer_config']['scan_type'] = 'constant energy'
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    yield from fly_scan_plan(metadata=metadata, **kwargs)


def get_johann_xes_step_scan_md(name, comment, detectors_dict, emission_energy_list, emission_time_list, element, e0, line, metadata):
    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element
    md_general = get_scan_md(name, comment, detectors_dict, '.dat')

    md_scan = {'experiment': 'step_scan',
               'spectrometer': 'johann',
               'spectrometer_config': {},
               'spectrometer_energy_steps': emission_energy_list,
               'spectrometer_time_steps': emission_time_list,
               'element': element,
               'element_full': full_element_name,
               'line': line,
               'e0': e0}
    return {**md_scan, **md_general, **metadata}

def step_scan_johann_xes_plan(name=None, comment=None, detectors=[],
                              mono_energy=None, mono_angle_offset=None,
                              emission_energy_list=None, emission_time_list=None,
                              element='', line='', e0=None,
                              metadata={}):

    # default_detectors = [apb_ave, hhm_encoder]
    default_detectors = []
    aux_detectors = get_detector_device_list(detectors, flying=False)
    all_detectors = default_detectors + aux_detectors
    detectors_dict = {k: {'device': v} for k, v in zip(detectors, aux_detectors)}
    md = get_johann_xes_step_scan_md(name, comment, detectors_dict, emission_energy_list, emission_time_list, element, e0, line, metadata)

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    yield from bps.mv(hhm.energy, mono_energy)
    yield from prepare_johann_scan_plan(detectors, emission_energy_list[0])

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
                            rixs_kwargs={}, metadata={}):
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
                                      'mono_angle_offset': mono_angle_offset,
                                      'metadata': metadata}})
        # deal with rixs_kwargs
    return plans

def fly_scan_johann_rixs_plan_bundle(**kwargs):
    return johann_rixs_plan_bundle('fly_scan_johann_herfd_plan', **kwargs)

def step_scan_johann_rixs_plan_bundle(**kwargs):
    return johann_rixs_plan_bundle('step_scan_johann_herfd_plan', **kwargs)


from xas.spectrometer import analyze_elastic_fly_scan

def obtain_spectrometer_resolution_plan(rois=None, plot_func=None, liveplot_kwargs=None, attempts=5, sleep=5):
    for i in range(attempts):
        try:
            print_to_gui(f'Analyzing resolution scan: attempt {i+1}', tag='Spectrometer', add_timestamp=True)
            analyze_elastic_fly_scan(db, -1, rois=rois, plot_func=plot_func)
            yield from bps.null()
            break
        except Exception as e:
            yield from bps.sleep(sleep)



def johann_resolution_scan_plan_bundle(e_cen=8000.0, e_width=10.0, e_velocity=2.0, rois=None, motor_info='', plan_gui_services=None, liveplot_kwargs=None, ):
    plans = []
    trajectory_filename = scan_manager.quick_linear_trajectory_filename(e_cen, e_width, e_velocity)


    name = f'Resolution scan {e_cen} {motor_info}'
    scan_kwargs = {'name': name, 'comment': '',
                   'trajectory_filename': trajectory_filename,
                   'detectors': ['Pilatus 100k'],
                   'element': '', 'e0': e_cen, 'edge': ''}

    plans.append({'plan_name': 'fly_scan_plan',
                  'plan_kwargs': {**scan_kwargs}})
    plans.append({'plan_name': 'obtain_spectrometer_resolution_plan',
                  'plan_kwargs': {'rois' : rois, 'liveplot_kwargs': liveplot_kwargs},
                  'plan_gui_services': plan_gui_services})

    return plans