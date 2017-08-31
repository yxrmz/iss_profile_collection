import bluesky as bs
import bluesky.plans as bp
import time as ttime
# import PyQt4.QtCore
from isstools.conversions import xray
import signal



def energy_scan(start, stop, num, flyers=[pb9.enc1, pba2.adc6, pba1.adc7], comment='', **metadata):
    """
    Example
    -------
    >>> RE(energy_scan(11350, 11450, 2))
    """
    def inner():
        md = {'plan_args': {}, 'plan_name': 'step scan', 'comment': comment}
        md.update(**metadata)
        yield from bp.open_run(md=md)

    # Start with a step scan.
    plan = bp.scan([hhm_en.energy], hhm_en.energy, start, stop, num, md={'comment': comment})
    # Wrap it in a fly scan with the Pizza Box.
    plan = bp.fly_during_wrapper(plan, flyers)
    # Working around a bug in fly_during_wrapper, stage and unstage the pizza box manually.

    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)

    plan = bp.pchain(plan)

    yield from plan


def energy_multiple_scans(start, stop, repeats, comment='', **metadata):
    """
    Example
    -------
    >>> RE(energy_scan(11350, 11450, 2))
    """
    flyers = [pb9.enc1, pba2.adc6, pba1.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'energy_multiple_scans', 'comment': comment}
        md.update(**metadata)
        yield from bp.open_run(md=md)

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

        yield from bp.close_run()


    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)

    yield from bp.fly_during_wrapper(inner(), flyers)

    yield from bp.unstage(hhm)
    for flyer in flyers:
        yield from bp.unstage(flyer)



def get_offsets_plan(detectors, num = 1, comment = '', **metadata):
    """
    Example
    -------
    >>> RE(get_offset([pba1.adc1, pba1.adc6, pba1.adc7, pba2.adc6]))
    """

    flyers = detectors 

    plan = bp.count(flyers, num, md={'plan_name': 'get_offset', 'comment': comment}, delay = 0.5)

    def set_offsets():
        for flyer in flyers:
            ret = flyer.volt.value
            yield from bp.abs_set(flyer.offset, ret, wait=True)

    yield from bp.fly_during_wrapper(bp.finalize_wrapper(plan, set_offsets()), flyers)



def tune(detectors, motor, start, stop, num, comment='', **metadata):
    """
    Example
    -------
    >>> RE(tune([pba1.adc7], hhm.pitch,-2, 2, 5, ''), LivePlot('pba1.adc7_volt', 'hhm_pitch'))
    """

    flyers = detectors 

    plan = bp.relative_scan(flyers, motor, start, stop, num, md={'plan_name': 'tune ' + motor.name, 'comment': comment})
    
    if hasattr(flyers[0], 'kickoff'):
        plan = bp.fly_during_wrapper(plan, flyers)
        plan = bp.pchain(plan)

    yield from plan

def get_xia_energy_grid(e0, preedge_start, xanes_start, xanes_end, exafs_end, preedge_spacing, xanes_spacing, exafsk_spacing, int_time_preedge = 1, int_time_xanes = 1, int_time_exafs = 1, k_power = 0):
    preedge = np.arange(e0 + preedge_start, e0 + xanes_start, preedge_spacing)
    preedge_int = np.ones(len(preedge)) * int_time_preedge

    edge = np.arange(e0 + xanes_start, e0 + xanes_end, xanes_spacing)
    edge_int = np.ones(len(edge)) * int_time_xanes

    iterator = exafsk_spacing
    kenergy = 0
    postedge = np.array([])

    energy_end = xray.k2e(exafs_end, e0)
    exafs_int = []
    while(kenergy + e0 + xanes_end < energy_end):
        kenergy = xray.k2e(iterator, e0) - e0
        postedge = np.append(postedge, e0 + xanes_end + kenergy)
        exafs_int.append(int_time_exafs * (iterator ** k_power))
        iterator += exafsk_spacing

    integration_times = np.append(np.append(preedge_int, edge_int), np.array(exafs_int))
    grid = np.append(np.append(preedge, edge), postedge)
    return grid[::-1], integration_times
    #return np.append(np.append(preedge, edge), postedge)

