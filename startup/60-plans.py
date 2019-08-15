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



def energy_scan(start, stop, num, flyers=None, name='', **metadata):
    """
    Example
    -------
    >>> RE(energy_scan(11350, 11450, 2))
    """
    if flyers is None:
        flyers = [pb9.enc1, pba2.adc6, pba1.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'step scan', 'name': name}
        md.update(**metadata)
        yield from bps.open_run(md=md)

    # Start with a step scan.
    plan = bp.scan([hhm_en.energy], hhm_en.energy, start, stop, num, md={'name': name})
    # Wrap it in a fly scan with the Pizza Box.
    plan = bpp.fly_during_wrapper(plan, flyers)
    # Working around a bug in fly_during_wrapper, stage and unstage the pizza box manually.

    for flyer in flyers:
        yield from bps.stage(flyer)
    yield from bps.stage(hhm)

    plan = bpp.pchain(plan)

    yield from plan


def energy_multiple_scans(start, stop, repeats, name='', **metadata):
    """
    Example
    -------
    >>> RE(energy_scan(11350, 11450, 2))
    """
    flyers = [pb9.enc1, pba2.adc6, pba1.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'energy_multiple_scans', 'name': name}
        md.update(**metadata)
        yield from bps.open_run(md=md)

        for i in range(0, repeats):
            print('Run:', i+1)
            hhm_en.energy.move(start)
            ttime.sleep(2)
            while (hhm_en.energy.moving == True):
                ttime.sleep(.1)
            hhm_en.energy.move(stop)
            ttime.sleep(2)
            while (hhm_en.energy.moving == True):
                ttime.sleep(.1)

        yield from bps.close_run()


    for flyer in flyers:
        yield from bps.stage(flyer)
    yield from bps.stage(hhm)

    yield from bpp.fly_during_wrapper(inner(), flyers)

    yield from bps.unstage(hhm)
    for flyer in flyers:
        yield from bps.unstage(flyer)



def get_offsets_plan(detectors, num = 1, name = '', **metadata):
    """
    Example
    -------
    >>> RE(get_offset([pba1.adc1, pba1.adc6, pba1.adc7, pba2.adc6]))
    """

    flyers = detectors

    plan = bp.count(flyers, num, md={'plan_name': 'get_offset', 'name': name}, delay = 0.5)

    def set_offsets():
        for flyer in flyers:
            ret = flyer.volt.value
            yield from bps.abs_set(flyer.offset, ret, wait=True)

    return (yield from bpp.fly_during_wrapper(bpp.finalize_wrapper(plan, set_offsets()), flyers))



def tune(detectors, motor, start, stop, num, name='', **metadata):
    """
    Example
    -------
    >>> RE(tune([pba1.adc7], hhm.pitch,-2, 2, 5, ''), LivePlot('pba1.adc7_volt', 'hhm_pitch'))
    """

    flyers = detectors 

    plan = bp.relative_scan(flyers, motor, start, stop, num, md={'plan_name': 'tune ' + motor.name, 'name': name})
    
    if hasattr(flyers[0], 'kickoff'):
        plan = bpp.fly_during_wrapper(plan, flyers)
        plan = bpp.pchain(plan)

    yield from plan



def step_list_plan(detectors, motor, positions_grid, name = ''):
    """
    Example
    -------
    >>> Ni_energy_grid, time_grid = get_xia_energy_grid(8333, -200, -50, 30, 16, 10, 0.2, 0.04)
    >>> Ni_positions_grid = xray.energy2encoder(Ni_energy_grid) / 360000
    >>> RE(step_list_plan([xia1, pba1.adc7], hhm.theta, Ni_positions_grid), LivePlot('xia1_mca1_roi0_sum', 'hhm_theta'))
    """
    
    plan = bp.list_scan(detectors, motor, list(positions_grid), md={'name': name, 'plan_name': 'step_list_plan'})
    
    flyers = []
    for det in detectors:
        if hasattr(det, 'kickoff'):
            flyers.append(det)
            
    if len(flyers) > 0:
        plan = bpp.fly_during_wrapper(plan, flyers)
        
    yield from plan
    

    
