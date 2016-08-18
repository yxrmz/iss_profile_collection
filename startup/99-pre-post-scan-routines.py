import matplotlib.pyplot as plt
from datetime import datetime
import time

def get_ion_energy_arrays(uid, comment, filepath='/GPFS/xf08id/pizza_box_data/'):
	run = db[uid]
	ion_file = run['descriptors'][0]['data_keys']['pba2_adc7']['filename']
	ion_file2 = run['descriptors'][1]['data_keys']['pba2_adc6']['filename']
	encoder_file = run['descriptors'][2]['data_keys']['pb9_enc1']['filename']
	ion_file = ion_file[len(ion_file)-9:len(ion_file)]
	ion_file2 = ion_file2[len(ion_file2)-9:len(ion_file2)]
	encoder_file = encoder_file[len(encoder_file)-9:len(encoder_file)]
	array_ion = []
	array_ion2 = []
	array_encoder = []
	parse_file(ion_file, array_ion)
	parse_file(ion_file2, array_ion2)
	parse_file(encoder_file, array_encoder)
	test_ion = np.array(array_ion)
	test_ion2 = np.array(array_ion2)
	test_encoder = np.array(array_encoder)
	test_encoder = test_encoder.astype(float)
	for i in range(len(test_encoder)):
		#test_encoder[i, 2] = (test_encoder[i, 2]/360000)
		test_encoder[i, 2] = -12400 / (2 * 3.1356 * math.sin(math.radians((test_encoder[i, 2]/360000)+0.134)))
	test_ion, test_ion2, test_encoder = interpolate(test_ion, test_ion2, test_encoder, trunc=True)
	#np.savetxt(filepath + ion_file + '-interp.txt', test_ion, fmt='%09i %09i %.6f %i %i', delimiter=" ")
	#np.savetxt(filepath + ion_file2 + '-interp.txt', test_ion2, fmt='%09i %09i %.6f %i %i', delimiter=" ")
	#np.savetxt(filepath + encoder_file + '-interp.txt', test_encoder, fmt='%09i %09i %f %i %i', delimiter=" ")

	create_user_folder(uid, comment, test_encoder, encoder_file, test_ion, ion_file, test_ion2, ion_file2)
	#result_ion = test_ion
	#result_ion[:,2] = np.log(test_ion[:,2] / test_ion2[:,2])
	return test_ion, test_ion2, test_encoder, encoder_file, ion_file, ion_file2
	#return test_encoder[:,2], result_ion[:,2], encoder_file, ion_file, ion_file2


#<p><b> Files: </b></p>
#<ul>
#  <li>en_b4a51e</li>
#  <li>an_b0363d</li>
#  <li>an_71491d</li>
#</ul>  

def create_user_folder(uuid, comment, encoder_array, encoder_file, ion_array1, ion_file, ion_array2, ion_file2, path='/GPFS/xf08id/User Data/'):
	print('Creating directory...')

	path = path + RE.md['year'] + '.' + RE.md['cycle'] + '.' + RE.md['PROPOSAL'] + '/'
	if(not os.path.exists(path)):
		os.makedirs(path)

	repeat = 1
	comment2 = comment
	while(os.path.exists(path + comment2)):
		repeat += 1
		comment2 = comment + '-' + str(repeat)

	os.makedirs(path + comment2)

	np.savetxt(path + comment2 + '/' + ion_file + '-adc7-interp.txt', ion_array1, fmt='%09i %09i %.6f %i %i', delimiter=" ")
	np.savetxt(path + comment2 + '/' + ion_file2 + '-adc6-interp.txt', ion_array2, fmt='%09i %09i %.6f %i %i', delimiter=" ")
	np.savetxt(path + comment2 + '/' + encoder_file + '-enc1-interp.txt', encoder_array, fmt='%09i %09i %f %i %i', delimiter=" ")
	

