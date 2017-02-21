import inspect
import bluesky.plans as bp
import os

def tscan(comment:str, prepare_traj:bool=True, absorp:bool=True):
    """
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller

    Parameters
    ----------
    comment : str
        Name of the scan - it will be stored in the metadata

    prepare_traj : bool (default = True)
        Boolean to tell the function to automatically run the routine "prepare trajectory" - the trajectory needs to be 'prepared' in the controller before every scan

    absorp : bool (default = True)
        Telling the function how to parse the data - TODO: remake this parameter


    Returns
    -------
    uid : str
        Unique id of the scan

    interp_filename : str
        Filename where the interpolated data was stored

    absorp : bool
        Just returning the parameter absorp that was passed to the scan


    See Also
    --------
    :func:`tscan_N`
    """

    if (prepare_traj == True):
        RE(prep_traj_plan())
    uid, = RE(execute_trajectory(comment))
    print(uid)

    # Check if tscan was called by the GUI
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp

def tscan_plan(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if prepare_traj:
        yield from prep_traj_plan()
    #uid = (yield from execute_trajectory(comment))
    yield from execute_trajectory(comment)
    uid = db[-1]['start']['uid']

    # Check if tscan was called by the GUI
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp
    

def tscan_N(comment:str, prepare_traj:bool=True, absorp:bool=True, n_cycles:int=1, delay:float=0):
    """
    Trajectory Scan N - Runs the monochromator along the trajectory that is previously loaded in the controller N times

    Parameters
    ----------
    comment : str
        Name of the scan - it will be stored in the metadata

    prepare_traj : bool (default = True)
        Boolean to tell the function to automatically run the routine "prepare trajectory" - the trajectory needs to be 'prepared' in the controller before every scan

    absorp : bool (default = True)
        Telling the function how to parse the data - TODO: remake this parameter

    n_cycles : int (default = 1)
        Number of times to run the scan automatically

    delay : float (default = 0)
        Delay in seconds between scans


    Returns
    -------
    uid : str
        Unique id of the scan

    interp_filename : str
        Filename where the interpolated data was stored

    absorp : bool
        Just returning the parameter absorp that was passed to the scan


    See Also
    --------
    :func:`tscan`
    """

    for indx in range(0, n_cycles): 
        comment_n = comment + ' ' + str(indx + 1)
        print(comment_n) 
        if (prepare_traj == True):
            RE(prep_traj_plan())
        uid, = RE(execute_trajectory(comment_n))
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        interp_filename = write_html_log(uid, comment_n, absorp=absorp, caller=calframe[1][3])
        time.sleep(delay)
    print('Done!')
    return uid, interp_filename, absorp
    

def tscan_N_plan(comment:str, prepare_traj:bool=True, absorp:bool=True, n_cycles:int=1, delay:float=0):
    for indx in range(0, n_cycles): 
        comment_n = comment + ' ' + str(indx + 1)
        print(comment_n) 
        if prepare_traj:
            yield from prep_traj_plan()
        #uid = (yield from execute_trajectory(comment_n))
        yield from execute_trajectory(comment_n)
        uid = db[-1]['start']['uid']
			
        # Check if tscan was called by the GUI
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        interp_filename = write_html_log(uid, comment_n, absorp=absorp, caller=calframe[1][3])
        yield from bp.sleep(delay)
    print('Done!')
    return uid, interp_filename, absorp


def tscan_Rrep(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if (prepare_traj == True):
        RE(prep_traj_plan())

    uid, = RE(execute_trajectory(comment))
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    uid, interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp


def tloopscan(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if (prepare_traj == True):
        RE(prep_traj_plan())
    uid, = RE(execute_loop_trajectory(comment))
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp


def tscanxia(comment:str, prepare_traj:bool=True, absorp:bool=False):
    """
    Trajectory Scan Xia - Runs the monochromator along the trajectory that is previously loaded in the controller and get data from the XIA

    Parameters
    ----------
    comment : str
        Name of the scan - it will be stored in the metadata

    prepare_traj : bool (default = True)
        Boolean to tell the function to automatically run the routine "prepare trajectory" - the trajectory needs to be 'prepared' in the controller before every scan

    absorp : bool (default = False)
        Telling the function how to parse the data - TODO: remake this parameter


    Returns
    -------
    uid : str
        Unique id of the scan

    interp_filename : str
        Filename where the interpolated data was stored

    absorp : bool
        Just returning the parameter absorp that was passed to the scan


    See Also
    --------
    :func:`tscan`
    """

    if (prepare_traj == True):
        RE(prep_traj_plan())
    uid, = RE(execute_xia_trajectory(comment)) # CHECK FILENAME (We need to know exactly the next filename)
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp


def tscanxia_plan(comment:str, prepare_traj:bool=True, absorp:bool=False):
    if prepare_traj:
        yield from prep_traj_plan()
    #uid = (yield from execute_xia_trajectory(comment))
    yield from execute_xia_trajectory(comment)
    uid = db[-1]['start']['uid']
	
	# Check if tscan was called by the GUI
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp


def get_offsets(num:int = 10):
    """
    Get Ion Chambers Offsets - Gets the offsets from the ion chambers and automatically subtracts from the acquired data in the next scans

    Parameters
    ----------
    num : int
        Number of points to acquire and average for each ion chamber


    Returns
    -------
    uid : str
        Unique id of the scan


    See Also
    --------
    :func:`tscan`
    """

    aver1=pba1.adc7.averaging_points.get()
    aver2=pba2.adc6.averaging_points.get()
    aver3=pba1.adc1.averaging_points.get()
    aver4=pba1.adc6.averaging_points.get()
    pba1.adc7.averaging_points.put(15)
    pba2.adc6.averaging_points.put(15)
    pba1.adc1.averaging_points.put(15)
    pba1.adc6.averaging_points.put(15)
    
    uid, = RE(get_offsets_plan([pba1.adc6, pba1.adc1, pba2.adc6, pba1.adc7], num = num))
    i0_array = db.get_table(db[-1])['pba1_adc7_volt']
    it_array = db.get_table(db[-1])['pba1_adc1_volt']
    ir_array = db.get_table(db[-1])['pba2_adc6_volt']
    iff_array = db.get_table(db[-1])['pba1_adc6_volt']
    i0_off = np.mean(i0_array[1:num])
    it_off = np.mean(it_array[1:num])
    ir_off = np.mean(ir_array[1:num])
    iff_off = np.mean(iff_array[1:num])
    pba1.adc7.offset.put(i0_off)
    pba1.adc1.offset.put(it_off)
    pba2.adc6.offset.put(ir_off)
    pba1.adc6.offset.put(iff_off)

    print('{}\nMean (i0) = {}'.format(i0_array, i0_off))
    print('{}\nMean (it) = {}'.format(it_array, it_off))
    print('{}\nMean (ir) = {}'.format(ir_array, ir_off))
    print('{}\nMean (ir) = {}'.format(iff_array, iff_off))

    pba1.adc7.averaging_points.put(aver1)
    pba2.adc6.averaging_points.put(aver2)
    pba1.adc1.averaging_points.put(aver3)
    pba1.adc6.averaging_points.put(aver4)
    
    os.remove(db[uid]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
    os.remove(db[uid]['descriptors'][1]['data_keys']['pba2_adc6']['filename'])
    os.remove(db[uid]['descriptors'][2]['data_keys']['pba1_adc1']['filename'])
    os.remove(db[uid]['descriptors'][3]['data_keys']['pba1_adc6']['filename'])

    print(uid)
    print('Done!')
    return uid, '', ''
