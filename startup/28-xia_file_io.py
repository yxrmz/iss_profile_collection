from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import math

from isstools.xiaparser import xiaparser

def save_mca_to_file(filename, path = '/GPFS/xf08id/xia_files/', mcas = [xia1.mca1, xia1.mca2, xia1.mca3, xia1.mca4]):
    if path[-1] != '/':
        path += '/'
    arrays = []
    header = ""
    for mca in mcas:
        arrays.append(mca.array.value)
        header += "{}  ".format(mca.name)
    
    arrays = np.array(arrays).transpose()
    np.savetxt("{}{}.txt".format(path, filename), arrays, fmt = "%d", header = header)

def parse_step_scan(set_name, roi_start, roi_end, path = '/GPFS/xf08id/xia_files/'):
    det_channels = []

    energies, i0_values = np.loadtxt("{}{}-{}".format(path, set_name, "i0")).transpose()
    det_channels.append(energies)
    det_channels.append(i0_values - pba1.adc7.offset.value)

    for i in range(4):
        cur_det = np.loadtxt("{}{}-{}".format(path, set_name, i + 1))
        cur_det_roi = [];
        for i in cur_det:
            cur_det_roi.append(np.sum(i[roi_start:roi_end + 1]))
        det_channels.append(cur_det_roi)

    det_channels.append(np.array(det_channels[2]) + np.array(det_channels[3]) + np.array(det_channels[4]) + np.array(det_channels[5]))
    det_channels = np.array(det_channels).transpose()
    np.savetxt("{}{}-parsed.txt".format(path, set_name), det_channels)
    return np.array(det_channels)

def gen_xia_comments(uid):
    info = db[uid]
    year = info['start']['year']
    cycle = info['start']['cycle']
    saf = info['start']['SAF']
    pi = info['start']['PI']
    proposal = info['start']['PROPOSAL']
    scan_id = info['start']['scan_id']
    plan_name = info['start']['plan_name']
    real_uid = info['start']['uid']
    human_start_time = str(datetime.fromtimestamp(info['start']['time']).strftime('%m/%d/%Y  %H:%M:%S'))
    human_stop_time = str(datetime.fromtimestamp(info['stop']['time']).strftime(' %m/%d/%Y  %H:%M:%S'))
    human_duration = str(datetime.fromtimestamp(info['stop']['time'] - info['start']['time']).strftime('%M:%S'))

    comments = '# Year: {}\n# Cycle: {}\n# SAF: {}\n# PI: {}\n# PROPOSAL: {}\n# Scan ID: {}\n# UID: {}\n# Plan name: {}\n# Start time: {}\n# Stop time: {}\n# Total time: {}\n#\n# '.format(year, cycle, saf, pi, proposal, scan_id, real_uid, plan_name, human_start_time, human_stop_time, human_duration)
    return comments

def plot_xia_step_scan(uid, ax = None):

    table = db.get_table(db[uid])

    xia_sum = table[xia1.mca1.roi0.sum.name] + \
              table[xia1.mca2.roi0.sum.name] + \
              table[xia1.mca3.roi0.sum.name] + \
              table[xia1.mca4.roi0.sum.name]

    i0_data = table[i0.volt.name]
    hhm_data = table[hhm.theta.name]
    energy_data = xray.encoder2energy(hhm_data * 360000)

    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    ax.plot(energy_data, -(xia_sum / i0_data))

def parse_xia_step_scan(uid, filename, path):
    table = db.get_table(db[uid])
    if path[-1] != '/':
        path += '/'


    xia_sum = table[xia1.mca1.roi0.sum.name] + \
              table[xia1.mca2.roi0.sum.name] + \
              table[xia1.mca3.roi0.sum.name] + \
              table[xia1.mca4.roi0.sum.name]

    xia_mca1 = table[xia1.mca1.array.name]
    xia_mca2 = table[xia1.mca2.array.name]
    xia_mca3 = table[xia1.mca3.array.name]
    xia_mca4 = table[xia1.mca4.array.name]

    i0_data = table[i0.volt.name] - table[i0.offset.name][1]
    it_data = table[it.volt.name] - table[it.offset.name][1]
    ir_data = table[ir.volt.name] - table[ir.offset.name][1]
    iff_data = table[iff.volt.name] - table[iff.offset.name][1]
    hhm_data = table[hhm.theta.name]
    energy_grid = xray.encoder2energy(hhm_data * 360000)

    if not os.path.exists(path):
        os.makedirs(path)
        call(['setfacl', '-m', 'g:iss-staff:rwx', path])
        call(['chmod', '770', log_path])

    if os.path.isfile('{}{}.txt'.format(path, filename)):
        i = 2
        while os.path.isfile('{}{}-{}.txt'.format(path, filename, i)):
            i += 1
        filename = '{}-{}'.format(filename, i)

    matrix = np.array([energy_grid, i0_data, it_data, ir_data, iff_data, xia_sum]).transpose()
    np.savetxt('{}{}.txt'.format(path, filename), 
                                 matrix, 
                                 fmt = '%12.6f %10.6f %10.6f %10.6f %10.6f %8d',
                                 header = 'Energy (eV)   i0(V)     it(V)     ir(V)     iff(V)     XIA_SUM',
                                 comments = gen_xia_comments(uid))

    return '{}{}.txt'.format(path, filename)




