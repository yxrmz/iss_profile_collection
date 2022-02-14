class BPM(SingleTrigger, ProsilicaDetector):
    image = Cpt(ImagePlugin, 'image1:')
    stats1 = Cpt(StatsPluginV33, 'Stats1:')
    stats2 = Cpt(StatsPluginV33, 'Stats2:')
    stats3 = Cpt(StatsPluginV33, 'Stats3:')
    stats4 = Cpt(StatsPluginV33, 'Stats4:')

    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')
    counts = Cpt(EpicsSignal, 'Pos:Counts')
    exp_time = Cpt(EpicsSignal, 'cam1:AcquireTime_RBV', write_pv='cam1:AcquireTime')
    image_mode = Cpt(EpicsSignal,'cam1:ImageMode')
    acquire = Cpt(EpicsSignal, 'cam1:Acquire')

    # Actuator
    insert = Cpt(EpicsSignal, 'Cmd:In-Cmd')
    inserted = Cpt(EpicsSignalRO, 'Sw:InLim-Sts')

    retract = Cpt(EpicsSignal, 'Cmd:Out-Cmd')
    retracted = Cpt(EpicsSignal, 'Sw:OutLim-Sts')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs['cam.image_mode'] = 'Single'
        self.polarity = 'pos'
        self.image_height = self.image.height.get()
        self.frame_rate = self.cam.ps_frame_rate
        # self._inserting = None
        # self._retracting = None

    def set(self, command):
        def callback(value, old_value, **kwargs):
            if value == 1:
                return True
            return False

        if command.lower() == 'insert':
            status = SubscriptionStatus(self.inserted, callback)
            self.insert.set('Insert')
            return status

        if command.lower() == 'retract':
            status = SubscriptionStatus(self.retracted, callback)
            self.retract.set('Retract')
            return status

    def adjust_camera_exposure_time(self, roi_index=1,
                                    target_max_counts=150, atol=10,
                                    max_exp_time_thresh=1,
                                    min_exp_time_thresh=0.00002):
        stats = getattr(self, f'stats{roi_index}')
        while True:
            current_maximum = stats.max_value.get()
            current_exp_time = self.exp_time.get()
            delta = np.abs(current_maximum - target_max_counts)
            ratio = target_max_counts / current_maximum
            new_exp_time = np.clip(current_exp_time * ratio, min_exp_time_thresh, max_exp_time_thresh)

            if new_exp_time != current_exp_time:
                if delta > atol:
                    set_and_wait(self.exp_time, new_exp_time)
                    ttime.sleep(np.max((0.5, new_exp_time)))
                    continue
            break

class FeedbackBPM(BPM):
    ioc_reboot_pv = None

    def append_ioc_reboot_pv(self, ioc_reboot_pv):
        self.ioc_reboot_pv = ioc_reboot_pv

    def reboot_ioc(self):
        if self.ioc_reboot_pv is not None:
            self.ioc_reboot_pv.put(1)
            ttime.sleep(10)
            self.acquire.put(1)
        else:
            print_to_gui('ioc_reboot_pv is not appended. IOC reboot impossible.')

    @property
    def acquiring(self):
        return bool(self.acquire.get())

    @property
    def image_centroid_y(self):
        y = self.stats1.centroid.y.get()
        return self.image_height - y

    @property
    def image_centroid_x(self):
        return self.stats1.centroid.x.get()


