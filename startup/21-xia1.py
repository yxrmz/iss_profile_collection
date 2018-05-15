import time as ttime

class ROI(Device):
    low =               Cpt(EpicsSignal, 'LO')
    high =              Cpt(EpicsSignal, 'HI')
    sum =               Cpt(EpicsSignal, '')
    net =               Cpt(EpicsSignal, 'N')
    label =             Cpt(EpicsSignal, 'NM')

class MCA(Device):
    array =             Cpt(EpicsSignal, '')
    roi0 =              Cpt(ROI, '.R0')
    roi1 =              Cpt(ROI, '.R1')
    roi2 =              Cpt(ROI, '.R2')
    roi3 =              Cpt(ROI, '.R3')
    roi4 =              Cpt(ROI, '.R4')
    roi5 =              Cpt(ROI, '.R5')
    roi6 =              Cpt(ROI, '.R6')
    roi7 =              Cpt(ROI, '.R7')
    roi8 =              Cpt(ROI, '.R8')
    roi9 =              Cpt(ROI, '.R9')
    roi10 =             Cpt(ROI, '.R10')
    roi11 =             Cpt(ROI, '.R11')
            

class XIA(Device):
    graph1 =           Cpt(EpicsSignal, 'mca1.VAL')
    graph2 =           Cpt(EpicsSignal, 'mca2.VAL')
    graph3 =           Cpt(EpicsSignal, 'mca3.VAL')
    graph4 =           Cpt(EpicsSignal, 'mca4.VAL')
    mode =             Cpt(EpicsSignal, 'PresetMode')
    collect_mode =     Cpt(EpicsSignal, 'CollectMode')
    start_sig =        Cpt(EpicsSignal, 'StartAll')
    stop_sig =         Cpt(EpicsSignal, 'StopAll')
    erase_start =      Cpt(EpicsSignal, 'EraseStart')
    erase =            Cpt(EpicsSignal, 'EraseAll')
    acquiring =        Cpt(EpicsSignalRO, 'Acquiring')
    polarity = 'pos'

    capt_start_stop =  Cpt(EpicsSignal, 'netCDF1:Capture_RBV', write_pv='netCDF1:Capture')
    pixels_per_run =   Cpt(EpicsSignal, 'PixelsPerRun')
    current_pixel =    Cpt(EpicsSignal, 'dxp1:CurrentPixel')
    next_pixel =       Cpt(EpicsSignal, 'NextPixel')
    pix_per_buf_auto = Cpt(EpicsSignal, 'AutoPixelsPerBuffer')
    pix_per_buf_set =  Cpt(EpicsSignal, 'PixelsPerBuffer')
    pix_per_buf_rb =   Cpt(EpicsSignal, 'PixelsPerBuffer_RBV') 

    pre_amp_gain1 = Cpt(EpicsSignal, 'dxp1:PreampGain')
    pre_amp_gain2 = Cpt(EpicsSignal, 'dxp2:PreampGain')
    pre_amp_gain3 = Cpt(EpicsSignal, 'dxp3:PreampGain')
    pre_amp_gain4 = Cpt(EpicsSignal, 'dxp4:PreampGain')
    pre_amp_gain5 = Cpt(EpicsSignal, 'dxp5:PreampGain')
    pre_amp_gain6 = Cpt(EpicsSignal, 'dxp6:PreampGain')
    pre_amp_gain7 = Cpt(EpicsSignal, 'dxp7:PreampGain')
    pre_amp_gain8 = Cpt(EpicsSignal, 'dxp8:PreampGain')
    pre_amp_gain9 = Cpt(EpicsSignal, 'dxp9:PreampGain')
    pre_amp_gain10 = Cpt(EpicsSignal, 'dxp10:PreampGain')
    pre_amp_gain11 = Cpt(EpicsSignal, 'dxp11:PreampGain')
    pre_amp_gain12 = Cpt(EpicsSignal, 'dxp12:PreampGain')
    pre_amp_gain13 = Cpt(EpicsSignal, 'dxp13:PreampGain')
    pre_amp_gain14 = Cpt(EpicsSignal, 'dxp14:PreampGain')
    pre_amp_gain15 = Cpt(EpicsSignal, 'dxp15:PreampGain')
    pre_amp_gain16 = Cpt(EpicsSignal, 'dxp16:PreampGain')

    real_time =        Cpt(EpicsSignal, 'PresetReal')
    real_time_rb =     Cpt(EpicsSignal, 'ElapsedReal')
    live_time =        Cpt(EpicsSignal, 'PresetLive')
    live_time_rb =     Cpt(EpicsSignal, 'ElapsedLive')

    mca1 =             Cpt(MCA, 'mca1')
    mca2 =             Cpt(MCA, 'mca2')
    mca3 =             Cpt(MCA, 'mca3')
    mca4 =             Cpt(MCA, 'mca4')
    mca5 =             Cpt(MCA, 'mca5')
    mca6 =             Cpt(MCA, 'mca6')
    mca7 =             Cpt(MCA, 'mca7')
    mca8 =             Cpt(MCA, 'mca8')
    mca9 =             Cpt(MCA, 'mca9')
    mca10 =             Cpt(MCA, 'mca10')
    mca11 =             Cpt(MCA, 'mca11')
    mca12 =             Cpt(MCA, 'mca12')
    mca13 =             Cpt(MCA, 'mca13')
    mca14 =             Cpt(MCA, 'mca14')
    mca15 =             Cpt(MCA, 'mca15')
    mca16 =             Cpt(MCA, 'mca16')


    mca_array1 =       Cpt(EpicsSignal, 'mca1')
    mca_array2 =       Cpt(EpicsSignal, 'mca2')
    mca_array3 =       Cpt(EpicsSignal, 'mca3')
    mca_array4 =       Cpt(EpicsSignal, 'mca4')
    mca_array5 =       Cpt(EpicsSignal, 'mca5')
    mca_array6 =       Cpt(EpicsSignal, 'mca6')
    mca_array7 =       Cpt(EpicsSignal, 'mca7')
    mca_array8 =       Cpt(EpicsSignal, 'mca8')
    mca_array9 =       Cpt(EpicsSignal, 'mca9')
    mca_array10 =       Cpt(EpicsSignal, 'mca10')
    mca_array11 =       Cpt(EpicsSignal, 'mca11')
    mca_array12 =       Cpt(EpicsSignal, 'mca12')
    mca_array13 =       Cpt(EpicsSignal, 'mca13')
    mca_array14 =       Cpt(EpicsSignal, 'mca14')
    mca_array15 =       Cpt(EpicsSignal, 'mca15')
    mca_array16 =       Cpt(EpicsSignal, 'mca16')

    mca_x =            Cpt(EpicsSignal, 'dxp1:Graph0X.AVAL')
    mca_max_energy = Cpt(EpicsSignal, 'dxp1:Graph0High')

    netcdf_filename = Cpt(EpicsSignal, 'netCDF1:FileName')
    netcdf_filename_rb = Cpt(EpicsSignal, 'netCDF1:FileName_RBV')
    netcdf_filenumber = Cpt(EpicsSignal, 'netCDF1:FileNumber')
    netcdf_filenumber_rb = Cpt(EpicsSignal, 'netCDF1:FileNumber_RBV')

    
    def start_trigger(self):
        yield from bps.abs_set(pb4.do0.enable, 1, wait=True)

    def stop_trigger(self):
        yield from bps.abs_set(pb4.do0.enable, 0, wait=True)

    def start_mapping_scan(self):
        yield from bps.abs_set(self.collect_mode, 'MCA mapping', wait=True)
        #self.collect_mode.put('MCA mapping')
        yield from bps.sleep(.25)
        #ttime.sleep(0.25)
        yield from bps.abs_set(pb4.do0.dutycycle_sp, 50, wait=True)
        yield from bps.abs_set(self.capt_start_stop, 1, wait=True)
        #self.capt_start_stop.put(1)
        yield from bps.abs_set(self.erase_start, 1, wait=True)
        #self.erase_start.put(1)
        yield from bps.sleep(1)
        #ttime.sleep(1)
        yield from bps.abs_set(pb4.do0.enable, 1, wait=True)
        #pb4.do0.enable.put(1) # Workaround
        return self._status

    def stop_scan(self):
        yield from bps.abs_set(pb4.do0.enable, 0, wait=True)
        while(pb4.do0.enable.value):
            pass
        #pb4.do0.enable.put(0) # Workaround
        yield from bps.sleep(1.5)
        yield from bps.abs_set(self.stop_sig, 1, wait=True)
        #self.stop_sig.put(1)
        yield from bps.sleep(0.5)
        #ttime.sleep(0.5)
        yield from bps.abs_set(self.capt_start_stop, 0, wait=True)
        #self.capt_start_stop.put(0)

    def __init__(self, *args, **kwargs):
        # link trigger to xia object
        if 'input_trigger' in kwargs:
            self.input_trigger = kwargs['input_trigger']#pb4.do0
            del kwargs['input_trigger']
        super().__init__(*args, **kwargs)
        self.stage_sigs[self.mode] = 'Real time'
        self._status = None

        self.mcas = [self.mca1, self.mca2, self.mca3, self.mca4, 
                self.mca5, self.mca6, self.mca7, self.mca8,
                self.mca9, self.mca10, self.mca11, self.mca12,
                self.mca13, self.mca14, self.mca15, self.mca16]


    def goto_next_pixel(self):
        self.next_pixel.put(1)

    def stage(self):
        self.collect_mode.put('MCA spectra')
        self.acquiring.subscribe(self._acquiring_changed)
        #pass

    def unstage(self):
        self.acquiring.clear_sub(self._acquiring_changed)
        #pass
        
    #def read(self):
        

    def trigger(self):
        self._status = DeviceStatus(self)
        ttime.sleep(0.1)
        self.erase_start.put(1)
        #pb4.do0.enable.put(1) # Workaround
        return self._status

    def _acquiring_changed(self, value=None, old_value=None, **kwargs):
        "This is run every time the value of 'acquiring' changes."
        if self._status is None:
            # We have not triggered anything; ignore this one.
            return
        if (old_value == 1) and (value == 0):
            # 'acquiring' has flipped from 'Acquiring' to 'Done'.
            #pb4.do0.enable.put(0) # Workaround
            self._status._finished()
           

xia1 = XIA('XF:08IDB-OP{XMAP}', name='xia1', input_trigger=pb4.do0)

xia1.read_attrs = []

for mca in xia1.mcas:
    if mca.connected:
        xia1.read_attrs.append(mca.name.split('_')[1])

list1 = [mca.name for mca in xia1.mcas]
list2 = ['roi{}'.format(number) for number in range(12)]

xia_list = ['{}_{}_sum'.format(x,y) for x in list1 for y in list2]

