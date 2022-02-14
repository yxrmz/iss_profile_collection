

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
        'fly_scan_johann_herfd_plan' : fly_scan_johann_herfd_plan,
        'fly_scan_johann_rixs_plan_bundle' : {'kind' : 'bundle', 'func' : fly_scan_johann_rixs_plan_bundle},
        'step_scan_johann_rixs_plan_bundle' : {'kind' : 'bundle', 'func' : step_scan_johann_rixs_plan_bundle},
    }

service_plan_funcs = {
        'sleep': sleep_plan,
        'get_offsets': get_offsets_plan,
        'set_gains': set_gains_plan,
        'optimize_gains': optimize_gains_plan,
        'set_reference_foil': set_reference_foil,
        'set_attenuator': set_attenuator,
        'prepare_beamline_plan': prepare_beamline_plan,
        'tune_beamline_plan_bundle': {'kind' : 'bundle', 'func' : tune_beamline_plan_bundle},
        'optimize_beamline_plan_bundle': {'kind' : 'bundle', 'func' : optimize_beamline_plan_bundle},
        'calibrate_mono_energy_plan': calibrate_mono_energy_plan,
        'johann_calibration_scan_plan' : johann_calibration_scan_plan,
        'random_xy_step' : move_sample_by_random_xy_step,
        'move_motor_plan' : move_motor_plan,
        'calibrate_mono_energy_plan_bundle' : {'kind' : 'bundle', 'func' : calibrate_mono_energy_plan_bundle}
        }


aux_plan_funcs = {
        'general_scan': general_scan,
        'tuning_scan': tuning_scan,
        'bender_scan_plan_bundle' : {'kind' : 'bundle', 'func' : bender_scan_plan_bundle},
        'single_bender_scan_bundle' : {'kind' : 'bundle', 'func' : single_bender_scan_bundle},
        'print_message_plan' : print_message_plan,
        'move_bpm_fm_plan' : move_bpm_fm_plan,
        'put_bpm_fm_to_continuous_mode' : put_bpm_fm_to_continuous_mode,
        'set_hhm_feedback_plan' : set_hhm_feedback_plan,
        'move_mono_energy' : move_mono_energy,
        'shutter_close_plan' : shutter.close_plan,
        'foil_camera_validate_barcode_plan' : foil_camera_validate_barcode_plan,
        'obtain_hhm_calibration_plan' : obtain_hhm_calibration_plan,
        'move_sample_stage_plan' : move_sample_stage_plan
    }

all_plan_funcs = {**data_collection_plan_funcs, **service_plan_funcs, **aux_plan_funcs}


def generate_plan_description(plan_name, plan_kwargs):
        output = plan_name  # + ': '

        # for key, value in plan_kwargs.items():
        #     output += f'{key} = {str(value)}, '
        return output

