from xas.image_analysis import analyze_spiral_scan


def optimize_sample_plan(*args, **kwargs):
    yield from adjust_ic_gains(**kwargs)
    yield from get_offsets(*args, **kwargs)

    # prelim spiral scan:
    uid = (yield from spiral_scan())
    conc = kwargs['conc']
    x, y = analyze_spiral_scan(db, uid, conc, None)
    yield from bps.mv(giant.x, x)
    yield from bps.mv(giant.y, y)

    yield from adjust_ic_gains(**kwargs)
    yield from get_offsets(*args, **kwargs)



