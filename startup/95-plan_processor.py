



# class PlanProcessor():
#     liveplot_maker = None
#     gui_services_dict = None
#     plan_list_update_signal = None
#     status_update_signal = None
#
#     def __init__(self):
#         self.logger = self.get_logger()
#         self.RE = RE
#         self.scan_manager = scan_manager
#         self.plan_list = []
#         self.status = 'idle'
#
#     def get_logger(self):
#         # Setup beamline specifics:
#         beamline_gpfs_path = '/nsls2/xf08id'
#
#         logger = logging.getLogger('xas_logger')
#         formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#
#         # only add handlers if not added before
#         if not len(logger.handlers):
#             logger.setLevel(logging.DEBUG)
#             # Write DEBUG and INFO messages to /var/log/data_processing_worker/debug.log.
#             debug_file = logging.handlers.RotatingFileHandler(
#                 beamline_gpfs_path + '/log/data_collection_debug.log',
#                 maxBytes=10000000, backupCount=9)
#             debug_file.setLevel(logging.DEBUG)
#             debug_file.setFormatter(formatter)
#             logger.addHandler(debug_file)
#         return logger
#
#     @property
#     def RE_state(self):
#         return self.RE.state
#
#     @property
#     def RE_is_running(self):
#         return self.RE_state == 'running'
#
#     def append_gui_plan_list_update_signal(self, signal):
#         self.plan_list_update_signal = signal
#
#     def append_gui_status_update_signal(self, signal):
#         self.status_update_signal = signal
#
#     def append_liveplot_maker(self, liveplot_maker):
#         self.liveplot_maker = liveplot_maker
#
#     def make_liveplots(self, plan, plan_kwargs):
#         if self.liveplot_maker is not None:
#             return self.liveplot_maker(plan, plan_kwargs)
#         else:
#             return []
#
#     def append_gui_services_dict(self, gui_services_dict):
#         self.gui_services_dict = gui_services_dict
#
#     def get_gui_services_kwargs(self, plan_info):
#         gui_services_kwargs = {}
#         if 'plan_gui_services' in plan_info.keys():
#             for service_key in plan_info['plan_gui_services']:
#                 service_dict = self.gui_services_dict[service_key]
#                 kwarg_name = service_dict['kwarg_name']
#                 kwarg_value = service_dict['kwarg_value']
#                 gui_services_kwargs[kwarg_name] = kwarg_value
#             # return gui_services_kwargs
#         return gui_services_kwargs
#
#     def plan_status_at_index(self, idx):
#         try:
#             return self.plan_list[idx]['plan_status']
#         except IndexError:
#             return 'normal'
#
#     def set_plan_status_at_index(self, index, status):
#         self.plan_list[index]['plan_status'] = status
#
#     @property
#     def top_plan_status(self):
#         return self.plan_status_at_index(0)
#
#     @property
#     def last_plan_status(self):
#         return self.plan_status_at_index(-1)
#
#     @property
#     def top_plan_executing(self):
#         return self.top_plan_status == 'executing'
#
#     def describe_plan(self, plan_dict):
#         if 'plan_description' not in plan_dict.keys():
#             plan_dict['plan_description'] = generate_plan_description(plan_dict['plan_name'], plan_dict['plan_kwargs'])
#
#     def add_plans(self, plans, add_at='tail', idx=None):
#         if type(plans) != list:
#             plans = [plans]
#
#         # plans = self.deal_with_bundles_in_plan_list(plans)
#
#         for plan_dict in plans:
#             self.describe_plan(plan_dict)
#
#         if add_at == 'tail':
#             _plan_status = self.last_plan_status
#             if _plan_status == 'executing': _plan_status = 'normal'
#             for plan_dict in plans:
#                 self.plan_list.append({'plan_info' : plan_dict, 'plan_status' : _plan_status})
#         elif add_at == 'head':
#             _plan_status = self.top_plan_status
#             if _plan_status == 'executing': _plan_status = 'normal'
#             idx = self.smallest_index
#             for plan_dict in plans[::-1]: # [::-1] is needed so insert doesn't revert the list order
#                 self.plan_list.insert(idx, {'plan_info': plan_dict, 'plan_status': _plan_status})
#         elif add_at == 'index':
#             _plan_status = self.plan_status_at_index(idx)
#             if _plan_status == 'executing':
#                 _plan_status = 'normal'
#             for plan_dict in plans[::-1]: # [::-1] is needed so insert doesn't revert the list order
#                 self.plan_list.insert(idx, {'plan_info': plan_dict, 'plan_status': _plan_status})
#
#         self._emit_plan_list_update_signal()
#
#     def plan_is_a_bundle(self, idx):
#         plan_info = self.plan_list[idx]['plan_info']
#         plan_name = plan_info['plan_name']
#         plan_func = all_plan_funcs[plan_name]
#         if type(plan_func) == dict:
#             if plan_func['kind'] == 'bundle':
#                 return True
#         return False
#
#     def unwrap_bundle(self, idx):
#         plan_info = self.plan_list[idx]['plan_info']
#         plan_name = plan_info['plan_name']
#         plan_func = all_plan_funcs[plan_name]
#         bundle_kwargs = plan_info['plan_kwargs']
#         bundle_gui_services = self.get_gui_services_kwargs(plan_info)
#         bundle_all_kwargs = {**bundle_kwargs, **bundle_gui_services}
#         plan_bundle = plan_func['func'](**bundle_all_kwargs)
#         self.plan_list.pop(idx)
#         self.add_plans(plan_bundle, add_at='index', idx=idx)
#
#     # def detect_and_unwrap_bundle(self, idx):
#     #     plan_info = self.plan_list[idx]['plan_info']
#     #     plan_name = plan_info['plan_name']
#     #     plan_func = all_plan_funcs[plan_name]
#     #     if type(plan_func) == dict:
#     #         if plan_func['kind'] == 'bundle':
#     #             bundle_kwargs = plan_info['plan_kwargs']
#     #             plan_bundle = plan_func['func'](**bundle_kwargs)
#     #             self.plan_list.pop(idx)
#     #             self.add_plans(plan_bundle, add_at='index', idx=idx)
#
#     def make_re_args(self, idx):
#         plan_info = self.plan_list[idx]['plan_info']
#         plan_name = plan_info['plan_name']
#         plan_func = all_plan_funcs[plan_name]
#         plan_kwargs = plan_info['plan_kwargs']
#         liveplots = self.make_liveplots(plan_name, plan_kwargs)
#         gui_services_kwargs = self.get_gui_services_kwargs(plan_info)
#         plan_all_kwargs = {**plan_kwargs, **gui_services_kwargs}
#         if len(liveplots) == 0:
#             return (plan_func(**plan_all_kwargs), )
#         else:
#             return (plan_func(**plan_all_kwargs), liveplots)
#
#     def execute_top_plan(self):
#         if self.plan_is_a_bundle(0):
#             self.unwrap_bundle(0)
#             self.execute_top_plan()
#         else:
#             re_args = self.make_re_args(0)
#             self.set_plan_status_at_index(0, 'executing')
#             self.RE(*re_args)
#             self.plan_list.pop(0)
#             self._emit_plan_list_update_signal()
#
#     def run(self):
#         self.unpause_plan_list()
#
#         while len(self.plan_list) > 0:
#
#             if self.top_plan_status == 'normal':
#                 self.update_status('running')
#                 self.execute_top_plan()
#                 # try:
#                 #     self.execute_top_plan()
#                 # except Exception as e:
#                 #     print(e)
#                 #     print('Found and issue with the top plan. Stopping the queue')
#                 #     break
#
#             elif self.top_plan_status == 'paused':
#                 break
#
#         self.unpause_plan_list()
#         self.update_status('idle')
#
#     def run_if_idle(self):
#         if self.status == 'idle':
#             self.run()
#
#     def add_plan_and_run_if_idle(self, plan_name, plan_kwargs, plan_gui_services=None):
#         plan_dict = {'plan_name': plan_name, 'plan_kwargs': plan_kwargs}
#         if plan_gui_services is not None:
#             plan_dict['plan_gui_services'] = plan_gui_services
#         self.add_plans(plan_dict)
#         self.run_if_idle()
#
#     def update_status(self, status):
#         self.status = status
#         self._emit_status_update_signal()
#
#     @property
#     def smallest_index(self):
#         if (self.status == 'running') or self.RE_is_running:
#             return 1
#         else:
#             return 0
#
#     def pause_plan_list(self):
#         index = self.smallest_index
#         self.pause_after_index(index)
#
#     def pause_after_index(self, index):
#         any_plan_status_changed = False # to reduce unnecessary emitting
#         for i in range(index, len(self.plan_list)):
#             if self.plan_status_at_index(i) == 'normal':
#                 self.plan_list[i]['plan_status'] = 'paused'
#                 any_plan_status_changed = True
#         if any_plan_status_changed:
#             self._emit_plan_list_update_signal()
#
#     def unpause_plan_list(self):
#         self.unpause_before_index(len(self.plan_list))
#
#     def unpause_before_index(self, index):
#         any_plan_status_changed = False # to reduce unnecessary emitting
#         for i in range(index):
#             if self.plan_list[i]['plan_status'] == 'paused':
#                 self.plan_list[i]['plan_status'] = 'normal'
#                 any_plan_status_changed = True
#         if any_plan_status_changed:
#             self._emit_plan_list_update_signal()
#
#
#     def clear_plan_list(self):
#         idx = self.smallest_index
#         for i in range(idx, len(self.plan_list)):
#             self.plan_list.pop(idx)
#         self._emit_plan_list_update_signal()
#
#
#     def _emit_plan_list_update_signal(self):
#         if self.plan_list_update_signal is not None:
#             self.plan_list_update_signal.emit()
#
#     def _emit_status_update_signal(self):
#         if self.status_update_signal is not None:
#             self.status_update_signal.emit()
#
#
#     def append_liveplot_func_dictionary(self, liveplot_funcs):
#         self.liveplot_funcs = liveplot_funcs
#
#     def generate_plan_liveplot(self, plan_name, plan_kwargs, plan_tag=None):
#         if (self.liveplot_funcs is not None):
#             if (plan_tag is not None):
#                 liveplot_info = self.liveplot_funcs[plan_tag]
#                 make_liveplot_func = liveplot_info['make_liveplot_func']
#                 preferences = liveplot_info['preferences']
#
#                 if plan_tag == 'data_collection':
#                     detectors = plan_kwargs['detectors']
#                     motor_name = 'SOMETHING'
#                     make_liveplot_func(detectors, motor_name)
#
#
#
#
#
# plan_processor = PlanProcessor()




