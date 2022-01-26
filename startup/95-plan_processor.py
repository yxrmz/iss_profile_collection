



class PlanProcessor():

    def __init__(self):
        self.logger = self.get_logger()
        self.RE = RE
        self.scan_manager = scan_manager
        self.plan_list = []
        self.status = 'stopped'
        self.plan_list_update_signal = None
        self.status_update_signal = None

    def append_gui_plan_list_update_signal(self, signal):
        self.plan_list_update_signal = signal

    def append_gui_status_update_signal(self, signal):
        self.status_update_signal = signal

    def get_logger(self):
        # Setup beamline specifics:
        beamline_gpfs_path = '/nsls2/xf08id'

        logger = logging.getLogger('xas_logger')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # only add handlers if not added before
        if not len(logger.handlers):
            logger.setLevel(logging.DEBUG)
            # Write DEBUG and INFO messages to /var/log/data_processing_worker/debug.log.
            debug_file = logging.handlers.RotatingFileHandler(
                beamline_gpfs_path + '/log/data_collection_debug.log',
                maxBytes=10000000, backupCount=9)
            debug_file.setLevel(logging.DEBUG)
            debug_file.setFormatter(formatter)
            logger.addHandler(debug_file)
        return logger

    def add_plans(self, plans):
        if type(plans) != list:
            plans = [plans]

        if len(self.plan_list) > 0:
            _status = self.plan_list[-1]['status']
        else:
            _status = 'normal'

        for plan in plans:
            self.plan_list.append({'plan_info' : plan, 'status' : _status})

        if self.plan_list_update_signal is not None:
            self.plan_list_update_signal.emit()

    def execute_top_plan_from_list(self):
        plan_dict = self.plan_list[0]['plan_info']
        plan = all_plan_funcs[plan_dict['plan_name']](**plan_dict['plan_kwargs'])
        # plan = bps.sleep(2)
        print(f'{ttime.ctime()}   started doing plan {plan}')
        self.RE(plan)
        # ttime.sleep(1)
        print(f'{ttime.ctime()}   done doing plan {plan}')
        self.plan_list.pop(0)
        if self.plan_list_update_signal is not None:
            self.plan_list_update_signal.emit()

    def run(self):
        while len(self.plan_list) > 0:

            if self.plan_list[0]['status'] == 'normal':
                self.update_status('running')
                self.execute_top_plan_from_list()

            elif self.plan_list[0]['status'] == 'paused':
                self.update_status('paused')
                break

        self.update_status('stopped')


    def update_status(self, status):
        self.status = status
        if self.status_update_signal is not None:
            self.status_update_signal.emit()

    @property
    def smallest_index(self):
        if self.status == 'running':
            return 1
        else:
            return 0

    def pause_plan_list(self):
        index = self.smallest_index
        self.pause_after_index(index)

    def pause_after_index(self, index):
        for i in range(index, len(self.plan_list)):
            self.plan_list[i]['status'] = 'paused'
        if self.plan_list_update_signal is not None:
            self.plan_list_update_signal.emit()

    def resume_plan_list(self):
        for i in range(len(self.plan_list)):
            self.plan_list[i]['status'] = 'normal'
        if self.plan_list_update_signal is not None:
            self.plan_list_update_signal.emit()
        self.run()

    def clear_plan_list(self):
        idx = self.smallest_index
        for i in range(idx, len(self.plan_list)):
            self.plan_list.pop(idx)

        if self.plan_list_update_signal is not None:
            self.plan_list_update_signal.emit()





plan_processor = PlanProcessor()



