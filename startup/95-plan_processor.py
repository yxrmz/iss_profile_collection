



class PlanProcessor():
    liveplot_funcs = None
    plan_list_update_signal = None
    status_update_signal = None

    def __init__(self):
        self.logger = self.get_logger()
        self.RE = RE
        self.scan_manager = scan_manager
        self.plan_list = []
        self.status = 'idle'

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

    @property
    def RE_state(self):
        return self.RE.state

    @property
    def RE_is_running(self):
        return self.RE_state == 'running'

    def append_gui_plan_list_update_signal(self, signal):
        self.plan_list_update_signal = signal

    def append_gui_status_update_signal(self, signal):
        self.status_update_signal = signal

    def append_liveplot_maker(self, liveplot_maker):
        self.liveplot_maker = liveplot_maker

    def make_liveplots(self, plan, plan_kwargs):
        return self.liveplot_maker(plan, plan_kwargs)

    def plan_status_at_index(self, idx):
        try:
            return self.plan_list[idx]['plan_status']
        except IndexError:
            return 'normal'

    def set_plan_status_at_index(self, index, status):
        self.plan_list[index]['plan_status'] = status

    @property
    def top_plan_status(self):
        return self.plan_status_at_index(0)

    @property
    def last_plan_status(self):
        return self.plan_status_at_index(-1)

    @property
    def top_plan_executing(self):
        return self.top_plan_status == 'executing'

    def add_plans(self, plans, add_at='tail'):
        if type(plans) != list:
            plans = [plans]

        for plan in plans:
            if 'plan_description' not in plan.keys():
                plan['plan_description'] = generate_plan_description(plan['plan_name'], plan['plan_kwargs'])

        if add_at == 'tail':
            _plan_status = self.last_plan_status
            if _plan_status == 'executing': _plan_status = 'normal'
            for plan in plans:
                self.plan_list.append({'plan_info' : plan, 'plan_status' : _plan_status})
        elif add_at == 'head':
            _plan_status = self.top_plan_status
            if _plan_status == 'executing': _plan_status = 'normal'
            idx = self.smallest_index
            for plan in plans[::-1]: # [::-1] is needed so insert doesn't revert the list order
                self.plan_list.insert(idx, {'plan_info': plan, 'plan_status': _plan_status})

        self._emit_plan_list_update_signal()

    def make_re_args(self, idx):
        plan_info = self.plan_list[idx]['plan_info']
        plan_name = plan_info['plan_name']
        plan_func = all_plan_funcs[plan_name]
        plan_kwargs = plan_info['plan_kwargs']
        liveplots = self.make_liveplots(plan_name, plan_kwargs)
        if len(liveplots) == 0:
            return (plan_func(**plan_kwargs), )
        else:
            return (plan_func(**plan_kwargs), liveplots)

    def execute_top_plan(self):
        re_args = self.make_re_args(0)
        self.set_plan_status_at_index(0, 'executing')
        self.RE(*re_args)
        self.plan_list.pop(0)
        self._emit_plan_list_update_signal()

    def run(self):
        self.unpause_plan_list()

        while len(self.plan_list) > 0:

            if self.top_plan_status == 'normal':
                self.update_status('running')
                self.execute_top_plan()

            elif self.top_plan_status == 'paused':
                break

        self.unpause_plan_list()
        self.update_status('idle')

    def run_if_idle(self):
        if self.status == 'idle':
            self.run()

    def update_status(self, status):
        self.status = status
        self._emit_status_update_signal()

    @property
    def smallest_index(self):
        if (self.status == 'running') or self.RE_is_running:
            return 1
        else:
            return 0

    def pause_plan_list(self):
        index = self.smallest_index
        self.pause_after_index(index)

    def pause_after_index(self, index):
        any_plan_status_changed = False # to reduce unnecessary emitting
        for i in range(index, len(self.plan_list)):
            if self.plan_status_at_index(i) == 'normal':
                self.plan_list[i]['plan_status'] = 'paused'
                any_plan_status_changed = True
        if any_plan_status_changed:
            self._emit_plan_list_update_signal()

    def unpause_plan_list(self):
        self.unpause_before_index(len(self.plan_list))

    def unpause_before_index(self, index):
        any_plan_status_changed = False # to reduce unnecessary emitting
        for i in range(index):
            if self.plan_list[i]['plan_status'] == 'paused':
                self.plan_list[i]['plan_status'] = 'normal'
                any_plan_status_changed = True
        if any_plan_status_changed:
            self._emit_plan_list_update_signal()


    def clear_plan_list(self):
        idx = self.smallest_index
        for i in range(idx, len(self.plan_list)):
            self.plan_list.pop(idx)
        self._emit_plan_list_update_signal()


    def _emit_plan_list_update_signal(self):
        if self.plan_list_update_signal is not None:
            self.plan_list_update_signal.emit()

    def _emit_status_update_signal(self):
        if self.status_update_signal is not None:
            self.status_update_signal.emit()


    def append_liveplot_func_dictionary(self, liveplot_funcs):
        self.liveplot_funcs = liveplot_funcs

    def generate_plan_liveplot(self, plan_name, plan_kwargs, plan_tag=None):
        if (self.liveplot_funcs is not None):
            if (plan_tag is not None):
                liveplot_info = self.liveplot_funcs[plan_tag]
                make_liveplot_func = liveplot_info['make_liveplot_func']
                preferences = liveplot_info['preferences']

                if plan_tag == 'data_collection':
                    detectors = plan_kwargs['detectors']
                    motor_name = 'SOMETHING'
                    make_liveplot_func(detectors, motor_name)





plan_processor = PlanProcessor()







