import sys
import subprocess
import os
import time as ttime
import pexpect
from pexpect import pxssh
from ftplib import FTP

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def trajectory_load(orig_file_name, new_file_path, new_file_name = 'hhm.txt', orig_file_path = '/GPFS/xf08id/trajectory/', ip = '10.8.2.86'):
    
	# Check if new_file_path is between the possible values
    if int(new_file_path) >= 10 or int(new_file_path) <= 0:
        print("Path '{}' not possible. Please use a value in the range 1 <= new_file_path <= 9.".format(new_file_path))
        return False
	
    # Get number of lines in file
    file_size = file_len(orig_file_path + orig_file_name)
    print('Number of lines in file:', file_size)

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
            print('mkdir:', '/usrflash/lut/' + str(new_file_path))
            ftp.mkd('/usrflash/lut/' + str(new_file_path))
            s.sendline ('chown ftp:root /var/ftp/usrflash/lut/' + str(new_file_path))
            s.sendline ('chmod a+wrx /var/ftp/usrflash/lut/' + str(new_file_path))

    ftp_file_path = '/var/ftp/usrflash/lut/' + str(new_file_path) + '/' + new_file_name 
    # Open file and transfer to the power pmac
    f = open(orig_file_path + str(orig_file_name), 'rb')
    if(f.readable()):
        result = ftp.storbinary('STOR ' + '/usrflash/lut/' + str(new_file_path) + '/' + new_file_name, f)
        if(result == '226 File receive OK.'):
            s.sendline ('chown ftp:root /var/ftp/usrflash/lut/' + str(new_file_path) + '/' + new_file_name)
            s.sendline ('chmod a+wrx /var/ftp/usrflash/lut/' + str(new_file_path) + '/' + new_file_name)
            sleep(0.001)
            ftp.close()

    print('File sent successfully')
    return True


def trajectory_init(lut_number, ip = '10.8.2.86', filename = 'hhm.txt'):

	class Reader:
		def __init__(self):
			self.rows = 0
		def __call__(self,s):
			self.rows += 1

	hhm.lut_number.put(lut_number)

	ttime.sleep(0.2)
	while (hhm.lut_number_rbv.value != lut_number):
		ttime.sleep(.1)

	hhm.lut_start_transfer.put("1")	
	while (hhm.lut_transfering.value == 0):
		ttime.sleep(.1)
	while (hhm.lut_transfering.value == 1):
		ttime.sleep(.1)

	ftp = FTP(ip)
	ftp.login()
	ftp.cwd('/usrflash/lut/' + str(lut_number))

	file_list = ftp.nlst()
	file_exists = 0
	for file_name in file_list:
		if file_name == filename:
			file_exists = 1
	if file_exists == 0:
		print('File not found. :(\nAre you sure this is the correct lut number?')
	else:
		r = Reader()
		ftp.retrlines('RETR ' + filename, r)
		hhm.cycle_limit.put(r.rows)
		while (hhm.cycle_limit_rbv.value != r.rows):
			ttime.sleep(.1)
		print('Transfer completed!\nNew lut number: ' + str(lut_number) + '\nNumber of points: ' + str(r.rows))
		






