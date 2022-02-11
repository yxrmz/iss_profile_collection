

tune_elements =  [{'motor': hhm.pitch.name,
                   'detector': 'Focusing mirror BPM',
                   'range': 10,
                   'step': 0.1,
                   'retries': 10,
                   'comment': 'rough monochromator pitch tune'},
                  {'motor': hhm.pitch.name,
                   'detector': 'Focusing mirror BPM',
                   'range': 1,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                  # {'motor': hhm.y.name,
                  #  'detector':'Focusing mirror BPM',
                  #  'range': 1,
                  #  'step': 0.025,
                  #  'retries': 3,
                  #  'comment': 'monochromator crystal distance tune'},
                  {'motor': hhrm.y.name, #'motor': [hhrm.y.name, i0_y.pos.name],
                   'detector': 'I0 ion Chamber',
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'Harmonic rejection mirror tune'},
                  {'motor': hhm.pitch.name,
                   'detector': 'I0 ion Chamber',
                   'range': 0.3,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                ]

tune_elements_ext =  [{'motor': hhm.pitch.name,
                   'detector': 'Focusing mirror BPM',
                   'range': 10,
                   'step': 0.1,
                   'retries': 10,
                   'comment': 'rough monochromator pitch tune'},
                  {'motor': hhm.pitch.name,
                   'detector': 'Focusing mirror BPM',
                   'range': 1,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                  {'motor': hhm.y_precise.name,
                   'detector':'Focusing mirror BPM',
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'monochromator crystal distance tune'},
                  {'motor': hhrm.y.name, #'motor': [hhrm.y.name, i0_y.pos.name],
                   'detector': 'I0 ion Chamber',
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'Harmonic rejection mirror tune'},
                  {'motor': hhm.pitch.name,
                   'detector': 'I0 ion Chamber',
                   'range': 0.3,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                  {'motor': hhm.y_precise.name,
                   'detector':'I0 ion Chamber',
                   'range': 0.6,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'fine monochromator crystal distance tune'},
                  {'motor': hhm.pitch.name,
                   'detector': 'I0 ion Chamber',
                   'range': 0.3,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                  {'motor': hhrm.y.name, #'motor': [hhrm.y.name, i0_y.pos.name],
                   'detector': 'I0 ion Chamber',
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'Fine harmonic rejection mirror tune'},
                  {'motor': hhm.pitch.name,
                   'detector': 'I0 ion Chamber',
                   'range': 0.3,
                   'step': 0.02,
                   'retries': 3,
                   'comment': 'fine monochromator pitch tune'},
                  {'motor': hhm.y_precise.name,
                   'detector':'I0 ion Chamber',
                   'range': 0.6,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'fine monochromator crystal distance tune',
                   'fb_enable': True},
                ]

# def tune_beamline_plan(extended_tuning : bool = False, enable_fb_in_the_end : bool = True):
#
#     if extended_tuning:
#         tune_elements_list = tune_elements_ext
#     else:
#         tune_elements_list = tune_elements
#
#     stdout = sys.stdout
#     print_to_gui(f'[Beamline tuning] Starting...',stdout=stdout)
#     yield from bps.mv(hhm.fb_status, 0)
#     print('bla')
#
#     # yield from bps.mv(bpm_fm, 'insert')
#
#     for element in tune_elements_list:
#         detector = detector_dictionary[element['detector']]['device']
#
#         if 'fb_enable' in element.keys():
#             if element['fb_enable']:
#                 hhm_feedback.update_center()
#                 hhm.fb_status.put(1)
#
#
#         if detector == bpm_fm:
#             yield from bps.mv(bpm_fm, 'insert')
#         else:
#             yield from bps.mv(bpm_fm, 'retract')
#
#
#         motor = motor_dictionary[element['motor']]['object']
#         yield from tuning_scan(motor, detector,
#                               element['range'],
#                               element['step'],
#                               retries=element['retries'],
#                               stdout=stdout
#                               )
#         # turn camera into continuous mode
#         if hasattr(detector, 'image_mode'):
#             yield from bps.mv(getattr(detector, 'image_mode'), 2)
#             yield from bps.mv(getattr(detector, 'acquire'), 1)
#
#     # yield from bps.mv(bpm_fm, 'retract')
#     if enable_fb_in_the_end:
#         hhm_feedback.update_center()
#         # yield from update_hhm_fb_center(truncate_data=truncate_data)
#         hhm.fb_status.put(1)
#     print('[Beamline tuning] Beamline tuning complete')


def tune_beamline_plan_bundle(extended_tuning : bool = False, enable_fb_in_the_end : bool = True, do_liveplot=False):

    if extended_tuning:
        tune_elements_list = tune_elements_ext
    else:
        tune_elements_list = tune_elements

    plans = [{'plan_name': 'print_message_plan',
              'plan_kwargs': {'msg': 'Starting...', 'tag': 'Beamline tuning'}}]

    plans.append({'plan_name' : 'set_hhm_feedback_plan',
                   'plan_kwargs' : {'state' : 0}})

    for element in tune_elements_list:
        detector_device = detector_dictionary[element['detector']]['device']
        if detector_device == bpm_fm:
            plans.append({'plan_name': 'move_bpm_fm_plan',
                          'plan_kwargs': {'action': 'insert'}})
        else:
            if bpm_fm.inserted.get():
                plans.append({'plan_name': 'move_bpm_fm_plan',
                              'plan_kwargs': {'action': 'retract'}})

        if 'fb_enable' in element.keys():
            if element['fb_enable']:
                plans.append({'plan_name' : 'set_hhm_feedback_plan',
                              'plan_kwargs' : {'state' : 1}})
        if do_liveplot:
            channel = detector_dictionary[element['detector']]['device'].hints['fields'][0]
            liveplot_kwargs = {'channel' : channel,
                               'channel_den' : '1',
                               'result_name' : channel,
                               'curr_mot_name' : element['motor']}
        else:
            liveplot_kwargs = {}
        # plans = [{'plan_name': 'print_message_plan',
        #           'plan_kwargs': {'msg': f'Step: {element["comment"]}', 'tag': 'Beamline tuning'}}]

        plan_dict = {'plan_name' : 'tuning_scan',
                     'plan_kwargs' : {'motor' : element['motor'],
                                      'detector' : element['detector'],
                                      'scan_range' : element['range'],
                                      'scan_step' : element['step'],
                                      'n_tries' : element['retries'],
                                      'liveplot_kwargs' : liveplot_kwargs}}
        plans.append(plan_dict)

        if detector_device == bpm_fm:
            plans.append({'plan_name': 'put_bpm_fm_to_continuous_mode',
                          'plan_kwargs': {}})

    if enable_fb_in_the_end:
        plans.append({'plan_name': 'set_hhm_feedback_plan',
                      'plan_kwargs': {'state': 1}})

    plans.append({'plan_name': 'print_message_plan',
                  'plan_kwargs': {'msg': 'Beamline tuning complete', 'tag' : 'Beamline tuning'}})

    return plans


#
# def optimize_beamline_plan(energy: int = -1, extended_tuning: bool = False, force_prepare = False, enable_fb_in_the_end=True):
#     old_energy = hhm.energy.position
#     if force_prepare or ((np.abs((energy-old_energy)/old_energy)> 0.1) or (np.sign(old_energy-13000)) != (np.sign(energy-13000))):
#         yield from shutter.close_plan()
#         yield from prepare_beamline_plan(energy, move_cm_mirror = True)
#         yield from tune_beamline_plan(extended_tuning=extended_tuning, enable_fb_in_the_end=enable_fb_in_the_end)
#     else:
#         # print_to_gui(f'Beamline is already prepared for {energy} eV', stdout=stdout)
#         yield from bps.mv(hhm.energy, energy)


def optimize_beamline_plan_bundle(energy: int = -1, extended_tuning: bool = False, force_prepare = False, enable_fb_in_the_end=True, do_liveplot=False):
    old_energy = hhm.energy.position
    plans = []
    if force_prepare or ((np.abs((energy-old_energy)/old_energy)> 0.1) or (np.sign(old_energy-13000)) != (np.sign(energy-13000))):
        plans.append({'plan_name' : 'shutter_close_plan', 'plan_kwargs' : {}})
        plans.append({'plan_name' : 'prepare_beamline_plan',
                      'plan_kwargs' : {'energy': energy, 'move_cm_mirror': True}})
        tuning_plans = tune_beamline_plan_bundle(extended_tuning=extended_tuning, enable_fb_in_the_end=enable_fb_in_the_end, do_liveplot=do_liveplot)
        plans.extend(tuning_plans)

    else:
        # print_to_gui(f'Beamline is already prepared for {energy} eV', stdout=stdout)
        plans.append({'plan_name': 'move_mono_energy',
                      'plan_kwargs': {'energy': energy}})
        plans.append({'plan_name': 'print_message_plan',
                      'plan_kwargs': {'msg': 'Beamline is already prepared for {energy} eV', 'tag': 'Beamline tuning'}})
    return plans

