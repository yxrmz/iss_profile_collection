import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
import math

def parse_file(file_name, array_out):
    with open('/GPFS/xf08id/pizza_box_data/' + str(file_name)) as f:
        #print('/GPFS/xf08id/pizza_box_data/' + str(file_name))
        ts, tn, enc, count, digital = [int(x) for x in next(f).split()] # read first line
        if "clear" in dir(array_out):
            array_out += []
            array_out.clear()
        else:
            print('Your array should be a list, just define it: my_array = []')
            return
        for line in f: # read rest of lines
            array_out.append([int(x) for x in line.split()])


# Usage: bigger_array = interpolate(bigger_array, smaller_array)
#def interpolate(bigger_array, smaller_array):
#    array_interp = np.copy(smaller_array)
#    array_interp2 = np.copy(bigger_array)
#    array_interp[:,2] = np.interp(array_interp[:,0] + array_interp[:,1]*1e-9, array_interp2[:,0] + array_interp2[:,1]*1e-9, array_interp2[:,2])
#    return array_interp



def interpolate(array1, array2, array3 = []):
    array_interp = np.copy(array1)
    array_interp2 = np.copy(array2)
    if(len(array3)):
        min_timestamp = np.array([array1[0,0] + array1[0,1] * 1e-9, array2[0,0] + array2[0,1] * 1e-9, array3[0,0] + array3[0,1] * 1e-9]).min()
        max_timestamp = np.array([array1[len(array1)-1,0] + array1[len(array1)-1,1] * 1e-9, array2[len(array2)-1,0] + array2[len(array2)-1,1] * 1e-9, array3[len(array3)-1,0] + array3[len(array3)-1,1] * 1e-9]).max()
    else:
        min_timestamp = np.array([array1[0,0] + array1[0,1] * 1e-9, array2[0,0] + array2[0,1] * 1e-9]).min()
        max_timestamp = np.array([array1[len(array1)-1,0] + array1[len(array1)-1,1] * 1e-9, array2[len(array2)-1,0] + array2[len(array2)-1,1] * 1e-9]).max()
    timestamps = np.arange(min_timestamp, max_timestamp, 0.0001)
    timestamps_sec = np.copy(timestamps)
    timestamps_nano = np.copy(timestamps)
    for i in range(len(timestamps)):
        timestamps_sec[i] = math.trunc(timestamps[i])
        timestamps_nano[i] = (timestamps[i] - timestamps_sec[i]) * 1e9
    new_array_interp = np.array([timestamps_sec, timestamps_nano, np.interp(timestamps, array_interp2[:,0] + array_interp2[:,1]*1e-9, array_interp2[:,2])]).transpose()
    array_return = np.zeros((len(new_array_interp), 5))
    array_return[:,:-2] = new_array_interp
    return array_return





# Calc mean between two arrays (Y):
def mean_array(test, test3):
    return ((test + test3)/2)
 
def plot_arrays(arrays, colors=['b', 'g', 'r', 'y'], xlabel='Time Stamp (s)', ylabel='', grid=True):
    index = 0
    for x in arrays:
        plt.plot(x[:,0] + x[:,1] * 1e-9, x[:,2], colors[index])
        index += 1
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(grid)

# yu_yd = test_yu
# yu_yd[:,2] = test_yu[:,2] - test_yd[:,2]
# yu_yd = yu_yd.astype(float)
# yu_yd[:,2] = yu_yd[:,2] * 1e-8

# pitch = yu_yd
# for x in range(len(yu_yd)):
#     pitch[x, 2] = (math.atan(yu_yd[x, 2]))
# 
# plt.plot(pitch[:,0] + pitch[:,1]*1e-9, pitch[:,2], 'r')
# plt.xlabel('Time Stamp (s)')
# plt.ylabel('Pitch (rad)')
# plt.grid(True)

