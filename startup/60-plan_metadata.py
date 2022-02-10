from xas.file_io import validate_file_exists


def get_general_md():
    gas_n2_flow = gas_n2.flow.get()
    gas_he_flow = gas_he.flow.get()
    gas_tot_flow = gas_n2_flow + gas_he_flow
    gas_he_perc = np.round(gas_he_flow / gas_tot_flow * 100)
    gas_n2_perc = np.round(gas_n2_flow / gas_tot_flow * 100)

    i0_volt = np.round(wps1.hv302.read_pv.get())
    it_volt = np.round(wps1.hv303.read_pv.get())
    ir_volt = np.round(wps1.hv305.read_pv.get())
    # print_to_gui('WARNING VOLTAGES ARE NOT BEING READ FOR METADATA')
    # i0_volt = 0
    # it_volt = 0
    # ir_volt = 0

    md = {'nslsii_current' : nsls_ii.beam_current.get(),
          'nslsii_status' : nsls_ii.return_status_string(),
          'nslsii_energy' : nsls_ii.energy_str,
          'pulses_per_degree': hhm.pulses_per_deg,
          'angle_offset': str(hhm.angle_offset.get()),
          'angle_offset_deg': f'{np.round(hhm.angle_offset.get() * 180 / np.pi, 3)} deg',
          'mono_encoder_resolution': str(np.round(hhm.main_motor_res.get() * np.pi / 180 * 1e9)) + ' nrad',
          'mono_scan_mode': 'pseudo-channel cut',
          'harmonic_rejection' : hhrm.current_stripe,
          'sample_stage': 'ISS.giant_xy stage',
          'sample_x_position': giantxy.x.user_readback.get(),
          'sample_y_position': giantxy.y.user_readback.get(),
          'i0_par' : f'17 cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'it_par' : f'30 cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'ir_par' : f'17 cm, He: {gas_he_perc}%, N2: {gas_n2_perc}%',
          'iff_par' : f'PIPS',
          'i0_volt' : i0_volt,
          'it_volt' : it_volt,
          'ir_volt' : ir_volt,
          'i0_gain' : i0_amp.get_gain()[0],
          'it_gain' : it_amp.get_gain()[0],
          'ir_gain' : ir_amp.get_gain()[0],
          'iff_gain' : iff_amp.get_gain()[0],
          }

    for indx in range(8):
        md[f'ch{indx+1}_offset'] = getattr(apb, f'ch{indx+1}_offset').get()
        amp = getattr(apb, f'amp_ch{indx+1}')
        if amp:
            md[f'ch{indx+1}_amp_gain']= amp.get_gain()[0]
        else:
            md[f'ch{indx+1}_amp_gain'] = 0
    return md



def create_interp_file_name(name, fn_ext):
    fn = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/{name}{fn_ext}"
    fn = validate_file_exists(fn)
    return fn

def get_scan_md(name, comment, detectors, fn_ext):
    fn = create_interp_file_name(name, fn_ext)
    md_general = get_general_md()
    md_scan = {'interp_filename': fn,
               'name': name,
               'comment': comment,
               'detectors': detectors,
               'plot_hint': '$5/$1'}
    return {**md_general, **md_scan}

def get_hhm_scan_md(name, comment, trajectory_filename, detectors, element, e0, edge, metadata, fn_ext='.raw'):
    try:
        full_element_name = getattr(elements, element).name.capitalize()
    except:
        full_element_name = element

    md_scan = get_scan_md(name, comment, detectors, fn_ext)

    md_hhm_scan = {'trajectory_filename': trajectory_filename,
               'element': element,
               'element_full': full_element_name,
               'edge': edge,
               'e0': e0}
    return {**md_hhm_scan, **md_scan, **metadata}


