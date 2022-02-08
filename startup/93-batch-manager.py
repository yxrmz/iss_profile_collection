# from xas.trajectory import trajectory, trajectory_manager
from bluesky.plan_stubs import mv


class Sample:
    position_data = pd.DataFrame(columns=['x', 'y', 'z', 'th', 'exposure_time', 'exposed', 'uids'])

    def __init__(self, name, comment='', coordinates=[], max_exposure=None):
        self.name = name
        self.comment = comment
        self.max_exposure = max_exposure
        self.add_new_positions_from_coordinates(coordinates)
        # self.add_positions(positions)

    def validate_coordinates(self, coordinates_dict):
        ok_flag = (type(coordinates_dict) == dict) or (len(coordinates_dict) != 4)
        assert ok_flag, 'Unacceptable position format. Coordinates must be a dict with 4 elements corresponding to x, y, z, th coordinates.'

    def add_new_positions_from_coordinates(self, coordinates):
        for coordinates_dict in coordinates:
            self.add_new_position(coordinates_dict)

    def add_new_position(self, coordinates_dict):
        self.validate_coordinates(coordinates_dict)
        point = {**coordinates_dict, **{'exposure_time': 0, 'exposed': False, 'uids': ''}}
        self.add_one_position(point)

    def add_one_position(self, point):
        self.position_data = self.position_data.append(point, ignore_index=True)

    def add_positions(self, positions):
        for position in positions:
            self.add_one_position(position)

    def remove_positions(self, index_list):
        self.position_data.drop(self.position_data.index[index_list], inplace=True)

    def to_dict(self):
        sample_dict = {}
        sample_dict['name'] = self.name
        sample_dict['comment'] = self.comment
        sample_dict['position_data'] = self.position_data.to_dict()
        return sample_dict

    def update_position_coordinates(self, index, new_coordinates):
        for axis, coordinate in new_coordinates.items():
            self.position_data[axis][index] = coordinate

    @property
    def number_of_points(self):
        return len(self.position_data.index)

    @property
    def number_of_unexposed_points(self):
        return (self.number_of_points - sum(self.position_data['exposed']))

    def index_coordinate_dict(self, index):
        return self.position_data.iloc[index][['x', 'y', 'z', 'th']].to_dict()

    def index_coordinate_str(self, index):
        coord_dict = self.index_coordinate_dict(index)
        return ' '.join([(f"{key}={value : 0.2f}") for key, value in coord_dict.items()])

    def index_exposed(self, index):
        return bool(self.position_data.iloc[index][['exposed']].item())

    @classmethod
    def from_dict(cls, sample_dict):
        name = sample_dict['name']
        comment = sample_dict['comment']
        result = cls(name, comment=comment)
        result.position_data = pd.DataFrame.from_dict(sample_dict['position_data'])
        return result


