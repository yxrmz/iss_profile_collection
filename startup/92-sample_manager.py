
# from PyQt5 import uic, QtGui, QtCore, QtWidgets
# from PyQt5.Qt import Qt

from pandas import DataFrame




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
