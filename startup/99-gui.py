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

motors_dict = {slits.v_gap.name: {'desc': '', 'object': slits.v_gap},
               slits.v_pos.name: {'desc': '', 'object': slits.v_pos},
               slits.hor_in.name: {'desc': '', 'object': slits.hor_in},
               slits.hor_out.name: {'desc': '', 'object': slits.hor_out},
               samplexy.x.name: {'desc': '', 'object': samplexy.x},
               samplexy.y.name: {'desc': '', 'object': samplexy.y},
               hhm.theta.name: {'desc': '', 'object': hhm.theta},
               hhm.energy.name: {'desc': '', 'object': hhm.energy},
               hhm.y.name: {'desc': '', 'object': hhm.y},
               hhm.pitch.name: {'desc': '', 'object': hhm.pitch},
               hhm.roll.name: {'desc': '', 'object': hhm.roll},
               hhrm.yu.name: {'desc': '', 'object': hhrm.yu},
               hhrm.yd1.name: {'desc': '', 'object': hhrm.yd1},
               hhrm.yd2.name: {'desc': '', 'object': hhrm.yd2},
               hhrm.mir_pitch.name: {'desc': '', 'object': hhrm.mir_pitch},
               hhrm.table_pitch.name: {'desc': '', 'object': hhrm.table_pitch},
               hhrm.y.name: {'desc': '', 'object': hhrm.y},
               hrm.theta.name: {'desc': '', 'object': hrm.theta},
               hrm.pitch.name: {'desc': '', 'object': hrm.pitch},
               hrm.y.name: {'desc': '', 'object': hrm.y},
               huber_stage.y.name: {'desc': '', 'object': huber_stage.y},
               huber_stage.pitch.name: {'desc': '', 'object': huber_stage.pitch},
               huber_stage.z.name: {'desc': '', 'object': huber_stage.z},
               xbic.dac1.name: {'desc': '', 'object': xbic.dac1},
               xbic.dac2.name: {'desc': '', 'object': xbic.dac2},
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
               huber_stage.z,
               xbic.dac1,
               xbic.dac2]

auto_tune_elements = [{'name' : hhm.pitch.name,
                      'object' : hhm.pitch,
                      'scan_range' : 5,
                      'step_size' : 0.025,#0.25,
                      'max_retries' : 3,#1,
                      #'step_size' : 0.25,
                      #'max_retries' : 1,
                      'detector_name' : bpm_fm.name,
                      'detector_signame' : bpm_fm.stats1.total.name},
                      {'name' : hhm.y.name,
                      'object' : hhm.y,
                      'scan_range' : 1,
                      'step_size' : 0.025,#0.25,
                      'max_retries' : 3,#1,
                      #'step_size' : 0.25,
                      #'max_retries' : 1,
                      'detector_name' : bpm_fm.name,
                      'detector_signame' : bpm_fm.stats1.total.name},
                      {'name' : hrm.y.name,
                      'object' : hrm.y,
                      'scan_range' : 1,
                      'step_size' : 0.025,#0.25,
                      'max_retries' : 3,#1,
                      #'step_size' : 0.25,
                      #'max_retries' : 1,
                      'detector_name' : i0.name,
                      'detector_signame' : i0.volt.name}
                     ]

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
                                 motors_list,
                                 general_scan,
                                 write_html_log = write_html_log,
                                 auto_tune_elements = auto_tune_elements,
                                 ic_amplifiers = ic_amplifiers)


def xlive():
    xlive_gui.show()

xlive()

def cleaning():
    if xlive_gui.piezo_thread.isRunning():
        xlive_gui.toggle_piezo_fb(0)

atexit.register(cleaning)
