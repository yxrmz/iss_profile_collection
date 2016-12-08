import matplotlib.pyplot as plt
from datetime import datetime
from subprocess import call
import time
from scipy.optimize import curve_fit
from isstools.xasdata import xasdata


def create_user_folder(uuid, comment, parser, path='/GPFS/xf08id/User Data/'):
    print('Creating directory...')

    path = path + RE.md['year'] + '.' + RE.md['cycle'] + '.' + RE.md['PROPOSAL'] + '/'
    if(not os.path.exists(path)):
        os.makedirs(path)
        call(['setfacl', '-m', 'g:iss-staff:rwx', path])
        call(['chmod', '770', path])

    return parser.export_trace(comment, filepath = path, uid = uuid)
    

def write_html_log(uuid='', comment='', log_path='/GPFS/xf08id/User Data/', absorp=True, caller=''):
    print('Plotting Ion Chambers x Energy and generating log...')

    if(absorp):
        parser = xas_abs
        load_abs_parser(uuid)
    else:
        parser = xas_flu
        load_flu_parser(uuid)
        xia_file = db[uuid]['start']['xia_filename']
        di_file = parser.trig_file

    encoder_file = parser.encoder_file
    ion_file = parser.i0_file
    ion_file2 = parser.it_file

    interp_filename = create_user_folder(uuid, comment, parser)

    # Creating folder /GPFS/xf08id/User Data/[year].[cycle].[proposal]/ if it doesn't exist
    log_path = log_path + RE.md['year'] + '.' + RE.md['cycle'] + '.' + RE.md['PROPOSAL'] + '/'
    if(not os.path.exists(log_path)):
        os.makedirs(log_path)

    # Creating folder /GPFS/xf08id/User Data/[year].[cycle].[proposal]/log if it doesn't exist
    log_path = log_path + 'log/'
    if(not os.path.exists(log_path)):
        os.makedirs(log_path)


    start_timestamp = db[uuid]['start']['time']
    stop_timestamp = db[uuid]['stop']['time']

    snapshots_path = log_path + 'snapshots/'
    if(not os.path.exists(snapshots_path)):
        os.makedirs(snapshots_path)

    file_path = 'snapshots/' + comment + '.png'
    fn = log_path + file_path
    repeat = 1
    while(os.path.isfile(fn)):
        repeat += 1
        file_path = 'snapshots/' + comment + '-' + str(repeat) + '.png'
        fn = log_path + file_path

    # Check if caller is the GUI, if not, plot graph outside
    if (caller != 'run_scan'):
        plt.clf()
        parser.plot()
        plt.show()
        plt.savefig(fn)
        #plt.close()

    fn = './' + file_path

    time_stamp_start=('<p><b> Scan start: </b> ' + str(datetime.fromtimestamp(start_timestamp).strftime('%m/%d/%Y    %H:%M:%S')) + '</p>')
    time_stamp=('<p><b> Scan complete: </b> ' + str(datetime.fromtimestamp(stop_timestamp).strftime('%m/%d/%Y    %H:%M:%S')) + '</p>')
    time_total=('<p><b> Total time: </b> ' + str(datetime.fromtimestamp(stop_timestamp - start_timestamp).strftime('%M:%S')) + '</p>')
    uuid=('<p><b> Scan ID: </b>'+ str(uuid))
    
    if(absorp):
        files= ('<ul>\n  <li><b>Encoder file: </b>' + encoder_file + '</li>\n  <li><b>ADC 6 file: </b>' + ion_file2 + '</li>\n  <li><b>ADC 7 file: </b>' + ion_file + '</li>\n</ul>')
    else:
        files= ('<ul>\n  <li><b>Encoder file: </b>' + encoder_file + '</li>\n  <li><b>ADC 6 file: </b>' + ion_file2 + '</li>\n  <li><b>ADC 7 file: </b>' + ion_file + '</li>\n  <li><b>DI file: </b>' + di_file + '</li>\n  <li><b>XIA file: </b>' + xia_file + '</li>\n</ul>')

    image=('<img src="'  + fn +  '" alt="' + comment + '" height="447" width="610">')

    if(not os.path.isfile(log_path + 'log.html')):
        create_file = open(log_path + 'log.html', "w")
        create_file.write('<html> <body>\n</body> </html>')
        create_file.close()

    text_file = open(log_path + 'log.html', "r")
    lines = text_file.readlines()
    text_file.close()

    text_file_new = open(log_path + 'log.html', "w")

    for indx,line in enumerate(lines):
        if indx is 1:
            text_file_new.write('<header><h2> ' + comment + ' </h2></header>\n')
            text_file_new.write(str(uuid) + '\n')
            text_file_new.write('<p><b> Files: </b></p>' + '\n')
            text_file_new.write(files + '\n')
            text_file_new.write(time_stamp_start + '\n')
            text_file_new.write(time_stamp + '\n')
            text_file_new.write(time_total + '\n')
            text_file_new.write(image + '\n')
            text_file_new.write('<hr>' + '\n\n')
        text_file_new.write(line)

    return interp_filename

