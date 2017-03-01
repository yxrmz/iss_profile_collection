import bluesky as bs
import bluesky.plans as bp
import time as ttime
import PyQt4.QtCore


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


def sampleXY_plan(detectors, motor, start, stop, num):
    """
    Example
    -------
    >>> RE(sampleXY_plan([pba1.adc7], samplexy.x, -2, 2, 5, ''), LivePlot('pba1.adc7_volt', 'samplexy_x'))
    """

    flyers = detectors 

    plan = bp.relative_scan(flyers, motor, start, stop, num)
    
    if hasattr(flyers[0], 'kickoff'):
        #plan = bp.fly_during_wrapper(plan, flyers)
        plan = bp.pchain(bp.fly_during_wrapper(plan, flyers))
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
    flyers = [pba1.adc6, pb9.enc1, pba1.adc1, pba2.adc6, pba1.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'execute_trajectory','experiment': 'transmission', 'comment': comment, pba1.adc1.name + ' offset': pba1.adc1.offset.value, pba1.adc6.name + ' offset': pba1.adc6.offset.value, pba2.adc6.name + ' offset': pba2.adc6.offset.value, pba1.adc7.name + ' offset': pba1.adc7.offset.value, 'trajectory_name': hhm.trajectory_name.value}
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
        yield from bp.clear_checkpoint()
        yield from shutter.open_plan()
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
        for flyer in flyers:
            yield from bp.unstage(flyer)
        yield from bp.unstage(hhm)

    for flyer in flyers:
        yield from bp.stage(flyer)

    yield from bp.stage(hhm)

    return (yield from bp.fly_during_wrapper(bp.finalize_wrapper(inner(), final_plan()),
                                              flyers))




def execute_xia_trajectory(comment, **metadata):
    flyers = [pba1.adc6, pb9.enc1, pba1.adc1, pba2.adc6, pba1.adc7, pb4.di]
    def inner():
        # Setting the name of the file
        xia1.netcdf_filename.put(comment) #yield from bp.abs_set(xia1.netcdf_filename, comment, wait=True)#
        next_file_number = xia1.netcdf_filenumber_rb.value #(yield from bp.read(xia1.netcdf_filenumber_rb))#

        md = {'plan_args': {}, 'plan_name': 'execute_xia_trajectory','experiment': 'fluorescence_sdd', 'comment': comment, 'xia_filename': '{}_{:03}.nc'.format(comment, next_file_number), pba1.adc1.name + ' offset': pba1.adc1.offset.value, pba1.adc6.name + ' offset': pba1.adc6.offset.value, pba2.adc6.name + ' offset': pba2.adc6.offset.value, pba1.adc7.name + ' offset': pba1.adc7.offset.value, 'trajectory_name': hhm.trajectory_name.value}
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
        yield from xia1.start_mapping_scan()
        # this must be a float
        yield from bp.abs_set(hhm.enable_loop, 0, wait=True)
        # this must be a string
        yield from bp.abs_set(hhm.start_trajectory, "1", wait=True)
		
		
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
        for flyer in flyers:
            yield from bp.unstage(flyer)
        yield from xia1.stop_scan()
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



