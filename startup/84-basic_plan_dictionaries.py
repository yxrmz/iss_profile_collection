

basic_plan_dict = {'step_scan_plan': step_scan_plan,
                   'sleep' : bps.sleep}

# plan_funcs = {
#
#     'Fly scan': fly_scan_with_apb,
#     'Fly scan w/SDD': fly_scan_with_xs3,
#     'Fly scan w/Pilatus100k': fly_scan_with_pil100k,
#     'fly scan Johann RIXS w/Pilatus': fly_scan_rixs_w_pilatus,
#     'Step scan': step_scan_plan,
#     'Step scan w/Pilatus': step_scan_w_pilatus,
#     'Step scan w/Xspress 3': step_scan_w_xs,
#     # 'Constant energy': constant_energy,
#     # 'Spiral fly scan': fly_scan_over_spiral,
#     'Step scan Johann Emission w/Pilatus': step_scan_emission_w_pilatus,
#     'Step scan Johann RIXS w/Pilatus': step_scan_rixs_w_pilatus,
#     'Calibration scan w PIL' : calibration_scan_w_pilatus,
#     'Point scan w PIL' : point_scan_w_pilatus,
#     'Von Hamos Calibration w/ Pilatus' : vonhamos_calibration_scan_plan}
#
# service_plan_funcs = {
#     'get_offsets': get_offsets,
#     'sleep': sleep,
#     'random_step': random_step,
#     'set_gains': set_gains,
#     'adjust_ic_gains': adjust_ic_gains,
#     'prepare_beamline_plan': prepare_beamline_plan,
#     'tune_beamline_plan': tune_beamline_plan,
#     'optimize_beamline_plan': optimize_beamline_plan,
#     'optimize_sample_plan': optimize_sample_plan,
#     'calibrate_energy_plan': calibrate_energy_plan,
#     'xs_count': xs_count,
#     'pil_count': pil_count,
#     'johann_calibration_scan_plan' : johann_calibration_scan_plan,
#     'n_pil100k_exposures_plan' : n_pil100k_exposures_plan,
#     'set_reference_foil': set_reference_foil,
#     'set_attenuator': set_attenuator
# }
#
#
# aux_plan_funcs = {
#     'get_adc_readouts': get_adc_readouts,
#     'prepare_traj_plan': prep_traj_plan,
#     'general_scan': general_scan,
#     'general_spiral_scan': general_spiral_scan,
#     'set_reference_foil': set_reference_foil,
#     'tuning_scan': tuning_scan,
#     'bender_scan': bender_scan,
#     'set_attenuator': set_attenuator,
#     'n_pil100k_exposures_plan': n_pil100k_exposures_plan,
# }