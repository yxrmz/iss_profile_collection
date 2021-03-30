from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus


class FlyerAPB:
    def __init__(self, det, pbs, motor):
        self.name = f'{det.name}-{"-".join([pb.name for pb in pbs])}-flyer'
        self.parent = None
        self.det = det
        self.pbs = pbs  # a list of passed pizza-boxes
        self.motor = motor
        self._motor_status = None

    def kickoff(self, traj_duration=None, *args, **kwargs):
        # set_and_wait(self.det.trig_source, 1)
        # TODO: handle it on the plan level
        # set_and_wait(self.motor, 'prepare')

        def callback(value, old_value, **kwargs):

            if int(round(old_value)) == 0 and int(round(value)) == 1:
                # Now start mono move
                self._motor_status = self.motor.set('start')
                return True
            else:
                return False

        # print(f'     !!!!! {datetime.now()} Flyer kickoff is complete at')

        streaming_st = SubscriptionStatus(self.det.streaming, callback)

        if traj_duration is None:
            traj_duration = get_traj_duration()

        self.det.stage(traj_duration)
        # Start apb after encoder pizza-boxes, which will trigger the motor.
        self.det.stream.set(1)

        for pb in self.pbs:
            pb.stage()
            pb.kickoff()

        return streaming_st

    def complete(self):
        def callback_motor():
            # When motor arrives to the position, it should stop streaming on
            # the detector. That will run 'callback_det' defined below, which
            # will perform the 'complete' step for all involved detectors.
            self.det.stream.put(0)
        self._motor_status.add_callback(callback_motor)

        def callback_det(value, old_value, **kwargs):
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                self.det.complete()
                for pb in self.pbs:
                    pb.complete()
                return True
            else:
                return False
        streaming_st = SubscriptionStatus(self.det.streaming, callback_det)

        return self._motor_status & streaming_st

    def describe_collect(self):
        return_dict = self.det.describe_collect()
        # Also do it for all pizza-boxes
        for pb in self.pbs:
            return_dict[pb.name] = pb.describe_collect()[pb.name]

        return return_dict

    def collect(self):
        def collect_and_unstage_all():
            for pb in self.pbs:
                yield from pb.collect()
            yield from self.det.collect()

            # The .unstage() method resets self._datum_counter, which is needed
            # by .collect(), so calling .unstage() afteer .collect().
            self.det.unstage()
            for pb in self.pbs:
                pb.unstage()

        return (yield from collect_and_unstage_all())

    def collect_asset_docs(self):
        yield from self.det.collect_asset_docs()
        for pb in self.pbs:
            yield from pb.collect_asset_docs()

    # def stop(self,*args, **kwargs):
    #     print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.. AT STOP ')

flyer_apb = FlyerAPB(det=apb_stream, pbs=[pb9.enc1], motor=hhm)


### aux function
def get_traj_duration():
    tr = trajectory_manager(hhm)
    info = tr.read_info(silent=True)
    lut = str(int(hhm.lut_number_rbv.get()))
    return int(info[lut]['size']) / 16000

def get_md_for_scan(name, mono_scan_type, **metadata):
    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Storing data at {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.get()))
    try:
        full_element_name = getattr(elements, curr_traj.elem.get()).name.capitalize()
    except:
        full_element_name = curr_traj.elem.get()
    md = {'plan_args': {},
          'plan_name': 'execute_trajectory_apb',
          'experiment': 'fly_energy_scan_apb',
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.get()),
          'trajectory_name': hhm.trajectory_name.get(),
          'element': curr_traj.elem.get(),
          'element_full': full_element_name,
          'edge': curr_traj.edge.get(),
          'e0': curr_traj.e0.get(),
          'pulses_per_degree': hhm.pulses_per_deg,
          'nslsii_current' : nsls_ii.beam_current.get(),
          'nslsii_status' : nsls_ii.return_status_string(),
          'nslsii_energy' : nsls_ii.energy_str,
          'i0_gain' : i0.amp.get_gain()[0],
          'it_gain' : it.amp.get_gain()[0],
          'ir_gain' : ir.amp.get_gain()[0],
          'iff_gain' : iff.amp.get_gain()[0],
          'mono_offset' : f'{np.round(hhm.angle_offset.get()*180/np.pi, 3)} deg',
          'mono_scan_type' : mono_scan_type,
          'sample_x_position' : giantxy.x.user_readback.get(),
          'sample_y_position' : giantxy.y.user_readback.get(),
          }
    for indx in range(8):
        md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
        amp = getattr(apb, f'amp_ch{indx+1}')
        if amp:
            md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
        else:
            md[f'ch{indx+1}_amp_gain']=0
    md.update(**metadata)
    return md



def execute_trajectory_apb(name, **metadata):
    md = get_md_for_scan(name, 'flyscan', **metadata)
    yield from bp.fly([flyer_apb], md=md)
