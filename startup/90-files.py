from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
import math
import csv
import databroker as data

# Parse file and return a list in 'array_out'
def parse_file(file_name, array_out, file_path = '/GPFS/xf08id/pizza_box_data/'):
    type = 'none'
    with open(file_path + str(file_name)) as f:
        len_of_line = len(next(f).split())
        if len_of_line == 5:
            f.seek(0)    
            ts, tn, enc, count, digital = [int(x) for x in next(f).split()] # read first line
            type = 'encoder'
        elif len_of_line == 4:
            f.seek(0)
            first_line = [x for x in next(f).split()]
            ts = int(first_line[0])
            tn = int(first_line[1])
            count = int(first_line[2])
            adc = int(first_line[3], 0)
            type = 'adc'
        if "clear" in dir(array_out):
            array_out += []
            array_out.clear()
        else:
            print('Your array should be a list, just define it: my_array = []')
            return
        for line in f: # read rest of lines
            if(len_of_line == 5):
                array_out.append([int(x) for x in line.split()])
            elif(len_of_line == 4):
                current_line = line.split()
                current_line[3] = int(current_line[3],0) >> 8
                if current_line[3] > 0x1FFFF:
                    current_line[3] -= 0x40000
                current_line[3] = float(current_line[3]) * 7.62939453125e-05
                array_out.append([int(current_line[0]), int(current_line[1]), current_line[3], int(current_line[2])])
        #if type == 'adc':
        #    np.savetxt(file_path + file_name + '.txt', np.array(array_out), fmt='%i %09i %.6f %i', delimiter=" ")
        #numpy.savetxt("/home/istavitski/test.csv", np.array(array_out), delimiter=" ")


# Interpolate arrays to have the same timestamp. array3 is optional.
# Setting the option 'trunc' to True will make the output arrays have the length of the smallest input array. 
# returns two or three interpolated arrays (return array_return, array_return2, array_return3)
def interpolate(array1, array2, array3 = [], trunc = False, interval = 0.001):
    array_interp = np.copy(array1)
    array_interp2 = np.copy(array2)
    array_interp3 = np.copy(array3)
    if(trunc):
        if(len(array3)):
            min_timestamp = np.array([array1[0,0] + array1[0,1] * 1e-9, array2[0,0] + array2[0,1] * 1e-9, array3[0,0] + array3[0,1] * 1e-9]).max()
            max_timestamp = np.array([array1[len(array1)-1,0] + array1[len(array1)-1,1] * 1e-9, array2[len(array2)-1,0] + array2[len(array2)-1,1] * 1e-9, array3[len(array3)-1,0] + array3[len(array3)-1,1] * 1e-9]).min()
        else:
            min_timestamp = np.array([array1[0,0] + array1[0,1] * 1e-9, array2[0,0] + array2[0,1] * 1e-9]).max()
            max_timestamp = np.array([array1[len(array1)-1,0] + array1[len(array1)-1,1] * 1e-9, array2[len(array2)-1,0] + array2[len(array2)-1,1] * 1e-9]).min()
    else:
        if(len(array3)):
            min_timestamp = np.array([array1[0,0] + array1[0,1] * 1e-9, array2[0,0] + array2[0,1] * 1e-9, array3[0,0] + array3[0,1] * 1e-9]).min()
            max_timestamp = np.array([array1[len(array1)-1,0] + array1[len(array1)-1,1] * 1e-9, array2[len(array2)-1,0] + array2[len(array2)-1,1] * 1e-9, array3[len(array3)-1,0] + array3[len(array3)-1,1] * 1e-9]).max()
        else:
            min_timestamp = np.array([array1[0,0] + array1[0,1] * 1e-9, array2[0,0] + array2[0,1] * 1e-9]).min()
            max_timestamp = np.array([array1[len(array1)-1,0] + array1[len(array1)-1,1] * 1e-9, array2[len(array2)-1,0] + array2[len(array2)-1,1] * 1e-9]).max()
    
    timestamps = np.arange(min_timestamp, max_timestamp, interval)
    timestamps_sec = np.copy(timestamps)
    timestamps_nano = np.copy(timestamps)
    for i in range(len(timestamps)):
        timestamps_sec[i] = math.trunc(timestamps[i])
        timestamps_nano[i] = (timestamps[i] - timestamps_sec[i]) * 1e9
    new_array_interp = np.array([timestamps_sec, timestamps_nano, np.interp(timestamps, array_interp2[:,0] + array_interp2[:,1]*1e-9, array_interp2[:,2])]).transpose()
    new_array_interp2 = np.array([timestamps_sec, timestamps_nano, np.interp(timestamps, array_interp[:,0] + array_interp[:,1]*1e-9, array_interp[:,2])]).transpose()
    if(len(array3)):
        new_array_interp3 = np.array([timestamps_sec, timestamps_nano, np.interp(timestamps, array_interp3[:,0] + array_interp3[:,1]*1e-9, array_interp3[:,2])]).transpose()
        array_return3 = np.zeros((len(new_array_interp3), 5))
        array_return3[:,:-2] = new_array_interp3
    array_return = np.zeros((len(new_array_interp), 5))
    array_return2 = np.zeros((len(new_array_interp2), 5))
    array_return2[:,:-2] = new_array_interp
    array_return[:,:-2] = new_array_interp2
    if(len(array3)):
        return array_return, array_return2, array_return3
    else:
        return array_return, array_return2



