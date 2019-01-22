import matplotlib.pyplot as plt
from datetime import datetime
from subprocess import call
import time
from scipy.optimize import curve_fit
from bluesky.plan_stubs import mv, mvr
import bluesky.preprocessors as bpp
from random import random
from xas.trajectory import trajectory_manager


def remove_pb_files(uid):
    run = db[uid]
    for i in run['descriptors']:
        if i['name'] != 'primary':
            os.remove(i['data_keys'][i['name']]['filename'])


def write_html_log(uuid, figure, log_path='/GPFS/xf08id/User Data/'):
    # Get needed data from db
    uuid = db[uuid]['start']['uid']

    if 'name' in db[uuid]['start']:
        scan_name = db[uuid]['start']['name']
    else:
        scan_name = 'General Scan'

    year = db[uuid]['start']['year']
    cycle = db[uuid]['start']['cycle']
    proposal = db[uuid]['start']['PROPOSAL']

    # Create dirs if they are not there
    if log_path[-1] != '/':
        log_path += '/'
    log_path = '{}{}.{}.{}/'.format(log_path, year, cycle, proposal)
    if(not os.path.exists(log_path)):
        os.makedirs(log_path)
        call(['setfacl', '-m', 'g:iss-staff:rwx', log_path])
        call(['chmod', '770', log_path])

    log_path = log_path + 'log/'
    if(not os.path.exists(log_path)):
        os.makedirs(log_path)
        call(['setfacl', '-m', 'g:iss-staff:rwx', log_path])
        call(['chmod', '770', log_path])

    snapshots_path = log_path + 'snapshots/'
    if(not os.path.exists(snapshots_path)):
        os.makedirs(snapshots_path)
        call(['setfacl', '-m', 'g:iss-staff:rwx', snapshots_path])
        call(['chmod', '770', snapshots_path])

    file_path = 'snapshots/{}.png'.format(scan_name)
    fn = log_path + file_path
    repeat = 1
    while(os.path.isfile(fn)):
        repeat += 1
        file_path = 'snapshots/{}-{}.png'.format(scan_name, repeat)
        fn = log_path + file_path

    # Save figure
    figure.savefig(fn)
    call(['setfacl', '-m', 'g:iss-staff:rw', fn])
    call(['chmod', '660', fn])

    # Create or update the html file
    relative_path = './' + file_path
    
    comment = ''
    if 'comment' in db[uuid]['start']:
        comment = db[uuid]['start']['comment']
    comment = '<p><b> Comment: </b> {} </p>'.format(comment)
    start_timestamp = db[uuid]['start']['time']
    stop_timestamp = db[uuid]['stop']['time']
    time_stamp_start='<p><b> Scan start: </b> {} </p>\n'.format(datetime.fromtimestamp(start_timestamp).strftime('%m/%d/%Y    %H:%M:%S'))
    time_stamp='<p><b> Scan complete: </b> {} </p>\n'.format(datetime.fromtimestamp(stop_timestamp).strftime('%m/%d/%Y    %H:%M:%S'))
    time_total='<p><b> Total time: </b> {} </p>\n'.format(datetime.fromtimestamp(stop_timestamp - start_timestamp).strftime('%M:%S'))
    uuid_html='<p><b> Scan ID: </b> {} </p>\n'.format(uuid)

    filenames = {}
    for i in db[uuid]['descriptors']:
        if i['name'] in i['data_keys']:
            if 'filename' in i['data_keys'][i['name']]:
                name = i['name']
                if 'devname' in i['data_keys'][i['name']]:
                    name = i['data_keys'][i['name']]['devname']
                filenames[name] = i['data_keys'][i['name']]['filename']
    
    fn_html = '<p><b> Files: </b></p>\n<ul>\n'
    for key in filenames.keys():
        fn_html += '  <li><b>{}:</b> {}</ln>\n'.format(key, filenames[key])
    fn_html += '</ul>\n'
    
    image = '<img src="{}" alt="{}" height="447" width="610">\n'.format(fn, scan_name)

    if(not os.path.isfile(log_path + 'log.html')):
        create_file = open(log_path + 'log.html', "w")
        create_file.write('<html> <body>\n</body> </html>')
        create_file.close()
        call(['setfacl', '-m', 'g:iss-staff:rw', log_path + 'log.html'])
        call(['chmod', '660', log_path + 'log.html'])

    text_file = open(log_path + 'log.html', "r")
    lines = text_file.readlines()
    text_file.close()

    text_file = open(log_path + 'log.html', "w")

    for indx,line in enumerate(lines):
        if indx is 1:
            text_file.write('<header><h2> {} </h2></header>\n'.format(scan_name))
            text_file.write(comment)
            text_file.write(uuid_html)
            text_file.write(fn_html)
            text_file.write(time_stamp_start)
            text_file.write(time_stamp)
            text_file.write(time_total)
            text_file.write(image)
            text_file.write('<hr>\n\n')
        text_file.write(line)
    text_file.close()





