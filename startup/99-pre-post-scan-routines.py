import matplotlib.pyplot as plt
from datetime import datetime
import time

def get_ion_energy_arrays(uid, filepath='/GPFS/xf08id/pizza_box_data/'):
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
	np.savetxt(filepath + ion_file + '-interp.txt', test_ion, fmt='%09i %09i %.6f %i %i', delimiter=" ")
	np.savetxt(filepath + ion_file2 + '-interp.txt', test_ion2, fmt='%09i %09i %.6f %i %i', delimiter=" ")
	np.savetxt(filepath + encoder_file + '-interp.txt', test_encoder, fmt='%09i %09i %f %i %i', delimiter=" ")

	result_ion = test_ion
	result_ion[:,2] = np.log(test_ion[:,2] / test_ion2[:,2])
	return test_encoder[:,2], result_ion[:,2], encoder_file, ion_file, ion_file2


#<p><b> Files: </b></p>
#<ul>
#  <li>en_b4a51e</li>
#  <li>an_b0363d</li>
#  <li>an_71491d</li>
#</ul>  

def write_html_log(uuid='', comment='', log_path='/GPFS/xf08id/log/'):
	print('Plotting Ion Chambers x Energy and generating log...')
	array_x, array_y, encoder_file, ion_file, ion_file2 = get_ion_energy_arrays(uuid)
	stop_timestamp = db[uuid]['stop']['time']

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
	time_stamp=('<p><b> Scan complete: </b> ' + str(datetime.fromtimestamp(stop_timestamp).strftime('%d/%m/%Y    %H:%M:%S')) + '</p>')
	uuid=('<p><b> Scan ID: </b>'+ uid)
	#files= ('<p><b> Files: </b>'+ encoder_file + '    |    ' + ion_file + '    |    ' + ion_file2 + '</p>')
	files= ('<ul>\n  <li><b>Encoder file: </b>' + encoder_file + '</li>\n  <li><b>ADC 6 file: </b>' + ion_file2 + '</li>\n  <li><b>ADC 7 file: </b>' + ion_file + '</li>\n</ul>')
	image=('<img src="'  + fn +  '" alt="' + comment + '" height="447" width="610">')

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