def plot_pitch(yu_file, ydo_file, ydi_file): #(ydi_file, ydo_file, yu_file)
    print('Plotting Pitch...')
    array_ydi, array_ydo, array_yu = [], [], []
    parse_file(ydi_file, array_ydi)
    parse_file(ydo_file, array_ydo)
    parse_file(yu_file, array_yu)
    test_ydi, test_ydo, test_yu = np.array(array_ydi), np.array(array_ydo), np.array(array_yu)
    test_ydo_interp = interpolate(test_ydi, test_ydo, test_yu)
    test_ydi_interp = interpolate(test_ydo, test_ydi, test_yu)
    test_yu_interp = interpolate(test_ydo, test_yu, test_ydi)
    mean_yd = mean_array(test_ydi_interp, test_ydo_interp)
    mean_yd[:,0] = test_ydi_interp[:,0]
    mean_yd[:,1] = test_ydi_interp[:,1]
    #mean_yd = mean_yd.astype(float)
    #mean_yd[:,2] = mean_yd[:,2]*1e-8
    #test_yu = interpolate(test_yu, mean_yd)
    pitch = mean_yd
    pitch[:,2] = mean_yd[:,2] - test_yu_interp[:,2]
    pitch = pitch.astype(float)
    pitch[:,2] = pitch[:,2] * 1e-8
    for x in range(len(pitch)):
        pitch[x, 2] = (math.atan(pitch[x, 2]/1.020)) # USING 1,0195 BECAUSE IT MADE THE GRAPHS GOOD LOOKING :)
    pitch[:, 2] = pitch[:, 2] * 1e6
    pitch[:,0] = pitch[:,0] - pitch[0,0] # Setting first timestamp position to 0 seconds
    pitch[:,1] = pitch[:,1] - pitch[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([pitch], ['b'], ylabel='Pitch (urad)')


def plot_roll(ydo_file, ydi_file):
    print('Plotting Roll...')
    array_ydi, array_ydo, array_yu = [], [], []
    parse_file(ydi_file, array_ydi)
    parse_file(ydo_file, array_ydo)
    test_ydi, test_ydo = np.array(array_ydi), np.array(array_ydo)
    test_ydi_interp = interpolate(test_ydo, test_ydi)
    test_ydo_interp = interpolate(test_ydi, test_ydo)
    roll = test_ydi_interp
    roll[:,2] = test_ydi_interp[:,2] - test_ydo_interp[:,2]
    roll = roll.astype(float)
    roll[:,2] = roll[:,2] * 1e-8
    for x in range(len(roll)):
        roll[x, 2] = (math.atan(roll[x, 2]/0.4))
    roll[:, 2] = roll[:, 2] * 1e6 
    roll[:,0] = roll[:,0] - roll[0,0] # Setting first timestamp position to 0 seconds
    roll[:,1] = roll[:,1] - roll[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([roll], ['r'], ylabel='Roll (urad)')

def plot_y(yu_file, ydo_file, ydi_file):
    print('Plotting Y...')
    array_ydi, array_ydo, array_yu = [], [], []
    parse_file(ydi_file, array_ydi)
    parse_file(ydo_file, array_ydo)
    parse_file(yu_file, array_yu)
    test_ydi, test_ydo, test_yu = np.array(array_ydi), np.array(array_ydo), np.array(array_yu)
    test_ydo_interp = interpolate(test_ydi, test_ydo, test_yu)
    test_ydi_interp = interpolate(test_ydo, test_ydi, test_yu)
    test_yu_interp = interpolate(test_ydo, test_yu, test_ydi)
    mean_yd = mean_array(test_ydi_interp, test_ydo_interp)
    mean_yd[:,0] = test_ydi_interp[:,0]
    mean_yd[:,1] = test_ydi_interp[:,1]
    #test_yu = interpolate(test_yu, mean_yd)
    mean_y = mean_array(mean_yd, test_yu_interp)
    mean_y[:,0] = test_yu_interp[:,0]
    mean_y[:,1] = test_yu_interp[:,1]
    mean_y = mean_y.astype(float)
    mean_y[:,2] = -mean_y[:,2] * 1e-5
    mean_y[:,0] = mean_y[:,0] - mean_y[0,0] # Setting first timestamp position to 0 seconds
    mean_y[:,1] = mean_y[:,1] - mean_y[0,1] # Setting first timestamp position to 0 seconds
    plot_arrays([mean_y], 'g', ylabel='Y (mm)')