# Calc mean between two arrays (Y):
# returns an array
def mean_array(test, test3):
    return ((np.array(test) + np.array(test3))/2)
 
# Plot [np.array] arrays. 'arrays' is a list of arrays.
def plot_arrays(arrays, colors=['b', 'g', 'r', 'y'], xlabel='Time Stamp (s)', ylabel='', grid=True, xy_plot=False, ycolumn=2, xcolumn=2):
    index = 0
    if(xy_plot):
        plt.plot(arrays[0][:,xcolumn], arrays[1][:,ycolumn], colors[index])
    else:
        for x in arrays:
            plt.plot(x[:,0] + x[:,1] * 1e-9, x[:,ycolumn], colors[index])
            index += 1
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(grid)


# Plot graphs getting the data directly from the files. 'files' is a list of file names.
def plot_array_from_file(files, colors=['b', 'g', 'r', 'y'], xlabel='Time Stamp (s)', ylabel='', grid=True, interpolate=True, trunc=False, xy_plot=False):
    print('Plotting Array(s)...')
    np_arrays = []
    for x in range(len(files)):
        exec('array' + str(x) + ' = []', locals())
        exec('parse_file(files[' + str(x) + '], array' + str(x) + ')', globals(), locals())
        exec('np_array' + str(x) + ' = np.array(array' + str(x) + ')', globals(), locals())
        if(interpolate and x > 0):
            if(trunc):
                locals()['np_array' + str(x-1)], locals()['np_array' + str(x)] = globals()['interpolate'](locals()['np_array' + str(x-1)], locals()['np_array' + str(x)], trunc=True)
            else:
                locals()['np_array' + str(x-1)], locals()['np_array' + str(x)] = globals()['interpolate'](locals()['np_array' + str(x-1)], locals()['np_array' + str(x)])
            np_arrays.pop()
            np_arrays.append(locals()['np_array' + str(x-1)])
        np_arrays.append(locals()['np_array' + str(x)])
    plot_arrays(np_arrays, colors, xlabel, ylabel, grid, xy_plot=xy_plot)

