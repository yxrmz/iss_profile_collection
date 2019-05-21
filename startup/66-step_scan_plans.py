def step_scan_plan(name, energy_grid, **metadata):
    pass
    '''
    flyers = [pba2.adc7, pba1.adc6, pba1.adc1, pba2.adc6, pba1.adc7, pb9.enc1]


    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Filepath  {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.value))
    try:
        full_element_name = getattr(elements, curr_traj.elem.value).name.capitalize()
    except:
        full_element_name = curr_traj.elem.value
    md = {'plan_args': {},
          'plan_name': 'execute_trajectory',
          'experiment': 'fly_energy_scan',
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.value),
          'trajectory_name': hhm.trajectory_name.value,
          'element': curr_traj.elem.value,
          'element_full': full_element_name,
          'edge': curr_traj.edge.value,
          'e0': curr_traj.e0.value,
          'pulses_per_degree': hhm.pulses_per_deg,
          }
    for flyer in flyers:
        # print(f'Flyer is {flyer}')
        if hasattr(flyer, 'offset'):
            md['{} offset'.format(flyer.name)] = flyer.offset.value
        if hasattr(flyer, 'amp'):
            md['{} gain'.format(flyer.name)] = flyer.amp.get_gain()[0]
    md.update(**metadata))
    '''

