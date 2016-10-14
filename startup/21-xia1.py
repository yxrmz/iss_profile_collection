import time as ttime

class XIA(Device):
    graph1 =         Cpt(EpicsSignal, 'mca1.VAL')
    graph2 =         Cpt(EpicsSignal, 'mca2.VAL')
    graph3 =         Cpt(EpicsSignal, 'mca3.VAL')
    graph4 =         Cpt(EpicsSignal, 'mca4.VAL')
    mode =         Cpt(EpicsSignal, 'PresetMode')
    collect_mode =     Cpt(EpicsSignal, 'CollectMode')
    start_sig =         Cpt(EpicsSignal, 'StartAll')
    stop_sig =         Cpt(EpicsSignal, 'StopAll')
    erase_start =    Cpt(EpicsSignal, 'EraseStart')
    erase =         Cpt(EpicsSignal, 'EraseAll')
    acquiring =         Cpt(EpicsSignalRO, 'Acquiring')

    capt_start_stop =    Cpt(EpicsSignal, 'netCDF1:Capture')
    pixels_per_run =     Cpt(EpicsSignal, 'PixelsPerRun')
    current_pixel =     Cpt(EpicsSignal, 'dxp1:CurrentPixel')
    next_pixel =       Cpt(EpicsSignal, 'NextPixel')
    pix_per_buf_auto =    Cpt(EpicsSignal, 'AutoPixelsPerBuffer')
    pix_per_buf_set =    Cpt(EpicsSignal, 'PixelsPerBuffer')
    pix_per_buf_rb =    Cpt(EpicsSignal, 'PixelsPerBuffer_RBV')

    def start_mapping_scan(self):
        self.collect_mode.put('MCA mapping')
        ttime.sleep(0.25)
        self.capt_start_stop.put(1)
        self.erase_start.put(1)
        ttime.sleep(1)
        pb4.do0.enable.put(1) # Workaround
        return self._status

    def stop_scan(self):
        pb4.do0.enable.put(0) # Workaround
        ttime.sleep(1)
        self.stop_sig.put(1)
        ttime.sleep(0.5)
        self.capt_start_stop.put(0)

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
