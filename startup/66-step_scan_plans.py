


from ophyd import Staged
import bluesky.plan_stubs as bps
import bluesky.plans as bp


def per_step_factory(acq):
    _acq = acq.copy()
    def per_step(dets, motor, step):
        print(f'--------------- Step {step}')
        acq_time = _acq.pop(0)
        freq = dets[0].acq_rate.get()
        yield from bps.abs_set(dets[0].samples,round(acq_time*freq*1000), wait=True)
        yield from bps.abs_set(motor,step, wait=True)
        yield from bps.trigger_and_read(list(dets) + [motor])
    return per_step


# yield from bps.mov(motor, step)
#
# for d in dets:
#     if d._staged != Staged.no:
#         yield from bps.unstage(d)
#     yield from bps.stage(d)
#     yield from bps.kickoff(d, group=f'kickoff_{step}')
# yield from bps.wait(group=f'kickoff_{step}')
# yield from bps.sleep(acq_time)
# for d in dets:
#     yield from bps.complete(d, group=f'complete_{step}')
# yield from bps.wait(group=f'complete_{step}')
# for d in dets:
#     yield from bps.collect(d)
# for d in dets:
#     yield from bps.unstage(d)

def step_scan_plan(name, energy_steps):
    acq_time=1
    detectors = [pba2.adc7, pba1.adc6, pba1.adc1, pba2.adc6, pba1.adc7]
    md = {'plan_args': {},
          'plan_name': 'execute_trajectory',
          'experiment': 'step_scan',
          'name': name,
          'interp_filename': name,
          'angle_offset': str(hhm.angle_offset.value),
          }


    for flyer in detectors:
        # print(f'Flyer is {flyer}')
        if hasattr(flyer, 'offset'):
            md['{} offset'.format(flyer.name)] = flyer.offset.value
        if hasattr(flyer, 'amp'):
            md['{} gain'.format(flyer.name)] = flyer.amp.get_gain()[0]




    yield from bp.list_scan(detectors, hhm.energy, energy_steps, per_step=per_step_factory(acq_time), md=md)
