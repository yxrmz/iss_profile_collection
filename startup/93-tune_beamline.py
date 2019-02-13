


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