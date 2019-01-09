import inspect
import bluesky.plans as bp
import bluesky.plan_stubs as bps
import os, sys
from bluesky.utils import FailedStatus



def tscan(name: str, comment: str, n_cycles: int = 1, delay: float = 0, **kwargs):
    """
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans


    See Also
    --------f
    :func:`tscanxia`
    """

    # uids = []
    RE.is_aborted = False
    for indx in range(int(n_cycles)):
        if RE.is_aborted:
            return 'Aborted'
        if n_cycles == 1:
            name_n = name
        else:
            name_n = name + ' ' + str(indx + 1)
        print('Current step: {} / {}'.format(indx + 1, n_cycles))
        RE(prep_traj_plan())
        uid = RE(execute_trajectory(name_n, comment=comment))
        yield uid
        # hhm.prepare_trajectory.put('1')
        # uids.append(uid)
        time.sleep(float(delay))
    # return uids


def fly_scan(name: str, comment: str, n_cycles: int = 1, delay: float = 0, reference = True, **kwargs):
    '''
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans


    See Also
    --------
    :func:
    '''

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []

    current_element = getattr(hhm, f'traj{int(hhm.lut_number_rbv.value)}').elem.value
    try:
        yield from set_reference_foil(current_element)
    except:
        pass

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)
        print(f'Filename is {name_n}')

        yield from prep_traj_plan()
        print(f'Trajectory prepared at {print_now()}')

        uid = (yield from execute_trajectory(name_n, comment=comment))

        uids.append(uid)

        print(f'Trajectory excecuted {print_now()}')
        yield from bps.sleep(float(delay))
    return uids


def tscanxia(name: str, comment: str, n_cycles: int = 1, delay: float = 0, **kwargs):
    """
    Trajectory Scan XIA - Runs the monochromator along the trajectory that is previously loaded in the controller and get data from the XIA N times

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans


    See Also
    --------
    :func:`tscan`
    """

    # uids = []
    RE.is_aborted = False
    for i in range(int(n_cycles)):
        if RE.is_aborted:
            return 'Aborted'
        if n_cycles == 1:
            name_n = name
        else:
            name_n = name + ' ' + str(i + 1)
        print('Current step: {} / {}'.format(i + 1, n_cycles))
        RE(prep_traj_plan())
        uid, = RE(execute_xia_trajectory(name_n, comment=comment))
        yield uid
        # uids.append(uid)
        time.sleep(float(delay))
    print('Done!')
    # return uids


def fly_scan_with_sdd(name: str, comment: str, n_cycles: int = 1, delay: float = 0, **kwargs):
    """
    Trajectory Scan XIA - Runs the monochromator along the trajectory that is previously loaded in the controller and get data from the XIA N times

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans


    See Also
    --------
    :func:`tscan`
    """
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    # uids = []
    for i in range(int(n_cycles)):
        if n_cycles == 1:
            name_n = name
        else:
            name_n = name + ' ' + str(i + 1)
        print('Current step: {} / {}'.format(i + 1, n_cycles))
        # RE(prep_traj_plan())
        # uid, = RE(execute_xia_trajectory(name_n, comment=comment))
        yield from prep_traj_plan()
        # uid = (yield from execute_trajectory(name_n))
        uid = (yield from execute_xia_trajectory(name_n, comment=comment))
        yield uid
        # uids.append(uid)
        yield from bps.sleep(float(delay))
    print('Done!')
    # return uids


def tscancam(name: str, comment: str, n_cycles: int = 1, delay: float = 0, **kwargs):
    """
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans


    See Also
    --------
    :func:`tscanxia`
    """

    # uids = []
    RE.is_aborted = False
    for indx in range(int(n_cycles)):
        if RE.is_aborted:
            return 'Aborted'
        if n_cycles == 1:
            name_n = name
        else:
            name_n = name + ' ' + str(indx + 1)
        print('Current step: {} / {}'.format(indx + 1, n_cycles))
        RE(prep_traj_plan())
        uid, = RE(execute_camera_trajectory(name_n, comment=comment))
        yield uid
        # uids.append(uid)
        time.sleep(float(delay))
    print('Done!')
    # return uids


