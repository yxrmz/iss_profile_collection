import sys
import collections


from ophyd.sim import motor
motor.move = motor.set


detector_dictionary =   {
                    'I0 ion Chamber': {'device': apb_ave, 'channels': ['apb_ave_ch1_mean']},
                    'It ion Chamber': {'device': apb_ave, 'channels': ['apb_ave_ch2_mean']},
                    'Ir ion Chamber': {'device': apb_ave, 'channels': ['apb_ave_ch3_mean']},
                    'PIPS detector': {'device': apb_ave, 'channels': ['apb_ave_ch4_mean']},
                    'Focusing mirror BPM': {'device': bpm_fm, 'channels': ['bpm_fm_stats1_total', 'bpm_fm_stats2_total']},
                    'Endstation BPM': {'device': bpm_es, 'channels': ['bpm_es_stats1_total','bpm_es_stats2_total']},
                    'Camera SP1': {'device': camera_sp1, 'channels': ['camera_sp1_stats1_total','camera_sp1_stats2_total']},
                    'Pilatus 100k': {'device': pil100k, 'channels': ['pil100k_stats1_total','pil100k_stats2_total',
                                                                     'pil100k_stats3_total','pil100k_stats4_total']}



                }


# detector_dictionary = \
#             {
#             bpm_fm.name: {'obj': bpm_fm, 'elements': ['bpm_fm_stats1_total', 'bpm_fm_stats2_total']},
#             bpm_cm.name: {'obj': bpm_cm, 'elements': ['bpm_cm_stats1_total','bpm_cm_stats2_total']},
#             bpm_bt1.name: {'obj': bpm_bt1, 'elements': ['bpm_bt1_stats1_total','bpm_bt1_stats2_total']},
#             bpm_bt2.name: {'obj': bpm_bt2, 'elements':['bpm_bt2_stats1_total','bpm_bt2_stats2_total']},
#             bpm_es.name: {'obj': bpm_es, 'elements':['bpm_es_stats1_total','bpm_es_stats2_total']},
#             pb9.enc1.name: {'obj': pb9.enc1, 'elements': ['pb9_enc1_pos_I']},
#             it.name: {'obj': it, 'elements': ['pba1_adc1_volt']},
#             iff.name: {'obj': iff, 'elements': ['pba1_adc6_volt']},
#             i0.name: {'obj': i0, 'elements': ['pba1_adc7_volt'],'channels': ['']},
#             ir.name: {'obj': ir, 'elements': ['pba2_adc6_volt']},
#             pba2.adc7.name: {'obj': pba2.adc7, 'elements': ['pba2_adc7_volt']},
#             xia1.name: {'obj': xia1, 'elements': xia_list},
#             apb_ave.name: {'obj': 'i0n', 'elements': ['abv_ave_ch1_mean']},
#             }