class SampleManager:

    sample_list_update_signal = None

    def __init__(self, json_file_path = '/nsls2/xf08id/settings/json/sample_manager.json'):
        self.local_file_default_path = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/"
        self.samples = []
        self.json_file_path = json_file_path
        self.init_from_settings()

    # dealing with save/load to file
    def init_from_settings(self):
        try:
            self.add_samples_from_file(self.json_file_path)
        except FileNotFoundError:
            self.save_to_settings()

    def add_samples_from_file(self, file):
        with open(file, 'r') as f:
            sample_dict_list = json.loads(f.read())
        self.add_samples_from_dict_list(sample_dict_list)

    def save_to_settings(self):
        self.save_to_file(self.json_file_path)

    def save_to_file(self, file):
        with open(file, 'w') as f:
            json.dump(self.samples_as_dict_list, f )

    def reset(self):
        self.samples = []
        self.emit_sample_list_update_signal()

    @property
    def samples_as_dict_list(self):
        sample_dict_list = []
        for sample in self.samples:
            sample_dict_list.append(sample.to_dict())
        return sample_dict_list

    # dealing with addition and deletion of samples
    def add_new_sample(self, name, comment='', coordinates=[], max_exopsure=None):
        sample = Sample(name, comment=comment, coordinates=coordinates, max_exposure=max_exopsure)
        self.add_sample(sample)

    def insert_new_sample_at_index(self, index, name, comment='', coordinates=[], max_exopsure=None):
        sample = Sample(name, comment=comment, coordinates=coordinates, max_exposure=max_exopsure)
        self.insert_sample_at_index(index, sample)

    def add_sample(self, sample, emit_signal=True):
        self.samples.append(sample)
        if emit_signal:
            self.emit_sample_list_update_signal()

    def add_samples_from_dict_list(self, sample_dict_list):
        for sample_dict in sample_dict_list:
            sample = Sample.from_dict(sample_dict)
            self.add_sample(sample, emit_signal=False)
        self.emit_sample_list_update_signal()

    def insert_sample_at_index(self, index, sample):
        self.samples.insert(index, sample)
        self.emit_sample_list_update_signal()

    def delete_sample_at_index(self, index, emit_signal=True):
        _sample = self.samples.pop(index)
        del(_sample)
        if emit_signal:
            self.emit_sample_list_update_signal()

    def delete_multiple_samples(self, index_list, emit_signal=True):
        new_samples = []
        for i, sample in enumerate(self.samples):
            if i not in index_list:
                new_samples.append(sample)
        del(self.samples)
        self.samples = new_samples
        if emit_signal:
            self.emit_sample_list_update_signal()

    def delete_with_index_dict(self, index_dict):
        sample_idx_to_delete = []
        for sample_index, point_index_list in index_dict.items():
            sample = self.samples[sample_index]
            point_index_set = set(point_index_list)
            if sample.number_of_points == len(point_index_set):
                sample_idx_to_delete.append(sample_index)
                # self.delete_sample_at_index(sample_index, emit_signal=False)
            else:
                sample.remove_positions(list(point_index_set))

        if len(sample_idx_to_delete) > 0:
            self.delete_multiple_samples(sample_idx_to_delete, emit_signal=False)
        self.emit_sample_list_update_signal()

    def update_sample_at_index(self, index, new_name, new_comment):
        self.samples[index].name = new_name
        self.samples[index].comment = new_comment
        self.emit_sample_list_update_signal()

    def update_sample_coordinates_at_index(self, sample_index, sample_point_index, new_coordinate_dict):
        self.samples[sample_index].update_position_coordinates(sample_point_index, new_coordinate_dict)
        self.emit_sample_list_update_signal()


    @property
    def number_of_samples(self):
        return len(self.samples)

    def sample_at_index(self, index):
        return self.samples[index]

    def sample_name_at_index(self, index):
        return self.sample_at_index(index).name

    def sample_comment_at_index(self, index):
        return self.sample_at_index(index).comment

    def sample_coord_str_at_index(self, sample_index, sample_point_index):
        return self.sample_at_index(sample_index).index_coordinate_str(sample_point_index)

    def sample_coordinate_dict_at_index(self, sample_index, sample_point_index):
        return self.samples[sample_index].index_coordinate_dict(sample_point_index)

    def append_sample_list_update_signal(self, sample_list_update_signal):
        self.sample_list_update_signal = sample_list_update_signal

    def emit_sample_list_update_signal(self):
        if self.sample_list_update_signal is not None:
            self.sample_list_update_signal.emit()
        self.save_to_settings()

sample_manager = SampleManager()


