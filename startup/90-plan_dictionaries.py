

data_collection_plan_funcs = {
        'step_scan_plan' : step_scan_plan,
        'fly_scan_plan' : fly_scan_plan,
        'collect_n_exposures_plan' : collect_n_exposures_plan,
        'collect_von_hamos_xes_plan' : collect_von_hamos_xes_plan,
        'step_scan_von_hamos_plan' : step_scan_von_hamos_plan,
        'fly_scan_von_hamos_plan' : fly_scan_von_hamos_plan,
        'collect_n_exposures_johann_plan' : collect_n_exposures_johann_plan,
        'step_scan_johann_xes_plan' : step_scan_johann_xes_plan,
        'step_scan_johann_herfd_plan' : step_scan_johann_herfd_plan,
        'fly_scan_johann_herfd_plan' : fly_scan_johann_herfd_plan
    }

service_plan_funcs = {
        'sleep': sleep_plan,
        'get_offsets': get_offsets_plan,
        'set_gains': set_gains_plan,
        'optimize_gains': optimize_gains_plan,
        'set_reference_foil': set_reference_foil,
        'set_attenuator': set_attenuator,
        'prepare_beamline_plan': prepare_beamline_plan,
        'tune_beamline_plan': tune_beamline_plan,
        'optimize_beamline_plan': optimize_beamline_plan,
        'calibrate_mono_energy_plan': calibrate_mono_energy_plan,
        'johann_calibration_scan_plan' : johann_calibration_scan_plan,
        'random_xy_step': move_sample_by_random_xy_step,
    }


aux_plan_funcs = {
        'general_scan': general_scan,
        'tuning_scan': tuning_scan,
        'bender_scan': bender_scan_plan,
    }

all_plan_funcs = {**data_collection_plan_funcs, **service_plan_funcs, **aux_plan_funcs}


