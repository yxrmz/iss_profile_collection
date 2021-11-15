def constant_energy(name: str, comment: str, n_cycles: int = 1, duration: float = 0, reference = True, **kwargs):

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)

        uid = (yield from execute_constant_energy(name_n, duration, comment=comment))
        uids.append(uid)


        yield from bps.sleep(float(delay))
    return uids




def sleep(delay:int=1, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    print_to_gui(f'Pausing for {delay} seconds....',sys.stdout)
    yield from (bps.sleep(int(delay)))
    print_to_gui(f'Resuming', sys.stdout)



def set_gains_and_offsets(i0_gain:int=5, it_gain:int=5, iff_gain:int=6,
                          ir_gain:int=5, hs:bool=False):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    RE(set_gains_and_offsets_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs))


def set_gains(i0_gain:int=5, it_gain:int=5, iff_gain:int=5,
                          ir_gain:int=5, hs:bool=False, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    yield from set_gains_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs)


def general_scan(detectors, motor, rel_start, rel_stop, num, **kwargs):

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    #print(f'Dets {detectors}')
    #print(f'Motors {motor}')
    print('[General Scan] Starting scan...')
    uid =  yield from (general_scan_plan(detectors, motor, rel_start, rel_stop, int(num)))
    print('[General Scan] Done!')
    return uid

def bender_scan():
    bender_current_position = bender.pos.user_readback.get()
    bender_positions = bender_current_position + np.arange(-15, 20, 5)
    for bender_position in bender_positions:
        yield from bps.mv(bender.pos, bender_position)
        yield from bps.sleep(3)
        loading = bender.load_cell.get()
        fname = f'Bender scan - {loading} N - {bender_position} um'

        yield from fly_scan_with_apb(fname,'')
    yield from bps.mv(bender.pos, bender_current_position)







