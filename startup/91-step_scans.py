


def step_scan(name: str, comment: str, n_cycles: int = 1, delay: float = 0, reference=True, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    energy_grid = kwargs.pop('energy_grid', [])
    time_grid = kwargs.pop('time_grid', [])
    element = kwargs.pop('element', [])
    e0 = kwargs.pop('e0', [])
    edge = kwargs.pop('edge', [])
    yield from shutter.open_plan()
    yield from step_scan_plan(name, comment, energy_grid, time_grid, [apb_ave], element=element, e0=e0, edge=edge )
    yield from shutter.close_plan()


def step_scan_w_pilatus(name: str, comment: str, n_cycles: int = 1, delay: float = 0, reference=True, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    energy_grid = kwargs.pop('energy_grid', [])
    time_grid = kwargs.pop('time_grid', [])
    element = kwargs.pop('element', [])
    e0 = kwargs.pop('e0', [])
    edge = kwargs.pop('edge', [])
    yield from shutter.open_plan()
    yield from step_scan_plan(name, comment, energy_grid, time_grid, [apb_ave, pil100k, hhm.enc.pos_I], element=element, e0=e0, edge=edge )
    yield from shutter.close_plan()
