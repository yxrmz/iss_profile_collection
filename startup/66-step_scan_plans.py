from ophyd import Staged
import bluesky.plan_stubs as bps
import bluesky.plans as bp


def per_step_factory(acq_time):
    def per_step_pb(dets, motor, step):

        yield from bps.mov(motor, step)

        for d in dets:
            if d._staged != Staged.no:
                yield from bps.unstage(d)
            yield from bps.stage(d)
            yield from bps.kickoff(d, group=f'kickoff_{step}')
        yield from bps.wait(group=f'kickoff_{step}')
        yield from bps.sleep(acq_time)
        for d in dets:
            yield from bps.complete(d, group=f'complete_{step}')
        yield from bps.wait(group=f'complete_{step}')
        for d in dets:
            yield from bps.collect(d)
        for d in dets:
            yield from bps.unstage(d)
        yield from bps.trigger_and_read([motor], motor.name)

    return per_step_pb


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

    yield from bp.list_scan(detectors, hhm.energy, energy_steps, per_step=per_step_factory(acq_time), md=md)
