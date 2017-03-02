import time as ttime

class MCA(Device):
    array =            Cpt(EpicsSignal, '')
    roi0_lo =          Cpt(EpicsSignal, '.R0LO')
    roi0_hi =          Cpt(EpicsSignal, '.R0HI')
    roi0_sum =          Cpt(EpicsSignal, '.R0')
    roi0_net =          Cpt(EpicsSignal, '.R0N')
    roi1_lo =          Cpt(EpicsSignal, '.R1LO')
    roi1_hi =          Cpt(EpicsSignal, '.R1HI')
    roi1_sum =          Cpt(EpicsSignal, '.R1')
    roi1_net =          Cpt(EpicsSignal, '.R1N')
    roi2_lo =          Cpt(EpicsSignal, '.R2LO')
    roi2_hi =          Cpt(EpicsSignal, '.R2HI')
    roi2_sum =          Cpt(EpicsSignal, '.R2')
    roi2_net =          Cpt(EpicsSignal, '.R2N')
    roi3_lo =          Cpt(EpicsSignal, '.R3LO')
    roi3_hi =          Cpt(EpicsSignal, '.R3HI')
    roi3_sum =          Cpt(EpicsSignal, '.R3')
    roi3_net =          Cpt(EpicsSignal, '.R3N')
    roi4_lo =          Cpt(EpicsSignal, '.R4LO')
    roi4_hi =          Cpt(EpicsSignal, '.R4HI')
    roi4_sum =          Cpt(EpicsSignal, '.R4')
    roi4_net =          Cpt(EpicsSignal, '.R4N')
    roi5_lo =          Cpt(EpicsSignal, '.R5LO')
    roi5_hi =          Cpt(EpicsSignal, '.R5HI')
    roi5_sum =          Cpt(EpicsSignal, '.R5')
    roi5_net =          Cpt(EpicsSignal, '.R5N')

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

    capt_start_stop =  Cpt(EpicsSignal, 'netCDF1:Capture')
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

    real_time =        Cpt(EpicsSignal, 'PresetReal')
    real_time_rb =     Cpt(EpicsSignal, 'ElapsedReal')
    live_time =        Cpt(EpicsSignal, 'PresetLive')
    live_time_rb =     Cpt(EpicsSignal, 'ElapsedLive')

    mca1 =             Cpt(MCA, 'mca1')
    mca2 =             Cpt(MCA, 'mca2')
    mca3 =             Cpt(MCA, 'mca3')
    mca4 =             Cpt(MCA, 'mca4')

    mca_array1 =       Cpt(EpicsSignal, 'mca1')
    mca_array2 =       Cpt(EpicsSignal, 'mca2')
    mca_array3 =       Cpt(EpicsSignal, 'mca3')
    mca_array4 =       Cpt(EpicsSignal, 'mca4')
    mca_x =            Cpt(EpicsSignal, 'dxp1:Graph0X.AVAL')

    netcdf_filename = Cpt(EpicsSignal, 'netCDF1:FileName')
    netcdf_filename_rb = Cpt(EpicsSignal, 'netCDF1:FileName_RBV')
    netcdf_filenumber = Cpt(EpicsSignal, 'netCDF1:FileNumber')
    netcdf_filenumber_rb = Cpt(EpicsSignal, 'netCDF1:FileNumber_RBV')

    def start_mapping_scan(self):
        yield from bp.abs_set(self.collect_mode, 'MCA mapping', wait=True)
        #self.collect_mode.put('MCA mapping')
        yield from bp.sleep(.25)
        #ttime.sleep(0.25)
        yield from bp.abs_set(self.capt_start_stop, 1, wait=True)
        #self.capt_start_stop.put(1)
        yield from bp.abs_set(self.erase_start, 1, wait=True)
        #self.erase_start.put(1)
        yield from bp.sleep(1)
        #ttime.sleep(1)
        yield from bp.abs_set(pb4.do0.enable, 1, wait=True)
        #pb4.do0.enable.put(1) # Workaround
        return self._status

    def stop_scan(self):
        yield from bp.abs_set(pb4.do0.enable, 0, wait=True)
        #pb4.do0.enable.put(0) # Workaround
        yield from bp.sleep(1)
        yield from bp.abs_set(self.stop_sig, 1, wait=True)
        #self.stop_sig.put(1)
        yield from bp.sleep(0.5)
        #ttime.sleep(0.5)
        yield from bp.abs_set(self.capt_start_stop, 0, wait=True)
        #self.capt_start_stop.put(0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs[self.mode] = 'Real time'
        self._status = None

    def goto_next_pixel(self):
        self.next_pixel.put(1)

    def stage(self):
        self.acquiring.subscribe(self._acquiring_changed)

    def unstage(self):
        self.acquiring.clear_sub(self._acquiring_changed)

    def trigger(self):
        self._status = DeviceStatus(self)
        self.erase_start.put(1)
        pb4.do0.enable.put(1) # Workaround
        return self._status

    def _acquiring_changed(self, value=None, old_value=None, **kwargs):
        "This is run every time the value of 'acquiring' changes."
        if self._status is None:
            # We have not triggered anything; ignore this one.
            return
        if (old_value == 1) and (value == 0):
            # 'acquiring' has flipped from 'Acquiring' to 'Done'.
            pb4.do0.enable.put(0) # Workaround
            self._status._finished()
           

xia1 = XIA('XF:08IDB-OP{XMAP}', name='xia1') #XIA('dxpXMAP:', name='xia1')
xia1.read_attrs = ['graph1', 'graph2', 'graph3', 'graph4']
