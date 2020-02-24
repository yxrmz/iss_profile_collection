


def step_scan(name: str, comment: str, n_cycles: int = 1, delay: float = 0, reference=True, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    energy_grid = kwargs.pop('energy_grid', [])
    time_grid = kwargs.pop('time_grid', [])
    element = kwargs.pop('element', [])
    e0 = kwargs.pop('e0', [])
    edge = kwargs.pop('element', [])


    yield from bps.mv(apb_ave.divide, 35)
    yield from step_scan_plan(name, comment, energy_grid, time_grid, element=element, e0=e0, edge=edge )