def step_list_plan(detectors, motor, positions_grid, comment = ''):
    """
    Example
    -------
    >>> Ni_energy_grid, time_grid = get_xia_energy_grid(8333, -200, -50, 30, 16, 10, 0.2, 0.04)
    >>> Ni_positions_grid = xray.energy2encoder(Ni_energy_grid) / 360000
    >>> RE(step_list_plan([xia1, pba1.adc7], hhm.theta, Ni_positions_grid), LivePlot('xia1_mca1_roi0_sum', 'hhm_theta'))
    """
    
    plan = bp.list_scan(detectors, motor, list(positions_grid), md={'comment': comment, 'plan_name': 'step_list_plan'})
    
    flyers = []
    for det in detectors:
        if hasattr(det, 'kickoff'):
            flyers.append(det)
            
    if len(flyers) > 0:
        plan = bp.fly_during_wrapper(plan, flyers)
        
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
        plan = bp.fly_during_wrapper(plan, detectors)

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
        plan = bp.fly_during_wrapper(plan, flyers)
        # Check if I can remove bp.pchain

    yield from plan


def pb_scan_plan(detectors, motor, scan_center, scan_range, comment = ''):

    flyers = detectors
    def inner():
        md = {'plan_args': {}, 'plan_name': 'pb_scan','experiment': 'pb_scan', 'comment': comment}
        #md.update(**metadata)
        yield from bp.open_run(md=md)
        yield from bp.sleep(.4)
        yield from bp.clear_checkpoint()
        yield from bp.abs_set(motor, scan_center + (scan_range / 2), wait=True)
        yield from bp.sleep(.4)
        yield from bp.close_run()
        yield from shutter.close_plan()
        yield from bp.abs_set(motor, scan_center, wait=True)

    def final_plan():
        for flyer in flyers:
            yield from bp.unstage(flyer)
        yield from bp.unstage(motor)

    yield from bp.abs_set(motor, scan_center - (scan_range / 2), wait=True)

    yield from shutter.open_plan()
    for flyer in flyers:
        yield from bp.stage(flyer)

    yield from bp.stage(motor)

    return (yield from bp.fly_during_wrapper(bp.finalize_wrapper(inner(), final_plan()),
                                              flyers))


def prep_trajectory(delay = 1):
    hhm.prepare_trajectory.put("1")
    while (hhm.trajectory_ready.value == 0):
        ttime.sleep(.1)
    while (hhm.trajectory_ready.value == 1):
        ttime.sleep(.1)
    ttime.sleep(delay)


def prep_traj_plan(delay = 0.25):
    yield from bp.abs_set(hhm.prepare_trajectory, '1', wait=True)

    # Poll the trajectory ready pv
    while True:
        ret = (yield from bp.read(hhm.trajectory_ready))
        if ret is None:
            break
        is_running = ret['hhm_trajectory_ready']['value']

        if is_running:
            break
        else:
            yield from bp.sleep(.1)

    while True:
        ret = (yield from bp.read(hhm.trajectory_ready))
        if ret is None:
            break
        is_running = ret['hhm_trajectory_ready']['value']

        if is_running:
            yield from bp.sleep(.05)
        else:
            break

    yield from bp.sleep(delay)


