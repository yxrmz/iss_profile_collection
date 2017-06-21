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
            xia1:['xia1_mca1_roi0_sum', 'xia1_mca1_roi1_sum', 
                  'xia1_mca2_roi0_sum', 'xia1_mca2_roi1_sum', 
                  'xia1_mca3_roi0_sum', 'xia1_mca3_roi1_sum',  
                  'xia1_mca4_roi0_sum', 'xia1_mca4_roi1_sum', 
                  'xia1_mca5_roi0_sum', 'xia1_mca5_roi1_sum', 
                  'xia1_mca6_roi0_sum', 'xia1_mca6_roi1_sum', 
                  'xia1_mca7_roi0_sum', 'xia1_mca7_roi1_sum', 
                  'xia1_mca8_roi0_sum', 'xia1_mca8_roi1_sum', 
                  'xia1_mca9_roi0_sum', 'xia1_mca9_roi1_sum', 
                  'xia1_mca10_roi0_sum', 'xia1_mca10_roi1_sum', 
                  'xia1_mca11_roi0_sum', 'xia1_mca11_roi1_sum', 
                  'xia1_mca12_roi0_sum', 'xia1_mca12_roi1_sum', 
                  'xia1_mca13_roi0_sum', 'xia1_mca13_roi1_sum', 
                  'xia1_mca14_roi0_sum', 'xia1_mca14_roi1_sum', 
                  'xia1_mca15_roi0_sum', 'xia1_mca15_roi1_sum',
                  'xia1_mca16_roi0_sum', 'xia1_mca16_roi1_sum']}

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
               hrm.yu,
               hrm.yd1,
               hrm.yd2,
               hrm.mir_pitch,
               hrm.hor_translation,
               hrm.table_pitch,
               hrm.y,
               huber_stage.y,
               huber_stage.pitch,
               xbic.dac1,
               xbic.dac2]

#shutters_dict = collections.OrderedDict([(shutter_fe.name, shutter_fe), 
shutters_dict = collections.OrderedDict([(shutter_ph.name, shutter_ph), 
                                         (shutter.name, shutter)])

xlive_gui = isstools.gui.ScanGui([tscan, tscan_N, tscanxia, tscanxia_N, get_offsets], 
                                 [tune_mono_pitch , tune_mono_y], 
                                 prep_traj_plan, 
                                 RE, 
                                 db, 
                                 hhm, 
                                 shutters_dict,
                                 det_dict,
                                 motors_list,
                                 general_scan,
                                 write_html_log = write_html_log)


def xlive():
    xlive_gui.show()

def cleaning():
    if xlive_gui.piezo_thread.isRunning():
        xlive_gui.toggle_piezo_fb(0)

atexit.register(cleaning)
