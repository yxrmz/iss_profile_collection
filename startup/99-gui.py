import isstools.gui
import collections
import atexit

det_dict = {bpm_fm:['bpm_fm_stats1_total', 'bpm_fm_stats2_total'], 
            bpm_cm:['bpm_cm_stats1_total','bpm_cm_stats2_total'],
            bpm_bt1:['bpm_bt1_stats1_total','bpm_bt1_stats2_total'],
            bpm_bt2:['bpm_bt2_stats1_total','bpm_bt2_stats2_total'],
            bpm_es:['bpm_es_stats1_total','bpm_es_stats2_total'],
            pb9.enc1:['pb9_enc1_pos_I'],
            it:['pba1_adc1_volt'],
            iff:['pba1_adc6_volt'],
            i0:['pba1_adc7_volt'],
            ir:['pba2_adc6_volt'],
            pba2.adc7:['pba2_adc7_volt'],
            xia1: xia_list}

motors_dict = {'slits_v_gap': {'name': slits.v_gap.name, 'object': slits.v_gap},
               'slits_v_pos': {'name': slits.v_pos.name, 'object': slits.v_pos},
               'slits_hor_in': {'name': slits.hor_in.name, 'object': slits.hor_in},
               'slits_hor_out': {'name': slits.hor_out.name, 'object': slits.hor_out},
               'samplexy_x': {'name': samplexy.x.name, 'object': samplexy.x},
               'samplexy_y': {'name': samplexy.y.name, 'object': samplexy.y},
               'hhm_theta': {'name': hhm.theta.name, 'object': hhm.theta},
               'hhm_energy': {'name': hhm.energy.name, 'object': hhm.energy},
               'hhm_y': {'name': hhm.y.name, 'object': hhm.y},
               'hhm_pitch': {'name': hhm.pitch.name, 'object': hhm.pitch},
               'hhm_roll': {'name': hhm.roll.name, 'object': hhm.roll},
               'hhrm_yu': {'name': hhrm.yu.name, 'object': hhrm.yu},
               'hhrm_yd1': {'name': hhrm.yd1.name, 'object': hhrm.yd1},
               'hhrm_yd2': {'name': hhrm.yd2.name, 'object': hhrm.yd2},
               'hhrm_mir_pitch': {'name': hhrm.mir_pitch.name, 'object': hhrm.mir_pitch},
               'hhrm_table_pitch': {'name': hhrm.table_pitch.name, 'object': hhrm.table_pitch},
               'hhrm_y': {'name': hhrm.y.name, 'object': hhrm.y},
               'hrm_theta': {'name': hrm.theta.name, 'object': hrm.theta},
               'hrm_pitch': {'name': hrm.pitch.name, 'object': hrm.pitch},
               'hrm_y': {'name': hrm.y.name, 'object': hrm.y},
               'huber_stage_y': {'name': huber_stage.y.name, 'object': huber_stage.y},
               'huber_stage_pitch': {'name': huber_stage.pitch.name, 'object': huber_stage.pitch},
               'huber_stage_z': {'name': huber_stage.z.name, 'object': huber_stage.z}
#               'xbic_dac1': {'name': xbic.dac1.name, 'object': xbic.dac1},
#               'xbic_dac2': {'name': xbic.dac2.name, 'object': xbic.dac2}
              }

motors_list = [slits.v_gap,
               slits.v_pos,
               slits.hor_in,
               slits.hor_out,
               samplexy.x,
               samplexy.y,
               hhm.theta,
               hhm.energy,
               hhm.y,
               hhm.pitch,
               hhm.roll,
               hhrm.yu,
               hhrm.yd1,
               hhrm.yd2,
               hhrm.mir_pitch,
               hhrm.hor_translation,
               hhrm.table_pitch,
               hhrm.y,
               hrm.theta,
               hrm.pitch,
               hrm.y,
               huber_stage.y,
               huber_stage.pitch,
               huber_stage.z]
               #xbic.dac1,
               #xbic.dac2]

auto_tune = { 'pre_elements':[{'name' : bpm_fm.name,
                               'motor' : bpm_fm.ins,
                               'read_back' : bpm_fm.switch_insert,
                               'tries' : 3,
                               'value' : 1}
                             ],
              'post_elements':[{'name' : bpm_fm.name,
                                'motor' : bpm_fm.ret,
                                'read_back' : bpm_fm.switch_retract,
                                'tries' : 3,
                                'value' : 1}
                              ],
              'elements':[{'name' : hhm.pitch.name,
                           'object' : hhm.pitch,
                           'scan_range' : 5,
                           'step_size' : 0.025,#0.25,
                           'max_retries' : 3,#1,
                           'detector_name' : bpm_fm.name,
                           'detector_signame' : bpm_fm.stats1.total.name},
                           {'name' : hhm.y.name,
                           'object' : hhm.y,
                           'scan_range' : 1,
                           'step_size' : 0.025,#0.25,
                           'max_retries' : 3,#1,
                           'detector_name' : bpm_fm.name,
                           'detector_signame' : bpm_fm.stats1.total.name},
                           {'name' : hhrm.y.name,
                           'object' : hhrm.y,
                           'scan_range' : 1,
                           'step_size' : 0.025,#0.25,
                           'max_retries' : 3,#1,
                           'detector_name' : i0.dev_name.value,
                           'detector_signame' : i0.volt.name}
                          ]
           }

shutters_dict = collections.OrderedDict([(shutter_fe.name, shutter_fe), 
                                         (shutter_ph.name, shutter_ph),
                                         (shutter.name, shutter)])

ic_amplifiers = {'i0_amp': i0_amp,
                 'it_amp': it_amp,
                 'ir_amp': ir_amp,
                 'iff_amp': iff_amp}

xlive_gui = isstools.gui.ScanGui([tscan, tscanxia, get_offsets, sleep_seconds], 
                                 prep_traj_plan, 
                                 RE,
                                 db, 
                                 hhm, 
                                 shutters_dict,
                                 det_dict,
                                 motors_dict,
                                 general_scan,
                                 write_html_log = write_html_log,
                                 auto_tune_elements = auto_tune,
                                 ic_amplifiers = ic_amplifiers,
                                 set_gains_offsets = set_gains_and_offsets)


def xlive():
    xlive_gui.show()

xlive()

def cleaning():
    if xlive_gui.piezo_thread.isRunning():
        xlive_gui.toggle_piezo_fb(0)

atexit.register(cleaning)