class CAMERA(SingleTrigger, ProsilicaDetector):
    image = Cpt(ImagePlugin, 'image1:')

    stats1 = Cpt(StatsPluginV33, 'Stats1:')
    stats2 = Cpt(StatsPluginV33, 'Stats2:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')

    exp_time = Cpt(EpicsSignal, 'cam1:AcquireTime_RBV', write_pv='cam1:AcquireTime')
    polarity = 'pos'
    tiff_filepath = Cpt(EpicsSignal, 'TIFF1:FilePath_RBV', write_pv='TIFF1:FilePath')
    tiff_filename = Cpt(EpicsSignal, 'TIFF1:FileName_RBV', write_pv='TIFF1:FileName')
    tiff_filenumber = Cpt(EpicsSignal, 'TIFF1:FileNumber_RBV', write_pv='TIFF1:FileNumber')
    tiff_filefmt = Cpt(EpicsSignal, 'TIFF1:FileTemplate_RBV', write_pv='TIFF1:FileTemplate')

    bar1 = Cpt(EpicsSignal, 'Bar1:BarcodeMessage1_RBV')
    bar2 = Cpt(EpicsSignal, 'Bar1:BarcodeMessage2_RBV')
    bar3 = Cpt(EpicsSignal, 'Bar1:BarcodeMessage3_RBV')
    bar4 = Cpt(EpicsSignal, 'Bar1:BarcodeMessage4_RBV')
    bar5 = Cpt(EpicsSignal, 'Bar1:BarcodeMessage5_RBV')

    bar1Corner1X = Cpt(EpicsSignal, 'Bar1:UpperLeftX_RBV')
    bar1Corner2X = Cpt(EpicsSignal, 'Bar1:UpperRightX_RBV')
    bar1Corner3X = Cpt(EpicsSignal, 'Bar1:LowerLeftX_RBV')
    bar1Corner4X = Cpt(EpicsSignal, 'Bar1:LowerRightX_RBV')
    bar1Corner1Y = Cpt(EpicsSignal, 'Bar1:UpperLeftY_RBV')
    bar1Corner2Y = Cpt(EpicsSignal, 'Bar1:UpperRightY_RBV')
    bar1Corner3Y = Cpt(EpicsSignal, 'Bar1:LowerLeftY_RBV')
    bar1Corner4Y = Cpt(EpicsSignal, 'Bar1:LowerRightY_RBV')

    bar2Corner1X = Cpt(EpicsSignal, 'Bar2:UpperLeftX_RBV')
    bar2Corner2X = Cpt(EpicsSignal, 'Bar2:UpperRightX_RBV')
    bar2Corner3X = Cpt(EpicsSignal, 'Bar2:LowerLeftX_RBV')
    bar2Corner4X = Cpt(EpicsSignal, 'Bar2:LowerRightX_RBV')
    bar2Corner1Y = Cpt(EpicsSignal, 'Bar2:UpperLeftY_RBV')
    bar2Corner2Y = Cpt(EpicsSignal, 'Bar2:UpperRightY_RBV')
    bar2Corner3Y = Cpt(EpicsSignal, 'Bar2:LowerLeftY_RBV')
    bar2Corner4Y = Cpt(EpicsSignal, 'Bar2:LowerRightY_RBV')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #self.stage_sigs.clear()  # default stage sigs do not apply

    def stage(self, acquire_time, image_mode, *args, **kwargs):
        self.stage_sigs['cam.acquire_time'] =  acquire_time
        self.stage_sigs['cam.image_mode'] = image_mode
        super().stage(*args, **kwargs)


class FoilCAMERA(CAMERA):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_foil_data()

    def _read_foil_info(self):
        with open('/nsls2/xf08id/settings/json/foil_wheel.json') as fp:
            foil_info = json.load(fp)
        return foil_info

    def read_foil_data(self):
        foil_info = self._read_foil_info()
        reference_foils = [item['element'] for item in foil_info]
        edges = [item['edge'] for item in foil_info]
        self.edge_dict = {}
        for foil, edge in zip(reference_foils, edges):
            self.edge_dict[foil] = edge

    @property
    def barcode1(self):
        return str(self.bar1.get()[:-1], encoding='UTF-8')

    @property
    def barcode2(self):
        return str(self.bar2.get()[:-1], encoding='UTF-8')

    def read_current_foil(self, error_message_func=None):
        if self.barcode1 != '':
            return self.barcode1
        if self.barcode2 != '':
            return self.barcode2
        msg = f'Reference foil not found'
        if error_message_func is not None:
            error_message_func(msg)
        print_to_gui(msg)
        raise Exception(msg)

    def check_if_foil_is_in(self, error_message_func=None):
        self.read_current_foil(error_message_func=error_message_func)

    def read_current_foil_and_edge(self, error_message_func=None):
        element = self.read_current_foil(error_message_func=error_message_func)
        # element = 'Fe'
        edge = self.edge_dict[element]
        return element, edge

    @property
    def current_foil_and_edge(self):
        return self.read_current_foil_and_edge()

    def validate_barcode(self, input, error_message_func):
        if input in (self.barcode1, self.barcode2):
            return
        msg = f'String {input} not found in {self.name} barcodes'
        if error_message_func is not None:
            error_message_func(msg)
        print_to_gui(msg)
        raise Exception(msg)