def execute_trajectory(comment, **metadata):
    flyers = [pb4.di, pba2.adc7, pba1.adc6, pb9.enc1, pba1.adc1, pba2.adc6, pba1.adc7]
    def inner():
        md = {'plan_args': {}, 
              'plan_name': 'execute_trajectory',
              'experiment': 'transmission', 
              'comment': comment, 
              'trajectory_name': hhm.trajectory_name.value,
              'angle_offset': str(hhm.angle_offset.value)}
        for flyer in flyers:
            if hasattr(flyer, 'offset'):
                md['{} offset'.format(flyer.name)] = flyer.offset.value
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
        yield from bp.clear_checkpoint()
        yield from shutter.open_plan()
        yield from xia1.start_trigger()
        # this must be a float
        yield from bp.abs_set(hhm.enable_loop, 0, wait=True)
        # this must be a string
        yield from bp.abs_set(hhm.start_trajectory, '1', wait=True)

        # this should be replaced by a status object
        def poll_the_traj_plan():
            while True:
                ret = (yield from bp.read(hhm.trajectory_running))
                if ret is None:
                    break
                is_running = ret['hhm_trajectory_running']['value']

                if is_running:
                    break
                else:
                    yield from bp.sleep(.1)

            while True:
                ret = (yield from bp.read(hhm.trajectory_running))
                if ret is None:
                    break
                is_running = ret['hhm_trajectory_running']['value']

                if is_running:
                    yield from bp.sleep(.05)
                else:
                    break


        yield from bp.finalize_wrapper(poll_the_traj_plan(), 
                                       bp.pchain(shutter.close_plan(), 
                                                 bp.abs_set(hhm.stop_trajectory, 
                                                            '1', wait=True)))

        yield from bp.close_run()

    def final_plan():
        yield from bp.abs_set(hhm.trajectory_running, 0, wait=True)
        yield from xia1.stop_trigger()
        for flyer in flyers:
            yield from bp.unstage(flyer)
        yield from bp.unstage(hhm)

    for flyer in flyers:
        yield from bp.stage(flyer)

    yield from bp.stage(hhm)

    return (yield from bp.fly_during_wrapper(bp.finalize_wrapper(inner(), final_plan()),
                                              flyers))


def execute_xia_trajectory(comment, **metadata):
    flyers = [pba2.adc7, pba1.adc6, pb9.enc1, pba1.adc1, pba2.adc6, pba1.adc7, pb4.di]
    def inner():
        # Setting the name of the file
        xia1.netcdf_filename.put(comment)
        next_file_number = xia1.netcdf_filenumber_rb.value

        xia_rois = {}
        max_energy = xia1.mca_max_energy.value
        for mca in xia1.read_attrs:
            for roi in range(12):
                if not (eval('xia1.{}.roi{}.low.value'.format(mca, roi)) < 0 or eval('xia1.{}.roi{}.high.value'.format(mca, roi)) < 0):
                    xia_rois[eval('xia1.{}.roi{}.high.name'.format(mca, roi))] = eval('xia1.{}.roi{}.high.value'.format(mca, roi)) * max_energy / 2048
                    xia_rois[eval('xia1.{}.roi{}.low.name'.format(mca, roi))] = eval('xia1.{}.roi{}.low.value'.format(mca, roi)) * max_energy / 2048

        md = {'plan_args': {}, 
              'plan_name': 'execute_xia_trajectory',
              'experiment': 'fluorescence_sdd', 
              'comment': comment, 
              'xia_max_energy': xia1.mca_max_energy.value,
              'xia_filename': '{}_{:03}.nc'.format(comment, next_file_number), 
              'xia_rois':xia_rois, 
              'trajectory_name': hhm.trajectory_name.value,
              'angle_offset': str(hhm.angle_offset.value)}
        for flyer in flyers:
            if hasattr(flyer, 'offset'):
                md['{} offset'.format(flyer.name)] = flyer.offset.value
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
        yield from bp.clear_checkpoint()

        name = ''.join(chr(i) for i in list(xia1.netcdf_filename_rb.value))
        name = name[0:len(name) - 1]
        while(name != comment):
            name = ''.join(chr(i) for i in list(xia1.netcdf_filename_rb.value))
            name = name[0:len(name) - 1]
            yield from bp.sleep(.05)
       
        yield from shutter.open_plan()
        yield from bp.sleep(.5)
        yield from xia1.start_mapping_scan()
        yield from bp.sleep(.5)

        # this must be a float
        yield from bp.abs_set(hhm.enable_loop, 0, wait=True)
        yield from bp.sleep(.5)
        # this must be a string
        yield from bp.abs_set(hhm.start_trajectory, "1", wait=True)
        yield from bp.sleep(.5)

        def poll_the_traj_plan():
            while True:
                ret = (yield from bp.read(hhm.trajectory_running))
                if ret is None:
                    break
                is_running = ret['hhm_trajectory_running']['value']

                if is_running:
                    break
                else:
                    yield from bp.sleep(.1)

            while True:
                ret = (yield from bp.read(hhm.trajectory_running))
                if ret is None:
                    break
                is_running = ret['hhm_trajectory_running']['value']

                if is_running:
                    yield from bp.sleep(.05)
                else:
                    break


        yield from bp.finalize_wrapper(poll_the_traj_plan(), 
                                       bp.pchain(xia1.stop_scan(),
                                                 shutter.close_plan(), 
                                                 bp.abs_set(hhm.stop_trajectory, 
                                                            '1', wait=True)))

        yield from bp.close_run()

    def final_plan():
        yield from bp.abs_set(hhm.trajectory_running, 0, wait=True)
