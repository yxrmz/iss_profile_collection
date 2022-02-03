
# from PyQt5 import uic, QtGui, QtCore, QtWidgets
# from PyQt5.Qt import Qt

from pandas import DataFrame

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

    @property
    def number_of_points(self):
        return len(self.position_data.index)

    @property
    def number_of_unexposed_points(self):
        return (self.number_of_points - sum(self.position_data['exposed']))

    def index_coordinate_dict(self, index):
        return self.position_data.iloc[index][['x', 'y', 'z', 'th']].to_dict()

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
        self.save_to_settings()
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

    def delete_multiple_samples(self, index_list):
        new_samples = []
        for i, sample in enumerate(self.samples):
            if i not in index_list:
                new_samples.append(sample)
        del(self.samples)
        self.samples = new_samples
        self.emit_sample_list_update_signal()

    def delete_with_index_dict(self, index_dict):
        for sample_index, point_index_list in index_dict.items():
            sample = self.samples[sample_index]
            point_index_set = set(point_index_list)
            if sample.number_of_points == len(point_index_set):
                self.delete_sample_at_index(sample_index, emit_signal=False)
            else:
                sample.remove_positions(list(point_index_set))
        self.emit_sample_list_update_signal()

    @property
    def number_of_samples(self):
        return len(self.samples)

    def sample_name_at_index(self, index):
        return self.samples[index].name

    def sample_coordinate_dict_at_index(self, sample_index, sample_point_index):
        return self.samples[sample_index].index_coordinate_dict(sample_point_index)

    def append_sample_list_update_signal(self, sample_list_update_signal):
        self.sample_list_update_signal = sample_list_update_signal

    def emit_sample_list_update_signal(self):
        if self.sample_list_update_signal is not None:
            self.sample_list_update_signal.emit()
        self.save_to_settings()

sample_manager = SampleManager()




# class SamplePointRegistry:
#     position_list = pd.DataFrame(columns=['x', 'y', 'z', 'exposed', 'uid'])
#     sample_x = giantxy.x
#     sample_y = giantxy.y
#     sample_z = usermotor2.pos
#     current_index = None
#     xyz1 = None
#     xyz2 = None
#     root_path = f"{ROOT_PATH}/{USER_FILEPATH}"
#     _dumpfile = None
#     npoints = None
#
#     def __init__(self):
#         pass
#
#     def initialize(self, x1, y1, z1, x2, y2, z2, step=0.2):
#         self.reset()
#         self.xyz1 = [x1, y1, z1]
#         self.xyz2 = [x2, y2, z2]
#
#         f = np.cos(np.deg2rad(45))
#         _xs = np.arange(x1, x2 + step/f, step / f * np.sign(x2 - x1))
#         _ys = np.arange(y1, y2 + step, step * np.sign(y2 - y1))
#         npt = _xs.size
#         _zs = np.linspace(z1, z2, npt)
#         # self.position_list = []
#         for _x, _z in zip(_xs, _zs):
#             for _y in _ys:
#                 point = {'x' : _x, 'y' : _y, 'z' : _z, 'exposed' : False, 'uid' : ''}
#                 self.position_list = self.position_list.append(point, ignore_index=True)
#         self.current_index = 0
#         self.npoints = len(self.position_list.index)
#
#     def reset(self):
#         self.position_list = pd.DataFrame(columns=['x', 'y', 'z', 'exposed', 'uid'])
#         self.current_index = None
#         self.xyz1 = None
#         self.xyz2 = None
#
#     def _get_point(self, index):
#         return self.position_list.iloc[index]
#
#     def _move_to_point_plan(self, point):
#         print(f'moving stage to x={point["x"]}, y={point["y"]}, z={point["z"]}')
#         # yield from bps.mv(self.sample_x, point['x'],
#         #                   self.sample_y, point['y'],
#         #                   self.sample_z, point['z'],
#         #                   )
#         yield from bps.mv(self.sample_x, point['x'],
#                           self.sample_y, point['y'],
#                           )
#         self.sample_z.user_setpoint.put(point['z'])
#         yield from bps.sleep(0.3)
#
#
#     def goto_start_plan(self):
#         self.current_index = 0
#         point = self._get_point(0)
#         yield from self._move_to_point_plan(point)
#
#     def goto_end_plan(self):
#         self.current_index = self.npoints - 1
#         point = self.position_list.iloc[self.current_index]
#         yield from self._move_to_point_plan(point)
#
#     def goto_next_point_plan(self):
#         self.current_index += 1
#         point = self._get_point(self.current_index)
#         yield from self._move_to_point_plan(point)
#
#     def goto_index_plan(self, idx):
#         self.current_index = idx
#         point = self._get_point(idx)
#         yield from self._move_to_point_plan(point)
#
#     def find_first_unexposed_point(self):
#         idx = self.position_list['exposed'].ne(False).idxmin()
#         p = self.position_list.iloc[idx]
#         return idx, p
#         # for i, p in enumerate(self.position_list):
#         #     if not p['exposed']:
#         #         return i, p
#         # return None
#
#     def set_current_point_exposed(self):
#         if self.current_index is not None:
#             self.position_list.at[self.current_index, 'exposed'] = True
#             if self._dumpfile is not None:
#                 self.dump_data()
#
#
#     def record_uid_for_current_point(self, uid):
#         self.position_list.at[self.current_index, 'uid'] = uid
#
#     def get_list_of_uid_positions(self):
#         # herfd_index_list = []
#         # for idx, point in enumerate(self.position_list):
#         #     if 'uid' in point.keys():
#         #         herfd_index_list.append(idx)
#         return self.position_list['uid'].loc[lambda x: x != ''].values
#
#     def get_current_point(self):
#         point = self._get_point(self, self.current_index)
#         return point['x'], point['y'], point['z']
#
#     def goto_unexposed_point_plan(self):
#         i, point = self.find_first_unexposed_point()
#         self.current_index = i
#         yield from self._move_to_point_plan(point)
#
#     def save(self, filename):
#         # with open(filename, 'w') as f:
#         #     f.write(json.dumps(self.position_list))
#         print(f'sample registry - saving data - {ttime.ctime()}')
#         self.position_list.to_json(filename)
#
#     def load(self, filename):
#         # with open(filename, 'r') as f:
#         #     self.position_list = json.loads(f.read())
#         self.position_list = pd.read_json(filename)
#         self.npoints = len(self.position_list.index)
#
#
#     def set_dump_file(self, filename):
#         self._dumpfile = filename
#
#     def dump_data(self):
#         self.save(self._dumpfile)
#
#     def get_nom_and_act_positions(self):
#         x_act = self.sample_x.user_readback.get()
#         y_act = self.sample_y.user_readback.get()
#         z_act = self.sample_z.user_readback.get()
#
#         point = self.position_list[self.current_index]
#         return point['x'], point['y'], point['z'], x_act, y_act, z_act
#
#
# sample_registry = SamplePointRegistry()