bpm_fm = BPM('XF:08IDA-BI{BPM:FM}', name='bpm_fm')
bpm_cm = BPM('XF:08IDA-BI{BPM:CM}', name='bpm_cm')
bpm_bt1 = BPM('XF:08IDA-BI{BPM:1-BT}', name='bpm_bt1')
bpm_bt2 = BPM('XF:08IDA-BI{BPM:2-BT}', name='bpm_bt2')

bpm_es = FeedbackBPM('XF:08IDB-BI{BPM:ES}', name='bpm_es')
bpm_es_ioc_reset = EpicsSignal('XF:08IDB-CT{IOC:BPM:ES}:SysReset', name='bpm_es_ioc_reset')
bpm_es.append_ioc_reboot_pv(bpm_es_ioc_reset)

camera_sp1 = BPM('XF:08IDB-BI{BPM:SP-1}', name='camera_sp1')
# camera_sp2 = CAMERA('XF:08IDB-BI{BPM:SP-2}', name='camera_sp2')
camera_sp2 = BPM('XF:08IDB-BI{BPM:SP-2}', name='camera_sp2')

#camera_sp3 = CAMERA('XF:08IDB-BI{BPM:SP-3}', name='camera_sp3')
camera_sp4 = CAMERA('XF:08IDB-BI{BPM:SP-4}', name='camera_sp4')
camera_sp5 = FoilCAMERA('XF:08IDB-BI{BPM:SP-5}', name='camera_sp5')
camera_sp6 = CAMERA('XF:08IDB-BI{BPM:SP-6}', name='camera_sp6')

foil_camera = camera_sp5

#bpm_ms1 = CAMERA('XF:08IDB-BI{BPM:MS-1}', name='bpm_ms1')

for bpm in [bpm_fm, bpm_cm, bpm_bt1, bpm_bt2, bpm_es,]: #camera_sp1, camera_sp2, camera_sp3, camera_sp4]:

    bpm.read_attrs = ['stats1', 'stats2']
    bpm.image.read_attrs = ['array_data']
    bpm.stats1.read_attrs = ['total', 'centroid']
    bpm.stats2.read_attrs = ['total', 'centroid']

bpm_fm.read_attrs = ['stats1', 'stats2', 'stats3', 'stats4']
bpm_fm.stats1.read_attrs = ['total', 'centroid']
bpm_fm.stats2.read_attrs = ['total', 'centroid']
bpm_fm.stats3.read_attrs = ['total', 'centroid']
bpm_fm.stats4.read_attrs = ['total', 'centroid']

for camera in [ camera_sp1, camera_sp2, camera_sp4]:   #camera_sp3,
    bpm.read_attrs = ['stats1', 'stats2']
    bpm.image.read_attrs = ['array_data']
    #bpm.stats1.read_attrs = ['total', 'centroid']
    #bpm.stats2.read_attrs = ['total', 'centroid']



tc_mask2_4 = EpicsSignal('XF:08IDA-OP{Mir:2-CM}T:Msk2_4-I',
                         name='tc_mask2_4')
tc_mask2_3 = EpicsSignal('XF:08IDA-OP{Mir:2-CM}T:Msk2_3-I',
                         name='tc_mask2_3')


bpm_fm.stats1.kind = 'hinted'
bpm_fm.stats1.total.kind = 'hinted'

bpm_es.stats1.kind = 'hinted'
bpm_es.stats1.total.kind = 'hinted'


camera_sp1.stats1.kind = 'hinted'
camera_sp1.stats1.total.kind = 'hinted'

camera_sp1.stats2.kind = 'hinted'
camera_sp1.stats2.total.kind = 'hinted'

camera_sp2.stats1.kind = 'hinted'
camera_sp2.stats1.total.kind = 'hinted'

camera_sp2.stats2.kind = 'hinted'
camera_sp2.stats2.total.kind = 'hinted'