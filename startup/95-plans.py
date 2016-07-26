import bluesky as bs
import bluesky.plans as bp


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


def energy_scan(start, stop, num):
    """
    Example
    -------
    >>> RE(energy_scan(11350, 11450, 2))
    """
    # Start with a step scan.
    plan = bp.scan([hhm_en.energy], hhm_en.energy, start, stop, num)
    # Wrap it in a fly scan with the Pizza Box.
    plan = bp.fly_during_wrapper(plan, [pb9.enc1, pba1.adc1])
    # Working around a bug in fly_during_wrapper, stage and unstage the pizza box manually.
    plan = bp.pchain(bp.stage(pb9.enc1), bp.stage(pba1.adc1),
                     plan,
                     bp.unstage(pb9.enc1), bp.unstage(pba1.adc1))
    yield from plan
