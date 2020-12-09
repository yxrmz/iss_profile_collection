def master_plan():
    yield from bps.mvr(giantxy.x,x_range/2)
    yield from bps.mvr(giantxy.y,y_range/2)
    for _ in range(6):
        yield from bps.mvr(giantxy.x,-x_range)
        yield from bps.mvr(giantxy.y,-1)
        yield from bps.mvr(giantxy.x,+x_range)
        yield from bps.mvr(giantxy.y,-1)
    yield from bps.mvr(giantxy.x,-x_range)
    yield from bps.mvr(giantxy.y,-1)
    yield from bps.mvr(giantxy.x,+x_range)
    yield from bps.mvr(giantxy.x,-x_range/2)
    yield from bps.mvr(giantxy.y,y_range/2)
