

'''

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


def tune_mono_pitch(scan_range, step, retries=1, ax=None):
    aver = pba1.adc7.averaging_points.get()
    pba1.adc7.averaging_points.put(10)
    num_points = int(round(scan_range / step) + 1)
    over = 0

    while (not over):
        RE(tune([pba1.adc7], hhm.pitch, -scan_range / 2, scan_range / 2, num_points, ''),
           LivePlot('pba1_adc7_volt', 'hhm_pitch', ax=ax))
        last_table = db.get_table(db[-1])
        min_index = np.argmin(last_table['pba1_adc7_volt'])
        hhm.pitch.move(last_table['hhm_pitch'][min_index])
        print(hhm.pitch.position)

        run = db[-1]
        os.remove(run['descriptors'][0]['data_keys'][run['descriptors'][0]['name']]['filename'])
        # for i in run['descriptors']:
        #        if 'devname' in i['data_keys'][i['name']]

        # os.remove(db[-1]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
        if (num_points >= 10):
            if (((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    pba1.adc7.averaging_points.put(aver)
    print('Pitch tuning complete!')


def tune_mono_pitch_encoder(scan_range, step, retries=1, ax=None):
    aver = pba1.adc7.averaging_points.get()
    pba1.adc7.averaging_points.put(10)
    num_points = int(round(scan_range / step) + 1)
    over = 0

    start_position = pb2.enc3.pos_I.value

    while (not over):
        RE(tune([pba1.adc7, pb2.enc3], hhm.pitch, -scan_range / 2, scan_range / 2, 2, ''))

        enc = xasdata.XASdataAbs.loadENCtrace('', '', db[-1]['descriptors'][0]['data_keys']['pb2_enc3']['filename'])
        i0 = xasdata.XASdataAbs.loadADCtrace('', '', db[-1]['descriptors'][1]['data_keys']['pba1_adc7']['filename'])

        min_timestamp = np.array([i0[0, 0], enc[0, 0]]).max()
        max_timestamp = np.array([i0[len(i0) - 1, 0], enc[len(enc) - 1, 0]]).min()
        interval = i0[1, 0] - i0[0, 0]
        timestamps = np.arange(min_timestamp, max_timestamp, interval)
        enc_interp = np.array([timestamps, np.interp(timestamps, enc[:, 0], enc[:, 1])]).transpose()
        i0_interp = np.array([timestamps, np.interp(timestamps, i0[:, 0], i0[:, 1])]).transpose()
        len_to_erase = int(np.round(0.015 * len(i0_interp)))
        enc_interp = enc_interp[len_to_erase:]
        i0_interp = i0_interp[len_to_erase:]

        xas_abs.data_manager.process_equal(i0_interp[:, 0],
                                           enc_interp[:, 1],
                                           i0_interp[:, 1],
                                           i0_interp[:, 1],
                                           i0_interp[:, 1],
                                           10)

        xas_abs.data_manager.en_grid = xas_abs.data_manager.en_grid[5:-5]
        xas_abs.data_manager.i0_interp = xas_abs.data_manager.i0_interp[5:-5]
        # plt.plot(enc_interp[:,1], i0_interp[:,1]) #not binned

        plt.plot(xas_abs.data_manager.en_grid, xas_abs.data_manager.i0_interp)  # binned
        minarg = np.argmin(xas_abs.data_manager.i0_interp)
        enc_diff = xas_abs.data_manager.en_grid[minarg] - start_position

        pitch_pos = enc_diff / 204  # Enc to pitch convertion
        print('Delta Pitch = {}'.format(pitch_pos))
        # convert enc_diff to position (need to know the relation)
        # then move to the new position

        print(hhm.pitch.position)
        # os.remove(db[-1]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
        over = 1

    pba1.adc7.averaging_points.put(aver)
    print('Pitch tuning complete!')


def tune_mono_y(scan_range, step, retries=1, ax=None):
    aver = pba1.adc7.averaging_points.get()
    pba1.adc7.averaging_points.put(10)
    num_points = int(round(scan_range / step) + 1)
    over = 0

    while (not over):
        RE(tune([pba1.adc7], hhm.y, -scan_range / 2, scan_range / 2, num_points, ''),
           LivePlot('pba1_adc7_volt', 'hhm_y', ax=ax))
        last_table = db.get_table(db[-1])
        min_index = np.argmin(last_table['pba1_adc7_volt'])
        hhm.y.move(last_table['hhm_y'][min_index])
        print('New position: {}'.format(hhm.y.position))
        run = db[-1]
        os.remove(run['descriptors'][0]['data_keys'][run['descriptors'][0]['name']]['filename'])
        # os.remove(db[-1]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
        if (num_points >= 10):
            if (((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    pba1.adc7.averaging_points.put(aver)
    print('Y tuning complete!')


def tune_mono_y_bpm(scan_range, step, retries=1, ax=None):
    num_points = int(round(scan_range / step) + 1)
    over = 0

    while (not over):
        RE(tune([bpm_fm], hhm.y, -scan_range / 2, scan_range / 2, num_points, ''),
           LivePlot('bpm_fm_stats1_total', 'hhm_y', ax=ax))
        last_table = db.get_table(db[-1])
        max_index = np.argmax(last_table['bpm_fm_stats1_total'])
        hhm.y.move(last_table['hhm_y'][max_index])
        print('New position: {}'.format(hhm.y.position))
        if (num_points >= 10):
            if (((max_index > 0.2 * num_points) and (max_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    print('Y tuning complete!')



    def prep_trajectory(delay = 1):
    hhm.prepare_trajectory.put("1")
    while (hhm.trajectory_ready.value == 0):
        ttime.sleep(.1)
    while (hhm.trajectory_ready.value == 1):
        ttime.sleep(.1)
    ttime.sleep(delay)




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
        uid = RE(execute_trajectory(name_n,delay,comment=comment))
        yield uid
        # hhm.prepare_trajectory.put('1')
        # uids.append(uid)
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






def xia_step_scan(name:str, comment:str, e0:int=8333, preedge_start:int=-200, xanes_start:int=-50, xanes_end:int=30, exafs_end:int=16, preedge_spacing:float=10, xanes_spacing:float=0.2, exafs_spacing:float=0.04, **kwargs):

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

record(ao,"$(P)Ch1:User:Offset-SP"){
  field(DTYP,"Soft Channel")
  field(VAL,0)
  field(UDF,1)
}

record(ao,"$(P)Ch2:User:Offset-SP"){
  field(DTYP,"Soft Channel")
  field(VAL,0)
  field(UDF,1)
}

record(ao,"$(P)Ch3:User:Offset-SP"){
  field(DTYP,"Soft Channel")
  field(VAL,0)
  field(UDF,1)
}

record(ao,"$(P)Ch4:User:Offset-SP"){
  field(DTYP,"Soft Channel")
  field(VAL,0)
  field(UDF,1)
}
"ADC.db" [readonly] 584L, 11404C


    sys.stdout = kwargs.pop('stdout', sys.stdout)

    energy_grid, time_grid = generate_energy_grid(e0, preedge_start, xanes_start, xanes_end, exafs_end, preedge_spacing, xanes_spacing, exafs_spacing)
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


def parse(db, uid):
    dataset = pd.DataFrame()
    hdr = db[uid]

    detectors = [pba1.adc6, pba1.adc1, pba2.adc6, pba1.adc7]

    channels = ['iff', 'it', 'ir', 'i0']
    for detector, channel in zip(detectors, channels):
        indx = 0
        spectrum = [];
        print(f'Detector {detector.name}')
        data = list(hdr.data(detector.name, stream_name=detector.name))
        for point in data:

            indx +=1
            print(f'We are at {indx}')
            adc = point['adc']
            try:
                adc = adc.apply(lambda x: (int(x, 16) >> 8) - 0x40000 if (int(x, 16) >> 8) > 0x1FFFF else int(x,
                                                                                                          16) >> 8) * 7.62939453125e-05
                mean_val = np.mean(adc)
            except:
                mena_val = 1
            spectrum.append(mean_val)
        dataset[channel] = np.array(spectrum)

    energies = np.array(hdr.start['plan_pattern_args']['object'])
    dataset['energy']= energies
    return dataset

def save_dataset(dataset, name):
    dataset.to_csv()


def pb_scan_plan(detectors, motor, scan_center, scan_range, name = ''):
    flyers = detectors
    def inner():
        md = {'plan_args': {}, 'plan_name': 'pb_scan','experiment': 'pb_scan', 'name': name}
        #md.update(**metadata)
        yield from bps.open_run(md=md)
        yield from bps.sleep(.4)
        yield from bps.clear_checkpoint()
        yield from bps.abs_set(motor, scan_center + (scan_range / 2), wait=True)
        yield from bps.sleep(.4)
        yield from bps.close_run()
        yield from shutter.close_plan()
        yield from bps.abs_set(motor, scan_center, wait=True)

    def final_plan():
        for flyer in flyers:
            yield from bps.unstage(flyer)
        yield from bps.unstage(motor)

    yield from bps.abs_set(motor, scan_center - (scan_range / 2), wait=True)

    yield from shutter.open_plan()
    for flyer in flyers:
        yield from bps.stage(flyer)

    yield from bps.stage(motor)

    return (yield from bpp.fly_during_wrapper(bpp.finalize_wrapper(inner(), final_plan()),
                                              flyers))

def wait_filter_in_place(status_pv):
    # for j in range(5):
    while True:
        ret = yield from bps.read(status_pv)
        if ret is None:
            break
        if ret[status_pv.name]['value'] == 1:
            break
        else:
            yield from bps.sleep(.1)

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



'''