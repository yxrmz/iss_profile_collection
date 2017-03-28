import isstools.gui

det_dict = {bpm_fm:['bpm_fm_stats1_total', 'bpm_fm_stats2_total'], 
            bpm_cm:['bpm_cm_stats1_total','bpm_cm_stats2_total'],
            bpm_bt1:['bpm_bt1_stats1_total','bpm_bt1_stats2_total'],
            bpm_bt2:['bpm_bt2_stats1_total','bpm_bt2_stats2_total'],
            bpm_es:['bpm_es_stats1_total','bpm_es_stats2_total'],
            it:['pba1_adc1_volt'],
            iff:['pba1_adc6_volt'],
            i0:['pba1_adc7_volt'],
            ir:['pba2_adc6_volt'],
            pba2.adc7:['pba2_adc7_volt'],
            xia1:['xia1_mca1_roi0_sum', 'xia1_mca1_roi1_sum', 
                  'xia1_mca2_roi0_sum', 'xia1_mca2_roi1_sum', 
                  'xia1_mca3_roi0_sum', 'xia1_mca3_roi1_sum', 
                  'xia1_mca4_roi0_sum', 'xia1_mca4_roi1_sum', ]}

motors_list = [samplexy.x,
               samplexy.y,
               hhm.theta,
               hhm.y,
               hhm.pitch,
               hhm.roll,
               hrm.yu,
               hrm.yd1,
               hrm.yd2,
               hrm.mir_pitch,
               hrm.hor_translation,
               hrm.table_pitch,
               hrm.y]

xlive_gui = isstools.gui.ScanGui([tscan, tscan_N, tscanxia, tscanxia_N, xia_step_scan, get_offsets], 
                                 [tune_mono_pitch , tune_mono_y], 
                                 prep_traj_plan, 
                                 RE, 
                                 db, 
                                 hhm, 
                                 {'xia':xia1, 'pba1':pba1, 'pba2':pba2}, 
                                 shutter, 
                                 det_dict,
                                 motors_list,
                                 general_scan,
                                 write_html_log = write_html_log2)

def xlive():
    xlive_gui.show()
