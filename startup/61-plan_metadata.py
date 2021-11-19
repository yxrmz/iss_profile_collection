
def get_md_for_scan(name, mono_scan_type, plan_name, experiment, **metadata):
    interp_fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}.raw"
    interp_fn = validate_file_exists(interp_fn)
    print(f'Storing data at {interp_fn}')
    curr_traj = getattr(hhm, 'traj{:.0f}'.format(hhm.lut_number_rbv.get()))
    try:
        full_element_name = getattr(elements, curr_traj.elem.get()).name.capitalize()
    except:
        full_element_name = curr_traj.elem.get()

    # try:
    #     nsls_ii_current = nsls_ii.beam_current.get()
    # except:
    #     nsls_ii_current = 0
    # try:
    #     nsls_ii_status = nsls_ii.return_status_string()
    # except:
    #     nsls_ii_status = 'Shutdown'
    if mono_scan_type == 'fly_scan':
        mono_direction = 'backward in energy'
    else:
        mono_direction = 'forward in energy'

    gas_n2_flow = gas_n2.flow.get()
    gas_he_flow = gas_he.flow.get()
    gas_tot_flow = gas_n2_flow + gas_he_flow
    gas_he_perc = np.round(gas_he_flow/gas_tot_flow * 100)
    gas_n2_perc = np.round(gas_n2_flow/gas_tot_flow * 100)

    i0_volt = np.round(wps1.hv302.read_pv.get())
    it_volt = np.round(wps1.hv303.read_pv.get())
    ir_volt = np.round(wps1.hv305.read_pv.get())

    md = {'plan_args': {},
          'plan_name': plan_name,
          'experiment': experiment,
          'name': name,
          'interp_filename': interp_fn,
          'angle_offset': str(hhm.angle_offset.get()),
          'trajectory_name': hhm.trajectory_name.get(),
          'element': curr_traj.elem.get(),
          'element_full': full_element_name,
          'edge': curr_traj.edge.get(),
          'e0': curr_traj.e0.get(),
          'pulses_per_degree': hhm.pulses_per_deg,
          'nslsii_current' : 0,#          'nslsii_current' : nsls_ii_current,
          'nslsii_status' : 'Shutdown', #'nslsii_status' : nsls_ii_status,
          'nslsii_energy' : nsls_ii.energy_str,
          'harmonic_rejection' : '', #hhrm.current_sripe(),
          'i0_par' : f'{i0.ic_length}cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'it_par' : f'{it.ic_length}cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'ir_par' : f'{ir.ic_length}cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'iff_par' : f'PIPS (300um Si)',
          'i0_volt' : i0_volt,
          'it_volt' : it_volt,
          'ir_volt' : ir_volt,
          'i0_gain' : i0.amp.get_gain()[0],
          'it_gain' : it.amp.get_gain()[0],
          'ir_gain' : ir.amp.get_gain()[0],
          'iff_gain' : iff.amp.get_gain()[0],
          'aux_detector' : '',
          'mono_offset' : f'{np.round(hhm.angle_offset.get()*180/np.pi, 3)} deg',
          'mono_encoder_resolution' : str(np.round(hhm.main_motor_res.get()*np.pi/180*1e9)) +' nrad',
          'mono_scan_mode' : 'pseudo-channel cut',
          'mono_scan_type' : mono_scan_type,
          'mono_direction' : mono_direction,
          'sample_stage' : 'ISS.giant_xy stage',
          'sample_x_position' : giantxy.x.user_readback.get(),
          'sample_y_position' : giantxy.y.user_readback.get(),
          'plot_hint' : '$5/$1'
          }
    for indx in range(8):
        md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
        amp = getattr(apb, f'amp_ch{indx+1}')
        if amp:
            md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
        else:
            md[f'ch{indx+1}_amp_gain']=0
    md.update(**metadata)
    return md