# class ItemListInteractingWithGUI:
#     list_update_signal = None
#
#     def __init__(self, json_file_path='', items_str='scans'):
#         setattr(self, items_str) = []


        # self.json_file_path = json_file_path
    #     self.init_from_settings()
    #
    #
    # def init_from_settings(self):
    #     try:
    #         self.add_sequences_from_file(self.json_file_path)
    #     except FileNotFoundError:
    #         self.save_to_settings()
    #
    # def add_sequences_from_file(self, file):
    #     with open(file, 'r') as f:
    #         self.scans += json.loads(f.read())
    #     self.emit_scan_list_update_signal()
    #
    # def save_to_settings(self):
    #     self.save_to_file(self.json_file_path)
    #
    # def save_to_file(self, file):
    #     with open(file, 'w') as f:
    #         json.dump(self.scans, f)
    #
    # def reset(self):
    #     self.scans = []
    #     self.emit_scan_list_update_signal()
    #
    # def append_scan_list_update_signal(self, scan_list_update_signal):
    #     self.scan_list_update_signal = scan_list_update_signal
    #
    # def emit_scan_list_update_signal(self):
    #     if self.scan_list_update_signal is not None:
    #         self.scan_list_update_signal.emit()
    #     self.save_to_settings()


class ScanSequenceManager:
    scan_list_update_signal = None

    def __init__(self, json_file_path='/nsls2/xf08id/settings/json/scan_sequence_manager.json'):
        self.scans = []
        self.json_file_path = json_file_path
        self.init_from_settings()

    def init_from_settings(self):
        try:
            self.add_sequences_from_file(self.json_file_path)
        except FileNotFoundError:
            self.save_to_settings()

    def add_sequences_from_file(self, file):
        with open(file, 'r') as f:
            self.scans += json.loads(f.read())
        self.emit_scan_list_update_signal()

    def save_to_settings(self):
        self.save_to_file(self.json_file_path)

    def save_to_file(self, file):
        with open(file, 'w') as f:
            json.dump(self.scans, f)

    def reset(self):
        self.scans = []
        self.emit_scan_list_update_signal()

    def append_scan_list_update_signal(self, scan_list_update_signal):
        self.scan_list_update_signal = scan_list_update_signal

    def emit_scan_list_update_signal(self):
        if self.scan_list_update_signal is not None:
            self.scan_list_update_signal.emit()
        self.save_to_settings()

    def validate_element(self, element_dict):
        if element_dict['type'] == 'scan':
            required_keys = ['name', 'repeat', 'delay', 'scan_idx']
        # elif element_dict['type'] == 'scan_sequence':
        #     required_keys = ['name', 'scan_list']
        #     for scan in element_dict['scan_list']:
        #         self.validate_element(scan)
        else:
            raise Exception(f'Type of scan element is unknown: {element_dict}')

        valid = all([(k in element_dict.keys()) for k in required_keys])
        if not valid: raise Exception(f'element contains missing keys.\n'
                                      f'Element: {element_dict}. Required keys: {required_keys}')

    def add_element(self, element_dict):
        self.validate_element(element_dict)
        self.scans.append(element_dict)
        self.emit_scan_list_update_signal()

    def delete_element(self, element_index, emit_signal=True):
        if type(element_index) == int:
            self.scans.pop(element_index)
        # else:
        #     idx1, idx2 = element_index
        #     self.scans[idx1]['scan_sequence'].pop(idx2)
        if emit_signal:
            self.emit_scan_list_update_signal()

    # def delete_many_elements(self, element_index_list):
    #     for element_index in element_index_list:
    #         self.delete_element(element_index, emit_signal=False)
    #     self.scan_list_update_signal.emit()

    def update_element(self, element_index, element_dict):
        self.validate_element(element_dict)
        if type(element_index) == int:
            self.scans[element_index] = element_dict
        # else:
        #     idx1, idx2 = element_index
        #     self.scans[idx1]['scan_sequence'][idx2] = element_dict
        self.emit_scan_list_update_signal()

    def check_if_scan_index_is_used(self, scan_index):
        bad_indexes = []
        for i, scan in enumerate(self.scans):
            if scan['type'] == 'scan':
                if scan['scan_idx'] == scan_index:
                    bad_indexes.append(i)
            # elif scan['type'] == 'scan_sequence':
            #     for j, sub_scan in enumerate(scan['scan_list']):
            #         if sub_scan['scan_idx'] == scan_index:
            #             bad_indexes.append((i, j))
        return bad_indexes

    def scan_at_index(self, index):
        return self.scans[index]

    def scan_str_at_index(self, index):
        return self.scan_at_index(index)['name']



