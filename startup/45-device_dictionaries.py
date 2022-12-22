import sys
import collections


from ophyd.sim import motor
motor.move = motor.set



detector_dictionary =   {

                    'I0 ion Chamber': {'device': apb_ave, 'channels': ['apb_ave_ch1_mean']},
                    'It ion Chamber': {'device': apb_ave, 'channels': ['apb_ave_ch2_mean']},
                    'Ir ion Chamber': {'device': apb_ave, 'channels': ['apb_ave_ch3_mean']},
                    'PIPS detector': {'device': apb_ave, 'channels': ['apb_ave_ch4_mean']},
                    'I0 ion Chamber instantaneous': {'device': apb, 'channels': ['apb_ch1']},
                    'It ion Chamber instantaneous': {'device': apb, 'channels': ['apb_ch2']},
                    'Ir ion Chamber instantaneous': {'device': apb, 'channels': ['apb_ch3']},
                    'PIPS detector instantaneous': {'device': apb, 'channels': ['apb_ch4']},
                    'Focusing mirror BPM': {'device': bpm_fm, 'channels': ['bpm_fm_stats1_total', 'bpm_fm_stats2_total']},
                    'Endstation BPM': {'device': bpm_es, 'channels': ['bpm_es_stats1_total','bpm_es_stats2_total']},
                    'Camera SP1': {'device': camera_sp1, 'channels': ['camera_sp1_stats1_total', 'camera_sp1_stats1_net', 'camera_sp1_stats2_total', 'camera_sp1_stats2_net']},
                    'Camera SP2': {'device': camera_sp2, 'channels': ['camera_sp2_stats1_total', 'camera_sp2_stats1_net', 'camera_sp2_stats2_total', 'camera_sp2_stats2_net']},
                    'Camera SP3': {'device': camera_sp3, 'channels': ['camera_sp3_stats1_total', 'camera_sp3_stats2_total']},
                    'Camera SP5': {'device': camera_sp5, 'channels': ['camera_sp5_stats1_total', 'camera_sp5_stats2_total']},
                    'Camera SP6': {'device': camera_sp6, 'channels': ['camera_sp5_stats1_total', 'camera_sp5_stats2_total']},
                    'Pilatus 100k': {'device': pil100k, 'flying_device' : pil100k_stream,
                                     'channels': ['pil100k_stats1_total','pil100k_stats2_total',
                                                                    'pil100k_stats3_total','pil100k_stats4_total',
                                                                     'pil100k_stats1_max_value']},
                    'Xspress3': {'device' : xs, 'flying_device' : xs_stream,
                                 'channels' : [     'xs_channel1_rois_roi01_value',
                                                    'xs_channel1_rois_roi02_value',
                                                    'xs_channel1_rois_roi03_value',
                                                    'xs_channel1_rois_roi04_value',
                                                    'xs_channel2_rois_roi01_value',
                                                    'xs_channel2_rois_roi02_value',
                                                    'xs_channel2_rois_roi03_value',
                                                    'xs_channel2_rois_roi04_value',
                                                    'xs_channel3_rois_roi01_value',
                                                    'xs_channel3_rois_roi02_value',
                                                    'xs_channel3_rois_roi03_value',
                                                    'xs_channel3_rois_roi04_value',
                                                    'xs_channel4_rois_roi01_value',
                                                    'xs_channel4_rois_roi02_value',
                                                    'xs_channel4_rois_roi03_value',
                                                    'xs_channel4_rois_roi04_value',
                                                    'xs_settings_acquire_time'
                                                    ]}
                }

def get_detector_device_list(key_list, flying=True):
    dets = []
    for key in key_list:
        if flying:
            device = detector_dictionary[key]['flying_device']
        else:
            device = detector_dictionary[key]['device']
        dets.append(device)
    return dets


class KeyDetectorNotIncluded(Exception):
    pass

def ensure_pilatus_is_in_detector_list(detectors):
    if not ('Pilatus 100k' in detectors):
        raise KeyDetectorNotIncluded(f'Error: Pilatus 100k not found in the detector list')



