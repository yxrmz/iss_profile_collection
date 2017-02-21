from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
import math
import csv
import databroker as data
import datamuxer
from isstools.xasdata import xasdata
from isstools.xiaparser import xiaparser

xas_parser = xasdata.XASdata()
xas_abs = xasdata.XASdataAbs()
xas_flu = xasdata.XASdataFlu()

xia_parser = xiaparser.xiaparser()
smbclient = xiaparser.smbclient()


########## load_abs_parser ##########
# Load files into the abs parser xas_abs and interpolate them passing scan uid as argument
# arg1 = uid = unique uid -> this can be an integer relative reference (e.g. -1) or a uid string (e.g. '9a329064') 
def load_abs_parser(uid):
	run = db[uid]
	check = 1
	for i in run['descriptors']:
		if 'devname' in i['data_keys'][i['name']]:
			check += 1
			if i['data_keys'][i['name']]['devname'] == 'i0':
				i0_file = i['data_keys'][i['name']]['filename']
				i0_offset = run['start'][i['name'] + ' offset']
			elif i['data_keys'][i['name']]['devname'] == 'it':
				it_file = i['data_keys'][i['name']]['filename']
				it_offset = run['start'][i['name'] + ' offset']
			elif i['data_keys'][i['name']]['devname'] == 'ir':
				ir_file = i['data_keys'][i['name']]['filename']
				ir_offset = run['start'][i['name'] + ' offset']
			elif i['data_keys'][i['name']]['devname'] == 'iff':
				iff_file = i['data_keys'][i['name']]['filename']
				iff_offset = run['start'][i['name'] + ' offset']
		else:
		    encoder_file = i['data_keys'][i['name']]['filename']

	# Keeping this if for back portability
	if check != len(run['descriptors']):
		i0_file = run['descriptors'][0]['data_keys'][run['descriptors'][0]['name']]['filename']
		it_file = run['descriptors'][1]['data_keys'][run['descriptors'][1]['name']]['filename']
		ir_file = run['descriptors'][2]['data_keys'][run['descriptors'][2]['name']]['filename']
		encoder_file = run['descriptors'][3]['data_keys'][run['descriptors'][3]['name']]['filename']
		if len(run['descriptors']) > 4:
			iff_file = run['descriptors'][4]['data_keys'][run['descriptors'][4]['name']]['filename']

		i0_offset = run['start']['pba2_adc7 offset']
		it_offset = run['start']['pba2_adc6 offset']
		ir_offset = run['start']['pba1_adc1 offset']
		if 'pba1_adc6 offset' in run['start']:
			iff_offset = run['start']['pba1_adc6 offset']
		
	i0_file = i0_file[len(i0_file)-9:len(i0_file)]
	ir_file = ir_file[len(ir_file)-9:len(ir_file)]
	it_file = it_file[len(it_file)-9:len(it_file)]
	encoder_file = encoder_file[len(encoder_file)-9:len(encoder_file)]
	iff_file = iff_file[len(iff_file)-9:len(iff_file)]

	if(xas_abs.encoder_file != encoder_file or xas_abs.i0_file != i0_file or xas_abs.it_file != it_file or xas_abs.ir_file != ir_file or xas_abs.if_file != iff_file):
		print('Parsing abs files...')
		xas_abs.load(encoder_file, i0_file, it_file, ir_file, iff_file, i0_offset, it_offset, ir_offset, iff_offset, float(run['start']['angle_offset']))
		xas_abs.interpolate()