def write_html_log(uuid='', comment='', log_path='/GPFS/xf08id/log/', log=True):
	print('Plotting Ion Chambers x Energy and generating log...')
	test_ion, test_ion2, test_encoder, encoder_file, ion_file, ion_file2 = get_ion_energy_arrays(uuid, comment)
	#array_x, array_y, encoder_file, ion_file, ion_file2 = get_ion_energy_arrays(uuid)

	log_path = log_path + RE.md['year'] + '.' + RE.md['cycle'] + '.' + RE.md['PROPOSAL'] + '/'
	if(not os.path.exists(log_path)):
		os.makedirs(log_path)

	result_ion = test_ion
	if(log == True):
		result_ion[:,2] = np.log(test_ion[:,2] / test_ion2[:,2])
	else:
		result_ion[:,2] = (test_ion2[:,2] / test_ion[:,2])
	array_x = test_encoder[:,2]
	array_y = result_ion[:,2]

	stop_timestamp = db[uuid]['stop']['time']

	snapshots_path = log_path + 'snapshots/'
	if(not os.path.exists(snapshots_path)):
		os.makedirs(snapshots_path)

	plt.clf()
	plt.plot(array_x, array_y)
	plt.show()
	file_path = 'snapshots/' + comment + '.png'
	fn = log_path + file_path
	repeat = 1
	while(os.path.isfile(fn)):
		repeat += 1
		file_path = 'snapshots/' + comment + '-' + str(repeat) + '.png'
		fn = log_path + file_path
	plt.savefig(fn)
	fn = './' + file_path

	uid = db[uuid]['start']['uid']
	time_stamp=('<p><b> Scan complete: </b> ' + str(datetime.fromtimestamp(stop_timestamp).strftime('%m/%d/%Y    %H:%M:%S')) + '</p>')
	uuid=('<p><b> Scan ID: </b>'+ uid)
	#files= ('<p><b> Files: </b>'+ encoder_file + '    |    ' + ion_file + '    |    ' + ion_file2 + '</p>')
	files= ('<ul>\n  <li><b>Encoder file: </b>' + encoder_file + '</li>\n  <li><b>ADC 6 file: </b>' + ion_file2 + '</li>\n  <li><b>ADC 7 file: </b>' + ion_file + '</li>\n</ul>')
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
			text_file_new.write(uuid + '\n')
			text_file_new.write('<p><b> Files: </b></p>' + '\n')
			text_file_new.write(files + '\n')
			text_file_new.write(time_stamp + '\n')
			text_file_new.write(image + '\n')
			text_file_new.write('<hr>' + '\n\n')
			#text_file_new.write('<p> </p>' + '\n')
		text_file_new.write(line)

def tune_mono_pitch(scan_range, step):
	aver=pba2.adc7.averaging_points.get()
	pba2.adc7.averaging_points.put(10)
	num_points = int(round(scan_range/step))
	RE(tune([pba2.adc7], hhm.pitch, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch'))
	last_table = db.get_table(db[-1])
	min_index = np.argmin(last_table['pba2_adc7_volt'])
	hhm.pitch.move(last_table['hhm_pitch'][min_index])
	print(hhm.pitch.position)
	pba2.adc7.averaging_points.put(aver)
	os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
	
	over = 0
	while(not over):
		RE(tune([pba2.adc7], hhm.pitch, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch'))
		last_table = db.get_table(db[-1])
		min_index = np.argmin(last_table['pba2_adc7_volt'])
		hhm.pitch.move(last_table['hhm_pitch'][min_index])
		print(hhm.pitch.position)
		pba2.adc7.averaging_points.put(aver)
		os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
		if (num_points >= 10):
			if ((min_index > 0.25 * num_points) and (min_index < 0.57 * num_points)):
				over = 1
		else:
			over = 1
	

def tune_mono_y(scan_range, step):
	aver=pba2.adc7.averaging_points.get()
	pba2.adc7.averaging_points.put(10)
	num_points = int(round(scan_range/step))
	RE(tune([pba2.adc7], hhm.y, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_y'))
	last_table = db.get_table(db[-1])
	min_index = np.argmin(last_table['pba2_adc7_volt'])
	hhm.y.move(last_table['hhm_y'][min_index])
	print(hhm.y.position)
	pba2.adc7.averaging_points.put(aver)
	os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
	over = 0

	while(not over):
		RE(tune([pba2.adc7], hhm.y, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_y'))
		last_table = db.get_table(db[-1])
		min_index = np.argmin(last_table['pba2_adc7_volt'])
		hhm.y.move(last_table['hhm_y'][min_index])
		print(hhm.y.position)
		pba2.adc7.averaging_points.put(aver)
		os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
		if (num_points >= 10):
			if ((min_index > 0.25 * num_points) and (min_index < 0.75 * num_points)):
				over = 1
		else:
			over = 1

def generate_xia_file(uuid, comment, log_path='/GPFS/xf08id/Sandbox/', graph='xia1_graph3'):
	arrays = db.get_table(db[uuid])[graph]
	np.savetxt('/GPFS/xf08id/Sandbox/' + comment, [np.array(x) for x in arrays], fmt='%i',delimiter=' ')

def generate_tune_table(motor=hhm_en.energy, start_energy=5000, stop_energy=13000, step=100):
	table = []
	for energy in range(start_energy, stop_energy + 1, step):
		motor.move(energy)
		tune_mono_pitch(1, 0.04)
		tune_mono_y(0.5, 0.025)
		table.append([energy, hhm.pitch.read()['hhm_pitch']['value'], hhm.y.read()['hhm_y']['value']])

	return table






