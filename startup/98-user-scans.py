import inspect
import bluesky.plans as bp
import os

def tscan(comment:str, prepare_traj:bool=True, absorp:bool=True):
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
    aver1=pba2.adc7.averaging_points.get()
    aver2=pba2.adc6.averaging_points.get()
    aver3=pba1.adc1.averaging_points.get()
    pba2.adc7.averaging_points.put(15)
    pba2.adc6.averaging_points.put(15)
    pba1.adc1.averaging_points.put(15)
    
    uid, = RE(get_offsets_plan([pba1.adc1, pba2.adc6, pba2.adc7], num = num))
    pba2.adc7.offset.put(np.mean(db.get_table(db[-1])['pba2_adc7_volt']))
    pba2.adc6.offset.put(np.mean(db.get_table(db[-1])['pba2_adc6_volt']))
    pba1.adc1.offset.put(np.mean(db.get_table(db[-1])['pba1_adc1_volt']))

    pba2.adc7.averaging_points.put(aver1)
    pba2.adc6.averaging_points.put(aver2)
    pba1.adc1.averaging_points.put(aver3)
    
    os.remove(db[uid]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
    os.remove(db[uid]['descriptors'][1]['data_keys']['pba2_adc6']['filename'])
    os.remove(db[uid]['descriptors'][2]['data_keys']['pba1_adc1']['filename'])

    print(uid)
    print('Done!')
    return uid, '', ''
