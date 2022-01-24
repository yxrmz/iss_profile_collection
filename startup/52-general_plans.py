
def sleep(delay:int=1, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    print_to_gui(f'Pausing for {delay} seconds....',sys.stdout)
    yield from (bps.sleep(int(delay)))
    print_to_gui(f'Resuming', sys.stdout)




def get_offsets_plan(detectors = [apb_ave], time = 2):
    for detector in detectors:
        # detector.divide_old = detector.divide.get()
        detector.save_current_status()

        yield from bps.abs_set(detector.divide,375) # set sampling to 1 kHz
        yield from bps.abs_set(detector.sample_len, int(time)*1e3)
        yield from bps.abs_set(detector.wf_len, int(time) * 1e3)

    uid = (yield from bp.count(detectors, 1, md={"plan_name": "get_offsets"}))

    for detector in detectors:
        # yield from bps.abs_set(detector.divide, detector.divide_old)
        yield from detector.restore_to_saved_status()

    table = db[uid].table()

    for detector in detectors:
        for i in range(0,8):
            mean =  float(table[f'apb_ave_ch{i+1}_mean'])
            print(f'Mean {(mean)}')
            ch_offset = getattr(detector, f'ch{i+1}_offset')
            yield from bps.abs_set(ch_offset, mean)

    return uid





def set_gains_plan(*args):
    """
    Parameters
    ----------
    Groups of three parameters: amplifier, gain, hs

    Example: set_gains_and_offsets(i0_amp, 5, False, it_amp, 4, False, iff_amp, 5, True)
    """

    mod = len(args) % 3
    if mod:
        args = args[:-mod]

    for ic, val, hs in zip([ic for index, ic in enumerate(args) if index % 3 == 0],
                       [val for index, val in enumerate(args) if index % 3 == 1],
                       [hs for index, hs in enumerate(args) if index % 3 == 2]):
        yield from ic.set_gain_plan(val, hs)

        if type(ic) != ICAmplifier:
            raise Exception('Wrong type: {} - it should be ICAmplifier'.format(type(ic)))
        if type(val) != int:
            raise Exception('Wrong type: {} - it should be int'.format(type(val)))
        if type(hs) != bool:
            raise Exception('Wrong type: {} - it should be bool'.format(type(hs)))

        print('set amplifier gain for {}: {}, {}'.format(ic.par.dev_name.get(), val, hs))


def set_gains(i0_gain: int = 5, it_gain: int = 5, iff_gain: int = 5,
              ir_gain: int = 5, hs: bool = False, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    yield from set_gains_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs)