def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))


def xia_gain_matching(center_energy, scan_range, channel_number):
    
    graph_x = xia1.mca_x.value
    graph_data = getattr(xia1, "mca_array" + "{}".format(channel_number) + ".value")

    condition = (graph_x <= (center_energy + scan_range)/1000) == (graph_x > (center_energy - scan_range)/1000)
    interval_x = np.extract(condition, graph_x)
    interval = np.extract(condition, graph_data)

    # p0 is the initial guess for fitting coefficients (A, mu and sigma)
    p0 = [.1, center_energy/1000, .1]
    coeff, var_matrix = curve_fit(gauss, interval_x, interval, p0=p0) 
    print('Intensity = ', coeff[0])
    print('Fitted mean = ', coeff[1])
    print('Sigma = ', coeff[2])

    # For testing (following two lines)
    plt.plot(interval_x, interval)
    plt.plot(interval_x, gauss(interval_x, *coeff))

    #return gauss(interval_x, *coeff)



def generate_xia_file(uuid, name, log_path='/GPFS/xf08id/Sandbox/', graph='xia1_graph3'):
    arrays = db.get_table(db[uuid])[graph]
    np.savetxt('/GPFS/xf08id/Sandbox/' + name, [np.array(x) for x in arrays], fmt='%i',delimiter=' ')


def generate_tune_table(motor=hhm.energy, start_energy=5000, stop_energy=13000, step=100):
    table = []
    for energy in range(start_energy, stop_energy + 1, step):
        motor.move(energy)
        time.sleep(0.5)
        tune_mono_pitch(2, 0.025)
        tune_mono_y(0.5, 0.01)
        table.append([energy, hhm.pitch.read()['hhm_pitch']['value'], hhm.y.read()['hhm_y']['value']])
    return table



def set_reference_foil(element = None):
    # Adding reference foil element list
    with open('/nsls2/xf08id/settings/json/foil_wheel.json') as fp:
        reference_foils = json.load(fp)
    elems = [item['element'] for item in reference_foils]


    if element is None:
        yield from mv(foil_wheel.wheel1, 0)
        yield from mv(foil_wheel.wheel2, 0)
    else:
        if element in elems:
            indx = elems.index(element)
            yield from mv(foil_wheel.wheel2, reference_foils[indx]['fw2'])
            yield from mv(foil_wheel.wheel1, reference_foils[indx]['fw1'])
        else:
            yield from mv(foil_wheel.wheel1, 0)
            yield from mv(foil_wheel.wheel2, 0)

        #yield from mv(foil_wheel.wheel2, reference[element]['foilwheel2'])
        #yield from mv(foil_wheel.wheel1, reference[element]['foilwheel1'])


def random_step(x: float = 0,y: float = 0, **kwargs):

    '''
    This plan will move the stage randomly by a random number between
    x/2 and x  and y/2 and y, sampling a donut around the original point
    '''


    if not 'motor_x' in kwargs.keys():
        motor_x = giantxy.x
    if not 'motor_y' in kwargs.keys():
        motor_y = giantxy.y
    random_x = 2 * x * (random()-0.5)
    random_x = random_x * 0.5 + 0.5 * np.sign(random_x)
    random_y = 2 * y*(random()-0.5)
    random_y = random_y * 0.5 + 0.5 * np.sign(random_y)
    yield from mvr(motor_x,random_x,motor_y,random_y)



