

tune_elements =  [#{'motor': hhm.pitch.name,
                  # 'detector': 'Focusing mirror BPM',
                  # 'range': 10,
                  # 'step': 0.1,
                  # 'retries': 10,
                  # 'comment': 'rough monochromator pitch tune'},
                  #{'motor': hhm.pitch.name,
                  # 'detector': 'Focusing mirror BPM',
                  # 'range': 1,
                  # 'step': 0.02,
                  # 'retries': 3,
                  # 'comment': 'fine monochromator pitch tune'},
                  {'motor': hhm.y.name,
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
                  #{'motor': hhm.pitch.name,
                  # 'detector': 'I0 ion Chamber',
                  # 'range': 0.3,
                  # 'step': 0.02,
                  # 'retries': 3,
                  # 'comment': 'fine monochromator pitch tune'},
                ]

'''
tune_elements =  [{'motor': [hhrm.y.name, i0_y.pos.name],
                   'detector': 'I0 ion Chamber',
                   'range': 1,
                   'step': 0.025,
                   'retries': 3,
                   'comment': 'Harmonic rejection mirror tune'},
                ]
'''

def tune_beamline_plan(stdout=sys.stdout, enable_fb_in_the_end=True, truncate_data=True):

    print_to_gui(f'[Beamline tuning] Starting...',stdout=stdout)
    yield from bps.mv(hhm.fb_status, 0)
    print('bla')

    yield from bps.mv(bpm_fm, 'insert')



    for element in tune_elements:
        detector = detector_dictionary[element['detector']]['device']
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
    if enable_fb_in_the_end:
        yield from update_hhm_fb_center(truncate_data=truncate_data)
        yield from bps.mv(hhm.fb_status, 1)
    print('[Beamline tuning] Beamline tuning complete')