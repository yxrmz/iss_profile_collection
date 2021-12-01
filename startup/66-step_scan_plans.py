


from ophyd import Staged
import bluesky.plan_stubs as bps
import bluesky.plans as bp


def step_scan_action_factory(energy_steps, time_steps):
    energy_to_time_step = dict(zip(energy_steps, time_steps))

    def per_step_action(detectors, motor, step):
        time_step=energy_to_time_step[step]

        for det in detectors:
            if det.name == 'apb_ave':
                samples = 250*(np.ceil(time_step*1005/250)) #hn I forget what that does... let's look into the new PB OPI
                yield from bps.abs_set(det.sample_len, samples, wait=True)
                yield from bps.abs_set(det.wf_len, samples, wait=True)
            elif det.name == 'pil100k':
                yield from bps.mv(det.cam.acquire_time, time_step)
            elif det.name == 'xs':
                yield from bps.mv(det.settings.acquire_time, time_step)

        yield from bps.mv(motor, step)
        devices = [*detectors, motor]
        start = ttime.time()
        yield from shutter.open_plan(printing=False)
        yield from bps.trigger_and_read(devices=devices)
        yield from shutter.close_plan(printing=False)
        print(f'Total exposure time for this point is {ttime.time() - start} s')

    return per_step_action


def read_step_scan_filename(filename):
    data = np.genfromtxt(filename)
    energy, dwell_time = data[:, 0], data[: 1]
    return energy, dwell_time

def get_step_scan_md(name, comment,trajectory_filename, detectors, element, e0, edge, metadata):
    fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.dat"
    fn = validate_file_exists(fn)

    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md_general = get_general_md()
    md_scan = {'plan_args': {'filename': trajectory_filename, 'detectors': detectors},
               'experiment': 'step_scan',
               'name': name,
               'comment': comment,
               'interp_filename': fn,
               'element': element,
               'element_full': full_element_name,
               'edge': edge,
               'e0': e0,
               'plot_hint': '$5/$1'}
    return {**md_general, **md_scan, **metadata}

def step_scan_plan(name=None, comment=None, trajectory_filename=None, offset=None, detectors=[], element='', e0=0, edge='', metadata={}):

    energy_grid, time_grid = read_step_scan_filename(trajectory_filename)
    if offset is not None: hhm.set_new_angle_offset(offset)
    default_detectors = [apb_ave, hhm.enc.pos_I]
    aux_detectors = get_detector_device_list(detectors)
    all_detectors = default_detectors + aux_detectors

    yield from bps.abs_set(apb_ave.divide, 373, wait=True)
    for det in detectors:
        if det.name == 'xs':
            yield from bps.mv(det.total_points, len(energy_grid))

    md = get_step_scan_md(name, comment, trajectory_filename, detectors, element, e0, edge, metadata)

    yield from shutter.open_plan()
    yield from bp.list_scan(all_detectors,
                            hhm.energy,
                            list(energy_grid),
                            per_step=step_scan_action_factory(energy_grid, time_grid), #and this function is colled at every step
                            md=md)
    yield from shutter.close_plan()