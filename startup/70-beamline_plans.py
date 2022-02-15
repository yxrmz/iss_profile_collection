


def vibration_diagnostics(time=1):
    cur_divide_value = apb_ave.divide.value
    cur_sample_len = apb_ave.sample_len.value
    cur_wf_len = apb_ave.wf_len.value

    yield from bps.abs_set(apb_ave.divide, 36, wait=True)
    yield from bps.abs_set(apb_ave.sample_len, time*1e4, wait=True)
    yield from bps.abs_set(apb_ave.wf_len, time*1e4, wait=True)

    uid = (yield from bp.count([apb_ave], int(time), md={"plan_name": "vibration_diagnostics"}))

    table = db[uid].table()

    data = np.zeros((int(time * 1e4), 9))
    # print(data.shape)
    data[:, 0] = table['apb_ave_time_wf'][1]

    for i in range(8):
        col_name = 'apb_ave_ch' + str(i + 1) + '_wf'
        data[:, i + 1] = table[col_name][1]

    yield from bps.abs_set(apb_ave.divide, cur_divide_value, wait=True)
    yield from bps.abs_set(apb_ave.sample_len, cur_sample_len, wait=True)
    yield from bps.abs_set(apb_ave.wf_len, cur_wf_len, wait=True)

    data_ft(data)


def single_bender_scan_bundle(bender_position=None, **kwargs):
    loading = bender.load_cell.get()
    name = f"Bender scan at {kwargs['element']}-{kwargs['edge']} edge - {loading} N - {bender_position} um"
    plan_kwargs = {**{'name' : name, 'comment' : 'Bender scan'}, **kwargs}
    plans = [{'plan_name' : 'fly_scan_plan',
              'plan_kwargs' : plan_kwargs}]
    return plans









from xas.energy_calibration import get_energy_offset
# from xas.image_analysis import determine_beam_position_from_fb_image

# # can be made into a bundle?
# def calibrate_mono_energy_plan(element='', edge='', dE=25, plot_func=None, error_message_func=None):
#     # # check if current trajectory is good for this calibration
#     # validate_element_edge_in_db_proc(element, edge, error_message_func=error_message_func)
#     try:
#         db_proc.validate_foil_edge(element, edge)
#     except Exception as e:
#         print_to_gui(e)
#         if error_message_func is not None:
#             error_message_func(e)
#
#     yield from set_reference_foil(element)
#     yield from bps.sleep(2)
#     foil_camera.validate_barcode(element, error_message_func=error_message_func)
#
#     trajectory_filename = scan_manager.standard_trajectory_filename(element, edge)
#
#     yield from optimize_gains_plan()
#     name = f'{element} {edge}-edge foil energy calibration'
#
#     plan = fly_scan_plan
#     plan_kwargs = {'name' : name, 'comment' : '',
#                    'trajectory_filename' : trajectory_filename,
#                    'element' : element, 'e0' : xraydb.xray_edge(element, edge).energy, 'edge' : edge}
#
#     yield from plan(**plan_kwargs)
#     energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)
#
#     print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual-energy_nominal:.2f} eV')
#     hhm.calibrate(energy_nominal, energy_actual, error_message_func=error_message_func)
#
#     yield from plan(**plan_kwargs)
#     energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)
#
#     print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual - energy_nominal:.2f} eV')
#     if np.abs(energy_actual - energy_nominal) < 0.1:
#         print_to_gui(f'{ttime.ctime()} [Energy calibration] Completed')
#     else:
#         print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy calibration error is > 0.1 eV. Check Manually.')


def foil_camera_validate_barcode_plan(element=None, error_message_func=None):
    foil_camera.validate_barcode(element, error_message_func=error_message_func)
    yield from bps.null()

def prepare_foil_scan(element, edge):
    plans = []
    plans.append({'plan_name': 'set_reference_foil', 'plan_kwargs': {'element': element}})
    plans.append({'plan_name': 'sleep', 'plan_kwargs': {'delay': 2}})
    plans.append({'plan_name': 'foil_camera_validate_barcode_plan',
                  'plan_kwargs': {'element': element},
                  'plan_gui_services': ['error_message_box']})
    trajectory_filename = scan_manager.standard_trajectory_filename(element, edge)
    plans.append({'plan_name': 'optimize_gains',
                  'plan_kwargs': {'trajectory_filename': trajectory_filename}})
    return plans, trajectory_filename


