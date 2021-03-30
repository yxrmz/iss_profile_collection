from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus



class FlyerAPBwithTrigger(FlyerAPB):

    def __init__(self, det, pbs, motor, trigger): #, xs_det):
        super().__init__( det, pbs, motor)
        self.trigger = trigger

    def kickoff(self, traj_duration=None):
        self.trigger.stage()
        st_super = super().kickoff(traj_duration=traj_duration)
        return st_super

    def complete(self):
        st_super = super().complete()
        def callback_motor():
            self.trigger.complete()

        self._motor_status.add_callback(callback_motor)
        return st_super & self._motor_status #& st_xs

    def describe_collect(self):
        dict_super = super().describe_collect()
        dict_trig = self.trigger.describe_collect()
        return {**dict_super, **dict_trig}#, **dict_xs}

    def collect_asset_docs(self):
        yield from super().collect_asset_docs()
        yield from self.trigger.collect_asset_docs()

    def collect(self):
        self.trigger.unstage()
        yield from super().collect()
        yield from self.trigger.collect()


flyer_apb_trigger = FlyerAPBwithTrigger(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger)



class FlyerXS(FlyerAPBwithTrigger):

    def __init__(self, det, pbs, motor, trigger, xs_det):
        super().__init__( det, pbs, motor, trigger)
        self.xs_det = xs_det

    def kickoff(self, traj_duration=None):
        traj_duration = get_traj_duration()
        acq_rate = self.trigger.freq.get()
        self.xs_det.stage(acq_rate, traj_duration)
        st_super = super().kickoff(traj_duration=traj_duration)
        return st_super

    def complete(self):
        st_super = super().complete()
        def callback_xs(value, old_value, **kwargs):
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                self.xs_det.complete()
                return True
            else:
                return False

        saving_st = SubscriptionStatus(self.xs_det.hdf5.capture, callback_xs)
        return st_super & saving_st

    def describe_collect(self):
        dict_super = super().describe_collect()
        dict_xs = self.xs_det.describe_collect()
        return {**dict_super, **dict_xs}

    def collect_asset_docs(self):
        yield from super().collect_asset_docs()
        yield from self.xs_det.collect_asset_docs()

    def collect(self):
        self.xs_det.unstage()
        yield from super().collect()
        yield from self.xs_det.collect()


flyer_xs = FlyerXS(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger, xs_det=xs_stream)


class FlyerPilatus(FlyerAPBwithTrigger):

    def __init__(self, det, pbs, motor, trigger, pil_det):
        super().__init__( det, pbs, motor, trigger)
        self.pil_det = pil_det

    def kickoff(self, traj_duration=None):
        print(f'     !!!!! {datetime.now()} PIL100K KICKOFF')
        traj_duration = get_traj_duration()
        acq_rate = self.trigger.freq.get()
        self.pil_det.stage(acq_rate, traj_duration)

        st_pil = self.pil_det.trigger()
        st_super = super().kickoff(traj_duration=traj_duration)
        return st_super & st_pil

    def complete(self):
        print(f'     !!!!! {datetime.now()} PIL100K COMPLETE')
        st_super = super().complete()
        # def callback_pil(value, old_value, **kwargs):
        #     print(f'     !!!!! {datetime.now()} callback_pil100k_capture {value} --> {old_value}')
        #     if int(round(old_value)) == 1 and int(round(value)) == 0:
        #         print(f'     !!!!! {datetime.now()} callback_pil100k_capture')
        #         self.pil_det.complete()
        #         return True
        #     else:
        #         return False
        # saving_st = SubscriptionStatus(self.pil_det.tiff.capture, callback_pil)
        self.pil_det.complete()
        return st_super# & saving_st

    def describe_collect(self):
        print(f'     !!!!! {datetime.now()} PIL100K DESCRIBE COLLECT')
        dict_super = super().describe_collect()
        dict_pil = self.pil_det.describe_collect()
        return {**dict_super, **dict_pil}

    def collect_asset_docs(self):
        print(f'     !!!!! {datetime.now()} PIL100K COLLECT ASSET DOCS')
        yield from super().collect_asset_docs()
        yield from self.pil_det.collect_asset_docs()

    def collect(self):
        print(f'     !!!!! {datetime.now()} PIL100K COLLECT')
        self.pil_det.unstage()
        yield from super().collect()
        yield from self.pil_det.collect()


