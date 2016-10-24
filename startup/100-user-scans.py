import inspect

def tscan(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if (prepare_traj == True):
        prep_trajectory()
    uid, = RE(execute_trajectory(comment))
    print(uid)

    # Check if tscan was called by the GUI
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp

def tcscan_plan(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if prepare_traj:
        yield from prep_traj_plan()
    uid = (yield from execute_trajectory(comment))

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
            prep_trajectory()
        uid, = RE(execute_trajectory(comment_n))
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        interp_filename = write_html_log(uid, comment_n, absorp=absorp, caller=calframe[1][3])
        time.sleep(delay)
    print('Done!')
    return uid, interp_filename, absorp


def tscan_Rrep(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if (prepare_traj == True):
        prep_trajectory()

    uid, = RE(execute_trajectory(comment))
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    uid, interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp


def tloopscan(comment:str, prepare_traj:bool=True, absorp:bool=True):
    if (prepare_traj == True):
        prep_trajectory()
    uid, = RE(execute_loop_trajectory(comment))
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp


def tscanxia(comment:str, prepare_traj:bool=True, absorp:bool=False):
    if (prepare_traj == True):
        prep_trajectory()
    uid, = RE(execute_xia_trajectory(comment)) # CHECK FILENAME (We need to know exactly the next filename)
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    interp_filename = write_html_log(uid, comment, absorp=absorp, caller=calframe[1][3])
    print('Done!')
    return uid, interp_filename, absorp

    #on the other side, do this:
    #xas_flu.load('encoderfile', 'adc7file', 'adc6file', 'difile')
    #xas_flu.interpolate()
    #smbclient.load(filename, dest_filename)
    #smbclient.copy()
    #xia_parser.parse(other_filename, path)
    #xia_parser.export()
    #write_html_log(-1, comment, absorp=absorp)