scan_sequence_manager = ScanSequenceManager()


class BatchManager:
    batch_list_update_signal = None

    def __init__(self, sample_manager : SampleManager, scan_manager: ScanManager, scan_sequence_manager : ScanSequenceManager,
                 json_file_path='/nsls2/xf08id/settings/json/batch_manager.json'):
        self.local_file_default_path = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/"
        self.experiments = []
        self.json_file_path = json_file_path
        self.init_from_settings()

        self.sample_manager = sample_manager
        self.scan_manager = scan_manager
        self.scan_sequence_manager = scan_sequence_manager

    # dealing with save/load to file
    def init_from_settings(self):
        try:
            self.read_from_file(self.json_file_path)
        except FileNotFoundError:
            self.save_to_settings()

    def read_from_file(self, file):
        with open(file, 'r') as f:
            self.experiments += json.loads(f.read())
        self.emit_batch_list_update_signal()

    def save_to_settings(self):
        self.save_to_file(self.json_file_path)

    def save_to_file(self, file):
        with open(file, 'w') as f:
            json.dump(self.experiments, f)

    def reset(self):
        self.experiments = []
        self.emit_batch_list_update_signal()

    def append_batch_list_update_signal(self, batch_list_update_signal):
        self.batch_list_update_signal = batch_list_update_signal

    def emit_batch_list_update_signal(self):
        if self.batch_list_update_signal is not None:
            self.batch_list_update_signal.emit()
        self.save_to_settings()

    def validate_element(self, element_dict):
        if element_dict['type'] == 'experiment':
            required_keys = ['name', 'repeat', 'element_list']
        elif element_dict['type'] == 'scan':
            required_keys = ['scan_sequence_index']
        elif element_dict['type'] == 'sample':
            required_keys = ['sample_index', 'sample_point_index']
        elif element_dict['type'] == 'service':
            required_keys = ['plan_name', 'plan_kwargs']
        else:
            raise Exception(f'Type of scan element is unknown: {element_dict}')

        valid = all([(k in element_dict.keys()) for k in required_keys])
        if not valid: raise Exception(f'element contains missing keys.\n'
                                      f'Element: {element_dict}. Required keys: {required_keys}')

        if 'element_list' in element_dict.keys():
            for element in element_dict['element_list']:
                self.validate_element(element)

    def add_experiment_from_dict(self, experiment_dict):
        self.validate_element(experiment_dict)
        self.experiments.append(experiment_dict)
        self.emit_batch_list_update_signal()

    def add_new_experiment(self, name, repeat):
        experiment_dict = {'type' : 'experiment', 'name' : name, 'repeat' : repeat, 'element_list' : []}
        self.add_experiment_from_dict(experiment_dict)

    def add_element_to_experiment(self, experiment_index, element_dict):
        self.validate_element(element_dict)
        self.experiments[experiment_index]['element_list'].append(element_dict)

    def sample_index_iterator(self, sample_index_dict):
        for sample_index, point_index_list in sample_index_dict.items():
            for point_index in point_index_list:
                yield (sample_index, point_index)

    def add_measurement_to_experiment(self, experiment_index, sample_index_dict, scan_indexes,
                                   priority='scan'):
        if priority == 'scan':
            for scan_index in scan_indexes:
                element_list = []
                for sample_index, sample_point_index in self.sample_index_iterator(sample_index_dict):
                    element_list.append({'type' : 'sample',
                                         'sample_index' : sample_index, 'sample_point_index' : sample_point_index})
                element_dict = {'type' : 'scan',
                                'scan_sequence_index' : scan_index,
                                'element_list' : element_list}
                self.add_element_to_experiment(experiment_index, element_dict)
        elif priority == 'sample':
            for sample_index, sample_point_index in self.sample_index_iterator(sample_index_dict):
                element_list = []
                for scan_index in scan_indexes:
                    element_list.append({'type' : 'scan',
                                         'scan_sequence_index' : scan_index})

                element_dict = {'type' : 'sample',
                                'sample_index' : sample_index, 'sample_point_index' : sample_point_index,
                                'element_list': element_list}
                self.add_element_to_experiment(experiment_index, element_dict)

        elif priority == 'sample_point':
            pass

        self.emit_batch_list_update_signal()

    def add_service_to_element_list(self, index_tuple, service_dict):
        self.validate_element(service_dict)
        nidx = len(index_tuple)
        if nidx == 1:
            experiment_index = index_tuple[0]
            self.experiments[experiment_index]['element_list'].insert(0, service_dict)
        elif nidx == 2:
            experiment_index, element_index1 = index_tuple
            self.experiments[experiment_index]['element_list'].insert(element_index1, service_dict)
        elif nidx == 3:
            experiment_index, element_index1, element_index2 = index_tuple
            self.experiments[experiment_index]['element_list'][element_index1]['element_list'].insert(element_index2, service_dict)
        self.emit_batch_list_update_signal()
    # def add_many_elements(self, index_tuple_list):

    # def sample_point_data_from_index(self, sample_index, sample_point_index):
    #     sample = self.sample_manager.samples[sample_index]
    #     return self.sample_manager.samples[sample_index].position_data.iloc[sample_point_index]

    def sample_str_from_element(self, sample_element):
        return self.sample_str_from_index(sample_element['sample_index'],
                                          sample_element['sample_point_index'])

    def sample_str_from_index(self, sample_index, sample_point_index):
        sample_str = self.sample_manager.sample_name_at_index(sample_index)
        point_str = self.sample_manager.sample_coord_str_at_index(sample_index, sample_point_index)
        return f'{sample_str} at {point_str} (point #{sample_point_index + 1})'

    def scan_str_from_element(self, scan_element):
        return self.scan_str_from_index(scan_element['scan_sequence_index'])

    def scan_str_from_index(self, scan_index):
        return self.scan_sequence_manager.scan_str_at_index(scan_index)

    def service_str_from_element(self, service_element):
        return f"{service_element['plan_name']} ({service_element['plan_kwargs']})"

    # def batch_items_iterator(self):

    # def trim_index_tuple_list_from_repeats(self, index_tuple_list):
    #
    #     # search level 0:
    #     unique_experiment_idx = []
    #     for index_tuple in index_tuple_list:
    #         if len(index_tuple) == 1:
    #             unique_experiment_idx.append(index_tuple[0])
    #
    #     unique_exp_elements_idx = []
    #     for index_tuple in index_tuple_list:
    #         if len(index_tuple) == 2:
    #             if index_tuple[0] not in unique_experiment_idx:
    #                 unique_exp_elements_idx.append(index_tuple)
    #
    #     unique_exp_el_elements_idx = []
    #     for index_tuple in index_tuple_list:
    #         if len(index_tuple) == 3:
    #             this_unique_element_idx = [_tuple[1] for _tuple in unique_exp_elements_idx if _tuple[0]==index_tuple[0]]
    #             if index_tuple[1] not in this_unique_element_idx:
    #                 unique_exp_el_elements_idx.append(index_tuple)
    #
    #     return [(idx, ) for idx in unique_experiment_idx] + unique_exp_elements_idx + unique_exp_el_elements_idx

    def delete_element(self, index_tuple):
        nidx = len(index_tuple)
        if nidx == 1:
            experiment_index = index_tuple[0]
            self.experiments.pop(experiment_index)
        elif nidx == 2:
            experiment_index, element_index1 = index_tuple
            self.experiments[experiment_index]['element_list'].pop(element_index1)
        elif nidx == 3:
            experiment_index, element_index1, element_index2 = index_tuple
            self.experiments[experiment_index]['element_list'][element_index1]['element_list'].pop(element_index2)
        self.emit_batch_list_update_signal()


    def get_booked_sample_points_list(self):
        pass

    # def parse_element_into_plan(self, element):
    #     plans = []
    #     if element['type'] == 'experiment':
    #         pass
    #     elif


    def get_sample_data_from_sample_element(self, sample_element):
        sample_index = sample_element['sample_index']
        sample_point_index = sample_element['sample_point_index']
        sample_name = self.sample_manager.sample_name_at_index(sample_index)
        sample_comment = self.sample_manager.sample_comment_at_index(sample_index)
        sample_coordinates = self.sample_manager.sample_coordinate_dict_at_index(sample_index,
                                                                                 sample_point_index)
        return sample_name, sample_comment, sample_coordinates

    def get_scan_data_from_scan_element(self, scan_element):
        scan_dict = self.scan_sequence_manager.scan_at_index(scan_element['scan_sequence_index'])
        return scan_dict['repeat'], scan_dict['delay'], scan_dict['scan_idx']

    def get_data_from_element(self, element):
        if element['type'] == 'scan':
            return self.get_scan_data_from_scan_element(element)
        elif element['type'] == 'sample':
            return self.get_sample_data_from_sample_element(element)
        elif element['type'] == 'service':
            return [{'plan_name': element['plan_name'], 'plan_kwargs' : element['plan_kwargs']}]

    def generate_plan_list(self):
        plans = []
        for experiment in self.experiments:
            for element in experiment['element_list']:
                if element['type'] == 'scan':
                    repeat, delay, scan_idx = self.get_data_from_element(element)
                    for sub_element in element['element_list']:
                        if sub_element['type'] == 'sample':
                            sample_name, sample_comment, sample_coordinates = self.get_data_from_element(sub_element)
                            new_plans = self.scan_manager.generate_plan_list(sample_name, sample_comment,
                                                                             repeat, delay, scan_idx,
                                                                             sample_coordinates=sample_coordinates)
                        elif sub_element['type'] == 'service':
                            new_plans = self.get_data_from_element(sub_element)
                        else:
                            new_plans = []
                        plans.extend(new_plans)

                elif element['type'] == 'sample':
                    sample_name, sample_comment, sample_coordinates = self.get_data_from_element(element)
                    for sub_element in element['element_list']:
                        if sub_element['type'] == 'scan':
                            repeat, delay, scan_idx = self.get_data_from_element(sub_element)
                            new_plans = self.scan_manager.generate_plan_list(sample_name, sample_comment,
                                                                             repeat, delay, scan_idx,
                                                                             sample_coordinates=sample_coordinates)

                        elif sub_element['type'] == 'service':
                            new_plans = self.get_data_from_element(sub_element)
                        else:
                            new_plans = []
                        plans.extend(new_plans)
                elif element['type'] == 'service':
                    new_plans = self.get_data_from_element(element)
                    plans.extend(new_plans)


        return plans


