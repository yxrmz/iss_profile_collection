from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus



class FlyerAPBwithTrigger(FlyerAPB):

    def __init__(self, det, pbs, motor, trigger): #, xs_det):
        super().__init__( det, pbs, motor)
        self.trigger = trigger
        # self.xs_det = xs_det

    def kickoff(self, traj_duration=None):
        # traj_duration = get_traj_duration()
        # acq_rate = self.trigger.freq.get()
        # self.xs_det.stage(acq_rate, traj_duration)
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
        # dict_xs = self.xs_det.describe_collect()
        return {**dict_super, **dict_trig}#, **dict_xs}

    def collect_asset_docs(self):
        yield from super().collect_asset_docs()
        yield from self.trigger.collect_asset_docs()

    def collect(self):
        self.trigger.unstage()
        yield from super().collect()
        yield from self.trigger.collect()






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

        ###
        # def callback_xs():
        #     self.xs_det.complete()
        #
        # self._motor_status.add_callback(callback_xs)
        # return st_super & self._motor_status #& st_xs
        ###
        def callback_xs(value, old_value, **kwargs):
            print(f'callback_xs: {old_value} --> {value}')
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                self.xs_det.complete()
                return True
            else:
                return False

        saving_st = SubscriptionStatus(self.xs_det.hdf5.capture, callback_xs)
        return st_super & saving_st

    def describe_collect(self):
        dict_super = super().describe_collect()
        # dict_trig = self.trigger.describe_collect()
        dict_xs = self.xs_det.describe_collect()
        return {**dict_super, **dict_xs}#, **dict_xs}

    def collect_asset_docs(self):
        yield from super().collect_asset_docs()
        print(f'xs_det._asset_docs_cache     : {self.xs_det._asset_docs_cache}')
        yield from self.xs_det.collect_asset_docs()

    def collect(self):
        self.xs_det.unstage()
        yield from super().collect()
        yield from self.xs_det.collect()




flyer_apb_trigger = FlyerAPBwithTrigger(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger)
flyer_xs = FlyerXS(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger, xs_det=xs_stream)

############################################
    # def describe_collect(self):
    #     return_dict = self.det.describe_collect()
    #     return_dict[self.trigger.name] = self.trigger.describe_collect()[self.trigger.name]
    #     # Also do it for all pizza-boxes
    #     for pb in self.pbs:
    #         return_dict[pb.name] = pb.describe_collect()[pb.name]
    #
    #     return return_dict
    #
    # def collect_asset_docs(self):
    #     yield from self.det.collect_asset_docs()
    #     yield from self.trigger.collect_asset_docs()
    #     for pb in self.pbs:
    #         yield from pb.collect_asset_docs()
    #
    # def collect(self):
    #     self.det.unstage()
    #     self.trigger.unstage()
    #     for pb in self.pbs:
    #         pb.unstage()
    #
    #     def collect_all():
    #         for pb in self.pbs:
    #             yield from pb.collect()
    #         yield from self.trigger.collect()
    #         yield from self.det.collect()
    #     # print(f'collect is being returned ({ttime.ctime(ttime.time())})')
    #     return collect_all()




# class FlyerAPBwithTrigger():
#     def __init__(self, det, pbs, motor, trigger):
#         self.name = f'{det.name}-{"-".join([pb.name for pb in pbs])}-flyer'
#         self.parent = None
#         self.det = det
#         self.trigger = trigger
#         self.pbs = pbs  # a list of passed pizza-boxes
#         self.motor = motor
#         self._motor_status = None
#         self._xs_num_points = None
#
#     def kickoff(self, *args, **kwargs):
#         # set_and_wait(self.det.trig_source, 1)
#         # TODO: handle it on the plan level
#         # set_and_wait(self.motor, 'prepare')
#
#         def callback(value, old_value, **kwargs):
#
#             if int(round(old_value)) == 0 and int(round(value)) == 1:
#                 # Now start mono move
#                 self._motor_status = self.motor.set('start')
#                 return True
#             else:
#                 return False
#
#         streaming_st = SubscriptionStatus(self.det.streaming, callback)
#
#         self.det.stage(get_traj_duration())
#         self.det.stream.set(1)
#         self.trigger.stage()
#
#         for pb in self.pbs:
#             pb.stage()
#             pb.kickoff()
#
#         return streaming_st
#
#     def complete(self):
#         def callback_det(value, old_value, **kwargs):
#             if int(round(old_value)) == 1 and int(round(value)) == 0:
#                 # print(f'     !!!!! {datetime.now()} callback_det')
#                 return True
#             else:
#                 return False
#         streaming_st = SubscriptionStatus(self.det.streaming, callback_det)
#
#         def callback_motor():
#             # print(f'     !!!!! {datetime.now()} callback_motor')
#
#             # print('      I am sleeping for 10 seconds')
#             # ttime.sleep(10.0)
#             # print('      Done sleeping for 10 seconds')
#
#             # TODO: see if this 'set' is still needed (also called in self.det.unstage()).
#             # Change it to 'put' to have a blocking call.
#             # self.det.stream.set(0)
#
#             # self.det.stream.put(0)
#
#             self.det.complete()
#             self.trigger.complete()
#
#             for pb in self.pbs:
#                 pb.complete()
#
#         self._motor_status.add_callback(callback_motor)
#         return streaming_st & self._motor_status
#
#     def describe_collect(self):
#         return_dict = self.det.describe_collect()
#         return_dict[self.trigger.name] = self.trigger.describe_collect()[self.trigger.name]
#         # Also do it for all pizza-boxes
#         for pb in self.pbs:
#             return_dict[pb.name] = pb.describe_collect()[pb.name]
#
#         return return_dict
#
#     def collect_asset_docs(self):
#         yield from self.det.collect_asset_docs()
#         yield from self.trigger.collect_asset_docs()
#         for pb in self.pbs:
#             yield from pb.collect_asset_docs()
#
#     def collect(self):
#         self.det.unstage()
#         self.trigger.unstage()
#         for pb in self.pbs:
#             pb.unstage()
#
#         def collect_all():
#             for pb in self.pbs:
#                 yield from pb.collect()
#             yield from self.trigger.collect()
#             yield from self.det.collect()
#         # print(f'collect is being returned ({ttime.ctime(ttime.time())})')
#         return collect_all()
#
#
#     def calc_num_points_for_xs(self):
#         tr = trajectory_manager(hhm)
#         info = tr.read_info(silent=True)
#         lut = str(int(hhm.lut_number_rbv.get()))
#         traj_duration = int(info[lut]['size']) / 16000
#         acq_rate = self.trigger.freq.get()
#         print(traj_duration, acq_rate)
#         self._xs_num_points = traj_duration * acq_rate







# flyer_apb_trigger = FlyerAPBwithTrigger(det=, pbs=[pb9.enc1], motor=hhm, trigger = apb_trigger)



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
    yield from bp.fly([flyer_xs], md=md)
