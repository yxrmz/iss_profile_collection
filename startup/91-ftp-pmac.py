import sys
import subprocess
import os
import time as ttime
import pexpect
from pexpect import pxssh
from ftplib import FTP

# Function used to count the number of lines in a file
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


########## trajectory_load ##########
# Transfer the trajectory file to the motor controller
# arg1 = orig_file_name 			-> Filename of the trajectory: E.g.: 'traj_Cu_fast.txt'
# arg2 = new_file_path  			-> LUT number where the new trajectory file will be stored
# arg3 (optional) = new_file_name 	-> New name that will be used as filename in the controller. Currently, it MUST be 'hhm.txt'
# arg4 (optional) = orig_file_path 	-> Path to look for the file that will be transfered. Default = '/GPFS/xf08id/trajectory/'
# arg5 (optional) = ip 				-> IP of the controller that will receive the file. Default = '10.8.2.86'
def trajectory_load(orig_file_name, new_file_path, new_file_name = 'hhm.txt', orig_file_path = '/GPFS/xf08id/trajectory/', ip = '10.8.2.86'):
   
    # Check if new_file_path is between the possible values
    if int(new_file_path) > 9 or int(new_file_path) < 1:
        print("Path '{}' not possible. Please use a value in the range 1 <= new_file_path <= 9.".format(new_file_path))
        return False
   
    # Get number of lines in file
    file_size = file_len(orig_file_path + orig_file_name)
    print('Number of lines in file: {}'.format(file_size))

    # Create ftp connection with default credential
    ftp = FTP(ip)
    ftp.login()
    s = pxssh.pxssh()
    s.login (ip, 'root', 'deltatau')

    # Check if the directory exists in '/usrflash/lut/. If it does not, create it.'
    if str(new_file_path) != '':
        ftp.cwd('/usrflash/lut/')
        dir_list = ftp.nlst()
        dir_exists = 0
        for dir_name in dir_list:
            if dir_name == str(new_file_path):
                dir_exists = 1
        if not dir_exists:
            print('mkdir: /usrflash/lut/{}'.format(new_file_path))
            ftp.mkd('/usrflash/lut/{}'.format(new_file_path))
            s.sendline ('chown ftp:root /var/ftp/usrflash/lut/{}'.format(new_file_path))
            s.sendline ('chmod a+wrx /var/ftp/usrflash/lut/{}'.format(new_file_path))

    ftp_file_path = '/var/ftp/usrflash/lut/{}/{}'.format(new_file_path, new_file_name)# + str(new_file_path) + '/' + new_file_name

    # Open file and transfer to the power pmac
    f = open(orig_file_path + str(orig_file_name), 'rb')
    if(f.readable()):
        result = ftp.storbinary('STOR ' + '/usrflash/lut/' + str(new_file_path) + '/' + new_file_name, f)
        if(result == '226 File receive OK.'):
            s.sendline ('chown ftp:root /var/ftp/usrflash/lut/{}/{}'.format(new_file_path, new_file_name))
            s.sendline ('chmod a+wrx /var/ftp/usrflash/lut/{}/{}'.format(new_file_path, new_file_name))
            s.sendline ('echo "{}\n{}" > /var/ftp/usrflash/lut/{}/hhm-size.txt'.format(file_size, orig_file_name, new_file_path))
            sleep(0.01)
            ftp.close()

    print('File sent successfully')
    return True


########## trajectory_init ##########
# Transfer the trajectory from the flash to the ram memory in the controller
# It must be called everytime you decide to use a different trajectory
# arg1 = lut_number				-> lookup table number of the trajectory that will be used - must be a number between 1 and 9
# arg2 (optional) = ip			-> IP of the controller that will receive the file. Default = '10.8.2.86'
# arg3 (optional) = filename	-> Filename of the trajectory file in the controller. Currently, it MUST be 'hhm.txt'
def trajectory_init(lut_number, ip = '10.8.2.86', filename = 'hhm.txt'):

	hhm.lut_number.put(lut_number)

	ttime.sleep(0.1)
	while (hhm.lut_number_rbv.value != lut_number):
		ttime.sleep(.01)

	hhm.lut_start_transfer.put("1")	
	while (hhm.lut_transfering.value == 0):
		ttime.sleep(.01)
	while (hhm.lut_transfering.value == 1):
		ttime.sleep(.01)

	ftp = FTP(ip)
	ftp.login()
	ftp.cwd('/usrflash/lut/{}'.format(lut_number))

	file_list = ftp.nlst()
	file_exists = 0
	for file_name in file_list:
		if file_name == filename:
			file_exists = 1
	if file_exists == 0:
		print('File not found. :(\nAre you sure \'{}\' is the correct lut number?'.format(lut_number))
	else:
		info = []
		def handle_binary(more_data):
			info.append(more_data)

		resp = ftp.retrlines('RETR hhm-size.txt', callback=handle_binary)
		if(len(info) == 2):
			size = int(info[0])
			name = info[1]
		else:
			print('Could not find the size and name info in the controller. Please, try sending the trajectory file again using trajectory_load(...)')	
			return False

		if(size == 0):
			print('Size seems to be equal to 0. Please, try sending the trajectory file again using trajectory_load(...)')
			return False
		else:
			hhm.cycle_limit.put(size)
			while (hhm.cycle_limit_rbv.value != size):
				ttime.sleep(.01)
			print('Transfer completed!\nNew lut number: {}\nTrajectory name: {}\nNumber of points: {}'.format(lut_number, name, size))
			return True

########## trajectory_read_info ##########
# Function that prints info about the trajectories currently stored in the controller
# arg1 (optional) = ip	-> IP of the controller. Default = '10.8.2.86'
def trajectory_read_info(ip = '10.8.2.86'):
	ftp = FTP(ip)
	ftp.login()
	ftp.cwd('/usrflash/lut/')
	print('-'*62)
	print('The trajectories found in the controller (ip: {}) are:'.format(ip))

	def handle_binary(more_data):
		info.append(more_data)

	for i in range(1, 10):
		ftp.cwd('/usrflash/lut/{}'.format(i))

		info = []
		
		resp = ftp.retrlines('RETR hhm-size.txt', callback=handle_binary)
		if(len(info) == 2):
			size = int(info[0])
			name = info[1]
			print('{}: {:<24} (Size: {})'.format(i, name, size))
		else:
			print('{}: Could not find the size and name info'.format(i))	

	print('-'*62)




