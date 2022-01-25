from xas.energy_calibration import get_foil_spectrum




def validate_element_edge_in_db_proc(element, edge, error_message_func=None):
    try:
        get_foil_spectrum(element, edge, db_proc)
        return
    except: # Denis, Oct 28, 2021: GUI breaks when error_message_func (the one opening the message box) is ran from exception, but this strange architecture works
        pass
    msg = f'Error: {element} {edge}-edge spectrum has not been added to the database yet'
    if error_message_func is not None:
        error_message_func(msg)
    print_to_gui(msg)
    raise Exception(msg)
    # return False

def standard_trajectory_filename_for_element_edge(element, edge, init_traj=True):
    return ''



def calibrate_mono_energy_plan(element, edge, dE=25, plot_func=None, error_message_func=None):
    # # check if current trajectory is good for this calibration
    validate_element_edge_in_db_proc(element, edge, error_message_func=error_message_func)

    # success = trajectory_manager.validate_element(element, edge, error_message_func=error_message_func)

    yield from set_reference_foil(element)
    yield from bps.sleep(1)
    foil_camera.validate_barcode(element, error_message_func=error_message_func)

    trajectory_filename = standard_trajectory_filename_for_element_edge(element, edge, init_traj=True)

    yield from adjust_ic_gains()
    name = f'{element} {edge} foil energy calibration'

    plan = fly_scan_plan
    plan_kwargs = {'name' : name, 'comment' : '',
                   'trajectory_filename' : trajectory_filename,
                   'element' : element, 'e0' : 0, 'edge' : edge}

    yield from plan(**plan_kwargs)
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)

    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual-energy_nominal:.2f} eV')
    hhm.calibrate(energy_nominal, energy_actual, error_message_func=error_message_func)

    yield from plan(**plan_kwargs)
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)

    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual - energy_nominal:.2f} eV')
    if np.abs(energy_actual - energy_nominal) < 0.1:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Completed')
    else:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy calibration error is > 0.1 eV. Check Manually.')
