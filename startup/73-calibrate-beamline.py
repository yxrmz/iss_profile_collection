from xas.energy_calibration import get_foil_spectrum




def validate_element_edge_in_db_proc(element, edge, error_message_func=None):
    try:
        get_foil_spectrum(element, edge, db_proc)
        return True
    except: # Denis, Oct 28, 2021: GUI breaks when error_message_func (the one opening the message box) is ran from exception, but this strange architecture works
        pass
    msg = f'Error: {element} {edge}-edge spectrum has not been added to the database yet'
    if error_message_func is not None:
        error_message_func(msg)
    print_to_gui(msg)
    return False


def calibrate_energy_plan(element, edge, dE=25, plot_func=None, error_message_func=None):
    # # check if current trajectory is good for this calibration
    success = validate_element_edge_in_db_proc(element, edge, error_message_func=error_message_func)
    if not success: return
    success = trajectory_manager.validate_element(element, edge, error_message_func=error_message_func)
    if not success: return
    yield from set_reference_foil(element)
    yield from bps.sleep(1)
    success = foil_camera.validate_barcode(element, error_message_func=error_message_func)
    if not success: return
    yield from adjust_ic_gains()
    name = f'{element} {edge} foil energy calibration'
    yield from fly_scan_with_apb(name, '')
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)
    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual-energy_nominal:.2f} eV')
    success = hhm.calibrate(energy_nominal, energy_actual, error_message_func=error_message_func)
    if not success: return
    trajectory_manager.reinit()
    yield from fly_scan_with_apb(name, '')
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)
    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual - energy_nominal:.2f} eV')
    if np.abs(energy_actual - energy_nominal) < 0.1:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Completed')
    else:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy calibration error is > 0.1 eV. Check Manually.')