def tune_mono_pitch(scan_range, step, retries = 1, fig = None):
    aver=pba2.adc7.averaging_points.get()
    pba2.adc7.averaging_points.put(10)
    num_points = int(round(scan_range/step))
    over = 0

    while(not over):
        RE(tune([pba2.adc7], hhm.pitch, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch', fig=fig))
        last_table = db.get_table(db[-1])
        min_index = np.argmin(last_table['pba2_adc7_volt'])
        hhm.pitch.move(last_table['hhm_pitch'][min_index])
        print(hhm.pitch.position)
        os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
        if (num_points >= 10):
            if (((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    pba2.adc7.averaging_points.put(aver)
    print('Pitch tuning complete!')

def tune_mono_pitch_encoder(scan_range, step, retries = 1, fig = None):
    aver=pba2.adc7.averaging_points.get()
    pba2.adc7.averaging_points.put(10)
    num_points = int(round(scan_range/step))
    over = 0
	
	start_position = pb2.enc3.pos_I.value

    while(not over):
        RE(tune([pba2.adc7, pb2.enc3], hhm.pitch, -scan_range/2, scan_range/2, 2, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch', fig=fig))

		enc = xasdata.XASdataAbs.loadENCtrace('', '', db[-1]['descriptors'][0]['data_keys']['pb2_enc3']['filename'])
		i0 = xasdata.XASdataAbs.loadADCtrace('', '', db[-1]['descriptors'][1]['data_keys']['pba2_adc7']['filename'])
		
        min_timestamp = np.array([i0[0,0], enc[0,0]]).max()
        max_timestamp = np.array([i0[len(i0)-1,0], enc[len(enc)-1,0]]).min()
        interval = i0[1,0] - i0[0,0]
        timestamps = np.arange(min_timestamp, max_timestamp, interval)
        enc_interp = np.array([timestamps, np.interp(timestamps, enc[:,0], enc[:,1])]).transpose()
        i0_interp = np.array([timestamps, np.interp(timestamps, i0[:,0], i0[:,1])]).transpose()
		len_to_erase = int(np.round(0.015 * len(i0_interp)))
        enc_interp = enc_interp[len_to_erase:]
        i0_interp = i0_interp[len_to_erase:]
		
		enc_grid = xas_abs.data_manager.energy_grid_equal(enc_interp[:, 1], 100)
		xas_abs.data_manager.process_equal(i0_interp[:,0],
		                                   enc_interp[:,1],
										   i0_interp[:,1],
										   i0_interp[:,1],
										   i0_interp[:,1],
										   1000)
												
        xas_abs.data_manager.en_grid = xas_abs.data_manager.en_grid[2:-2]
        xas_abs.data_manager.i0_interp = xas_abs.data_manager.i0_interp[2:-2]
		#plt.plot(enc_interp[:,1], i0_interp[:,1]) #not binned
		
		plt.plot(xas_abs.data_manager.en_grid, xas_abs.data_manager.i0_interp) #binned
		minarg = np.argmin(xas_abs.data_manager.i0_interp)
		enc_diff = xas_abs.data_manager.en_grid[minarg] - start_position
		
		#convert enc_diff to position (need to know the relation)
		#then move to the new position
		
        print(hhm.pitch.position)
        #os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
		over = 1

    pba2.adc7.averaging_points.put(aver)
    print('Pitch tuning complete!')


def tune_mono_y(scan_range, step, retries = 1, fig = None):
    aver=pba2.adc7.averaging_points.get()
    pba2.adc7.averaging_points.put(10)
    num_points = int(round(scan_range/step))
    over = 0

    while(not over):
        RE(tune([pba2.adc7], hhm.y, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_y', fig=fig))
        last_table = db.get_table(db[-1])
        min_index = np.argmin(last_table['pba2_adc7_volt'])
        hhm.y.move(last_table['hhm_y'][min_index])
        print('New position: {}'.format(hhm.y.position))
        os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
        if (num_points >= 10):
            if (((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    pba2.adc7.averaging_points.put(aver)
    print('Y tuning complete!')


def tune_mono_y_bpm(scan_range, step, retries = 1, fig = None):
    num_points = int(round(scan_range/step))
    over = 0

    while(not over):
        RE(tune([bpm_fm], hhm.y, -scan_range/2, scan_range/2, num_points, ''), LivePlot('bpm_fm_stats1_total', 'hhm_y', fig=fig))
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



def generate_xia_file(uuid, comment, log_path='/GPFS/xf08id/Sandbox/', graph='xia1_graph3'):
    arrays = db.get_table(db[uuid])[graph]
    np.savetxt('/GPFS/xf08id/Sandbox/' + comment, [np.array(x) for x in arrays], fmt='%i',delimiter=' ')


def generate_tune_table(motor=hhm_en.energy, start_energy=5000, stop_energy=13000, step=100):
    table = []
    for energy in range(start_energy, stop_energy + 1, step):
        motor.move(energy)
        time.sleep(0.5)
        tune_mono_pitch(2, 0.025)
        tune_mono_y(0.5, 0.01)
        table.append([energy, hhm.pitch.read()['hhm_pitch']['value'], hhm.y.read()['hhm_y']['value']])

    return table


