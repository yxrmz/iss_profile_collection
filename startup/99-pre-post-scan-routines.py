import matplotlib.pyplot as plt
from datetime import datetime
import time


def create_user_folder(uuid, comment, parser, path='/GPFS/xf08id/User Data/'):
	print('Creating directory...')

	path = path + RE.md['year'] + '.' + RE.md['cycle'] + '.' + RE.md['PROPOSAL'] + '/'
	if(not os.path.exists(path)):
		os.makedirs(path)

#	repeat = 1
#	comment2 = comment
#	while(os.path.exists(path + comment2)):
#		repeat += 1
#		comment2 = comment + '-' + str(repeat)

#	os.makedirs(path + comment2)

#	parser.export_trace(comment, filepath = path + comment2 + '/')

	parser.export_trace(comment, filepath = path, uid = uuid)
	

def write_html_log(uuid='', comment='', log_path='/GPFS/xf08id/log/', absorp=True):
	print('Plotting Ion Chambers x Energy and generating log...')

	if(absorp):
		parser = xas_abs
		load_abs_parser(uuid)
	else:
		parser = xas_flu
		load_flu_parser(uuid)

	encoder_file = parser.encoder_file
	ion_file = parser.i0_file
	ion_file2 = parser.it_file

	create_user_folder(uuid, comment, parser)

	log_path = log_path + RE.md['year'] + '.' + RE.md['cycle'] + '.' + RE.md['PROPOSAL'] + '/'
	if(not os.path.exists(log_path)):
		os.makedirs(log_path)

	plt.clf()
	parser.plot()
	plt.show()

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
	plt.savefig(fn)
	fn = './' + file_path

	uid = db[uuid]['start']['uid']
	time_stamp_start=('<p><b> Scan start: </b> ' + str(datetime.fromtimestamp(start_timestamp).strftime('%m/%d/%Y    %H:%M:%S')) + '</p>')
	time_stamp=('<p><b> Scan complete: </b> ' + str(datetime.fromtimestamp(stop_timestamp).strftime('%m/%d/%Y    %H:%M:%S')) + '</p>')
	time_total=('<p><b> Total time: </b> ' + str(datetime.fromtimestamp(stop_timestamp - start_timestamp).strftime('%M:%S')) + '</p>')
	uuid=('<p><b> Scan ID: </b>'+ uid)
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
			text_file_new.write(time_stamp_start + '\n')
			text_file_new.write(time_stamp + '\n')
			text_file_new.write(time_total + '\n')
			text_file_new.write(image + '\n')
			text_file_new.write('<hr>' + '\n\n')
			#text_file_new.write('<p> </p>' + '\n')
		text_file_new.write(line)

def tune_mono_pitch(scan_range, step):
	aver=pba2.adc7.averaging_points.get()
	pba2.adc7.averaging_points.put(10)
	num_points = int(round(scan_range/step))
	over = 0

	while(not over):
		RE(tune([pba2.adc7], hhm.pitch, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch'))
		last_table = db.get_table(db[-1])
		min_index = np.argmin(last_table['pba2_adc7_volt'])
		hhm.pitch.move(last_table['hhm_pitch'][min_index])
		print(hhm.pitch.position)
		os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
		if (num_points >= 10):
			if ((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)):
				over = 1
		else:
			over = 1

	pba2.adc7.averaging_points.put(aver)


def tune_mono_y(scan_range, step):
	aver=pba2.adc7.averaging_points.get()
	pba2.adc7.averaging_points.put(10)
	num_points = int(round(scan_range/step))
	over = 0

	while(not over):
		RE(tune([pba2.adc7], hhm.y, -scan_range/2, scan_range/2, num_points, ''), LivePlot('pba2_adc7_volt', 'hhm_y'))
		last_table = db.get_table(db[-1])
		min_index = np.argmin(last_table['pba2_adc7_volt'])
		hhm.y.move(last_table['hhm_y'][min_index])
		print(hhm.y.position)
		os.remove(db[-1]['descriptors'][0]['data_keys']['pba2_adc7']['filename'])
		if (num_points >= 10):
			if ((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)):
				over = 1
		else:
			over = 1

	pba2.adc7.averaging_points.put(aver)


def generate_xia_file(uuid, comment, log_path='/GPFS/xf08id/Sandbox/', graph='xia1_graph3'):
	arrays = db.get_table(db[uuid])[graph]
	np.savetxt('/GPFS/xf08id/Sandbox/' + comment, [np.array(x) for x in arrays], fmt='%i',delimiter=' ')

def generate_tune_table(motor=hhm_en.energy, start_energy=5000, stop_energy=13000, step=100):
	table = []
	for energy in range(start_energy, stop_energy + 1, step):
		motor.move(energy)
		time.sleep(0.5)
		tune_mono_pitch(2, 0.1)
		tune_mono_y(0.5, 0.025)
		table.append([energy, hhm.pitch.read()['hhm_pitch']['value'], hhm.y.read()['hhm_y']['value']])

	return table