########## interpolate ##########
# Interpolate arrays to have the same timestamp.
# arg1 = array1 (np.array)
# arg2 = array2 (np.array)
# arg3 = array3 (np.array)
# arg4 = trunc = Truncate files to have the smallest length (default = True)
def interpolate(array1, array2, array3 = [], trunc = True):
	array_interp = np.copy(array1)
	array_interp2 = np.copy(array2)
	array_interp3 = np.copy(array3)
	if(trunc):
		if(len(array3)):
			min_timestamp = np.array([array1[0,0], array2[0,0], array3[0,0]]).max()
			max_timestamp = np.array([array1[len(array1)-1,0], array2[len(array2)-1,0], array3[len(array3)-1,0]]).min()
		else:
			min_timestamp = np.array([array1[0,0], array2[0,0]]).max()
			max_timestamp = np.array([array1[len(array1)-1,0], array2[len(array2)-1,0]]).min()
	else:
		if(len(array3)):
			min_timestamp = np.array([array1[0,0], array2[0,0], array3[0,0]]).min()
			max_timestamp = np.array([array1[len(array1)-1,0], array2[len(array2)-1,0], array3[len(array3)-1,0]]).max()
		else:
			min_timestamp = np.array([array1[0,0], array2[0,0]]).min()
			max_timestamp = np.array([array1[len(array1)-1,0], array2[len(array2)-1,0]]).max()

	if(len(array3)):
		interval = np.array([array1[1,0] - array1[0,0], array2[1,0] - array2[0,0], array3[1,0] - array3[0,0]]).min()
	else:
		interval = np.array([array1[1,0] - array1[0,0], array2[1,0] - array2[0,0]]).min()

	timestamps = np.arange(min_timestamp, max_timestamp, interval)
	new_array_interp = np.array([timestamps, np.interp(timestamps, array_interp2[:,0], array_interp2[:,1])]).transpose()
	new_array_interp2 = np.array([timestamps, np.interp(timestamps, array_interp[:,0], array_interp[:,1])]).transpose()
	if(len(array3)):
		new_array_interp3 = np.array([timestamps, np.interp(timestamps, array_interp3[:,0], array_interp3[:,1])]).transpose()
		array_return3 = np.zeros((len(new_array_interp3), 3))
		array_return3[:,:-1] = new_array_interp3
	array_return = np.zeros((len(new_array_interp), 3))
	array_return2 = np.zeros((len(new_array_interp2), 3))
	array_return2[:,:-1] = new_array_interp
	array_return[:,:-1] = new_array_interp2
	if(len(array3)):
		return array_return, array_return2, array_return3
	else:
		return array_return, array_return2



########## mean_array ##########
# Calc mean between two arrays. Returns a np.array.
# arg1 = array1 (np.array)
# arg2 = array2 (np.array)
def mean_array(array1, array2):
	return ((np.array(array1) + np.array(array2))/2)
 
########## plot_arrays ##########
# Plot [np.array] arrays. 'arrays' is a list of arrays.
# arg1 = arrays (list of arrays to plot)
# arg2 (optional) = colors (list of strings defining the plots colors - default = ['b', 'g', 'r', 'y'])
# arg3 (optional) = xlabel (string to use as x label of the plot - default = 'Time (s)')
# arg4 (optional) = ylabel (string to use as y label of the plot - default = '')
# arg5 (optional) = xy_plot (bool that indicates if it is a xy plot or a regular plot - default = False)
# arg6 (optional) = ycolumn (integer to indicate which column of the file is the one to plot in Y axe)
# arg7 (optional) = xcolumn (integer to indicate which column of the file is the one to plot in X axe)
def plot_arrays(arrays, colors=['b', 'g', 'r', 'y'], xlabel='Time (s)', ylabel='', xy_plot=False, ycolumn=1, xcolumn=1):
	index = 0
	if(xy_plot):
		plt.plot(arrays[0][:,xcolumn], arrays[1][:,ycolumn], colors[index])
	else:
		for x in arrays:
			plt.plot(x[:,0], x[:,ycolumn], colors[index])
			index += 1
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	plt.grid(True)


