print(ttime.ctime() + ' >>>> ' + __file__)
from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus, DeviceStatus
from ophyd.sim import NullStatus

import threading

class FlyerWithMotor(Device):
    def __init__(self, default_dets, motor, shutter, *args, **kwargs):
        super().__init__(parent=None, **kwargs)

        # apb_stream_idx = dets.index(apb_stream)
        # self.apb_stream = dets[apb_stream_idx]

        self.default_dets = default_dets
        self.aux_dets = []
        self.dets = []
        self.motor = motor
        self.shutter = shutter
        self.complete_status = None

    def set_aux_dets(self, aux_dets):
        self.aux_dets = aux_dets

    def flush_dets(self):
        self.aux_dets = []
        self.dets = []

    def stage(self):
        print_to_gui(f'Preparing mono starting...', add_timestamp=True, tag='Flyer')
        self.motor.prepare()
        print_to_gui(f'Preparing mono complete', add_timestamp=True, tag='Flyer')
        self.dets = self.default_dets + self.aux_dets
        print_to_gui(f'Fly scan staging starting...', add_timestamp=True, tag='Flyer')
        staged_list = super().stage()
        scan_duration = motor.current_trajectory_duration
        for det in self.dets:
            if hasattr(det, 'prepare_to_fly'):
                det.prepare_to_fly(scan_duration)
            print_to_gui(f'{det.name} staging starting', add_timestamp=True, tag='Flyer')
            staged_list += det.stage()
        print_to_gui(f'Fly scan staging complete', add_timestamp=True, tag='Flyer')
        return staged_list

    def unstage(self):
        print_to_gui(f'Fly scan unstaging starting...', add_timestamp=True, tag='Flyer')
        unstaged_list = super().unstage()
        for det in self.dets:
            unstaged_list += det.unstage()
        self.flush_dets()
        print_to_gui(f'Fly scan unstaging complete', add_timestamp=True, tag='Flyer')
        return unstaged_list

    def kickoff(self):
        self.kickoff_status = DeviceStatus(self)
        self.complete_status = DeviceStatus(self)
        thread = threading.Thread(target=self.action_sequence, daemon=True)
        thread.start()
        return self.kickoff_status

    def action_sequence(self):

        print_to_gui(f'Detector kickoff starting...', add_timestamp=True, tag='Flyer')
        self.shutter.open(time_opening=True)
        # priority_det = self.dets[0]
        # priority_det_kickoff_status = priority_det.kickoff()
        # priority_det_kickoff_status.wait()
        # ttime.sleep(1)
        # det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets[1:]])
        det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets])
        det_kickoff_status.wait()

        print_to_gui(f'Detector kickoff complete', add_timestamp=True, tag='Flyer')

        print_to_gui(f'Mono trajectory motion starting...', add_timestamp=True, tag='Flyer')

        self.motor_flying_status = self.motor.kickoff()
        self.kickoff_status.set_finished()

        self.motor_flying_status.wait()

        print_to_gui(f'Mono trajectory motion complete', add_timestamp=True, tag='Flyer')

        print_to_gui(f'Detector complete starting...', add_timestamp=True, tag='Flyer')
        det_complete_status = combine_status_list([det.complete() for det in self.dets])
        det_complete_status.wait()
        # det_complete_status = combine_status_list([det.complete() for det in self.dets[1:]])
        # det_complete_status.wait()
        # ttime.sleep(1)
        # priority_det_complete_status = priority_det.complete()
        # priority_det_complete_status.wait()
        self.motor.complete()
        self.shutter.close()

        print_to_gui(f'Detector complete complete', add_timestamp=True, tag='Flyer')
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
        # print_to_gui(f'{ttime.ctime()} Collect starting')
        print_to_gui(f'Collect starting...', add_timestamp=True, tag='Flyer')
        for det in self.dets:
            yield from det.collect()
        # print_to_gui(f'{ttime.ctime()} Collect finished')
        print_to_gui(f'Collect complete', add_timestamp=True, tag='Flyer')

    def collect_asset_docs(self):
        print_to_gui(f'Collect asset docs starting...', add_timestamp=True, tag='Flyer')
        for det in self.dets:
            yield from det.collect_asset_docs()
        print_to_gui(f'Collect asset docs complete', add_timestamp=True, tag='Flyer')


# flyer_apb = FlyerHHM([apb_stream, pb9.enc1, xs_stream], hhm, shutter, name='flyer_apb')
# flyer_apb = FlyerHHM([apb_stream, pb9.enc1], hhm, shutter, name='flyer_apb')
flyer_hhm = FlyerWithMotor([apb_stream, hhm_encoder], hhm, shutter, name='flyer_hhm')
# flyer_hhm_em = FlyerHHM([em_stream, hhm_encoder], hhm, shutter, name='flyer_apb')

def get_fly_scan_md(name, comment, trajectory_filename, detectors_dict, element, e0, edge, metadata):
    md_general = get_hhm_scan_md(name, comment, trajectory_filename, detectors_dict, element, e0, edge, metadata, fn_ext='.raw')
    md_scan = {'experiment': 'fly_scan'}
    return {**md_general, **md_scan}


def fly_scan_plan(name=None, comment=None, trajectory_filename=None, mono_angle_offset=None, detectors=[],
                  element='', e0=0, edge='', metadata={}):

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    trajectory_stack.set_trajectory(trajectory_filename, offset=mono_angle_offset)
    aux_detectors = get_detector_device_list(detectors, flying=True)
    flyer_hhm.set_aux_dets(aux_detectors)
    detectors_dict = {k :{'device' : v} for k, v in zip(detectors, aux_detectors)}
    md = get_fly_scan_md(name, comment, trajectory_filename, detectors_dict, element, e0, edge, metadata)

    @bpp.stage_decorator([flyer_hhm])
    def _fly(md):
        yield from bp.fly([flyer_hhm], md=md)
    yield from _fly(md)









