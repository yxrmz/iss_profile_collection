def elastic_scan_plan(DE=5, dE=0.1):
    npt = np.round(DE/dE + 1)
    name = 'elastic spectrometer scan'
    plan = bp.relative_scan([pil100k, apb_ave], hhm.energy, -DE/2, DE/2, npt, md={'plan_name': 'elastic_scan ' + motor.name, 'name' : name})
    yield from plan


def johann_calibration_scan_plan(energies, DE=5, dE=0.1):
    for energy in energies:
        yield from bps.mv(hhm.energy, energy)
        # yield from move_emission_energy_plan(energy)
        yield from bps.mv(motor_emission, energy)
        yield from elastic_scan_plan(DE=DE, dE=dE)



def plot_radiation_damage_scan_data(db, uid):
    t = db[uid].table()
    plt.figure()
    plt.plot(t['time'], t['pil100k_stats1_total']/np.abs(t['apb_ave_ch1_mean']))




def prepare_johann_scan_plan(detectors, spectrometer_energy):
    ensure_pilatus_is_in_detector_list(detectors)
    yield from bp.mv(johann_spectrometer_motor.energy, spectrometer_energy)

def prepare_johann_metadata_and_kwargs(**kwargs):
    metadata = kwargs.pop('metadata')
    j_metadata = {'spectrometer': 'johann'}
    if spectrometer_energy in kwargs.keys():
        spectrometer_energy = kwargs.pop('spectrometer_energy')
        j_metadata['spectrometer_energy'] = spectrometer_energy
    return {**j_metadata, **metadata}, kwargs


def collect_n_exposures_johann_plan(**kwargs):
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    yield from collect_n_exposures_plan(metadata=metadata, **kwargs)


def step_scan_johann_herfd_plan(**kwargs):
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    yield from step_scan_plan(metadata=metadata, **kwargs)

def fly_scan_johann_herfd_plan(**kwargs):
    # rixs_file_name = kwargs.pop('rixs_file_name')
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    yield from fly_scan_plan(metadata=metadata, **kwargs)


def get_johann_xes_step_scan_md(name, comment, detectors, emission_energy_list, emission_time_list, element, e0, line, metadata):
    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md_general = get_scan_md(name, comment, detectors, '.dat')

    md_scan = {'experiment': 'step_scan',
               'spectrometer': 'johann',
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

    default_detectors = [apb_ave, hhm_encoder]
    aux_detectors = get_detector_device_list(detectors)
    all_detectors = default_detectors + aux_detectors

    md = get_johann_xes_step_scan_md(name, comment, detectors, emission_energy_list, emission_time_list, element, e0, line, metadata)

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    yield from bp.mv(hhm.energy, mono_energy)
    yield from prepare_johann_scan_plan(all_detectors, emission_energy_list[0])

    yield from general_energy_step_scan(all_detectors, johann_spectrometer_motor.energy, emission_energy_list, emission_time_list, md=md)



def deal_with_sample_coordinates_for_rixs(sample_coordinates, emission_energy_list):
    if type(sample_coordinates) == list:
        assert len(sample_coordinates) == len(emission_energy_list), 'number of positions on the sample must match the number of energy points on emission grid'
    else:
        sample_coordinates = [sample_coordinates] * len(emission_energy_list)
        return sample_coordinates

def get_johann_rixs_md(name, element_line, line, e0_line, metadata):
    metadata['rixs_file_name'] = create_interp_file_name(name, '.rixs')
    metadata['element_line'] = element_line
    metadata['line'] = line
    metadata['e0_line'] = e0_line
    return metadata


def johann_rixs_plan_bundle(plan_name, name=None, comment=None, detectors=[],
                            trajectory_filename=None, mono_angle_offset=None,
                            emission_energy_list=None, sample_coordinates=None,
                            element='', edge='', e0=None, element_line='', line='', e0_line=None,
                            rixs_kwargs={}, metadata={}):
    sample_coordinates = deal_with_sample_coordinates_for_rixs(sample_coordinates, emission_energy_list)
    metadata = get_johann_rixs_md(name, element_line, line, e0_line, metadata)
    plans = []
    for emission_energy, sample_position in zip(emission_energy_list, sample_coordinates):

        if sample_position is not None:
            plans.append({'plan_name': 'move_sample_stage_plan',
                          'plan_kwargs': {'sample_coordinates': sample_position}})

        plans.append({'plan_name': plan_name,
                      'plan_kwargs': {'name': name,
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





