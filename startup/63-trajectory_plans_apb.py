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
    def __init__(self, dets, hhm, shutter, *args, **kwargs):
        super().__init__(parent=None, **kwargs)
        self.dets = dets
        self.hhm = hhm
        self.shutter = shutter
        self.complete_status = None

    def stage(self):
        self.hhm.prepare()
        staged_list = super().stage()
        scan_duration = trajectory_manager.current_trajectory_duration
        for det in self.dets:
            if hasattr(det, 'set_num_points'):
                det.set_num_points(scan_duration)
            staged_list += det.stage()
        return staged_list

    def unstage(self):
        unstaged_list = super().unstage()
        for det in self.dets:
            unstaged_list += det.unstage()
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
        self.shutter.open(time_opening=True)
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

    # def describe_collect(self):
    #     return_dict = self.det.describe_collect()
    #     # Also do it for all pizza-boxes
    #     for pb in self.pbs:
    #         return_dict[pb.name] = pb.describe_collect()[pb.name]
    #
    #     return return_dict

    def describe_collect(self):
        # print(f'{ttime.ctime()} >>> DESCRIBE_COLLECT: begin')
        return_dict = {}
        for det in self.dets:
            return_dict = {**return_dict, **det.describe_collect()}
        return return_dict

    def collect(self):
        # print(f'{ttime.ctime()} >>> COLLECT: begin')
        for det in self.dets:
            yield from det.collect()
        # def collect_all():
        #     for det in self.dets:
        #         yield from det.collect()
        # return (yield from collect_all())

    def collect_asset_docs(self):
        # print(f'{ttime.ctime()} >>> COLLECT_ASSET_DOCS: begin')
        for det in self.dets:
            yield from det.collect_asset_docs()



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
flyer_apb = FlyerHHM([apb_stream, pb9.enc1, apb_trigger], hhm, shutter, name='flyer_apb')


def get_md_for_scan(name, mono_scan_type, plan_name, experiment, **metadata):
    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Storing data at {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.get()))
    try:
        full_element_name = getattr(elements, curr_traj.elem.get()).name.capitalize()
    except:
        full_element_name = curr_traj.elem.get()

    # try:
    #     nsls_ii_current = nsls_ii.beam_current.get()
    # except:
    #     nsls_ii_current = 0
    # try:
    #     nsls_ii_status = nsls_ii.return_status_string()
    # except:
    #     nsls_ii_status = 'Shutdown'
    if mono_scan_type == 'fly_scan':
        mono_direction = 'backward in energy'
    else:
        mono_direction = 'forward in energy'

    gas_n2_flow = gas_n2.flow.get()
    gas_he_flow = gas_he.flow.get()
    gas_tot_flow = gas_n2_flow + gas_he_flow
    gas_he_perc = np.round(gas_he_flow/gas_tot_flow * 100)
    gas_n2_perc = np.round(gas_n2_flow/gas_tot_flow * 100)

    i0_volt = np.round(wps1.hv302.read_pv.get())
    it_volt = np.round(wps1.hv303.read_pv.get())
    ir_volt = np.round(wps1.hv305.read_pv.get())

    md = {'plan_args': {},
          'plan_name': plan_name,
          'experiment': experiment,
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.get()),
          'trajectory_name': hhm.trajectory_name.get(),
          'element': curr_traj.elem.get(),
          'element_full': full_element_name,
          'edge': curr_traj.edge.get(),
          'e0': curr_traj.e0.get(),
          'pulses_per_degree': hhm.pulses_per_deg,
          'nslsii_current' : 0,#          'nslsii_current' : nsls_ii_current,
          'nslsii_status' : 'Shutdown', #'nslsii_status' : nsls_ii_status,
          'nslsii_energy' : nsls_ii.energy_str,
          'harmonic_rejection' : '', #hhrm.current_sripe(),
          'i0_par' : f'{i0.ic_length}cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'it_par' : f'{it.ic_length}cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'ir_par' : f'{ir.ic_length}cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'iff_par' : f'PIPS (300um Si)',
          'i0_volt' : i0_volt,
          'it_volt' : it_volt,
          'ir_volt' : ir_volt,
          'i0_gain' : i0.amp.get_gain()[0],
          'it_gain' : it.amp.get_gain()[0],
          'ir_gain' : ir.amp.get_gain()[0],
          'iff_gain' : iff.amp.get_gain()[0],
          'aux_detector' : '',
          'mono_offset' : f'{np.round(hhm.angle_offset.get()*180/np.pi, 3)} deg',
          'mono_encoder_resolution' : str(np.round(hhm.main_motor_res.get()*np.pi/180*1e9)) +' nrad',
          'mono_scan_mode' : 'pseudo-channel cut',
          'mono_scan_type' : mono_scan_type,
          'mono_direction' : mono_direction,
          'sample_stage' : 'ISS.giant_xy stage',
          'sample_x_position' : giantxy.x.user_readback.get(),
          'sample_y_position' : giantxy.y.user_readback.get(),
          'plot_hint' : '$5/$1'
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
    md = get_md_for_scan(name,
                         'fly_scan',
                         'execute_trajectory_apb',
                         'fly_energy_scan_apb',
                         **metadata)

    @bpp.stage_decorator([flyer_apb])
    def _fly(md):
        yield from bp.fly([flyer_apb], md=md)
    yield from _fly(md)
