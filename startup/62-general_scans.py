import bluesky as bs
import bluesky.plans as bp
import time as ttime
from subprocess import call
import os
from isstools.conversions import xray
import signal
from periodictable import elements

from ophyd.device import Kind
import time


def general_scan_plan(detectors, motor, rel_start, rel_stop, num):
    
    plan = bp.relative_scan(detectors, motor, rel_start, rel_stop, num)
    
    if hasattr(detectors[0], 'kickoff'):
        plan = bpp.fly_during_wrapper(plan, detectors)
    yield from shutter.open_plan()
    yield from plan
    yield from shutter.close_plan()

def general_scan(detectors=[], motor=None, rel_start=None, rel_stop=None, num_steps=1, liveplot_kwargs={}):

    # sys.stdout = kwargs.pop('stdout', sys.stdout)
    #print(f'Dets {detectors}')
    #print(f'Motors {motor}')
    motor_device = get_motor_device(motor)
    detector_devices = get_detector_device_list(detectors, flying=False)
    # print('[General Scan] Starting scan...')
    print_to_gui('[General Scan] Starting scan...')
    yield from (general_scan_plan(detector_devices, motor_device, rel_start, rel_stop, int(num_steps)))
    # print('[General Scan] Done!')
    print_to_gui('[General Scan] Done!')


def tuning_scan(motor=None, detector=None, scan_range=None, scan_step=None, n_tries = 3, liveplot_kwargs={}):
    # sys.stdout = kwargs.pop('stdout', sys.stdout)

    if type(motor) == list:
        motor = get_motor_device(motor[0], based_on='object_name')
        motor2 = get_motor_device(motor[1], based_on='object_name')
    else:
        motor = get_motor_device(motor, based_on='object_name')
        motor2 = None

    channel = detector.hints['fields'][0]
    for jj in range(n_tries):
        motor_init_position = motor.read()[motor.name]['value']
        min_limit = motor_init_position - scan_range / 2
        max_limit = motor_init_position + scan_range / 2 + scan_step / 2
        scan_positions = np.arange(min_limit, max_limit, scan_step)
        if motor2:
            motor2_init_position = motor2.read()[motor2.name]['value']
            min_limit = motor2_init_position - scan_range / 2
            max_limit = motor2_init_position + scan_range / 2 + scan_step / 2
            scan_positions2 = np.arange(min_limit, max_limit, scan_step)
        scan_range = (scan_positions[-1] - scan_positions[0])
        min_threshold = scan_positions[0] + scan_range / 10
        max_threshold = scan_positions[-1] - scan_range / 10
        if motor2:
            plan = bp.list_scan([detector], motor, scan_positions.tolist(),
                                            motor2, scan_positions2.tolist())
        else:
            plan = bp.list_scan([detector], motor, scan_positions.tolist())
        if hasattr(detector, 'kickoff'):
            plan = bpp.fly_during_wrapper(plan, [detector])
        uid = (yield from plan)
        if uid:
            hdr = db[uid]
            if detector.polarity == 'pos':
                idx = getattr(hdr.table()[channel], 'idxmax')()
            elif detector.polarity == 'neg':
                idx = getattr(hdr.table()[channel], 'idxmin')()
            motor_pos = hdr.table()[motor.name][idx]
            print_to_gui(f'New motor position {motor_pos}')

            if motor_pos < min_threshold:
                yield from bps.mv(motor,min_limit)
                if jj+1 < n_tries:
                    print_to_gui(f' Starting {jj+2} try')
            elif max_threshold < motor_pos:
                print_to_gui('max')
                if jj+1 < n_tries:
                    print_to_gui(f' Starting {jj+2} try')
                yield from bps.mv(motor, max_limit)
            else:
                yield from bps.mv(motor, motor_pos)
                break


def prepare_detectors_for_exposure_plan(detectors, n_exposures=1):
    for det in detectors:
        if det.name == 'apb_ave':
            yield from bps.abs_set(apb_ave.divide, 373, wait=True)
        if det.name == 'xs':
            yield from bps.mv(det.total_points, n_exposures)


def set_detector_exposure_time_plan(detectors, exposure_time):
    for det in detectors:
        if det.name == 'apb_ave':
            samples = 250*(np.ceil(exposure_time*1005/250)) #hn I forget what that does... let's look into the new PB OPI
            yield from bps.abs_set(det.sample_len, samples, wait=True)
            yield from bps.abs_set(det.wf_len, samples, wait=True)
        elif det.name == 'pil100k':
            yield from bps.mv(det.cam.acquire_time, exposure_time)
        elif det.name == 'xs':
            yield from bps.mv(det.settings.acquire_time, exposure_time)


def get_n_exposures_plan_md(name, comment, energy, detectors, n_exposures, dwell_time, metadata):
        fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.dat"
        fn = validate_file_exists(fn)

        md_general = get_general_md()
        md_scan = {'experiment': 'collect_n_exposures',
                   'interp_filename': fn,
                   'name': name,
                   'comment': comment,
                   'hhm_energy' : energy,
                   'detectors': detectors,
                   'n_exposures' : n_exposures,
                   'dwell_time' : dwell_time,
                   'plot_hint': '$5/$1'}

        return {**md_general, **md_scan, **metadata}


def general_n_exposures(detectors, n_exposures, dwell_time, md):
    yield from prepare_detectors_for_exposure_plan(detectors, n_exposures=n_exposures)
    yield from set_detector_exposure_time_plan(detectors, dwell_time)
    yield from shutter.open_plan()
    yield from bp.count(detectors, n_exposures, md=md)
    yield from shutter.close_plan()


def collect_n_exposures_plan(name : str = '', comment : str = '',
                             n_exposures : int = 1, dwell_time : float = 1.0,
                             mono_energy : float = 7112,
                             detectors : list = [], mono_angle_offset=None, metadata={}):

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    default_detectors = [apb_ave, hhm_encoder]
    aux_detectors = get_detector_device_list(detectors)
    all_detectors = default_detectors + aux_detectors

    md = get_n_exposures_plan_md(name, comment, mono_energy, detectors, n_exposures, dwell_time, metadata)

    yield from bps.mv(hhm.energy, mono_energy)
    yield from general_n_exposures(all_detectors, n_exposures, dwell_time, md)







