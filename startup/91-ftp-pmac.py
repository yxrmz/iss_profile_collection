import sys
import subprocess
import os

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def send_motion_file(orig_file_name, new_file_name = '', orig_file_path = '/GPFS/xf08id/pizza_box_data/', new_file_path = '10', ip = '10.8.2.86'):
    
    # Create ftp connection with default credential
    from ftplib import FTP
    ftp = FTP(ip)
    ftp.login()
    s = pxssh.pxssh()
    s.login (ip, 'root', 'deltatau')

    # Check if the directory exists in '/usrflash/lut/. If it does not, create it.'
    if new_file_path != '':
        ftp.cwd('/usrflash/lut/')
        dir_list = ftp.nlst()
        dir_exists = 0
        for dir_name in dir_list:
            if dir_name == new_file_path:
                dir_exists = 1
        if not dir_exists:
            print('mkdir:', '/usrflash/lut/' + new_file_path)
            ftp.mkd('/usrflash/lut/' + new_file_path)
            s.sendline ('chown ftp:root /var/ftp/usrflash/lut/' + new_file_path)
            s.sendline ('chmod a+wrx /var/ftp/usrflash/lut/' + new_file_path)

    # Check if the file already exists in the controller 
    ftp.cwd('/usrflash/lut/' + new_file_path + '/')
    file_list = ftp.nlst()
    file_exists = 0
    if new_file_name == '':
        new_file_name = orig_file_name
    for file_name in file_list:
        if file_name == new_file_name:
            file_exists = 1
    if file_exists == 1:
        if query_yes_no('File "' + new_file_name +'" already exists in the controller. Would you like to replace it?'):
            ftp.delete(new_file_name)
        else:
            print('File already exists, try other name or directory.')
            ftp.close()
            return False

    # Open file and transfer to the power pmac
    f = open(orig_file_path + str(orig_file_name), 'rb')
    if(f.readable()):
        result = ftp.storbinary('STOR ' + '/usrflash/lut/' + new_file_path + '/' + new_file_name, f)
        if(result == '226 File receive OK.'):
            s.sendline ('chown ftp:root /var/ftp/usrflash/lut/' + new_file_path + '/' + new_file_name)
            #sleep(0.1)
            s.sendline ('chmod a+wrx /var/ftp/usrflash/lut/' + new_file_path + '/' + new_file_name)
            sleep(0.001)
            print('File sent successfully')
            ftp.close()