########## plot_arrays_from_file ##########
# Plot graphs getting the data directly from the files. 'files' is a list of file names.
# arg1 = files (list of file names to plot)
# arg2 (optional) = colors (list of strings defining the plots colors - default = ['b', 'g', 'r', 'y'])
# arg3 (optional) = xlabel (string to use as x label of the plot - default = 'Time (s)')
# arg4 (optional) = ylabel (string to use as y label of the plot - default = '')
# arg5 (optional) = interp (bool to interpolate files to have the same timestamp - default = True)
# arg6 (optional) = truncate (bool to truncate files to have the smallest length - default = False)
# arg7 (optional) = xy_plot (bool that indicates if it is a xy plot or a regular plot - default = False)
# arg8 (optional) = set_to_0s (bool to shift the timestamps to start at 0 - default = False)
def plot_array_from_file(files, colors=['b', 'g', 'r', 'y'], xlabel='Time (s)', ylabel='', interp=False, truncate=False, xy_plot=False, set_to_0s = False):
	print('Plotting Array(s)...')

	files[0][0:3]

	np_arrays = []
	for x in range(len(files)):
		if files[x][0:3] == 'en_':
			np_array = xas_parser.loadENCtrace(files[x])
		elif files[x][0:3] == 'an_':
			np_array = xas_parser.loadADCtrace(files[x])
		elif files[x][0:3] == 'di_':
			np_array = xas_parser.loadTRIGtrace(files[x])

		if(interp and x > 0):
			np_arrays[x-1], np_array = interpolate(np_arrays[x-1], np_array, trunc=truncate)
		np_arrays.append(np_array)
	if(set_to_0s):
		for x in range(len(np_arrays)):
			np_arrays[x][:,0] = np_arrays[x][:,0] - np_arrays[x][0,0]
	plot_arrays(np_arrays, colors, xlabel, ylabel, xy_plot=xy_plot)


########## plot_pitch ##########
# Plot Pitch graph in mm passing file names as arguments.
# arg1 = yu_file = file generated by the pizzabox encoder input 
# arg2 = ydo_file = file generated by the pizzabox encoder input 
# arg3 = ydi_file = file generated by the pizzabox encoder input 
# arg4 (optional) = color = string describing the color for matplotlib (default = 'b')
# arg5 (optional) = set_to_0s = boolean to shift the timestamps to start at 0 (default = True)
def plot_pitch(yu_file, ydo_file, ydi_file, color = 'b', set_to_0s = True):
	print('Plotting Pitch...')

	ydo_array, ydi_array, yu_array = xas_parser.loadENCtrace(ydo_file), xas_parser.loadENCtrace(ydi_file), xas_parser.loadENCtrace(yu_file)

	ydo_interp, ydi_interp, yu_interp = interpolate(ydi_array, ydo_array, yu_array)

	mean_yd = mean_array(ydi_interp, ydo_interp)
	pitch = mean_yd
	pitch[:,1] = mean_yd[:,1] - yu_interp[:,1]
	pitch = pitch.astype(float)
	pitch[:,1] = pitch[:,1] * 1e-8
	for x in range(len(pitch)):
		pitch[x, 1] = (math.atan(pitch[x, 1]/1.020)) # USING 1,0195 BECAUSE IT MADE THE GRAPHS GOOD LOOKING :)
	pitch[:, 1] = pitch[:, 1] * 1e6
	if set_to_0s:
		pitch[:,0] = pitch[:,0] - pitch[0,0] # Setting first timestamp position to 0 seconds
	plt.plot(pitch[:,0], pitch[:,1], color)
	plt.xlabel('Time (s)')
	plt.ylabel('Pitch (urad)')
	plt.grid(True)


########## plot_roll ##########
# Plot Roll graph in urad passing file names as arguments. 
# arg1 = ydo_file = file generated by the pizzabox encoder input 
# arg2 = ydi_file = file generated by the pizzabox encoder input 
# arg3 (optional) = color = string describing the color for matplotlib (default = 'r')
# arg4 (optional) = set_to_0s = boolean to shift the timestamps to start at 0 (default = True)
def plot_roll(ydo_file, ydi_file, color = 'r', set_to_0s = True):
	print('Plotting Roll...')

	ydi_array, ydo_array = xas_parser.loadENCtrace(ydo_file), xas_parser.loadENCtrace(ydi_file)

	ydo_interp, ydi_interp = interpolate(ydi_array, ydo_array)
	roll = ydi_interp
	roll[:,1] = ydi_interp[:,1] - ydo_interp[:,1]
	roll = roll.astype(float)
	roll[:,1] = roll[:,1] * 1e-8
	for x in range(len(roll)):
		roll[x, 1] = (math.atan(roll[x, 1]/0.4))
	roll[:, 1] = roll[:, 1] * 1e6 
	if set_to_0s:
		roll[:,0] = roll[:,0] - roll[0,0] # Setting first timestamp position to 0 seconds
	plt.plot(roll[:,0], roll[:,1], color)
	plt.xlabel('Time (s)')
	plt.ylabel('Roll (urad)')
	plt.grid(True)