def fly_scan_with_camera(name: str, comment: str, n_cycles: int = 1, delay: float = 0, **kwargs):
    """
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans


    See Also
    --------
    :func:`tscanxia`
    """

    # uids = []
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    for indx in range(int(n_cycles)):
        if n_cycles == 1:
            name_n = name
        else:
            name_n = name + ' ' + str(indx + 1)
        print('Current step: {} / {}'.format(indx + 1, n_cycles))
        yield from prep_traj_plan()
        uid = (yield from execute_camera_trajectory(name_n, comment=comment))
        yield uid
        # uids.append(uid)
        yield from bps.sleep(float(delay))
    print('Done!')
    # return uids



def general_scan(detectors, num_name, den_name, result_name, motor, rel_start, rel_stop, num, find_min_max, retries, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    for index, detector in enumerate(detectors):
        if type(detector) == str:
            detectors[index] = eval(detector)

    if type(motor) == str:
        motor = eval(motor)

    print('[General Scan] Starting scan...')
    ax = kwargs.get('ax')

    if find_min_max:
        over = False
        while(not over):
            uid = RE(general_scan_plan(detectors, motor, rel_start, rel_stop, int(num)), NormPlot(num_name, den_name, result_name, result_name, motor.name, ax=ax))
            yield uid
            last_table = db.get_table(db[-1])
            if detectors[0].polarity == 'pos':
                index = np.argmax(last_table[num_name])
            else:
                index = np.argmin(last_table[num_name])
            motor.move(last_table[motor.name][index])
            print('[General Scan] New {} position: {}'.format(motor.name, motor.position))
            if (num >= 10):
                if (((index > 0.2 * num) and (index < 0.8 * num)) or retries == 1):
                    over = True
                if retries > 1:
                    retries -= 1
            else:
                over = True
        print('[General Scan] {} tuning complete!'.format(motor.name))
    else:
        uid, = RE(general_scan_plan(detectors, motor, rel_start, rel_stop, int(num)), NormPlot(num_name, den_name, result_name, result_name, motor.name, ax=ax))
        yield uid
        print('[General Scan] Done!')






def xia_step_scan(name:str, comment:str, e0:int=8333, preedge_start:int=-200, xanes_start:int=-50, xanes_end:int=30, exafs_end:int=16, preedge_spacing:float=10, xanes_spacing:float=0.2, exafs_spacing:float=0.04, **kwargs):
    '''
    xia_step_scan - Runs the monochromator along the trajectory defined in the parameters. Gets data from the XIA and the ion chambers after each step. 

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
        Other parameters: TODO


    Returns
    -------
    uid : str
        Unique id of the scan

    interp_filename : str
    Filename where the interpolated data was stored


    See Also
    --------
    :func:`tscan`

    '''
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    energy_grid, time_grid = get_xia_energy_grid(e0, preedge_start, xanes_start, xanes_end, exafs_end, preedge_spacing, xanes_spacing, exafs_spacing)
    positions_grid = xray.energy2encoder(energy_grid) / 360000

    ax = kwargs.get('ax')
    if ax is not None:
        uid, = RE(step_list_plan([xia1, i0, it, iff, ir], hhm.theta, positions_grid, name), LivePlot(xia1.mca1.roi0.sum.name, hhm.theta.name, ax=ax))
    else:
        uid, = RE(step_list_plan([xia1, i0, it, iff, ir], hhm.theta, positions_grid, name))

    path = '/GPFS/xf08id/User Data/{}.{}.{}/'.format(db[uid]['start']['year'], db[uid]['start']['cycle'], db[uid]['start']['PROPOSAL'])
    filename = parse_xia_step_scan(uid, name, path)

    ax.cla()
    plot_xia_step_scan(uid, ax=ax) 

    print('Done!')
    return uid



def sleep(delay:float=1, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    yield from (sleep_plan(delay))
    yield None


def set_gains_and_offsets(i0_gain:int=5, it_gain:int=5, iff_gain:int=6,
                          ir_gain:int=5, hs:bool=False):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    RE(set_gains_and_offsets_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs))

def set_gains(i0_gain:int=5, it_gain:int=5, iff_gain:int=5,
                          ir_gain:int=5, hs:bool=False, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    yield from set_gains_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs)




