from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus, DeviceStatus
from ophyd.sim import NullStatus


# class FlyerAPB:
#     def __init__(self, det, pbs, motor):
#         self.name = f'{det.name}-{"-".join([pb.name for pb in pbs])}-flyer'
#         self.parent = None
#         self.det = det
#         self.pbs = pbs  # a list of passed pizza-boxes
#         self.motor = motor
#         self._motor_status = None
#
#     def kickoff(self, traj_duration=None, *args, **kwargs):
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
#         # print(f'     !!!!! {datetime.now()} Flyer kickoff is complete at')
#
#         streaming_st = SubscriptionStatus(self.det.streaming, callback)
#
#         if traj_duration is None:
#             traj_duration = trajectory_manager.current_trajectory_duration
#
#         self.det.stage(traj_duration)
#         # Start apb after encoder pizza-boxes, which will trigger the motor.
#         self.det.stream.set(1)
#
#         for pb in self.pbs:
#             pb.stage()
#             pb.kickoff()
#
#         return streaming_st
#
#     def complete(self):
#         def callback_motor():
#             # When motor arrives to the position, it should stop streaming on
#             # the detector. That will run 'callback_det' defined below, which
#             # will perform the 'complete' step for all involved detectors.
#             self.det.stream.put(0)
#         self._motor_status.add_callback(callback_motor)
#
#         def callback_det(value, old_value, **kwargs):
#             if int(round(old_value)) == 1 and int(round(value)) == 0:
#                 self.det.complete()
#                 for pb in self.pbs:
#                     pb.complete()
#                 return True
#             else:
#                 return False
#         streaming_st = SubscriptionStatus(self.det.streaming, callback_det)
#
#         return self._motor_status & streaming_st
#
#     def describe_collect(self):
#         return_dict = self.det.describe_collect()
#         # Also do it for all pizza-boxes
#         for pb in self.pbs:
#             return_dict[pb.name] = pb.describe_collect()[pb.name]
#
#         return return_dict
#
#     def collect(self):
#         def collect_and_unstage_all():
#             for pb in self.pbs:
#                 yield from pb.collect()
#             yield from self.det.collect()
#
#             # The .unstage() method resets self._datum_counter, which is needed
#             # by .collect(), so calling .unstage() afteer .collect().
#             self.det.unstage()
#             for pb in self.pbs:
#                 pb.unstage()
#
#         return (yield from collect_and_unstage_all())
#
#     def collect_asset_docs(self):
#         yield from self.det.collect_asset_docs()
#         for pb in self.pbs:
#             yield from pb.collect_asset_docs()
#
#     # def stop(self,*args, **kwargs):
#     #     print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.. AT STOP ')
#
# flyer_apb = FlyerAPB(det=apb_stream, pbs=[pb9.enc1], motor=hhm)


def combine_status_list(status_list):
    st_all = status_list[0]
    for st in status_list[1:]:
        st_all = st_all and st
    return st_all

import threading

class FlyerHHM(Device):
    def __init__(self, default_dets, hhm, shutter, *args, **kwargs):
        super().__init__(parent=None, **kwargs)

        # apb_stream_idx = dets.index(apb_stream)
        # self.apb_stream = dets[apb_stream_idx]

        self.default_dets = default_dets
        self.aux_dets = []
        self.dets = []
        self.hhm = hhm
        self.shutter = shutter
        self.complete_status = None

    def set_aux_dets(self, aux_dets):
        self.aux_dets = aux_dets

    def flush_aux_dets(self):
        self.aux_dets = []

    def stage(self):
        self.dets = self.default_dets + self.aux_dets
        self.hhm.prepare()
        staged_list = super().stage()
        scan_duration = trajectory_manager.current_trajectory_duration
        for det in self.dets:
            if hasattr(det, 'prepare_to_fly'):
                det.prepare_to_fly(scan_duration)
            staged_list += det.stage()
        return staged_list

    def unstage(self):
        self.dets = []
        unstaged_list = super().unstage()
        for det in self.dets:
            unstaged_list += det.unstage()
        self.flush_detectors()
        return unstaged_list

    def kickoff(self):
        # print(f'{ttime.ctime()} >>> KICKOFF: begin')
        self.kickoff_status = DeviceStatus(self)
        self.complete_status = DeviceStatus(self)
        thread = threading.Thread(target=self.action_sequence, daemon=True)
        thread.start()
        return self.kickoff_status

    def action_sequence(self):
        print(f'{ttime.ctime()} Detector kickoff starting...')

        # apb_status = self.apb_stream.kickoff()
        # apb_status.wait()
        # ttime.sleep(1)

        self.shutter.open(time_opening=True)
        # det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets if (det is not self.apb_stream)])
        det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets])
        det_kickoff_status.wait()
        print(f'{ttime.ctime()} Detector kickoff finished')
        # self.shutter.open() # this could be a better place to have shutter open
        print(f'{ttime.ctime()} Mono flight starting...')
        self.hhm_flying_status = self.hhm.kickoff()
        self.kickoff_status.set_finished()

        self.hhm_flying_status.wait()
        print(f'{ttime.ctime()} Mono flight finished')
        self.shutter.close()
        print(f'{ttime.ctime()} Detector complete starting...')
        det_complete_status = combine_status_list([det.complete() for det in self.dets])
        det_complete_status.wait()
        print(f'{ttime.ctime()} Detector complete finished')
        self.complete_status.set_finished()

    def complete(self):
        # print(f'{ttime.ctime()} >>> COMPLETE: begin')
        if self.complete_status is None:
            raise RuntimeError("No collection in progress")
        return self.complete_status

    def describe_collect(self):
        return_dict = {}
        for det in self.dets:
            return_dict = {**return_dict, **det.describe_collect()}
        return return_dict

    def collect(self):
        for det in self.dets:
            yield from det.collect()

    def collect_asset_docs(self):
        for det in self.dets:
            yield from det.collect_asset_docs()


# flyer_apb = FlyerHHM([apb_stream, pb9.enc1, xs_stream], hhm, shutter, name='flyer_apb')
# flyer_apb = FlyerHHM([apb_stream, pb9.enc1], hhm, shutter, name='flyer_apb')
flyer_hhm = FlyerHHM([apb_stream, pb9.enc1], hhm, shutter, name='flyer_apb')


def fly_scan_plan(name=None, comment=None, filename=None, detectors=[], element='', e0=0, edge=''):
    fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    fn = validate_file_exists(fn)

    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md_general = get_general_md()
    md_scan = {'plan_args': {'filename': filename, 'detectors': detectors},
               'experiment': 'fly_scan',
               'name': name,
               'comment': comment,
               'interp_filename': fn,
               'element': element,
               'element_full': full_element_name,
               'edge': edge,
               'e0': e0,
               'plot_hint': '$5/$1'}
    md = {**md_general, **md_scan}

    trajectory_stack.init_trajectory(filename)
    aux_detectors = get_detector_device_list(detectors)
    flyer_hhm.set_aux_dets(aux_detectors)

    @bpp.stage_decorator([flyer_hhm])
    def _fly(md):
        yield from bp.fly([flyer_hhm], md=md)
    yield from _fly(md)