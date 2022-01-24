import bluesky as bs
import bluesky.plans as bp
import time as ttime
from subprocess import call
import os
from isstools.conversions import xray
import signal
from periodictable import elements

from ophyd.device import Kind
from xas.file_io import validate_file_exists
import time


def general_scan_plan(detectors, motor, rel_start, rel_stop, num):
    
    plan = bp.relative_scan(detectors, motor, rel_start, rel_stop, num)
    
    if hasattr(detectors[0], 'kickoff'):
        plan = bpp.fly_during_wrapper(plan, detectors)
    yield from shutter.open_plan()
    yield from plan
    yield from shutter.close_plan()

def general_scan(detectors, motor, rel_start, rel_stop, num, **kwargs):

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    #print(f'Dets {detectors}')
    #print(f'Motors {motor}')
    print('[General Scan] Starting scan...')
    uid =  yield from (general_scan_plan(detectors, motor, rel_start, rel_stop, int(num)))
    print('[General Scan] Done!')
    return uid


def tuning_scan(motor, detector, scan_range, scan_step, n_tries = 3, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    if type(motor) == list:
        motor2 = motor[1]
        motor = motor[0]
    else:
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
            print(f'New motor position {motor_pos}')

            if motor_pos < min_threshold:
                yield from bps.mv(motor,min_limit)
                if jj+1 < n_tries:
                    print(f' Starting {jj+2} try')
            elif max_threshold < motor_pos:
                print('max')
                if jj+1 < n_tries:
                    print(f' Starting {jj+2} try')
                yield from bps.mv(motor, max_limit)
            else:
                yield from bps.mv(motor, motor_pos)
                break




