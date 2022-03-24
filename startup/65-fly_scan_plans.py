from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus, DeviceStatus
from ophyd.sim import NullStatus

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

    def flush_dets(self):
        self.aux_dets = []
        self.dets = []

    def stage(self):
        # print_to_gui(f'{ttime.ctime()} Preparing mono start')
        print_to_gui(f'Preparing mono start', add_timestamp=True, tag='Flyer')
        self.hhm.prepare()
        # print_to_gui(f'{ttime.ctime()} Preparing mono done')
        print_to_gui(f'Preparing mono done', add_timestamp=True, tag='Flyer')

        self.dets = self.default_dets + self.aux_dets
        print_to_gui(f'Staging start', add_timestamp=True, tag='Flyer')
        # print_to_gui(f'{ttime.ctime()} Staging start')
        staged_list = super().stage()
        scan_duration = trajectory_manager.current_trajectory_duration
        for det in self.dets:
            if hasattr(det, 'prepare_to_fly'):
                det.prepare_to_fly(scan_duration)
            print_to_gui(f'start staging {det.name} ...', add_timestamp=True, tag='Flyer', ntabs=1)
            staged_list += det.stage()
        # print_to_gui(f'{ttime.ctime()} Staging done')
        print_to_gui(f'Staging done', add_timestamp=True, tag='Flyer')
        return staged_list

    def unstage(self):
        # print_to_gui(f'{ttime.ctime()} Unstaging start')
        print_to_gui(f'Unstaging start', add_timestamp=True, tag='Flyer')
        unstaged_list = super().unstage()
        for det in self.dets:
            unstaged_list += det.unstage()
        self.flush_dets()
        # print_to_gui(f'{ttime.ctime()} Unstaging done')
        print_to_gui(f'Unstaging done', add_timestamp=True, tag='Flyer')
        return unstaged_list

    def kickoff(self):
        # print(f'{ttime.ctime()} >>> KICKOFF: begin')
        self.kickoff_status = DeviceStatus(self)
        self.complete_status = DeviceStatus(self)
        thread = threading.Thread(target=self.action_sequence, daemon=True)
        thread.start()
        return self.kickoff_status

    def action_sequence(self):
        # print_to_gui(f'{ttime.ctime()} Detector kickoff starting...')
        print_to_gui(f'Detector kickoff starting...', add_timestamp=True, tag='Flyer')
        # apb_status = self.apb_stream.kickoff()
        # apb_status.wait()
        # ttime.sleep(1)

        self.shutter.open(time_opening=True)
        # det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets if (det is not self.apb_stream)])
        det_kickoff_status = combine_status_list([det.kickoff() for det in self.dets])
        det_kickoff_status.wait()
        # print_to_gui(f'{ttime.ctime()} Detector kickoff finished')
        print_to_gui(f'Detector kickoff finished', add_timestamp=True, tag='Flyer')
        # self.shutter.open() # this could be a better place to have shutter open
        # print_to_gui(f'{ttime.ctime()} Mono flight starting...')
        print_to_gui(f'Mono trajectory motion started', add_timestamp=True, tag='Flyer')
        self.hhm_flying_status = self.hhm.kickoff()
        self.kickoff_status.set_finished()

        self.hhm_flying_status.wait()
        # print_to_gui(f'{ttime.ctime()} Mono flight finished')
        print_to_gui(f'Mono trajectory motion ended', add_timestamp=True, tag='Flyer')
        # print_to_gui(f'{ttime.ctime()} Detector complete starting...')
        print_to_gui(f'Detector complete starting...', add_timestamp=True, tag='Flyer')
        det_complete_status = combine_status_list([det.complete() for det in self.dets])
        det_complete_status.wait()
        self.hhm.complete()
        self.shutter.close()
        # print_to_gui(f'{ttime.ctime()} Detector complete finished')
        print_to_gui(f'Detector complete finished', add_timestamp=True, tag='Flyer')
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
        print_to_gui(f'Collect starting', add_timestamp=True, tag='Flyer')
        for det in self.dets:
            yield from det.collect()
        # print_to_gui(f'{ttime.ctime()} Collect finished')
        print_to_gui(f'Collect finished', add_timestamp=True, tag='Flyer')

    def collect_asset_docs(self):
        print_to_gui(f'Collect Asset Docs starting', add_timestamp=True, tag='Flyer')
        for det in self.dets:
            yield from det.collect_asset_docs()
        print_to_gui(f'Collect Asset Docs finished', add_timestamp=True, tag='Flyer')


# flyer_apb = FlyerHHM([apb_stream, pb9.enc1, xs_stream], hhm, shutter, name='flyer_apb')
# flyer_apb = FlyerHHM([apb_stream, pb9.enc1], hhm, shutter, name='flyer_apb')
flyer_hhm = FlyerHHM([apb_stream, hhm_encoder], hhm, shutter, name='flyer_apb')

def get_fly_scan_md(name, comment, trajectory_filename, detectors, element, e0, edge, metadata):
    md_general = get_hhm_scan_md(name, comment, trajectory_filename, detectors, element, e0, edge, metadata, fn_ext='.raw')
    md_scan = {'experiment': 'fly_scan'}
    return {**md_general, **md_scan}


def fly_scan_plan(name=None, comment=None, trajectory_filename=None, mono_angle_offset=None, detectors=[], element='', e0=0, edge='', metadata={}):

    if mono_angle_offset is not None: hhm.set_new_angle_offset(mono_angle_offset)
    trajectory_stack.set_trajectory(trajectory_filename, offset=mono_angle_offset)
    aux_detectors = get_detector_device_list(detectors, flying=True)
    flyer_hhm.set_aux_dets(aux_detectors)

    md = get_fly_scan_md(name, comment, trajectory_filename, detectors, element, e0, edge, metadata)

    @bpp.stage_decorator([flyer_hhm])
    def _fly(md):
        yield from bp.fly([flyer_hhm], md=md)
    yield from _fly(md)