motor_dictionary = {'slits_v_gap': {'name': slits.v_gap.name, 'description':'B1 Slit Vertical Gap','object': slits.v_gap},
               'slits_v_pos': {'name': slits.v_pos.name, 'description':'B1 Slit Vertical Position','object': slits.v_pos},
               'slits_hor_in': {'name': slits.hor_in.name,'description':'B1 Slit Horisontal Inboard Position', 'object': slits.hor_in},
               'slits_hor_out': {'name': slits.hor_out.name,'description':'B1 Slit Horisontal Outboard Position', 'object': slits.hor_out},
               'samplexy_x': {'name': samplexy.x.name, 'description':'B2 Sample Stage X','object': samplexy.x},
               'samplexy_y': {'name': samplexy.y.name, 'description':'B2 Sample Stage Y','object': samplexy.y},
               'giantxy_x': {'name': giantxy.x.name, 'description':'B2 Giant Stage X','object': giantxy.x},
               'giantxy_y': {'name': giantxy.y.name, 'description':'B2 Giant Stage Y','object': giantxy.y},
               'auxxy_x': {'name': auxxy.x.name, 'description':'B2 Aux Stage X','object': auxxy.x},
               'auxxy_y': {'name': auxxy.y.name, 'description':'B2 Aux Stage Y','object': auxxy.y},
               'hhm_theta': {'name': hhm.theta.name,'description':'A Monochromator Theta', 'object': hhm.theta},
               'hhm_energy': {'name': hhm.energy.name, 'description':'A Monochromator Energy','object': hhm.energy},
               'hhm_y': {'name': hhm.y.name,'description':'A Monochromator Y', 'object': hhm.y},
               'hhm_pitch': {'name': hhm.pitch.name, 'description':'A Monochromator Pitch','object': hhm.pitch},
               'hhm_roll': {'name': hhm.roll.name, 'description':'A Monochromator Roll', 'object': hhm.roll},
               #'hhrm_yu': {'name': hhrm.yu.name, 'object': hhrm.yu},
               #'hhrm_yd1': {'name': hhrm.yd1.name, 'object': hhrm.yd1},
               #'hhrm_yd2': {'name': hhrm.yd2.name, 'object': hhrm.yd2},
               'hhrm_mir_pitch': {'name': hhrm.mir_pitch.name, 'description':'B1 HHR Mirror Pitch','object': hhrm.mir_pitch},
               'hhrm_table_pitch': {'name': hhrm.table_pitch.name, 'description':'B1 HR Mirror Table Pitch','object': hhrm.table_pitch},
               'hhrm_y': {'name': hhrm.y.name, 'description':'B1 HHR Mirror Table Height','object': hhrm.y},
               #'hrm_theta': {'name': hrm.theta.name, 'object': hrm.theta},
               #'hrm_pitch': {'name': hrm.pitch.name, 'object': hrm.pitch},
               #'hrm_y': {'name': hrm.y.name, 'object': hrm.y},
               'huber_stage_y': {'name': huber_stage.y.name,  'description':'B2 Huber Stage Y','object': huber_stage.y},
               'huber_stage_pitch': {'name': huber_stage.pitch.name, 'description':'B2 Huber Stage Pitch','object': huber_stage.pitch},
               'huber_stage_z': {'name': huber_stage.z.name, 'description':'B2 Huber Stage Z','object': huber_stage.z},
               'Dummy Motor': {'name': motor.name, 'description':'A dummy motor','object': motor},
               'goniometer_1_th ': {'name': gonio_meter.th1.name , 'description':'B2 Goniometer 1-Th', 'object': gonio_meter.th1},
               'goniometer_2_th ': {'name': gonio_meter.th2.name , 'description':'B2 Goniometer 2-Th', 'object': gonio_meter.th2},
#               'xbic_dac1': {'name': xbic.dac1.name, 'object': xbic.dac1},
#               'xbic_dac2': {'name': xbic.dac2.name, 'object': xbic.dac2}
               'six_axes_stage_x': {'name': six_axes_stage.x.name, 'description':'B2 Six Axes Stage X', 'object': six_axes_stage.x},
               'six_axes_stage_y': {'name': six_axes_stage.y.name, 'description':'B2 Six Axes Stage Y', 'object': six_axes_stage.y},
               'six_axes_stage_z': {'name': six_axes_stage.z.name, 'description':'B2 Six Axes Stage Z', 'object': six_axes_stage.z},
               'six_axes_stage_pitch': {'name': six_axes_stage.pitch.name, 'description':'B2 Six Axes Stage Pitch', 'object': six_axes_stage.pitch},
               'six_axes_stage_yaw': {'name': six_axes_stage.yaw.name, 'description':'B2 Six Axes Stage Yaw', 'object': six_axes_stage.yaw},
               'six_axes_stage_roll': {'name': six_axes_stage.roll.name, 'description':'B2 Six Axes Stage Roll', 'object': six_axes_stage.roll},
               'detstage_x': {'name': detstage.x.name, 'description': 'Detector Stage X','object': detstage.x},
               'detstage_y': {'name': detstage.y.name, 'description': 'Detector Stage Y','object': detstage.y},
               'detstage_z': {'name': detstage.z.name, 'description': 'Detector Stage Z','object': detstage.z},
               'cm1_x' : {'name' : cm1.x.name, 'description': 'Collimating mirror X','object': cm1.x},
              'usermotor2' : {'name' : usermotor2.name, 'description' : 'Small sample Z', 'object' : usermotor2.pos},
              'sample_shutter_angle' : {'name' : usermotor3.name, 'description' : 'sample shutter angle ', 'object' : usermotor3.pos}}


shutter_dictionary = collections.OrderedDict([(shutter_fe.name, shutter_fe),
                                         (shutter_ph.name, shutter_ph),
                                         (shutter.name, shutter)])

ic_amplifiers = {'i0_amp': i0_amp,
                 'it_amp': it_amp,
                 'ir_amp': ir_amp,
                 'iff_amp': iff_amp}

camera_dictionary = {'camera_sample1': camera_sp1,
                     'camera_sample2': camera_sp2,
                     'camera_sample4': camera_sp4,

                     }