########## plot_y ##########
# Plot Y graph in mm passing file names as arguments.
# arg1 = yu_file = file generated by the pizzabox encoder input 
# arg2 = ydo_file = file generated by the pizzabox encoder input 
# arg3 = ydi_file = file generated by the pizzabox encoder input 
# arg4 (optional) = color = string describing the color for matplotlib (default = 'g')
# arg5 (optional) = set_to_0s = boolean to shift the timestamps to start at 0 (default = True)
def plot_y(yu_file, ydo_file, ydi_file, color = 'g', set_to_0s = True):
	print('Plotting Y...')

	ydo_array, ydi_array, yu_array = xas_parser.loadENCtrace(ydo_file), xas_parser.loadENCtrace(ydi_file), xas_parser.loadENCtrace(yu_file)

	ydo_interp, ydi_interp, yu_interp = interpolate(ydi_array, ydo_array, yu_array)
	mean_yd = mean_array(ydi_interp, ydo_interp)
	mean_y = mean_array(mean_yd, yu_interp)
	mean_y[:,0] = yu_interp[:,0]
	mean_y = mean_y.astype(float)
	mean_y[:,1] = -mean_y[:,1] * 1e-5
	if set_to_0s:
		mean_y[:,0] = mean_y[:,0] - mean_y[0,0] # Setting first timestamp position to 0 seconds
	plt.plot(mean_y[:,0], mean_y[:,1], color)
	plt.xlabel('Time (s)')
	plt.ylabel('Y (mm)')
	plt.grid(True)


########## plot_adc ##########
# Plot ADC in volts passing file name as argument.
# arg1 = adc_file = file generated by the analog pizzabox adc input
# arg2 (optional) = color = string describing the color for matplotlib (default = 'r')
# arg3 (optional) = set_to_0s = boolean to shift the timestamps to start at 0 (default = False)
def plot_adc(adc_file, color = 'r', set_to_0s = False):
	print('Plotting ADC...')

	adc_parsed = xas_parser.loadADCtrace(adc_file)

	if set_to_0s:
		adc_parsed[:,0] = adc_parsed[:,0] - adc_parsed[0,0] # Setting first timestamp position to 0 seconds
	plt.plot(adc_parsed[:,0], adc_parsed[:,1], color)
	plt.xlabel('Time (s)')
	plt.ylabel('ADC (V)')
	plt.grid(True)


########## plot_hhm_deg ##########
# Plot HHM theta in degrees passing file name as argument.
# arg1 = enc_file = file generated by the pizzabox encoder input
# arg2 (optional) = color = string describing the color for matplotlib (default = 'r')
# arg3 (optional) = set_to_0s = boolean to shift the timestamps to start at 0 (default = False)
def plot_hhm_deg(enc_file, color = 'r', set_to_0s = False):
	print('Plotting HHM Deg...')

	encoder_parsed = xas_parser.loadENCtrace(enc_file)
	encoder_parsed[:,1] = encoder_parsed[:,1] / 360000

	if set_to_0s:
		encoder_parsed[:,0] = encoder_parsed[:,0] - encoder_parsed[0,0] # Setting first timestamp position to 0 seconds
	plt.plot(encoder_parsed[:,0], encoder_parsed[:,1], color)
	plt.xlabel('Time (s)')
	plt.ylabel('Theta (deg)')
	plt.grid(True)



########## plot_di ##########
# Plot digital input (trigger) passing file name as argument.
# arg1 = di_file = file generated by the pizzabox digital input
# arg2 (optional) = color = string describing the color for matplotlib (default = 'ro')
# arg3 (optional) = set_to_0s = boolean to shift the timestamps to start at 0
def plot_di(di_file, color = 'ro', set_to_0s = False):
	print('Plotting DI...')

	di_parsed = xas_parser.loadTRIGtrace(di_file)

	if set_to_0s:
		di_parsed[:,0] = di_parsed[:,0] - di_parsed[0,0] # Setting first timestamp position to 0 seconds
	plt.plot(di_parsed[:,0], np.ones(len(di_parsed[:,0])), color)
	plt.xlabel('Time (s)')
	plt.ylabel('Trigger')
	plt.grid(True)