batch_manager = BatchManager(sample_manager, scan_manager, scan_sequence_manager)



# def batch_parse_and_run(hhm,sample_stage,batch,plans_dict ):
#     # tm = trajectory_manager(hhm)
#     for ii in range(batch.rowCount()):
#         experiment = batch.item(ii)
#         print(experiment.item_type)
#         repeat=experiment.repeat
#         print(repeat)
#         for jj in range(experiment.rowCount()):
#             child = experiment.child(jj)
#             print(child.item_type)
#             if child.item_type == 'sample':
#                 print('  ' + sample.name)
#                 print('  ' + str(sample.x))
#                 print('  ' + str(sample.y))
#                 yield from mv(sample_stage.x, sample.x, sample_stage.y, sample.y)
#                 for kk in range(sample.rowCount()):
#                     scan = sample.child(kk)
#                     traj_index= scan.trajectory
#                     print('      ' + scan.scan_type)
#                     plan = plans_dict[scan.scan_type]
#                     kwargs = {'name': sample.name,
#                               'comment': '',
#                               'delay': 0,
#                               'n_cycles': repeat}
#                     trajectory_manager.init(traj_index+1)
#                     yield from plan(**kwargs)
#             elif child.item_type == 'service':
#                     print(child.service_plan)

# summarize_plan(parse_and_execute())