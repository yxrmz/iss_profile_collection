


from ophyd import Staged
import bluesky.plan_stubs as bps
import bluesky.plans as bp


def adaq_pb_step_per_step_factory(energy_steps, time_steps):

    scantime = sum(time_steps)
    elapsed_time = 0

    energy_to_time_step = dict(zip(energy_steps, time_steps))

    def per_step_pb(dets, motor, energy_step):

        time_step=energy_to_time_step[energy_step]
        samples = 250*(np.ceil(time_step*10443/250))

        yield from bps.abs_set(dets[0].sample_len, samples, wait=True )
        yield from bps.abs_set(dets[0].wf_len, samples, wait=True )

        yield from bps.mv(motor, energy_step)
        devices = [*dets, motor]
        yield from bps.trigger_and_read(devices=devices)
        yield from bps.sleep(0.1)

    return per_step_pb


def step_scan_plan(name, energy_steps, time_steps, element='', e0 =0, edge=''):


    fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.dat"
    fn = validate_file_exists(fn)


    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md = {'plan_args': {},
          'experiment': 'step_scan',
          'name': name,
          'interp_filename': fn,
          'element': element,
          'element_full': full_element_name,
          'edge': edge,
          'e0': e0,
          }
    #yield from bp.list_scan(detectors=[adaq_pb_step], motor=hhm.energy, steps=energy_grid)
    detectors = [adaq_pb_step]

    yield from bp.list_scan(
        detectors,
        hhm.energy,
        energy_steps,
        per_step=adaq_pb_step_per_step_factory(energy_steps,time_steps),
        md=md
    )