########## load_flu_parser ##########
# Load files into the abs parser xas_flu and interpolate them passing scan uid as argument
# arg1 = uid = unique uid -> this can be an integer relative reference (e.g. -1) or a uid string (e.g. '9a329064') 
def load_flu_parser(uid):
	run = db[uid]
	check = 2
	for i in run['descriptors']:
		if 'devname' in i['data_keys'][i['name']]:
			check += 1
			if i['data_keys'][i['name']]['devname'] == 'i0':
				i0_file = i['data_keys'][i['name']]['filename']
				ion_offset = run['start'][i['name'] + ' offset']
			elif i['data_keys'][i['name']]['devname'] == 'it':
				it_file = i['data_keys'][i['name']]['filename']
				ion_offset2 = run['start'][i['name'] + ' offset']
			elif i['data_keys'][i['name']]['devname'] == 'ir':
				ir_file = i['data_keys'][i['name']]['filename']
				ion_offset3 = run['start'][i['name'] + ' offset']
			elif i['data_keys'][i['name']]['devname'] == 'iff':
				iff_file = i['data_keys'][i['name']]['filename']
				ion_offset4 = run['start'][i['name'] + ' offset']
		
	if check != len(run['descriptors']):		
		di_file = run['descriptors'][0]['data_keys']['pb4_di']['filename']
		i0_file = run['descriptors'][1]['data_keys']['pba1_adc7']['filename']
		ir_file = run['descriptors'][2]['data_keys']['pba2_adc6']['filename']
		it_file = run['descriptors'][3]['data_keys']['pba1_adc1']['filename']
		encoder_file = run['descriptors'][4]['data_keys']['pb9_enc1']['filename']
		iff_file = run['descriptors'][5]['data_keys']['pba1_adc6']['filename']

		ion_offset = run['start']['pba2_adc7 offset']
		ion_offset2 = run['start']['pba2_adc6 offset']
		ion_offset3 = run['start']['pba1_adc1 offset']
		if 'pba1_adc6 offset' in run['start']:
			ion_offset4 = run['start']['pba1_adc6 offset']
		
	di_file = di_file[len(di_file)-9:len(di_file)]
	i0_file = i0_file[len(i0_file)-9:len(i0_file)]
	ir_file = ir_file[len(ir_file)-9:len(ir_file)]
	it_file = it_file[len(it_file)-9:len(it_file)]
	encoder_file = encoder_file[len(encoder_file)-9:len(encoder_file)]
	iff_file = iff_file[len(iff_file)-9:len(iff_file)]

	if(xas_flu.encoder_file != encoder_file or xas_flu.i0_file != i0_file or xas_flu.it_file != it_file or xas_flu.ir_file != ir_file or xas_flu.if_file != iff_file or xas_flu.trig_file != di_file):
		print('Parsing flu files...')
		xas_flu.load(encoder_file, i0_file, it_file, ir_file, iff_file, di_file, ion_offset, ion_offset2, ion_offset3, ion_offset4, float(run['start']['angle_offset']))
		xas_flu.interpolate()


########## plot_abs_files ##########
# Plot absorption passing file names as arguments.
# arg1 = ion_file = file generated by i0 chamber
# arg2 = ion_file2 = file generated by it chamber
# arg3 = encoder_file = file generated by the encoder pizzabox
# arg4 (optional) = color = string describing the color for matplotlib (default = 'r')
def plot_abs_files(ion_file, ion_file2, ion_file3, ion_file4, encoder_file, color='r'):
	print('Plotting Ion Chambers x Energy...')
	
	if(xas_abs.encoder_file != encoder_file or xas_abs.i0_file != ion_file or xas_abs.it_file != ion_file2 or xas_abs.ir_file != ion_file3 or xas_abs.if_file != ion_file4):
		print('Parsing abs files...')
		xas_abs.load(encoder_file, ion_file, ion_file2, ion_file3, ion_file4)
		xas_abs.interpolate()

	xas_abs.plot(color = color)


########## export_abs_traces ##########
# Export the three files generated by absorption scans as a single text file.
# arg1 = uid = unique uid -> this can be an integer relative reference (e.g. -1) or a uid string (e.g. '9a329064') 
# arg2 = out_filename = file name of the new file
# arg3 (optional) = out_filepath = file path of the new file (default = '/GPFS/xf08id/Sandbox/')
def export_abs_traces(uid, out_filename, out_filepath = '/GPFS/xf08id/Sandbox/'):
	load_abs_parser(uid)
	xas_abs.export_trace(out_filename, out_filepath, uid = uid)


########## plot_abs_db ##########
# Plot absorption passing scan uid as argument.
# arg1 = uid = unique uid -> this can be an integer relative reference (e.g. -1) or a uid string (e.g. '9a329064') 
# arg2 (optional) = color = string describing the color for matplotlib (default = 'r')
def plot_abs_db(uid, color='r'):
	print('Plotting Ion Chambers x Energy...')
	
	load_abs_parser(uid)
	xas_abs.plot(color = color)






#def copy_xia_file(filename, dest_filename):
#	smbclient.load(filename, dest_filename)
#	smbclient.copy()











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



