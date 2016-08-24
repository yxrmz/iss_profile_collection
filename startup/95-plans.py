import bluesky as bs
import bluesky.plans as bp
import time as ttime


def fly_testing(flyers):
    def inner():
        yield from open_run()
        # maybe?
        # yield from upload_to_controller
        #st = yield from start_the_controller()
        #yield from wait_for(st)
        yield from sleep(50)
        yield from close_run()
        
    yield from fly_during_wrapper(inner(), flyers)


def repeater(count, plan, *args, **kwargs):
    for j in range(count):
        yield from plan(*args, **kwargs)


def energy_scan(start, stop, num, flyers=[pb9.enc1, pba2.adc6, pba2.adc7], comment='', **metadata):
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
    #plan = bp.pchain(bp.stage(pb9.enc1), bp.stage(pba2.adc6), bp.stage(pba2.adc7),
    #                 plan,
    #                 bp.unstage(pb9.enc1), bp.unstage(pba2.adc6), bp.unstage(pba2.adc7))
    yield from plan

def hhm_theta_scan(start, stop, num, flyers=[pb9.enc1, pba2.adc6, pba2.adc7], comment='', **metadata):
    """
    Example
    -------
    >>> RE(hhm_theta_scan(-0.1, 0.1, 2, [pb4.di, xia]))
    """
    def inner():
        md = {'plan_args': {}, 'plan_name': 'step scan', 'comment': comment}
        md.update(**metadata)
        yield from bp.open_run(md=md)

    # Start with a step scan.
    plan = bp.relative_scan([hhm_en.energy], hhm_en.energy, start, stop, num, md={'comment': comment})
    # Wrap it in a fly scan with the Pizza Box.
    plan = bp.fly_during_wrapper(plan, flyers)
    # Working around a bug in fly_during_wrapper, stage and unstage the pizza box manually.

    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)

    plan = bp.pchain(plan)
    #plan = bp.pchain(bp.stage(pb9.enc1), bp.stage(pba2.adc6), bp.stage(pba2.adc7),
    #                 plan,
    #                 bp.unstage(pb9.enc1), bp.unstage(pba2.adc6), bp.unstage(pba2.adc7))
    yield from plan

def energy_multiple_scans(start, stop, repeats, comment='', **metadata):
    """
    Example
    -------
    >>> RE(energy_scan(11350, 11450, 2))
    """
    flyers = [pb9.enc1, pba2.adc6, pba2.adc7]
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
        #write_file(comment, [flyers[0].filepath.value, flyers[1].filepath.value, flyers[2].filepath.value] , '')

        yield from bp.close_run()


    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)

    yield from bp.fly_during_wrapper(inner(), flyers)

    yield from bp.unstage(hhm)
    for flyer in flyers:
        yield from bp.unstage(flyer)



def tune(detectors, motor, start, stop, num, comment='', **metadata):
    """
    Example
    -------
    >>> RE(tune([pba2.adc7],-2, 2, 5, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch'))
    """

    flyers = detectors #[pba2.adc6, pba2.adc7]
    # Start with a step scan.
    plan = bp.relative_scan(flyers, motor, start, stop, num, md={'plan_name': 'tune ' + motor.name, 'comment': comment})
    plan = bp.fly_during_wrapper(plan, flyers)

    #for flyer in flyers:
    #    yield from bp.stage(flyer)

    plan = bp.pchain(plan)
    yield from plan


def prep_trajectory(delay = 1):
	hhm.prepare_trajectory.put("1")
	while (hhm.trajectory_ready.value == 0):
		ttime.sleep(.1)
	while (hhm.trajectory_ready.value == 1):
		ttime.sleep(.1)
	ttime.sleep(delay)

def write_file(comment, filenames, uid, file_path = '/GPFS/xf08id/pizza_box_data/'):
    with open(file_path + str(comment), access_mode='w') as f:
        f.write('uid: ' + uid + '\n')
        for i in range(len(filenames)):
            f.write('file ' + i + ': ' + filenames[i] + '\n')

def execute_trajectory(comment='', **metadata):
    flyers = [pb9.enc1, pba2.adc6, pba2.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'execute_trajectory', 'comment': comment}
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
        hhm.enable_loop.put("0")
        hhm.start_trajectory.put("1")
        ttime.sleep(3)
        finished = 0
        while (hhm.theta.moving == True or finished == 0):
            finished = 0
            ttime.sleep(.1)
            if (hhm.theta.moving == False):
                ttime.sleep(.5)
                finished = 1

        #write_file(comment, [flyers[0].filepath.value, flyers[1].filepath.value, flyers[2].filepath.value] , '')

        yield from bp.close_run()


    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)

    yield from bp.fly_during_wrapper(inner(), flyers)

    yield from bp.unstage(hhm)
    for flyer in flyers:
        yield from bp.unstage(flyer)