def step_xia_scan(motor, filename, energy_grid, integration_times = np.array([])):
    """
    Example
    -------
    >>> TODO
    """
    xia1_chan1_array = []
    xia1_chan2_array = []
    xia1_chan3_array = []
    xia1_chan4_array = []
    i0_array = []

    if(len(integration_times)) == 0:
        integration_times = np.ones(len(energy_grid)) * xia1.real_time.value

    #energy_grid = np.arange(7112 - 50, 7112 + 50, 1)#get_xia_energy_grid(energy_start, e0, edge_start, edge_end, energy_end, preedge_spacing, xanes, exafsk)

    pba1.adc7.filepath.put('')
    pba1.adc7.enable_sel.put(0)
    xia1.collect_mode.put(0)
    while(xia1.collect_mode.value != 0):
        ttime.sleep(.01)
    for i in range(len(energy_grid)):
        print("[{}/{}]".format(i + 1, len(energy_grid)))
        if(xia1.real_time.value != integration_times[i]):
            xia1.real_time.put(integration_times[i])
        ttime.sleep(.005)
        motor.move(xray.energy2encoder(energy_grid[i])/360000)
        while(np.abs(motor.read()['hhm_theta']['value'] - motor.read()['hhm_theta_user_setpoint']['value']) > 0.00001 or motor.moving == True):
            ttime.sleep(.005)

        xia1.erase_start.put(1)
        ttime.sleep(.1)
        while(xia1.acquiring.value):
            ttime.sleep(.005)
        
        ttime.sleep(.1)

        i0_array.append([energy_grid[i], pba1.adc7.volt.value])
        xia1_chan1_array.append(xia1.mca_array1.value)
        xia1_chan2_array.append(xia1.mca_array2.value)
        xia1_chan3_array.append(xia1.mca_array3.value)
        xia1_chan4_array.append(xia1.mca_array4.value)
        
    pba1.adc7.enable_sel.put(1)
    
    np.savetxt('/GPFS/xf08id/xia_files/' + filename + '-i0', np.array(i0_array))
    np.savetxt('/GPFS/xf08id/xia_files/' + filename + '-1', np.array(xia1_chan1_array))
    np.savetxt('/GPFS/xf08id/xia_files/' + filename + '-2', np.array(xia1_chan2_array))
    np.savetxt('/GPFS/xf08id/xia_files/' + filename + '-3', np.array(xia1_chan3_array))
    np.savetxt('/GPFS/xf08id/xia_files/' + filename + '-4', np.array(xia1_chan4_array))

def general_scan_plan(detectors, motor, rel_start, rel_stop, num):
    
    plan = bp.relative_scan(detectors, motor, rel_start, rel_stop, num)
    
    if hasattr(detectors[0], 'kickoff'):
        plan = bpp.fly_during_wrapper(plan, detectors)

    yield from plan


def sampleXY_plan(detectors, motor, start, stop, num):
    """
    Example
    -------
    >>> RE(sampleXY_plan([pba1.adc7], samplexy.x, -2, 2, 5, ''), LivePlot('pba1.adc7_volt', 'samplexy_x'))
    """

    flyers = detectors 

    plan = bp.relative_scan(flyers, motor, start, stop, num)
    
    if hasattr(flyers[0], 'kickoff'):
        plan = bpp.fly_during_wrapper(plan, flyers)
        # Check if I can remove bpp.pchain

    yield from plan


def pb_scan_plan(detectors, motor, scan_center, scan_range, name = ''):
    flyers = detectors
    def inner():
        md = {'plan_args': {}, 'plan_name': 'pb_scan','experiment': 'pb_scan', 'name': name}
        #md.update(**metadata)
        yield from bps.open_run(md=md)
        yield from bps.sleep(.4)
        yield from bps.clear_checkpoint()
        yield from bps.abs_set(motor, scan_center + (scan_range / 2), wait=True)
        yield from bps.sleep(.4)
        yield from bps.close_run()
        yield from shutter.close_plan()
        yield from bps.abs_set(motor, scan_center, wait=True)

    def final_plan():
        for flyer in flyers:
            yield from bps.unstage(flyer)
        yield from bps.unstage(motor)

    yield from bps.abs_set(motor, scan_center - (scan_range / 2), wait=True)

    yield from shutter.open_plan()
    for flyer in flyers:
        yield from bps.stage(flyer)

    yield from bps.stage(motor)

    return (yield from bpp.fly_during_wrapper(bpp.finalize_wrapper(inner(), final_plan()),
                                              flyers))