def bender_scan_plan_bundle(element, edge, error_message_func=None):
    # element, edge = foil_camera.read_current_foil_and_edge(error_message_func=error_message_func)
    # trajectory_filename = scan_manager.standard_trajectory_filename(element, edge)

    bender_current_position = bender.pos.user_readback.get()
    bender_positions = bender_current_position + np.arange(-15, 20, 5)

    plans, trajectory_filename = prepare_foil_scan(element, edge)

    for bender_position in bender_positions:
        plans.append({'plan_name' : 'move_motor_plan',
                      'plan_kwargs' : {'motor_attr' : bender.name,
                                       'based_on' : 'object_name',
                                       'position' : bender_position}})
        plans.append({'plan_name' : 'sleep',
                      'plan_kwargs': {'delay': 3}})
        plans.append({'plan_name' : 'single_bender_scan_bundle',
                      'plan_kwargs' : {'trajectory_filename' : trajectory_filename,
                                       'detectors' : [],
                                       'element' : element,
                                       'e0' : xraydb.xray_edge(element, edge).energy,
                                       'edge' : edge}})
    plans.append({'plan_name': 'move_motor_plan',
                  'plan_kwargs': {'motor_attr': bender.name,
                                  'based_on': 'object_name',
                                  'position': bender_current_position}})
    return plans


def obtain_hhm_calibration_plan(dE=25, is_final=False, plot_func=None, error_message_func=None):
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)

    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual - energy_nominal:.2f} eV')
    hhm.calibrate(energy_nominal, energy_actual, error_message_func=error_message_func)

    if is_final:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual - energy_nominal:.2f} eV')
        if np.abs(energy_actual - energy_nominal) < 0.1:
            print_to_gui(f'{ttime.ctime()} [Energy calibration] Completed')
        else:
            print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy calibration error is > 0.1 eV. Check Manually.')
    yield from bps.null()


def calibrate_mono_energy_plan_bundle(element='', edge='', dE=25, plan_gui_services=None, question_message_func=None, ):
    # # check if current trajectory is good for this calibration
    # validate_element_edge_in_db_proc(element, edge, error_message_func=error_message_func)
    run_calibration = True
    run_simple_scan = False
    try:
        db_proc.validate_foil_edge(element, edge)
    except Exception as e:
        print_to_gui(e)
        if question_message_func is not None:
            ret = question_message_func('Warning', f'{e}\n would you like to take a spectrum from this foil anyway to calibrate manually?'
                                             f'\n If the spectum is good, do not forget to add to the library!')
            run_calibration = False
            run_simple_scan = ret

    if run_calibration or run_simple_scan:
        plans, trajectory_filename = prepare_foil_scan(element, edge)


        name = f'{element} {edge}-edge foil energy calibration'
        scan_kwargs = {'name': name, 'comment': '',
                       'trajectory_filename': trajectory_filename,
                       'detectors': [],
                       'element': element, 'e0': xraydb.xray_edge(element, edge).energy, 'edge': edge}


    if run_calibration:
        plans.append({'plan_name': 'fly_scan_plan',
                      'plan_kwargs': {**scan_kwargs}})
        plans.append({'plan_name': 'obtain_hhm_calibration_plan',
                      'plan_kwargs': {'dE' : dE, 'is_final' : False},
                     'plan_gui_services': plan_gui_services})
        plans.append({'plan_name': 'fly_scan_plan',
                      'plan_kwargs': {**scan_kwargs}})
        plans.append({'plan_name': 'obtain_hhm_calibration_plan',
                      'plan_kwargs': {'dE' : dE, 'is_final' : True},
                      'plan_gui_services': plan_gui_services})
    else:
        if run_simple_scan:
            plans.append({'plan_name': 'fly_scan_plan',
                          'plan_kwargs': {**scan_kwargs}})
    return plans





















def scan_beam_position_vs_energy(camera=camera_sp2):
    camera.stats4.centroid_threshold.put(10)
    centers = []
    energies = np.linspace(6000, 14000, 11)
    for energy in energies:
        print_to_gui(f'Energy is {energy}')
        hhm.energy.move(energy)
        ttime.sleep(3)
        camera.adjust_camera_exposure_time(target_max_counts=150, atol=10)
        # adjust_camera_exposure_time(camera)
        _centers = []
        for i in range(10):
            ttime.sleep(0.05)
            center = camera.stats4.centroid.x.get()
            _centers.append(center)
        centers.append(np.mean(_centers))
        print_to_gui(f'Center is {np.mean(_centers)}')

    return energies, np.array(centers)
