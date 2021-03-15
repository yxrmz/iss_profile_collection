from ophyd import EpicsSignal,PVPositioner, EpicsSignalRO, EpicsMotor
from ophyd import Device, Component
from ophyd import DeviceStatus
import time
from xas.file_io import validate_file_exists
import sys
from matplotlib import pyplot as plt

class PPMAC_Bias1(Device):
    """
    A device with a setpoint and readback
    """
    readback = Component(EpicsSignalRO, '-I', kind='hinted')
    setpoint = Component(EpicsSignal, 'R-SP')
    
    def set(self, setpoint):
        """
        Set the setpoint and return a Status object that monitors the readback.
        """
        status = DeviceStatus(self)
        
        # Wire up a callback that will mark the status object as finished
        # when the readback approaches within some tolerance of the setpoint.
        def callback(old_value, value, **kwargs):
            TOLERANCE = 0.0008  # hard-coded; we'll make this configurable later on...
            if abs(value - setpoint) < TOLERANCE:
                status._finished()
                self.readback.clear_sub(callback)
            
        self.readback.subscribe(callback)
        
        # Now 'put' the value.
        self.setpoint.put(setpoint)

        # And return the Status object, which the caller can use to
        # tell when the action is complete.
        return status

pbias1 = PPMAC_Bias1('XF:08IDB-OP{MC:XBIC}DAC1', name='Bias Voltage')

