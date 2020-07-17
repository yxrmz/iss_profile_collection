


from ophyd import Staged
import bluesky.plan_stubs as bps
import bluesky.plans as bp


def adaq_pb_step_per_step_factory(energy_steps, time_steps):

    #scantime = sum(time_steps)
    #elapsed_time = 0

    energy_to_time_step = dict(zip(energy_steps, time_steps))

    def per_step_pb(dets, motor, energy_step):
        #print(f' Energy {energy_step}')
        time_step=energy_to_time_step[energy_step]


        for det in dets:
            if det.name == 'apb_ave':
                samples = 250*(np.ceil(time_step*10443/250)) #hn I forget what that does... let's look into the new PB OPI
                yield from bps.abs_set(det.sample_len, samples, wait=True )
                yield from bps.abs_set(det.wf_len, samples, wait=True )
            else:
                yield from bps.mv(det.cam.acquire_time, time_step)

        yield from bps.mv(motor, energy_step)
        devices = [*dets, motor]
        yield from bps.trigger_and_read(devices=devices)

    return per_step_pb

#OK so it seems that is the function that's we need



def step_scan_plan(name, comment, energy_steps, time_steps, detectors, element='', e0=0, edge=''):
    print(f'Edge in plan {edge}')
    fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.dat"
    fn = validate_file_exists(fn)


    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md = {'plan_args': {},
          'experiment': 'step_scan',
          'name': name,
          'comment': comment,
          'interp_filename': fn,
          'element': element,
          'element_full': full_element_name,
          'edge': edge,
          'e0': e0,
          }
    #yield from bp.list_scan(detectors=[adaq_pb_step], motor=hhm.energy, steps=energy_grid)
    yield from bps.abs_set(apb_ave.divide, 35, wait=True)

    yield from bp.list_scan( #this is the scan
        detectors,
        hhm.energy,
        energy_steps,
        per_step=adaq_pb_step_per_step_factory(energy_steps,time_steps), #and this function is colled at every step
        md=md
    )


