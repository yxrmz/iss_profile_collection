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
    yield from prepare_johann_scan_plan(kwargs['detectors'], kwargs['spectrometer_energy'])
    metadata, kwargs = prepare_johann_metadata_and_kwargs(**kwargs)
    yield from fly_scan_plan(metadata=metadata, **kwargs)


def step_scan_plan(name=None, comment=None, trajectory_filename=None, mono_angle_offset=None, detectors=[], element='',
                   e0=0, edge='', metadata={}):
    energy_list, time_list = read_step_scan_filename(trajectory_filename)
    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    default_detectors = [apb_ave, hhm_encoder]
    aux_detectors = get_detector_device_list(detectors)
    all_detectors = default_detectors + aux_detectors
    md = get_step_scan_md(name, comment, trajectory_filename, detectors, element, e0, edge, metadata)

    yield from general_energy_step_scan(all_detectors, hhm.energy, energy_list, time_list, md=md)





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




