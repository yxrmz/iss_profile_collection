from xas.image_analysis import analyze_spiral_scan


def optimize_sample_plan(*args, **kwargs):
    yield from adjust_ic_gains(**kwargs)
    yield from get_offsets(*args, **kwargs)

    # prelim spiral scan:
    spiral_plan = general_spiral_scan([apb_ave],
                                      motor1=giantxy.x, motor2=giantxy.y,
                                      motor1_range=15, motor2_range=15,
                                      motor1_nsteps=15, motor2_nsteps=15,
                                      time_step=0.1)
    uid = (yield from spiral_plan)
    conc = kwargs['conc']
    x, y = analyze_spiral_scan(db, uid, conc, None)
    yield from bps.mv(giant.x, x)
    yield from bps.mv(giant.y, y)

    yield from adjust_ic_gains(**kwargs)
    yield from get_offsets(*args, **kwargs)



