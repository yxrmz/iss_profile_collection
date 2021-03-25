def johann_emission_scan_plan(name, comment, energy_steps, time_steps, detectors, element='', e0=0, line=''):
    print(f'Line in plan {line}')
    fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.dat"
    fn = validate_file_exists(fn)

    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md = {'plan_args': {},
          'experiment': 'step_scan_emission',
          'name': name,
          'comment': comment,
          'interp_filename': fn,
          'element': element,
          'element_full': full_element_name,
          'line': line,
          'e0': e0,
          }
    #yield from bp.list_scan(detectors=[adaq_pb_step], motor=hhm.energy, steps=energy_grid)
    yield from bps.abs_set(apb_ave.divide, 373, wait=True)

    # for det in detectors:
    #     if det.name == 'xs':
    #         yield from bps.mv(det.total_points, len(energy_steps))

    yield from bp.list_scan( #this is the scan
        detectors,
        motor_emission, list(energy_steps),
        per_step=adaq_pb_step_per_step_factory(energy_steps, time_steps), #and this function is colled at every step
        md=md
    )