motor_dictionary = {
    'cm1_x':                    {'name' : cm1.x.name,               'description': 'A Collimating mirror X',                  'object': cm1.x},
    'bender':                   {'name' : bender.name,              'description': 'A CM2 bender',                          'object': bender.pos,           'group': 'spectrometer'},
    'hhm_theta':                {'name': hhm.theta.name,            'description': 'A Monochromator Theta',                 'object': hhm.theta},
    'hhm_energy':               {'name': hhm.energy.name,           'description': 'A Monochromator Energy',                'object': hhm.energy,           'group': 'spectrometer','user':True},
    'hhm_y':                    {'name': hhm.y.name,                'description': 'A Monochromator Y',                     'object': hhm.y,                'user': True},
    'hhm_y_precise':            {'name': hhm.y_precise.name,        'description': 'A Monochromator Y precise',             'object': hhm.y_precise,        'user': True},
    'hhm_pitch':                {'name': hhm.pitch.name,            'description': 'A Monochromator Pitch',                 'object': hhm.pitch,            'user': True},
    'hhm_roll':                 {'name': hhm.roll.name,             'description': 'A Monochromator Roll',                  'object': hhm.roll, },
    'fm_pitch':                 {'name': fm.pitch.name,             'description': 'A Focusing Mirror Pitch',               'object': fm.pitch},
    'hhrm_mir_pitch':           {'name': hhrm.mir_pitch.name,       'description': 'B1 HHR Mirror Pitch',                   'object': hhrm.mir_pitch},
    'hhrm_table_pitch':         {'name': hhrm.table_pitch.name,     'description': 'B1 HHR Mirror Table Pitch',             'object': hhrm.table_pitch},
    'hhrm_y':                   {'name': hhrm.y.name,               'description': 'B1 HHR Mirror Table Height',            'object': hhrm.y,               'user': True},
    'hhrm_yu':                  {'name': hhrm.yu.name,              'description': 'B1 HHR Mirror Y Upstream',              'object': hhrm.yu},
    'hhrm_yd':                  {'name': hhrm.yd1.name,             'description': 'B1 HHR Mirror Y Downstream',            'object': hhrm.yd1},
    'slits_v_gap':              {'name': slits.v_gap.name,          'description': 'B1 Slit Vertical Gap',                  'object': slits.v_gap},
    'slits_v_pos':              {'name': slits.v_pos.name,          'description': 'B1 Slit Vertical Position',             'object': slits.v_pos},
    'slits_hor_in':             {'name': slits.hor_in.name,         'description': 'B1 Slit Horisontal Inboard Position',   'object': slits.hor_in},
    'slits_hor_out':            {'name': slits.hor_out.name,        'description': 'B1 Slit Horisontal Outboard Position',  'object': slits.hor_out},
    'sample_shutter_angle':     {'name': usermotor3.name,           'description': 'B1 User shutter angle ',                'object': usermotor3.pos},
    # 'usermotor3' :              {'name' : usermotor3.name,          'description' : 'User shutter angle',                   'object' : usermotor3.pos},
    'i0_y_pos':                 {'name': i0_y.pos.name,             'description': 'B1 I0 Chamber height',                  'object': i0_y.pos},
    'it_y_pos':                 {'name': it_y.pos.name,             'description': 'B1 It Chamber height',                  'object': it_y.pos},
    'ir_y_pos':                 {'name': ir_y.pos.name,             'description': 'B1 Ir Chamber height',                  'object': ir_y.pos},
    'sample_stage_x':           {'name': sample_stage.x.name,       'description': 'Sample stage X',                        'object': sample_stage.x,       'group': 'spectrometer',    'user':True},
    'sample_stage_y':           {'name': sample_stage.y.name,       'description': 'Sample stage Y',                        'object': sample_stage.y,       'group': 'spectrometer',    'user':True},
    'sample_stage_z':           {'name': sample_stage.z.name,       'description': 'Sample stage Z',                        'object': sample_stage.z,       'group': 'spectrometer',    'user':True},
    'sample_stage_th':          {'name': sample_stage.th.name,      'description': 'Sample stage Th',                       'object': sample_stage.th,      'group': 'spectrometer',    'user':True},
    'foil_wheel_wheel1' :       {'name': foil_wheel.wheel1.name,    'description': 'B1 Reference foil wheel 1',             'object' : foil_wheel.wheel1},
    'foil_wheel_wheel2' :       {'name': foil_wheel.wheel2.name,    'description': 'B1 Reference foil wheel 2',             'object' : foil_wheel.wheel2},
    'det2_stage_x':             {'name': det2_stage_x.pos.name,     'description': 'B1 Detector stage 2 X',                 'object': det2_stage_x.pos,     'user':True},
    'det2_stage_y':             {'name': det2_stage_y.pos.name,     'description': 'B1 Detector stage 2 Y',                 'object': det2_stage_y.pos,     'user':True},
    # 'huber_stage_y':            {'name': huber_stage.y.name,        'description':'Pilatus motion X',                       'object': huber_stage.y,        'group': 'spectrometer'},
    # 'huber_stage_pitch':        {'name': huber_stage.pitch.name,    'description':'B2 Huber Stage Pitch',                   'object': huber_stage.pitch},
    # 'huber_stage_z':            {'name': huber_stage.z.name,        'description':'Pilatus motion Y',                       'object': huber_stage.z,        'group': 'spectrometer'},
    # 'detstage_x':               {'name': detstage.x.name,           'description': 'PIPS Stage X',                          'object': detstage.x},
    # 'detstage_y':               {'name': detstage.y.name,           'description': 'PIPS Stage Y',                          'object': detstage.y},
    # 'detstage_z':               {'name': detstage.z.name,           'description': 'PIPS Stage Z',                          'object': detstage.z},
    'six_axes_stage_x':         {'name': six_axes_stage.x.name,     'description': 'PCL Six Axes Stage X',                  'object': six_axes_stage.x,     'group': 'spectrometer'},
    'six_axes_stage_y':         {'name': six_axes_stage.y.name,     'description': 'PCL Six Axes Stage Y',                  'object': six_axes_stage.y,     'group': 'spectrometer'},
    'six_axes_stage_z':         {'name': six_axes_stage.z.name,     'description': 'PCL Six Axes Stage Z',                  'object': six_axes_stage.z,     'group': 'spectrometer'},
    'six_axes_stage_pitch':     {'name': six_axes_stage.pitch.name, 'description': 'PCL Six Axes Stage Pitch',              'object': six_axes_stage.pitch, 'group': 'spectrometer'},
    'six_axes_stage_yaw':       {'name': six_axes_stage.yaw.name,   'description': 'PCL Six Axes Stage Yaw',                'object': six_axes_stage.yaw,   'group': 'spectrometer'},
    'six_axes_stage_roll':      {'name': six_axes_stage.roll.name,  'description': 'PCL Six Axes Stage Roll',               'object': six_axes_stage.roll,  'group': 'spectrometer'},
    'auxxy_x':                  {'name': auxxy.x.name,              'description': 'Johann Crystal Assy X',                 'object': auxxy.x,              'group': 'spectrometer'},
    'auxxy_y':                  {'name': auxxy.y.name,              'description': 'Johann Detector X',                     'object': auxxy.y,              'group': 'spectrometer'},
}

def get_motor_device(motor_attr, based_on='description'):
    for key, motor_dict in motor_dictionary.items():
        if based_on == 'description':
            if motor_attr == motor_dict['description']:
                return motor_dict['object']
        elif based_on == 'object_name':
            if motor_attr == motor_dict['name']:
                return motor_dict['object']


shutter_dictionary = collections.OrderedDict([(shutter_fe.name, shutter_fe),
                                         (shutter_ph.name, shutter_ph),
                                         (shutter.name, shutter)])

ic_amplifiers = {'i0_amp': i0_amp,
                 'it_amp': it_amp,
                 'ir_amp': ir_amp,
                 'iff_amp': iff_amp}

camera_dictionary = {'camera_sample1': camera_sp1,
                     'camera_sample2': camera_sp2,
                     'camera_sample4': camera_sp4}