def sleep(delay:float=1, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    yield from bps.sleep(float(delay))
    yield None


class CannotActuateShutter(Exception):
    pass


def get_adc_offsets(times: int = 20, *args, **kwargs):
    """
       Get Ion Chambers Offsets - Gets the offsets from the ion chambers and automatically subtracts from the acquired data in the next scans

       Parameters
       ----------
       num : int
           Number of points to acquire and average for each ion chamber


       Returns
       -------
       uid : list(str)
           List containing the unique id of the scan


       See Also
       --------
       :func:`tscan`
       """
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    adcs = list(args)
    if not len(adcs):
        adcs = [pba2.adc7, pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]

    old_avers = []
    for adc in adcs:
        old_avers.append(adc.averaging_points.get())
        adc.averaging_points.put(15)

    try:
        yield from bps.mv(shutter_ph_2b, 'Close')
    except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to close.')

    uid = (yield from get_offsets_plan(adcs, num=int(times)))

    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        print('Error: Photon shutter failed to open')


    print('Updating values...')

    arrays = []
    offsets = []
    df = db[uid].table()

    for index, adc in enumerate(adcs):
        key = '{}_volt'.format(adc.name)
        array = df[key]
        offset = np.mean(df[key][2:int(times)])

        arrays.append(array)
        offsets.append(offset)
        adc.offset.put(offset)
        print('{}\n New offset for {}) is  {}'.format(array, adc.dev_name.value, offset))
        adc.averaging_points.put(old_avers[index])

    remove_pb_files(uid)

def get_adc_readouts(times: int = 20, *args, **kwargs):
    """
    Get Ion Chambers Offsets - Gets the offsets from the ion chambers and automatically subtracts from the acquired data in the next scans

    Parameters
    ----------
    num : int
        Number of points to acquire and average for each ion chamber


    Returns
    -------
    uid : list(str)
        List containing the unique id of the scan


    See Also
    --------
    :func:`tscan`
    """
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    adcs = list(args)
    if not len(adcs):
        adcs = [pba2.adc7, pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]

    old_avers = []
    for adc in adcs:
        old_avers.append(adc.averaging_points.get())
        adc.averaging_points.put(15)
    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to open.')
    uid = (yield from get_offsets_plan(adcs, num=int(times)))


    readouts = []
    df = db[uid].table()

    for index, adc in enumerate(adcs):
        key = '{}_volt'.format(adc.name)
        array = df[key]
        readout = np.mean(df[key][2:int(times)])

        readouts.append(readout)
        print('Channel readout for {}  is {} V'.format(adc.dev_name.value, readout))
        adc.averaging_points.put(old_avers[index])

    remove_pb_files(uid)

    print('ADC readout complete!')

def adjust_ic_gains( **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    if 'detectors' not in kwargs:
        detectors = [pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
    else:
        detectors = kwargs['detectors']

    current_lut = int(hhm.lut_number_rbv.value)
    traj_manager = trajectory_manager(hhm)
    info = traj_manager.read_info(silent=True)
    if 'max' not in info[str(current_lut)] or 'min' not in info[str(current_lut)]:
        raise Exception(
            'Could not find max or min information in the trajectory.'
            ' Try sending it again to the controller.')

    e_min = int(info[str(current_lut)]['min'])
    e_max = int(info[str(current_lut)]['max'])


    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        print('ERROR: Photon shutter failed to open')
    shutter.open()



    scan_positions = np.arange(e_max + 50, e_min - 50, -50)

    plan = bp.list_scan(detectors, hhm.energy, scan_positions)
    flyers = []
    for detector in detectors:
        if hasattr(detector, 'kickoff'):
            flyers.append(detector)
    for jj in range(2):
        uid = (yield from bpp.fly_during_wrapper(plan, flyers))

        table = db[uid].table()
        for det in detectors:
            name = f'{det.name}_volt'
            current_gain = det.amp.get_gain()[0]
            if det.polarity == 'neg':
                trace_extreme = table[name].min()
            else:
                trace_extreme = table[name].max()

            print(f'Extreme value {trace_extreme} for detector {det.channel}')
            if abs(trace_extreme) > 3.7:
                print(f'Decreasing gain for detector {det.channel}')
                yield from det.amp.set_gain_plan(current_gain-1, False)

            elif abs(trace_extreme) <= 3.7 and abs(trace_extreme) > 0.35:
                print(f'Correct gain for detector {det.channel}')
            elif abs(trace_extreme) <= 0.35:
                print(f'Increasing gain for detector {det.channel}')
                yield from det.amp.set_gain_plan(current_gain + 1, False)

    shutter.close()
    print('[Adjust Gain] Complete\n')
    remove_pb_files(uid)



def  tune_beamline_plan(motor1,det1,field1):
    yield from tuning_scan(motor, bpm_fm, 'stats1_total', 5, 0.5, n_tries=3)
    yield from tuning_scan(hhm.pitch, bpm_fm, 'stats1_total', 1, 0.025, n_tries=3)



