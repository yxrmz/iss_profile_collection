import inspect
import bluesky.plans as bp
import bluesky.plan_stubs as bps
from bluesky.plan_patterns import spiral_square_pattern
import os, sys
from bluesky.utils import FailedStatus






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

    '''

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []

    # current_element = getattr(hhm, f'traj{int(hhm.lut_number_rbv.value)}').elem.value
    # try:
    #     yield from set_reference_foil(current_element)
    # except:
    #     pass

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)
        yield from prep_traj_plan()
        print(f'Trajectory prepared at {print_now()}')
        uid = (yield from execute_trajectory(name_n, comment=comment))
        uids.append(uid)

        print(f'Trajectory excecuted {print_now()}')
        yield from bps.sleep(float(delay))
    #yield from prep_traj_plan()
    # yield from pre_stage_the_mono()
    return uids


def fly_scan_with_em(name: str, comment: str, n_cycles: int = 1, delay: float = 0, reference = True, **kwargs):
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

    '''

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    uids = []

    # current_element = getattr(hhm, f'traj{int(hhm.lut_number_rbv.value)}').elem.value
    # try:
    #     yield from set_reference_foil(current_element)
    # except:
    #     pass

    for indx in range(int(n_cycles)):
        name_n = '{} {:04d}'.format(name, indx + 1)
        yield from prep_traj_plan()
        print(f'Trajectory prepared at {print_now()}')
        uid = (yield from execute_trajectory_em(name_n, comment=comment))
        uids.append(uid)
        print(f'Trajectory excecuted {print_now()}')
        yield from bps.sleep(float(delay))
    return uids






def fly_scan_over_spiral(name: str, comment: str, n_cycles: int = 1, delay: float = 0, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    motor_x = motor_dictionary['giantxy_x']['object']
    motor_y = motor_dictionary['giantxy_y']['object']

    x_center = motor_x.read()[motor_x.name]['value']
    y_center = motor_y.read()[motor_y.name]['value']

    cycler = spiral_square_pattern(motor_x, motor_y, x_center, y_center, 10, 10, 11, 11) #10*2+1, 10*2+1)

    pos_cache={motor_x:x_center, motor_y: y_center}

    for i in range(n_cycles):
        name_n = '{} {:04d}'.format(name, i+1)
        position = list(cycler)[i]
        yield from bps.move_per_step(position, pos_cache)
        yield from fly_scan(name=name_n, comment=comment, n_cycles = 1, delay = delay, **kwargs)

    yield from bps.mv(motor_x,x_center,motor_y,y_center)





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

    uids = []
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
        print(f'uid: {uid}')

        uids.append(uid)
        yield from bps.sleep(float(delay))
    print('Done!')
    return uids





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