def prep_traj_plan(delay = 0.05):
    yield from bps.abs_set(hhm.prepare_trajectory, '1', wait=True)

    # Poll the trajectory ready pv
    while True:
        ret = (yield from bps.read(hhm.trajectory_ready))
        if ret is None:
            break
        is_running = ret['hhm_trajectory_ready']['value']

        if is_running:
            break
        else:
            yield from bps.sleep(.1)

    while True:
        ret = (yield from bps.read(hhm.trajectory_ready))
        if ret is None:
            break
        is_running = ret['hhm_trajectory_ready']['value']

        if is_running:
            yield from bps.sleep(.05)
        else:
            break

    yield from bps.sleep(delay)

    curr_energy = (yield from bps.read(hhm.energy))

    if curr_energy is None:
        return
        raise Exception('Could not read current energy')

    curr_energy = curr_energy['hhm_energy']['value']
    print('Curr Energy: {}'.format(curr_energy))
    if curr_energy >= 10000:
        print('>10000')
        yield from bps.mv(hhm.energy, curr_energy + 200)
        yield from bps.sleep(1)
        yield from bps.mv(hhm.energy, curr_energy)
        yield from bps.sleep(1)




def set_gains_plan(*args):
    """
    Parameters
    ----------
    Groups of three parameters: amplifier, gain, hs

    Example: set_gains_and_offsets(i0_amp, 5, False, it_amp, 4, False, iff_amp, 5, True)
    """

    mod = len(args) % 3
    if mod:
        args = args[:-mod]

    for ic, val, hs in zip([ic for index, ic in enumerate(args) if index % 3 == 0],
                       [val for index, val in enumerate(args) if index % 3 == 1],
                       [hs for index, hs in enumerate(args) if index % 3 == 2]):
        yield from ic.set_gain_plan(val, hs)

        if type(ic) != ICAmplifier:
            raise Exception('Wrong type: {} - it should be ICAmplifier'.format(type(ic)))
        if type(val) != int:
            raise Exception('Wrong type: {} - it should be int'.format(type(val)))
        if type(hs) != bool:
            raise Exception('Wrong type: {} - it should be bool'.format(type(hs)))

        print('set amplifier gain for {}: {}, {}'.format(ic.par.dev_name.value, val, hs))


def tuning_scan(motor, detector, scan_range, scan_step, n_tries = 3, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    channel = detector.hints['fields'][0]
    for jj in range(n_tries):
        motor_init_position = motor.read()[motor.name]['value']
        min_limit = motor_init_position - scan_range / 2
        max_limit = motor_init_position + scan_range / 2 + scan_step / 2
        scan_positions = np.arange(min_limit,max_limit,scan_step)
        scan_range = (scan_positions[-1] - scan_positions[0])
        min_threshold = scan_positions[0] + scan_range / 10
        max_threshold = scan_positions[-1] - scan_range / 10
        plan = bp.list_scan([detector], motor,scan_positions)
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

def wait_filter_in_place(status_pv):
    # for j in range(5):
    while True:
        ret = yield from bps.read(status_pv)
        if ret is None:
            break
        if ret[status_pv.name]['value'] == 1:
            break
        else:
            yield from bps.sleep(.1)


def set_gains_and_offsets_plan(*args):
    """
    Parameters
    ----------
    Groups of three parameters: amplifier, gain, hs

    Example: set_gains_and_offsets(i0_amp, 5, False, it_amp, 4, False, iff_amp, 5, True)
    """

    mod = len(args) % 3
    if mod:
        args = args[:-mod]

    for ic, val, hs in zip([ic for index, ic in enumerate(args) if index % 3 == 0],
                           [val for index, val in enumerate(args) if index % 3 == 1],
                           [hs for index, hs in enumerate(args) if index % 3 == 2]):
        yield from ic.set_gain_plan(val, hs)
        yield from ic.set_gain_plan(val, hs)

        if type(ic) != ICAmplifier:
            raise Exception('Wrong type: {} - it should be ICAmplifier'.format(type(ic)))
        if type(val) != int:
            raise Exception('Wrong type: {} - it should be int'.format(type(val)))
        if type(hs) != bool:
            raise Exception('Wrong type: {} - it should be bool'.format(type(hs)))

        print('set amplifier gain for {}: {}, {}'.format(ic.par.dev_name.value, val, hs))
        if hs:
            hs_str = 'hs'
        else:
            hs_str = 'ln'
        yield from bps.mv(ic.par.offset, lut_offsets[ic.par.dev_name.value][hs_str][str(val)])
        print('{}.offset -> {}'.format(ic.par.dev_name.value, lut_offsets[ic.par.dev_name.value][hs_str][str(val)]))

