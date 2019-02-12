import sys

from ophyd.sim import motor
motor.move = motor.set



detector_dictionary = {bpm_fm.name: {'obj': bpm_fm, 'elements': ['bpm_fm_stats1_total', 'bpm_fm_stats2_total']},
            bpm_cm.name: {'obj': bpm_cm, 'elements': ['bpm_cm_stats1_total','bpm_cm_stats2_total']},
            bpm_bt1.name: {'obj': bpm_bt1, 'elements': ['bpm_bt1_stats1_total','bpm_bt1_stats2_total']},
            bpm_bt2.name: {'obj': bpm_bt2, 'elements':['bpm_bt2_stats1_total','bpm_bt2_stats2_total']},
            bpm_es.name: {'obj': bpm_es, 'elements':['bpm_es_stats1_total','bpm_es_stats2_total']},
            pb9.enc1.name: {'obj': pb9.enc1, 'elements': ['pb9_enc1_pos_I']},
            it.name: {'obj': it, 'elements': ['pba1_adc1_volt']},
            iff.name: {'obj': iff, 'elements': ['pba1_adc6_volt']},
            i0.name: {'obj': i0, 'elements': ['pba1_adc7_volt'],'channels': ['']},
            ir.name: {'obj': ir, 'elements': ['pba2_adc6_volt']},
            pba2.adc7.name: {'obj': pba2.adc7, 'elements': ['pba2_adc7_volt']},
            xia1.name: {'obj': xia1, 'elements': xia_list}}



motor_dictionary = {'slits_v_gap': {'name': slits.v_gap.name, 'description':'B1 Slit Vertical Gap','object': slits.v_gap},
               'slits_v_pos': {'name': slits.v_pos.name, 'description':'B1 Slit Vertical Position','object': slits.v_pos},
               'slits_hor_in': {'name': slits.hor_in.name,'description':'B1 Slit Horisontal Inboard Position', 'object': slits.hor_in},
               'slits_hor_out': {'name': slits.hor_out.name,'description':'B1 Slit Horisontal Outboard Position', 'object': slits.hor_out},
               'detctorsamplexy_x': {'name': samplexy.x.name, 'description':'B2 Sample Stage X','object': samplexy.x},
               'samplexy_y': {'name': samplexy.y.name, 'description':'B2 Sample Stage Y','object': samplexy.y},
               'giantxy_x': {'name': giantxy.x.name, 'description':'B2 Giant Stage X','object': giantxy.x},
               'giantxy_y': {'name': giantxy.y.name, 'description':'B2 Giant Stage Y','object': giantxy.y},
               'hhm_theta': {'name': hhm.theta.name,'description':'A Monochromator Theta', 'object': hhm.theta},
               'hhm_energy': {'name': hhm.energy.name, 'description':'A Monochromator Energy','object': hhm.energy},
               'hhm_y': {'name': hhm.y.name,'description':'A Monochromator Y', 'object': hhm.y},
               'hhm_pitch': {'name': hhm.pitch.name, 'description':'A Monochromator Pitch','object': hhm.pitch},
               'hhm_roll': {'name': hhm.roll.name, 'description':'A Monochromator Roll', 'object': hhm.roll},
               #'hhrm_yu': {'name': hhrm.yu.name, 'object': hhrm.yu},
               #'hhrm_yd1': {'name': hhrm.yd1.name, 'object': hhrm.yd1},
               #'hhrm_yd2': {'name': hhrm.yd2.name, 'object': hhrm.yd2},
               'hhrm_mir_pitch': {'name': hhrm.mir_pitch.name, 'description':'B1 HHR Mirror Pitch','object': hhrm.mir_pitch},
               'hhrm_table_pitch': {'name': hhrm.table_pitch.name, 'description':'B1 HHR Mirror Table Pitch','object': hhrm.table_pitch},
               'hhrm_y': {'name': hhrm.y.name, 'description':'B1 HHR Mirror Table Height','object': hhrm.y},
               #'hrm_theta': {'name': hrm.theta.name, 'object': hrm.theta},
               #'hrm_pitch': {'name': hrm.pitch.name, 'object': hrm.pitch},
               #'hrm_y': {'name': hrm.y.name, 'object': hrm.y},
               'huber_stage_y': {'name': huber_stage.y.name,  'description':'B2 Huber Stage Y','object': huber_stage.y},
               'huber_stage_pitch': {'name': huber_stage.pitch.name, 'description':'B2 Huber Stage Pitch','object': huber_stage.pitch},
               'huber_stage_z': {'name': huber_stage.z.name, 'description':'B2 Huber Stage Z','object': huber_stage.z},
               'Dummy Motor': {'name': motor.name, 'description':'A dummy motor','object': motor},
#               'xbic_dac1': {'name': xbic.dac1.name, 'object': xbic.dac1},
#               'xbic_dac2': {'name': xbic.dac2.name, 'object': xbic.dac2}
               'six_axes_stage_x': {'name': six_axes_stage.x.name, 'description':'Six Axes Stage X', 'object': six_axes_stage.x},
               'six_axes_stage_y': {'name': six_axes_stage.y.name, 'description':'Six Axes Stage Y', 'object': six_axes_stage.y},
               'six_axes_stage_z': {'name': six_axes_stage.z.name, 'description':'Six Axes Stage Z', 'object': six_axes_stage.z},
               'six_axes_stage_pitch': {'name': six_axes_stage.pitch.name, 'description':'Six Axes Stage Pitch', 'object': six_axes_stage.pitch},
               'six_axes_stage_yaw': {'name': six_axes_stage.yaw.name, 'description':'Six Axes Stage Yaw', 'object': six_axes_stage.yaw},
               'six_axes_stage_roll': {'name': six_axes_stage.roll.name, 'description':'Six Axes Stage Roll', 'object': six_axes_stage.roll}
              }



tune_elements =  [{'motor': hhm.pitch.name,
                   'detector': bpm_fm.name,
                   'range': 10,
                   'step': 0.1,
                   'retries': 10,
                   'comment': 'rough monochromator pitch tune'},
                  {'motor': hhm.pitch.name,
                   'detector': bpm_fm.name,
                   'range': 1,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                  {'motor': hhm.y.name,
                   'detector': bpm_fm.name,
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'monochromator crystal distance tune'},
                  {'motor': hhrm.y.name,
                   'detector': i0.name,
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'Harmonic rejection mirror tune'},
                ]

def tune_beamline_plan(stdout=sys.stdout):

    print_to_gui(f'[Beamline tuning] Starting...',stdout=stdout)
    yield from bps.mv(hhm.fb_status,0)


    yield from bps.mv(bpm_fm,'insert')



    for element in tune_elements:
        detector = detector_dictionary[element['detector']]['obj']
        motor = motor_dictionary[element['motor']]['object']
        yield from tuning_scan(motor, detector,
                              element['range'],
                              element['step'],
                              retries=element['retries'],
                              stdout=stdout
                              )
        # turn camera into continuous mode
        if hasattr(detector, 'image_mode'):
            yield from bps.mv(getattr(detector, 'image_mode'), 2)
            yield from bps.mv(getattr(detector, 'acquire'), 1)

    yield from bps.mv(bpm_fm, 'retract')
    print('[Beamline tuning] Beamline tuning complete')