#        yield from xia1.stop_scan()
        while xia1.capt_start_stop.value:
            pass
        print('Stopped XIA')
        for flyer in flyers:
            yield from bp.unstage(flyer)
        yield from bp.unstage(hhm)

    for flyer in flyers:
        yield from bp.stage(flyer)

    yield from bp.stage(hhm)

    return (yield from bp.fly_during_wrapper(bp.finalize_wrapper(inner(), final_plan()), flyers))


def execute_loop_trajectory(comment, **metadata):

    flyers = [pba1.adc6, pb9.enc1, pba1.adc1, pba2.adc6, pba1.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'execute_loop_trajectory','experiment': 'transmission', 'comment': comment, pba1.adc1.name + ' offset': pba1.adc1.offset.value, pba1.adc6.name + ' offset': pba1.adc6.offset.value, pba2.adc6.name + ' offset': pba2.adc6.offset.value, pba1.adc7.name + ' offset': pba1.adc7.offset.value, 'trajectory_name': hhm.trajectory_name.value}
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
        yield from shutter.open_plan()
        yield from bp.abs_set(hhm.enable_loop, 1, wait=True)#hhm.enable_loop.put("1")
        yield from bp.abs_set(hhm.start_trajectory, "1", wait=True) # NOT SURE IF THIS LINE SHOULD BE HERE

        def poll_the_traj_plan():
            while True:
                ret = (yield from bp.read(hhm.trajectory_running))
                if ret is None:
                    break
                is_running = ret['hhm_trajectory_running']['value']

                if is_running:
                    break
                else:
                    yield from bp.sleep(.1)

            while True:
                ret = (yield from bp.read(hhm.trajectory_running))
                retloop = (yield from bp.read(hhm.enable_loop_rbv))
                if ret is None or retloop is None:
                    break
                loop_is_running = retloop['hhm_enable_loop_rbv']['value']

                if loop_is_running:
                    yield from bp.sleep(.05)
                else:
                    break

        yield from bp.finalize_wrapper(poll_the_traj_plan(), 
                                       bp.pchain(shutter.close_plan(), 
                                                 bp.abs_set(hhm.stop_trajectory, 
                                                            '1', wait=True), 
                                                 bp.abs_set(hhm.enable_loop, 
                                                            0, wait=True)))

        yield from bp.close_run()

    def final_plan():
        yield from bp.abs_set(hhm.trajectory_running, 0, wait=True)
        for flyer in flyers:
            yield from bp.unstage(flyer)
        yield from bp.unstage(hhm)

    for flyer in flyers:
        yield from bp.stage(flyer)

    yield from bp.stage(hhm)

    return (yield from bp.fly_during_wrapper(bp.finalize_wrapper(inner(), final_plan()),
                                              flyers))


def wait_filter_in_place(status_pv):
    #for j in range(5):
    while True:
        ret = yield from bp.read(status_pv)
        if ret is None:
            break
        if ret[status_pv.name]['value'] == 1:
            break
        else:
            yield from bp.sleep(.1)