def execute_xia_trajectory(comment='', **metadata):
    flyers = [pb9.enc1, pba2.adc7, pb4.di]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'execute_xia_trajectory', 'comment': comment}
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
       
        xia1.start_mapping_scan()
        hhm.enable_loop.put("0")
        hhm.start_trajectory.put("1")
        ttime.sleep(3)
        finished = 0
        while (hhm.theta.moving == True or finished == 0):
            finished = 0
            ttime.sleep(.1)
            if (hhm.theta.moving == False):
                ttime.sleep(.5)
                finished = 1

        xia1.stop_scan()
        #write_file(comment, [flyers[0].filepath.value, flyers[1].filepath.value, flyers[2].filepath.value] , '')

        yield from bp.close_run()


    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)
    #yield from bp.stage(xia1)

    yield from bp.fly_during_wrapper(inner(), flyers)

    #yield from bp.unstage(xia1)
    yield from bp.unstage(hhm)
    for flyer in flyers:
        yield from bp.unstage(flyer)


def execute_loop_trajectory(comment='', **metadata):

    flyers = [pb9.enc1, pba2.adc6, pba2.adc7]
    def inner():
        md = {'plan_args': {}, 'plan_name': 'execute_trajectory', 'comment': comment}
        md.update(**metadata)
        yield from bp.open_run(md=md)

        # TODO Replace this with actual status object logic.
        hhm.enable_loop.put("1")
        ttime.sleep(2)
        while (hhm.theta.moving == True or hhm.enable_loop_rbv.value == 1):
            ttime.sleep(.1)
        #write_file(comment, [flyers[0].filepath.value, flyers[1].filepath.value, flyers[2].filepath.value] , '')

        yield from bp.close_run()


    for flyer in flyers:
        yield from bp.stage(flyer)
    yield from bp.stage(hhm)

    yield from bp.fly_during_wrapper(inner(), flyers)

    yield from bp.unstage(hhm)
    for flyer in flyers:
        yield from bp.unstage(flyer)

def test_steps(comment=''):
    flyers = [pb9.enc1, pba2.adc6, pba2.adc7]
    plan = bp.relative_scan([hhm.theta, pb9.enc1, pba2.adc6, pba2.adc7], hhm.theta, -0.1, 0.1, 5)
    plan = bp.fly_during_wrapper(plan, flyers)
    plan = bp.pchain(plan)
    yield from plan

def run_trajectory(comment=''):
    #xia1.stage()
    #pb4.di.stage()
    pb9.enc1.stage()
    pba2.adc6.stage()
    pba2.adc7.stage()

    #pb4.di.kickoff()
    pb9.enc1.kickoff()
    pba2.adc6.kickoff()
    pba2.adc7.kickoff()

    #hhm.prepare_trajectory.put(1)
    #ttime.sleep(.25)
    #while (hhm.trajectory_ready.read()['hhm_trajectory_ready']['value'] == 1):
    #    ttime.sleep(.1)
    ttime.sleep(.25)
    hhm.start_trajectory.put("1")
    ttime.sleep(2)

    while (hhm.theta.moving == True):
        ttime.sleep(.1)


    #pb4.di.complete()
    pb9.enc1.complete()
    pba2.adc6.complete()
    pba2.adc7.complete()

    #pb4.di.collect()
    pb9.enc1.collect()
    pba2.adc6.collect()
    pba2.adc7.collect()

    #xia1.unstage()
    #pb4.di.unstage()
    pb9.enc1.unstage()
    pba2.adc6.unstage()
    pba2.adc7.unstage()
    
    encoder_path = pb9.enc1.filepath.value[len(pb9.enc1.filepath.value)-9 : len(pb9.enc1.filepath.value)]
    adc_path1 = pba2.adc7.filepath.value[len(pba2.adc7.filepath.value)-9 : len(pba2.adc7.filepath.value)]
    adc_path2 = pba2.adc6.filepath.value[len(pba2.adc6.filepath.value)-9 : len(pba2.adc6.filepath.value)]

    return [comment, adc_path1, adc_path2, encoder_path]