class PlanProcessor(PersistentListInteractingWithGUI):
    liveplot_maker = None
    gui_services_dict = None
    plan_list_update_signal = None
    status_update_signal = None

    def __init__(self, json_file_path = '/nsls2/xf08id/settings/json/plan_processor.json'):
        super().__init__(json_file_path)
        self.logger = self.get_logger()
        self.RE = RE
        self.scan_manager = scan_manager
        # self.plan_list = []
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

    #class specific property
    @property
    def plan_list(self):
        return self.items

    @plan_list.setter
    def plan_list(self, value):
        self.items = value

    @plan_list.deleter
    def plan_list(self):
        del self.items

    def reset(self):
        super().reset()
        self.update_status('idle')

    # dealing with RE
    @property
    def RE_state(self):
        return self.RE.state

    @property
    def RE_is_running(self):
        return self.RE_state == 'running'

    # def append_gui_plan_list_update_signal(self, signal):
    #     self.plan_list_update_signal = signal

    # delaing with GUI interactions
    def append_gui_status_update_signal(self, signal):
        self.status_update_signal = signal

    def append_liveplot_maker(self, liveplot_maker):
        self.liveplot_maker = liveplot_maker

    def make_liveplots(self, plan, plan_kwargs):
        if self.liveplot_maker is not None:
            return self.liveplot_maker(plan, plan_kwargs)
        else:
            return []

    def append_gui_services_dict(self, gui_services_dict):
        self.gui_services_dict = gui_services_dict

    def get_gui_services_kwargs(self, plan_info):
        gui_services_kwargs = {}
        if 'plan_gui_services' in plan_info.keys():
            for service_key in plan_info['plan_gui_services']:
                service_dict = self.gui_services_dict[service_key]
                kwarg_name = service_dict['kwarg_name']
                kwarg_value = service_dict['kwarg_value']
                gui_services_kwargs[kwarg_name] = kwarg_value
            # return gui_services_kwargs
        return gui_services_kwargs

    # plan misc
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

    def describe_plan(self, plan_dict):
        if 'plan_description' not in plan_dict.keys():
            plan_dict['plan_description'] = generate_plan_description(plan_dict['plan_name'], plan_dict['plan_kwargs'])

    # dealing with plan adding and converting to RE-digestible pieces
    @emit_list_update_signal_decorator
    def add_plans(self, plans, add_at='tail', idx=None):
        if type(plans) != list:
            plans = [plans]

        # plans = self.deal_with_bundles_in_plan_list(plans)

        for plan_dict in plans:
            self.describe_plan(plan_dict)

        if add_at == 'tail':
            _plan_status = self.last_plan_status
            if _plan_status == 'executing': _plan_status = 'normal'
            for plan_dict in plans:
                # self.plan_list.append({'plan_info' : plan_dict, 'plan_status' : _plan_status})
                self.add_item({'plan_info': plan_dict, 'plan_status': _plan_status}, emit_signal=False)
        elif add_at == 'head':
            _plan_status = self.top_plan_status
            if _plan_status == 'executing': _plan_status = 'normal'
            idx = self.smallest_index
            for plan_dict in plans[::-1]: # [::-1] is needed so insert doesn't revert the list order
                self.insert_item_at_index(idx, {'plan_info': plan_dict, 'plan_status': _plan_status}, emit_signal=False)
        elif add_at == 'index':
            _plan_status = self.plan_status_at_index(idx)
            if _plan_status == 'executing':
                _plan_status = 'normal'
            for plan_dict in plans[::-1]: # [::-1] is needed so insert doesn't revert the list order
                self.insert_item_at_index(idx, {'plan_info': plan_dict, 'plan_status': _plan_status}, emit_signal=False)

    def plan_is_a_bundle(self, idx):
        plan_info = self.plan_list[idx]['plan_info']
        plan_name = plan_info['plan_name']
        plan_func = all_plan_funcs[plan_name]
        if type(plan_func) == dict:
            if plan_func['kind'] == 'bundle':
                return True
        return False

    def unwrap_bundle(self, idx):
        plan_info = self.plan_list[idx]['plan_info']
        plan_name = plan_info['plan_name']
        plan_func = all_plan_funcs[plan_name]
        bundle_kwargs = plan_info['plan_kwargs']
        bundle_gui_services = self.get_gui_services_kwargs(plan_info)
        bundle_all_kwargs = {**bundle_kwargs, **bundle_gui_services}
        plan_bundle = plan_func['func'](**bundle_all_kwargs)
        self.plan_list.pop(idx)
        self.add_plans(plan_bundle, add_at='index', idx=idx)


    def make_re_args(self, idx):
        plan_info = self.plan_list[idx]['plan_info']
        plan_name = plan_info['plan_name']
        plan_func = all_plan_funcs[plan_name]
        plan_kwargs = plan_info['plan_kwargs']
        liveplots = self.make_liveplots(plan_name, plan_kwargs)
        gui_services_kwargs = self.get_gui_services_kwargs(plan_info)
        plan_all_kwargs = {**plan_kwargs, **gui_services_kwargs}
        if len(liveplots) == 0:
            return (plan_func(**plan_all_kwargs), )
        else:
            return (plan_func(**plan_all_kwargs), liveplots)

    # execution of the queue
    @emit_list_update_signal_decorator
    def execute_top_plan(self):
        if self.plan_is_a_bundle(0):
            self.unwrap_bundle(0)
            self.execute_top_plan()
        else:
            re_args = self.make_re_args(0)
            self.set_plan_status_at_index(0, 'executing')
            self.RE(*re_args)
            self.plan_list.pop(0)

    def run(self):
        self.unpause_plan_list()

        while len(self.plan_list) > 0:

            if self.top_plan_status == 'normal':
                self.update_status('running')
                self.execute_top_plan()
                # try:
                #     self.execute_top_plan()
                # except Exception as e:
                #     print(e)
                #     print('Found and issue with the top plan. Stopping the queue')
                #     break

            elif self.top_plan_status == 'paused':
                break

        # self.unpause_plan_list()
        self.update_status('idle')

    def run_if_idle(self):
        if self.status == 'idle':
            self.run()

    def add_plan_and_run_if_idle(self, plan_name, plan_kwargs, plan_gui_services=None):
        plan_dict = {'plan_name': plan_name, 'plan_kwargs': plan_kwargs}
        if plan_gui_services is not None:
            plan_dict['plan_gui_services'] = plan_gui_services
        self.add_plans(plan_dict)
        self.run_if_idle()

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
            self.emit_list_update_signal()

    def unpause_plan_list(self):
        self.unpause_before_index(len(self.plan_list))

    def unpause_before_index(self, index):
        any_plan_status_changed = False # to reduce unnecessary emitting
        for i in range(index):
            if self.plan_list[i]['plan_status'] == 'paused':
                self.plan_list[i]['plan_status'] = 'normal'
                any_plan_status_changed = True
        if any_plan_status_changed:
            self.emit_list_update_signal()

    @emit_list_update_signal_decorator
    def clear_plan_list(self):
        idx = self.smallest_index
        for i in range(idx, len(self.plan_list)):
            self.plan_list.pop(idx)
        # self._emit_plan_list_update_signal()

    # def _emit_plan_list_update_signal(self):
    #     if self.plan_list_update_signal is not None:
    #         self.plan_list_update_signal.emit()

    def _emit_status_update_signal(self):
        if self.status_update_signal is not None:
            self.status_update_signal.emit()


    def append_liveplot_func_dictionary(self, liveplot_funcs):
        self.liveplot_funcs = liveplot_funcs

    # def generate_plan_liveplot(self, plan_name, plan_kwargs, plan_tag=None):
    #     if (self.liveplot_funcs is not None):
    #         if (plan_tag is not None):
    #             liveplot_info = self.liveplot_funcs[plan_tag]
    #             make_liveplot_func = liveplot_info['make_liveplot_func']
    #             preferences = liveplot_info['preferences']
    #
    #             if plan_tag == 'data_collection':
    #                 detectors = plan_kwargs['detectors']
    #                 motor_name = 'SOMETHING'
    #                 make_liveplot_func(detectors, motor_name)





plan_processor = PlanProcessor()