def prepare_bl_plan(energy: int = -1, debug=False):
    if debug:
        print('[Prepare BL] Running Prepare Beamline in Debug Mode! (Not moving anything)')

    energy = int(energy)
    if energy < 0:
        curr_energy = (yield from bp.read(hhm.energy))[hhm.energy.name]['value']
    else:
        curr_energy = energy

    print('[Prepare BL] Setting up the beamline to {} eV'.format(curr_energy))

    curr_range = [ran for ran in prepare_bl_def[0] if
                  ran['energy_end'] > 8000 >= ran['energy_start']]
    if not len(curr_range):
        print('Current energy is not valid. :( Aborted.')
        return

    curr_range = curr_range[0]
    pv_he = curr_range['pvs']['IC Gas He']['object']
    print('[Prepare BL] Setting HE to {}'.format(curr_range['pvs']['IC Gas He']['value']))
    if not debug:
        yield from bp.mv(pv_he, curr_range['pvs']['IC Gas He']['value'])

    pv_n2 = curr_range['pvs']['IC Gas N2']['object']
    print('[Prepare BL] Setting N2 to {}'.format(curr_range['pvs']['IC Gas N2']['value']))
    if not debug:
        yield from bp.mv(pv_n2, curr_range['pvs']['IC Gas N2']['value'])

    # If you go from less than 1000 V to more than 1400 V, you need a delay. 2 minutes
    # For now if you increase the voltage (any values), we will have the delay. 2 minutes

    pv_i0_volt = curr_range['pvs']['I0 Voltage']['object']
    old_i0 = (yield from bp.read(pv_i0_volt))[pv_i0_volt.name]['value']
    print('[Prepare BL] Old I0 Voltage: {} | New I0 Voltage: {}'.format(old_i0,
                                                                        curr_range['pvs']['I0 Voltage']['value']))

    pv_it_volt = curr_range['pvs']['It Voltage']['object']
    old_it = (yield from bp.read(pv_it_volt))[pv_it_volt.name]['value']
    print('[Prepare BL] Old It Voltage: {} | New It Voltage: {}'.format(old_it,
                                                                        curr_range['pvs']['It Voltage']['value']))

    pv_ir_volt = curr_range['pvs']['Ir Voltage']['object']
    old_ir = (yield from bp.read(pv_ir_volt))[pv_ir_volt.name]['value']
    print('[Prepare BL] Old Ir Voltage: {} | New Ir Voltage: {}'.format(old_ir,
                                                                        curr_range['pvs']['Ir Voltage']['value']))

    # check if bpm_cm will move
    close_shutter = 0
    cm = [bpm for bpm in curr_range['pvs']['BPMs'] if bpm['name'] == bpm_cm.name][0]
    new_cm_value = cm['value']
    if new_cm_value == 'OUT':
        pv = cm['object'].switch_retract
    elif new_cm_value == 'IN':
        pv = cm['object'].switch_insert
    yield from bp.sleep(0.1)
    if (yield from bp.read(pv))[pv.name]['value'] == 0:
        close_shutter = 1

    # check if filtebox will move
    mv_fb = 0
    fb_value = prepare_bl_def[1]['FB Positions'][curr_range['pvs']['Filterbox Pos']['value'] - 1]
    pv_fb_motor = curr_range['pvs']['Filterbox Pos']['object']
    yield from bp.sleep(0.1)
    curr_fb_value = (yield from bp.read(pv_fb_motor))[pv_fb_motor.name]['value']
    if abs(fb_value - curr_fb_value) > 20 * (10 ** (-pv_fb_motor.precision)):
        close_shutter = 1
        mv_fb = 1

    def handler(signum, frame):
        print("[Prepare BL] Could not activate FE Shutter")
        raise Exception("Timeout")

    if close_shutter:
        print('[Prepare BL] Closing FE Shutter...')
        if not debug:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(6)
            try:
                yield from shutter_fe.close_plan()
            except Exception as exc:
                print('[Prepare BL] Timeout! Could not close FE Shutter. Aborting! (Try once again, maybe?)')
                return

            tries = 3
            while (yield from bp.read(shutter_fe.state))[shutter_fe.state.name]['value'] != 1:
                yield from bp.sleep(0.1)
                if tries:
                    yield from shutter_fe.close_plan()
                    tries -= 1

            signal.alarm(0)
        print('[Prepare BL] FE Shutter closed')

    yield from bp.sleep(0.1)
    fb_sts_pv = curr_range['pvs']['Filterbox Pos']['STS PVS'][curr_range['pvs']['Filterbox Pos']['value'] - 1]
    if mv_fb:
        print('[Prepare BL] Moving Filterbox to {}'.format(fb_value))
        if not debug:
            yield from bp.abs_set(pv_fb_motor, fb_value, group='prepare_bl')

    pv_hhrm_hor = curr_range['pvs']['HHRM Hor Trans']['object']
    yield from bp.sleep(0.1)
    print('[Prepare BL] Moving HHRM Horizontal to {}'.format(curr_range['pvs']['HHRM Hor Trans']['value']))
    if not debug:
        yield from bp.abs_set(pv_hhrm_hor, curr_range['pvs']['HHRM Hor Trans']['value'], group='prepare_bl')

    bpm_pvs = []
    for bpm in curr_range['pvs']['BPMs']:
        if bpm['value'] == 'IN':
            pv_set = bpm['object'].ins
            pv_read = bpm['object'].switch_insert
        elif bpm['value'] == 'OUT':
            pv_set = bpm['object'].ret
            pv_read = bpm['object'].switch_retract
        try:
            if pv:
                print('[Prepare BL] Moving {} {}'.format(bpm['name'], bpm['value']))
                for i in range(3):
                    if not debug:
                        yield from bp.abs_set(pv_set, 1)
                    yield from bp.sleep(0.1)
                bpm_pvs.append([pv_set, pv_read])
        except Exception as exp:
            print(exp)

    if close_shutter:
        yield from wait_filter_in_place(fb_sts_pv)
        #while fb_sts_pv.value != 1:
        #    pass
        print('[Prepare BL] Opening shutter...')
        if not debug:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(6)
            try:
                yield from shutter_fe.open_plan()
            except Exception as exc:
                print('[Prepare BL] Timeout! Could not open FE Shutter. Aborting! (Try once again, maybe?)')
                return

            tries = 3
            while (yield from bp.read(shutter_fe.state))[shutter_fe.state.name]['value'] != 1:
                yield from bp.sleep(0.1)
                if tries:
                    yield from shutter_fe.open_plan()
                    tries -= 1

            signal.alarm(0)
        print('[Prepare BL] FE Shutter open')

    if curr_range['pvs']['I0 Voltage']['value'] - old_i0 > 2 or \
            curr_range['pvs']['It Voltage']['value'] - old_it > 2 or \
            curr_range['pvs']['Ir Voltage']['value'] - old_ir > 2:
        old_time = ttime.time()
        wait_time = 120
        print('[Prepare BL] Waiting for gas ({}s)...'.format(wait_time))
        percentage = 0
        if not debug:
            while ttime.time() - old_time < wait_time:  # 120 seconds
                if ttime.time() - old_time >= percentage * wait_time:
                    print(
                        '[Prepare BL] {:3}% ({:.1f}s)'.format(int(np.round(percentage * 100)), percentage * wait_time))
                    percentage += 0.1
                yield from bp.sleep(0.1)
        print('[Prepare BL] 100% ({:.1f}s)'.format(wait_time))
        print('[Prepare BL] Done waiting for gas...')

    print('[Prepare BL] Setting i0 {}'.format(curr_range['pvs']['I0 Voltage']['value']))
    print('[Prepare BL] Setting it {}'.format(curr_range['pvs']['It Voltage']['value']))
    print('[Prepare BL] Setting ir {}'.format(curr_range['pvs']['Ir Voltage']['value']))
    if not debug:
        yield from bp.abs_set(pv_i0_volt, curr_range['pvs']['I0 Voltage']['value'], group='prepare_bl')
        yield from bp.abs_set(pv_it_volt, curr_range['pvs']['It Voltage']['value'], group='prepare_bl')
        yield from bp.abs_set(pv_ir_volt, curr_range['pvs']['Ir Voltage']['value'], group='prepare_bl')

    yield from bp.sleep(0.1)

    print('[Prepare BL] Waiting for everything to be in position...')
    if not debug:
        yield from bp.wait(group='prepare_bl')
    print('[Prepare BL] Everything seems to be in position')
    print('[Prepare BL] Beamline preparation done!')

#    yield from bp.mv(hhm.energy, E)
#    yield from bp.mv(other_thing, f(E))
#    yield from bp.mv(t1, v1, t2, v2)
#    yield from bp.abs_set(motor, val, group='A')
#    yield from bp.abs_set(motor2, val2, group='A')
#    yield from bp.wait(group='A')


def sleep_plan(sleep_time, **metadata):
    yield from bp.sleep(float(sleep_time))