# BU_012_150_500_S_5803842_IVscan.txt
def diamond_scan(fname, scantype, serialnumber, ampgains):
    # fname string, scantype string, serialnumber string, ampgains string 'x x x x'
    # Valid scantype strings are bias, linex, liney, raster
    print(f'{scantype} scan')
    fpath = '/nsls2/xf08id/Sandbox/ErikDiamond_090820/'
    
    # Set up plots
    f, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(15,12))
    # After plotting adjust sizes
    f.subplots_adjust(hspace=0.05)
    f.subplots_adjust(wspace=0.06)
    f.subplots_adjust(left=0.05, right=0.9, bottom=0.05, top=0.95)
    
    plt.ion()
    plt.show(block=False)
    plt.draw()
    
    ch5_vals = []
    ch6_vals = []
    ch7_vals = []
    ch8_vals = []
    xmotor_vals = []
    ymotor_vals = []
    bias_vals = []
    izero_vals = []
    itrans_vals = []
        
    if scantype=='bias':
        with open(validate_file_exists(fpath + fname), 'w') as f:
            try:
                # Write metadata here
                f.write(f'SN: {serialnumber}  \tAmp_gains {ampgains} \n ')
                f.write('Bias Voltage (V)\tIA(mV)\tIB(mV)\t(IC(mV)\tID(mV)\tI0(mV)\tIt(mV)\n')
                for j in np.linspace(0,1,11):
                    RE(bps.mv(pbias1, j/11 ))
                    time.sleep(0.1)
                    trigstatus = apb_ave.trigger()
                    while (trigstatus.done!=True):
                        time.sleep(0.01)
    
                    #bias = pbias1.read()['Bias Voltage_readback']['value']
                    pb_read_data = apb_ave.read()
                    pb_read_data5 = pb_read_data['apb_ave_ch5_mean']['value']
                    pb_read_data6 = pb_read_data['apb_ave_ch6_mean']['value']
                    pb_read_data7 = pb_read_data['apb_ave_ch7_mean']['value']
                    pb_read_data8 = pb_read_data['apb_ave_ch8_mean']['value']
                    # Channel I0
                    pb_read_data1 = pb_read_data['apb_ave_ch1_mean']['value']
                    # Channel IT
                    pb_read_data2 = pb_read_data['apb_ave_ch2_mean']['value']
                    pbias1_read_data = pbias1.read()['Bias Voltage_readback']['value']
    
                    print(f'Bias is {pbias1_read_data}')
    
                    f.write(f'{pbias1_read_data}\t' \
                        f'{pb_read_data5}\t{pb_read_data6}\t{pb_read_data7}\t{pb_read_data8}\t'\
                        f'{pb_read_data1}\t{pb_read_data2}\n')
                    
                    # append the data
                    ch5_vals.append(pb_read_data5)
                    ch6_vals.append(pb_read_data6)
                    ch7_vals.append(pb_read_data7)
                    ch8_vals.append(pb_read_data8)
                    bias_vals.append(pbias1_read_data)
                    izero_vals.append(pb_read_data1)
                    itrans_vals.append(pb_read_data2)

                                        
                    # update the plots
                    ax1.cla()
                    ax2.cla()
                    ax3.cla()
                    ax4.cla()
                    ax5.cla()
                    ax6.cla()
                    ax1.plot(bias_vals, ch5_vals)
                    ax2.plot(bias_vals, ch6_vals)
                    ax3.plot(bias_vals, ch7_vals)
                    ax4.plot(bias_vals, ch8_vals)
                    ax5.plot(bias_vals, izero_vals)
                    ax6.plot(bias_vals, itrans_vals)
                    
                    plt.draw()
                    plt.show(block=False)
            except:
                print('Unexpected Errror', sys.exc_info())
         
        
    elif scantype=='linex':
        with open(validate_file_exists(fpath + fname), 'w') as f:
            try:
                # Write metadata here
                f.write(f'SN: {serialnumber}  \tAmp_gains {ampgains} \n ')
                f.write('xmotor(mm)\tymotor(mm)\tBias Voltage(V)\tIA(mV)\tIB(mV)\t(IC(mV)\tID(mV)\tI0(mV)\tIt(mV)\n')
                for j in range(11):
                    RE(bps.mv(giantxy.x, j/11 ))
                    time.sleep(0.1)
                    trigstatus = apb_ave.trigger()
                    while (trigstatus.done!=True):
                        time.sleep(0.01)
    
                    #bias = pbias1.read()['Bias Voltage_readback']['value']
                    pb_read_data = apb_ave.read()
                    pb_read_data5 = pb_read_data['apb_ave_ch5_mean']['value']
                    pb_read_data6 = pb_read_data['apb_ave_ch6_mean']['value']
                    pb_read_data7 = pb_read_data['apb_ave_ch7_mean']['value']
                    pb_read_data8 = pb_read_data['apb_ave_ch8_mean']['value']
                    # Channel I0
                    pb_read_data1 = pb_read_data['apb_ave_ch1_mean']['value']
                    # Channel IT
                    pb_read_data2 = pb_read_data['apb_ave_ch2_mean']['value']
                    pbias1_read_data = pbias1.read()['Bias Voltage_readback']['value']
                    #Check this and edit as needed
                    xypos_read_data = giantxy.read()
                    x_read_data = xypos_read_data['x']['value']
                    y_read_data = xypos_read_data['y']['value']
    
                    print(f'Bias is {pbias1_read_data}')
    
                    f.write(f'{x_read_data}\t{y_read_data}\t{pbias1_read_data}\t' \
                        f'{pb_read_data5}\t{pb_read_data6}\t{pb_read_data7}\t{pb_read_data8}\t'\
                        f'{pb_read_data1}\t{pb_read_data2}\n')
                    
                    # append the data
                    ch5_vals.append(pb_read_data5)
                    ch6_vals.append(pb_read_data6)
                    ch7_vals.append(pb_read_data7)
                    ch8_vals.append(pb_read_data8)
                    #bias_vals.append(pbias1_read_data)
                    izero_vals.append(pb_read_data1)
                    itrans_vals.append(pb_read_data2)
                    xmotor_vals.append(x_read_data)
                    ymotor_vals.append(y_read_data)
                                        
                    # update the plots
                    ax1.cla()
                    ax2.cla()
                    ax3.cla()
                    ax4.cla()
                    ax5.cla()
                    ax6.cla()
                    ax1.plot(xmotor_vals, ch5_vals)
                    ax2.plot(xmotor_vals, ch6_vals)
                    ax3.plot(xmotor_vals, ch7_vals)
                    ax4.plot(xmotor_vals, ch8_vals)
                    ax5.plot(xmotor_vals, izero_vals)
                    ax6.plot(xmotor_vals, itrans_vals)
                    
                    plt.draw()
                    plt.show(block=False)
            except:
                print('Unexpected Errror', sys.exc_info())
          
    elif scantype=='liney':
        with open(validate_file_exists(fpath + fname), 'w') as f:
            try:
                # Write metadata here
                f.write(f'SN: {serialnumber}  \tAmp_gains {ampgains} \n ')
                f.write('xmotor(mm)\tymotor(mm)\tBias Voltage(V)\tIA(mV)\tIB(mV)\t(IC(mV)\tID(mV)\tI0(mV)\tIt(mV)\n')
                for j in range(11):
                    RE(bps.mv(giantxy.y, j/11 ))
                    time.sleep(0.1)
                    trigstatus = apb_ave.trigger()
                    while (trigstatus.done!=True):
                        time.sleep(0.01)
    
                    #bias = pbias1.read()['Bias Voltage_readback']['value']
                    pb_read_data = apb_ave.read()
                    pb_read_data5 = pb_read_data['apb_ave_ch5_mean']['value']
                    pb_read_data6 = pb_read_data['apb_ave_ch6_mean']['value']
                    pb_read_data7 = pb_read_data['apb_ave_ch7_mean']['value']
                    pb_read_data8 = pb_read_data['apb_ave_ch8_mean']['value']
                    # Channel I0
                    pb_read_data1 = pb_read_data['apb_ave_ch1_mean']['value']
                    # Channel IT
                    pb_read_data2 = pb_read_data['apb_ave_ch2_mean']['value']
                    pbias1_read_data = pbias1.read()['Bias Voltage_readback']['value']
                    #Check this and edit as needed
                    xypos_read_data = giantxy.read()
                    x_read_data = xypos_read_data['x']['value']
                    y_read_data = xypos_read_data['y']['value']
    
                    print(f'Bias is {pbias1_read_data}')
    
                    f.write(f'{x_read_data}\t{y_read_data}\t{pbias1_read_data}\t' \
                        f'{pb_read_data5}\t{pb_read_data6}\t{pb_read_data7}\t{pb_read_data8}\t'\
                        f'{pb_read_data1}\t{pb_read_data2}\n')
                    # append the data
                    ch5_vals.append(pb_read_data5)
                    ch6_vals.append(pb_read_data6)
                    ch7_vals.append(pb_read_data7)
                    ch8_vals.append(pb_read_data8)
                    #bias_vals.append(pbias1_read_data)
                    izero_vals.append(pb_read_data1)
                    itrans_vals.append(pb_read_data2)
                    xmotor_vals.append(x_read_data)
                    ymotor_vals.append(y_read_data)
                                        
                    # update the plots
                    ax1.cla()
                    ax2.cla()
                    ax3.cla()
                    ax4.cla()
                    ax5.cla()
                    ax6.cla()
                    ax1.plot(ymotor_vals, ch5_vals)
                    ax2.plot(ymotor_vals, ch6_vals)
                    ax3.plot(ymotor_vals, ch7_vals)
                    ax4.plot(ymotor_vals, ch8_vals)
                    ax5.plot(ymotor_vals, izero_vals)
                    ax6.plot(ymotor_vals, itrans_vals)
                    
                    plt.draw()
                    plt.show(block=False)
            except:
                print('Unexpected Errror', sys.exc_info())
                    
                    
    elif scantype=='raster':
        with open(validate_file_exists(fpath + fname), 'w') as f:
            try: 
                # Write metadata here
                f.write(f'SN: {serialnumber}  \tAmp_gains {ampgains} \n ')
                f.write('xmotor(mm)\tymotor(mm)\tBias Voltage(V)\tIA(mV)\tIB(mV)\t(IC(mV)\tID(mV)\tI0(mV)\tIt(mV)\n')
                for j in range(11):
                    RE(bps.mv(giantxy.y, j/11 ))
                    for i in range(11):
                        RE(bps.mv(giantxy.x, i/11 ))
                        time.sleep(0.1)
                        trigstatus = apb_ave.trigger()
                        while (trigstatus.done!=True):
                            time.sleep(0.01)
        
                        #bias = pbias1.read()['Bias Voltage_readback']['value']
                        pb_read_data = apb_ave.read()
                        pb_read_data5 = pb_read_data['apb_ave_ch5_mean']['value']
                        pb_read_data6 = pb_read_data['apb_ave_ch6_mean']['value']
                        pb_read_data7 = pb_read_data['apb_ave_ch7_mean']['value']
                        pb_read_data8 = pb_read_data['apb_ave_ch8_mean']['value']
                        # Channel I0
                        pb_read_data1 = pb_read_data['apb_ave_ch1_mean']['value']
                        # Channel IT
                        pb_read_data2 = pb_read_data['apb_ave_ch2_mean']['value']
                        pbias1_read_data = pbias1.read()['Bias Voltage_readback']['value']
                        #Check this and edit as needed
                        xypos_read_data = giantxy.read()
                        x_read_data = xypos_read_data['x']['value']
                        y_read_data = xypos_read_data['y']['value']
        
                        print(f'Bias is {pbias1_read_data}')
        
                        f.write(f'{x_read_data}\t{y_read_data}\t{pbias1_read_data}\t' \
                            f'{pb_read_data5}\t{pb_read_data6}\t{pb_read_data7}\t{pb_read_data8}\t'\
                            f'{pb_read_data1}\t{pb_read_data2}\n')
                        
                        # append the data
                        ch5_vals.append(pb_read_data5)
                        ch6_vals.append(pb_read_data6)
                        ch7_vals.append(pb_read_data7)
                        ch8_vals.append(pb_read_data8)
                        #bias_vals.append(pbias1_read_data)
                        izero_vals.append(pb_read_data1)
                        itrans_vals.append(pb_read_data2)
                        xmotor_vals.append(x_read_data)
                        ymotor_vals.append(y_read_data)
                                            
                        # update the plots
                        ax1.cla()
                        ax2.cla()
                        ax3.cla()
                        ax4.cla()
                        ax5.cla()
                        ax6.cla()
                        ax1.plot(xmotor_vals, ch5_vals)
                        ax2.plot(xmotor_vals, ch6_vals)
                        ax3.plot(xmotor_vals, ch7_vals)
                        ax4.plot(xmotor_vals, ch8_vals)
                        ax5.plot(xmotor_vals, izero_vals)
                        ax6.plot(xmotor_vals, itrans_vals)
                        
                        plt.draw()
                        plt.show(block=False)
            except:
                print('Unexpected Errror', sys.exc_info())
    else:
        print('Not a valid scan type for 2nd argument')