def plot_volt_energy(files, colors=['b', 'g', 'r', 'y'], xlabel='Energy (eV)', ylabel='V', grid=True):
    print('Plotting V x Energy...')
    np_arrays = []
    for x in range(len(files)):
        exec('array' + str(x) + ' = []', locals())
        exec('parse_file(files[' + str(x) + '], array' + str(x) + ')', globals(), locals())
        exec('np_array' + str(x) + ' = np.array(array' + str(x) + ')', globals(), locals())
        if(x > 0):
            locals()['np_array' + str(x-1)], locals()['np_array' + str(x)] = globals()['interpolate'](locals()['np_array' + str(x-1)], locals()['np_array' + str(x)], trunc=True)
            np_arrays.pop()
            np_arrays.append(locals()['np_array' + str(x-1)])
        elif (x == 0):
            for i in range(len(locals()['np_array' + str(x)])):
                locals()['np_array' + str(x)][i, 2] = -12400 / (2 * 3.1356 * math.sin(math.radians(locals()['np_array' + str(x)][i, 2]/360000)))
        np_arrays.append(locals()['np_array' + str(x)])
    plot_arrays(np_arrays, colors, xlabel, ylabel, grid, xy_plot=True)


# Plot pitch graph passing the files names as arguments (yu_file, ydo_file and ydi_file)
def plot_pitch(yu_file, ydo_file, ydi_file, color = 'b', set_to_0s = True): #(ydi_file, ydo_file, yu_file)
    print('Plotting Pitch...')
    array_ydi, array_ydo, array_yu = [], [], []
    parse_file(ydi_file, array_ydi)
    parse_file(ydo_file, array_ydo)
    parse_file(yu_file, array_yu)
    test_ydi, test_ydo, test_yu = np.array(array_ydi), np.array(array_ydo), np.array(array_yu)
    test_ydo_interp, test_ydi_interp, test_yu_interp = interpolate(test_ydi, test_ydo, test_yu)
    mean_yd = mean_array(test_ydi_interp, test_ydo_interp)
    pitch = mean_yd
    pitch[:,2] = mean_yd[:,2] - test_yu_interp[:,2]
    pitch = pitch.astype(float)
    pitch[:,2] = pitch[:,2] * 1e-8
    for x in range(len(pitch)):
        pitch[x, 2] = (math.atan(pitch[x, 2]/1.020)) # USING 1,0195 BECAUSE IT MADE THE GRAPHS GOOD LOOKING :)
    pitch[:, 2] = pitch[:, 2] * 1e6
    if set_to_0s:
        pitch[:,0] = pitch[:,0] - pitch[0,0] # Setting first timestamp position to 0 seconds
        pitch[:,1] = pitch[:,1] - pitch[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([pitch], [color], ylabel='Pitch (urad)')


# Plot roll graph passing the files names as arguments (ydo_file and ydi_file)
def plot_roll(ydo_file, ydi_file, color = 'r', set_to_0s = True):
    print('Plotting Roll...')
    array_ydi, array_ydo, array_yu = [], [], []
    parse_file(ydi_file, array_ydi)
    parse_file(ydo_file, array_ydo)
    test_ydi, test_ydo = np.array(array_ydi), np.array(array_ydo)
    test_ydo_interp, test_ydi_interp = interpolate(test_ydi, test_ydo)
    roll = test_ydi_interp
    roll[:,2] = test_ydi_interp[:,2] - test_ydo_interp[:,2]
    roll = roll.astype(float)
    roll[:,2] = roll[:,2] * 1e-8
    for x in range(len(roll)):
        roll[x, 2] = (math.atan(roll[x, 2]/0.4))
    roll[:, 2] = roll[:, 2] * 1e6 
    if set_to_0s:
        roll[:,0] = roll[:,0] - roll[0,0] # Setting first timestamp position to 0 seconds
        roll[:,1] = roll[:,1] - roll[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([roll], ['r'], ylabel='Roll (urad)')


# Plot y graph passing the files names as arguments (yu_file, ydo_file and ydi_file)
def plot_y(yu_file, ydo_file, ydi_file, color = 'g', set_to_0s = True):
    print('Plotting Y...')
    array_ydi, array_ydo, array_yu = [], [], []
    parse_file(ydi_file, array_ydi)
    parse_file(ydo_file, array_ydo)
    parse_file(yu_file, array_yu)
    test_ydi, test_ydo, test_yu = np.array(array_ydi), np.array(array_ydo), np.array(array_yu)
    test_ydo_interp, test_ydi_interp, test_yu_interp = interpolate(test_ydi, test_ydo, test_yu)
    mean_yd = mean_array(test_ydi_interp, test_ydo_interp)
    mean_y = mean_array(mean_yd, test_yu_interp)
    mean_y[:,0] = test_yu_interp[:,0]
    mean_y[:,1] = test_yu_interp[:,1]
    mean_y = mean_y.astype(float)
    mean_y[:,2] = -mean_y[:,2] * 1e-5
    if set_to_0s:
        mean_y[:,0] = mean_y[:,0] - mean_y[0,0] # Setting first timestamp position to 0 seconds
        mean_y[:,1] = mean_y[:,1] - mean_y[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([mean_y], [color], ylabel='Y (mm)')


# Plot adc graph from analog pizzabox input file passing the file name as argument (adc_file)
def plot_adc(adc_file, color = 'r', set_to_0s = True, ycolumn=2):
    print('Plotting ADC...')
    array_adc = []
    parse_file(adc_file, array_adc)
    test_adc = np.array(array_adc)
    if set_to_0s:
        test_adc[:,0] = test_adc[:,0] - test_adc[0,0] # Setting first timestamp position to 0 seconds
        test_adc[:,1] = test_adc[:,1] - test_adc[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([test_adc], [color], ylabel='ADC (V)', ycolumn=ycolumn)

# Plot adc graph from analog pizzabox input file passing the file name as argument (adc_file)
def plot_hhm_deg(enc_file, color = 'r', set_to_0s = True):
    print('Plotting HHM Deg...')
    array_enc = []
    parse_file(enc_file, array_enc)
    test_enc = np.array(array_enc)
    test_enc = test_enc.astype(float)
    test_enc[:,2] = test_enc[:,2] / 360000
    #print(test_enc[:,2])
    if set_to_0s:
        test_enc[:,0] = test_enc[:,0] - test_enc[0,0] # Setting first timestamp position to 0 seconds
        test_enc[:,1] = test_enc[:,1] - test_enc[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([test_enc], [color], ylabel='Theta (deg)')

# Plot DI graph from pizzabox input file passing the file name as argument (di_file)
def plot_di(di_file, color = 'r', set_to_0s = True):
    print('Plotting DI...')
    array_di = []
    parse_file(di_file, array_di)
    test_di = np.array(array_di)
    if set_to_0s:
        test_di[:,0] = test_di[:,0] - test_di[0,0] # Setting first timestamp position to 0 seconds
        test_di[:,1] = test_di[:,1] - test_di[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([test_di], [color], ylabel='ADC (V)', ycolumn=4)

# Plot ion chambers (log(first file / second file)) graph from analog pizzabox input file passing filenames as arguments (ion_file and ion_file 2)
def plot_ion_chambers(ion_file, ion_file2, color = 'r', set_to_0s = False, ycolumn=2):
    print('Plotting Ion Chambers...')
    array_ion = []
    array_ion2 = []
    parse_file(ion_file, array_ion)
    parse_file(ion_file2, array_ion2)
    test_ion = np.array(array_ion)
    test_ion2 = np.array(array_ion2)
    test_ion, test_ion2 = interpolate(test_ion, test_ion2)
    result = test_ion
    result[:,2] = np.log(test_ion[:,2] / test_ion2[:,2])
    if set_to_0s:
        result[:,0] = result[:,0] - result[0,0] # Setting first timestamp position to 0 seconds
        result[:,1] = result[:,1] - result[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([result], [color], ylabel='log(ion1 / ion2)', ycolumn=ycolumn)


# fig = plt.figure()
# plot_ion_chambers('an_28b23e', 'an_ac0ff0')
# ax = fig.add_subplot(111)
# ax2 = ax.twinx()
# plot_hhm_deg('en_fdecac', color='b',set_to_0s=False)

def plot_ion_energy(ion_file, ion_file2, encoder_file, colors=['b', 'g', 'r', 'y'], xlabel='Energy (eV)', ylabel='log(ion1 / ion2)', grid=True, set_to_0s=False, filepath='/GPFS/xf08id/pizza_box_data/'):
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
        test_encoder[i, 2] = -12400 / (2 * 3.1356 * math.sin(math.radians(test_encoder[i, 2]/360000)))
    test_ion, test_ion2, test_encoder = interpolate(test_ion, test_ion2, test_encoder, trunc=True)
    np.savetxt(filepath + ion_file + '-interp.txt', test_ion, fmt='%09i %09i %.6f %i %i', delimiter=" ")
    np.savetxt(filepath + ion_file2 + '-interp.txt', test_ion2, fmt='%09i %09i %.6f %i %i', delimiter=" ")
    np.savetxt(filepath + encoder_file + '-interp.txt', test_encoder, fmt='%09i %09i %f %i %i', delimiter=" ")

    result_ion = test_ion
    result_ion[:,2] = np.log(test_ion[:,2] / test_ion2[:,2])

    if set_to_0s:
        result_ion[:,0] = result_ion[:,0] - result_ion[0,0] # Setting first timestamp position to 0 seconds
        result_ion[:,1] = result_ion[:,1] - result_ion[0,1] # Setting first timestamp position to 0 seconds
        test_encoder[:,0] = test_encoder[:,0] - test_encoder[0,0]
        test_encoder[:,1] = test_encoder[:,1] - test_encoder[0,1]

    plot_arrays([test_encoder, result_ion], colors, xlabel, ylabel, grid, xy_plot=True)

# Parse file and write a new file with adc values in V
def parse_adc(in_filename, in_filepath = '/GPFS/xf08id/pizza_box_data/', out_filename = '', out_filepath = '/home/istavitski/parsed_adc_files/'):
    array_list = []
    with open(in_filepath + str(in_filename)) as f:
        len_of_line = len(next(f).split())
        if len_of_line == 4:
            f.seek(0)
            first_line = [x for x in next(f).split()]
            ts = int(first_line[0])
            tn = int(first_line[1])
            count = int(first_line[2])
            adc = int(first_line[3], 0)
        if "clear" in dir(array_list):
            array_list += []
            array_list.clear()
        for line in f: # read rest of lines
            if(len_of_line == 5):
                array_list.append([int(x) for x in line.split()])
            elif(len_of_line == 4):
                current_line = line.split()
                current_line[3] = int(current_line[3],0) >> 8
                if current_line[3] > 0x1FFFF:
                    current_line[3] -= 0x40000
                current_line[3] = float(current_line[3]) * 7.62939453125e-05
                array_list.append([int(current_line[0]), int(current_line[1]), current_line[3], int(current_line[2])])
        if out_filename == '':
            out_filename = 'noname.txt'
        np.savetxt(out_filepath + out_filename, np.array(array_list), fmt='%09i %09i %.6f %i ', delimiter=" ")


# Plot log(ion1/ion2) x energy getting data from the scan defined by uid.
def plot_ion_energy_db(uid, colors=['b', 'g', 'r', 'y'], xlabel='Energy (eV)', ylabel='log(ion1 / ion2)', grid=True, set_to_0s=False, filepath='/GPFS/xf08id/pizza_box_data/'):
    print('Plotting Ion Chambers x Energy...')
    
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
        test_encoder[i, 2] = -12400 / (2 * 3.1356 * math.sin(math.radians(test_encoder[i, 2]/360000)))
    test_ion, test_ion2, test_encoder = interpolate(test_ion, test_ion2, test_encoder, trunc=True)
    np.savetxt(filepath + ion_file + '-interp.txt', test_ion, fmt='%09i %09i %.6f %i %i', delimiter=" ")
    np.savetxt(filepath + ion_file2 + '-interp.txt', test_ion2, fmt='%09i %09i %.6f %i %i', delimiter=" ")
    np.savetxt(filepath + encoder_file + '-interp.txt', test_encoder, fmt='%09i %09i %f %i %i', delimiter=" ")

    result_ion = test_ion
    result_ion[:,2] = np.log(test_ion[:,2] / test_ion2[:,2])

    if set_to_0s:
        result_ion[:,0] = result_ion[:,0] - result_ion[0,0] # Setting first timestamp position to 0 seconds
        result_ion[:,1] = result_ion[:,1] - result_ion[0,1] # Setting first timestamp position to 0 seconds
        test_encoder[:,0] = test_encoder[:,0] - test_encoder[0,0]
        test_encoder[:,1] = test_encoder[:,1] - test_encoder[0,1]

    plot_arrays([test_encoder, result_ion], colors, xlabel, ylabel, grid, xy_plot=True)

#    run = db[uid]
#    adc1_data = list(db.get_events(run, stream_name='pba2_adc6', fill=True))
#    adc2_data = list(db.get_events(run, stream_name='pba2_adc7', fill=True))
#    encoder_data = list(db.get_events(run, stream_name='pb9_enc1', fill=True))
#    array_ion = []
#    array_ion2 = []
#    array_encoder = []

#    array_ion.append([_.ts_s for d in adc1_data for _ in d['data']['pba2_adc6']])
#    array_ion2.append([_.ts_s for d in adc2_data for _ in d['data']['pba2_adc7']])
#    array_encoder.append([_.ts_s for d in encoder_data for _ in d['data']['pb9_enc1']])
    

#    array_ion.append([_.ts_ns for d in adc1_data for _ in d['data']['pba2_adc6']])
#    array_ion2.append([_.ts_ns for d in adc2_data for _ in d['data']['pba2_adc7']])
#    array_encoder.append([_.ts_ns for d in encoder_data for _ in d['data']['pb9_enc1']])

#    array_ion.append([_.adc for d in adc1_data for _ in d['data']['pba2_adc6']]) #db.get_table(run, stream_name='pba2_adc6',fill=True)
#    array_ion2.append([_.adc for d in adc2_data for _ in d['data']['pba2_adc7']]) #db.get_table(run, stream_name='pba2_adc7',fill=True)
#    array_encoder.append([_.encoder for d in encoder_data for _ in d['data']['pb9_enc1']]) #db.get_table(run, stream_name='pb9_enc1',fill=True)

#    array_ion = np.array(array_ion)
#    array_ion2 = np.array(array_ion2)
#    array_encoder = np.array(array_encoder)
#    array_encoder = array_encoder.astype(float)
#    print(array_ion)
#    print(len(array_encoder[0]))

#    for i in range(len(array_encoder[0])):
#        array_encoder[i, 2] = -12400 / (2 * 3.1356 * math.sin(math.radians(array_encoder[i, 2]/360000)))
#    array_ion, array_ion2, array_encoder = interpolate(array_ion, array_ion2, array_encoder, trunc=True)

#    result_ion = array_ion
#    result_ion[:,2] = np.log(array_ion[:,2] / array_ion2[:,2])

#    if set_to_0s:
#        result_ion[:,0] = result_ion[:,0] - result_ion[0,0] # Setting first timestamp position to 0 seconds
#        result_ion[:,1] = result_ion[:,1] - result_ion[0,1] # Setting first timestamp position to 0 seconds
#        array_encoder[:,0] = array_encoder[:,0] - array_encoder[0,0]
#        array_encoder[:,1] = array_encoder[:,1] - array_encoder[0,1]

#    plot_arrays([array_encoder, result_ion], colors, xlabel, ylabel, grid, xy_plot=True)