flyer_pil = FlyerPilatus(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger, pil_det=pil100k_stream)


def execute_trajectory_apb_trigger(name, **metadata):
    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Storing data at {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.value))
    try:
        full_element_name = getattr(elements, curr_traj.elem.value).name.capitalize()
    except:
        full_element_name = curr_traj.elem.value
    md = {'plan_args': {},
          'plan_name': 'execute_trajectory_apb',
          'experiment': 'fly_energy_scan_apb',
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.value),
          'trajectory_name': hhm.trajectory_name.value,
          'element': curr_traj.elem.value,
          'element_full': full_element_name,
          'edge': curr_traj.edge.value,
          'e0': curr_traj.e0.value,
          'pulses_per_degree': hhm.pulses_per_deg,
          }
    for indx in range(8):
        md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
        amp = getattr(apb, f'amp_ch{indx+1}')
        if amp:
            md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
        else:
            md[f'ch{indx+1}_amp_gain']=0
    md.update(**metadata)
    yield from bp.fly([flyer_apb_trigger], md=md)




def execute_trajectory_xs(name, **metadata):
    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Storing data at {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.value))
    try:
        full_element_name = getattr(elements, curr_traj.elem.value).name.capitalize()
    except:
        full_element_name = curr_traj.elem.value
    md = {'plan_args': {},
          'plan_name': 'execute_trajectory_apb',
          'experiment': 'fly_energy_scan_xs3',
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.value),
          'trajectory_name': hhm.trajectory_name.value,
          'element': curr_traj.elem.value,
          'element_full': full_element_name,
          'edge': curr_traj.edge.value,
          'e0': curr_traj.e0.value,
          'pulses_per_degree': hhm.pulses_per_deg,
          }
    for indx in range(8):
        md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
        amp = getattr(apb, f'amp_ch{indx+1}')
        if amp:
            md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
        else:
            md[f'ch{indx+1}_amp_gain']=0
    md.update(**metadata)
    yield from bp.fly([flyer_xs], md=md)



def execute_trajectory_pil100k(name, **metadata):
    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Storing data at {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.value))
    try:
        full_element_name = getattr(elements, curr_traj.elem.value).name.capitalize()
    except:
        full_element_name = curr_traj.elem.value
    md = {'plan_args': {},
          'plan_name': 'execute_trajectory_apb',
          'experiment': 'fly_energy_scan_pil100k',
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.value),
          'trajectory_name': hhm.trajectory_name.value,
          'element': curr_traj.elem.value,
          'element_full': full_element_name,
          'edge': curr_traj.edge.value,
          'e0': curr_traj.e0.value,
          'pulses_per_degree': hhm.pulses_per_deg,
          }
    for indx in range(8):
        md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
        amp = getattr(apb, f'amp_ch{indx+1}')
        if amp:
            md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
        else:
            md[f'ch{indx+1}_amp_gain']=0
    md.update(**metadata)


    roi_data = [[pil100k.roi1.min_xyz.min_x.get(), pil100k.roi1.min_xyz.min_y.get(),
                 pil100k.roi1.size.x.get(),        pil100k.roi1.size.y.get()        ],
                [pil100k.roi2.min_xyz.min_x.get(), pil100k.roi2.min_xyz.min_y.get(),
                 pil100k.roi2.size.x.get(),        pil100k.roi2.size.y.get()        ],
                [pil100k.roi3.min_xyz.min_x.get(), pil100k.roi3.min_xyz.min_y.get(),
                 pil100k.roi3.size.x.get(),        pil100k.roi3.size.y.get()],
                [pil100k.roi4.min_xyz.min_x.get(), pil100k.roi4.min_xyz.min_y.get(),
                 pil100k.roi4.size.x.get(),        pil100k.roi4.size.y.get()]]
    md['roi'] = roi_data



    yield from bp.fly([flyer_pil], md=md)
