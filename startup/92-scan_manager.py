import copy
import json
import uuid

import numpy as np
from PyQt5 import QtGui
from xas.trajectory import TrajectoryCreator
from xas.xray import generate_energy_grid_from_dict, generate_emission_energy_grid_from_dict
import os

import logging
import logging.handlers








class ScanManager():
    def __init__(self, json_file_path = '/nsls2/xf08id/settings/json/scan_manager.json'):
        self.init_global_manager(json_file_path)
        self.load_local_manager()
        self.trajectory_path = trajectory_manager.trajectory_path
        self.trajectory_creator = TrajectoryCreator()

    def init_global_manager(self, json_file_path):
        self.json_file_path = json_file_path
        with open(self.json_file_path, 'r') as f:
            self.scan_dict = json.loads(f.read())

    def init_local_manager(self):
        self.json_file_path_local = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/scan_manager.json"
        self.scan_list_local = []

    def load_local_manager(self):
        self.json_file_path_local = f"{ROOT_PATH}/{USER_FILEPATH}/{RE.md['year']}/{RE.md['cycle']}/{RE.md['PROPOSAL']}/scan_manager.json"
        try:
            with open(self.json_file_path_local, 'r') as f:
                self.scan_list_local = json.loads(f.read())
        except FileNotFoundError:
            self.init_local_manager()

    def dump_local_scan_list(self):
        with open(self.json_file_path_local, 'w') as f:
            json.dump(self.scan_list_local, f )

    def add_scan(self, scan, aux_parameters, name):
        uid = self.check_if_brand_new(scan)
        scan_def = f"{name} ({aux_parameters['scan_description']})"
        scan_local = {'uid' : uid, 'scan_def' : scan_def, 'aux_parameters' : aux_parameters}
        self.scan_list_local.append(scan_local)
        self.dump_local_scan_list()
        return uid

    def delete_local_scan(self, idx):
        self.scan_list_local.pop(idx)
        self.dump_local_scan_list()

    def check_if_brand_new(self, new_scan):
        for uid, scan in self.scan_dict.items():
            if scan['scan_type'] == scan['scan_type']:
                scan_parameters = scan['scan_parameters']
                new_scan_parameters = new_scan['scan_parameters']
                keys =  scan_parameters.keys()
                new_keys = new_scan_parameters.keys()
                if all([(new_k in keys) for new_k in new_keys]):
                    parameters_match = True
                    for k in keys:
                        if k != 'filename':
                            if scan_parameters[k] != new_scan_parameters[k]:
                                parameters_match = False
                                break
                    if parameters_match:
                        print('SCAN IS OLD')
                        return uid

        new_uid = self.make_scan_uid()
        print('SCAN IS NEW')
        self.scan_dict[new_uid] = new_scan
        self.create_trajectory_file(new_scan, new_uid)
        os.rename(self.json_file_path, f'{os.path.splitext(self.json_file_path)[0]}.bak')
        with open(self.json_file_path, 'w') as f:
            json.dump(self.scan_dict, f )
        return new_uid

    def make_scan_uid(self):
        return str(uuid.uuid4())[:13]

    def create_scan_preview(self, scan, aux_parameters, plot_func):
        self.determine_and_describe_type_of_scan(scan, aux_parameters)
        self.create_lightweight_trajectory(scan, plot_func)
        self.add_spectrometer_grids_if_needed(aux_parameters)

    def determine_and_describe_type_of_scan(self, scan, aux_parameters):
        mono_is_moving = (scan['scan_type'] != 'constant energy')
        spectrometer_is_used = ('spectrometer' in aux_parameters.keys())

        scan_parameters = scan['scan_parameters']

        if spectrometer_is_used:
            spectrometer_is_moving = (aux_parameters['spectrometer']['scan_type'] != 'constant energy')
            spectrometer_is_vonhamos = (aux_parameters['spectrometer']['kind'] == 'von_hamos')
        else: # redundant but why not
            spectrometer_is_moving = False
            spectrometer_is_vonhamos = False

        if mono_is_moving:
            if (not spectrometer_is_used):
                scan_key = 'xas'
                scan_description = f"mono {scan['scan_type']} at {scan_parameters['element']}-{scan_parameters['edge']} edge"
            else:
                if spectrometer_is_moving: # only johann can move together with mono
                    scan_key = 'johann_rixs'
                    element = aux_parameters['spectrometer']['scan_parameters']['element']
                    line = aux_parameters['spectrometer']['scan_parameters']['line']
                    scan_description = f"RIXS with mono {scan['scan_type']} at {scan_parameters['element']}-{scan_parameters['edge']} edge and Johann at {element}-{line} line"

                else:
                    if spectrometer_is_vonhamos:
                        scan_key = 'von_hamos_rixs'
                        scan_description = f"RIXS with mono {scan['scan_type']} at {scan_parameters['element']}-{scan_parameters['edge']} edge with Von Hamos"
                    else:
                        scan_key = 'johann_herfd'
                        spectrometer_energy = aux_parameters['spectrometer']['scan_parameters']['energy']
                        scan_description = f"mono {scan['scan_type']} at {scan_parameters['element']}-{scan_parameters['edge']} edge with Johann at Eout={spectrometer_energy}"
        else:
            if (not spectrometer_is_used):
                scan_key = 'constant_e'
                scan_description = f"mono at Ein={scan_parameters['energy']} x{scan_parameters['n_exposures']} for {scan_parameters['dwell_time']} s"
            else:
                if spectrometer_is_moving:
                    scan_key = 'johann_xes'
                    element = aux_parameters['spectrometer']['scan_parameters']['element']
                    line = aux_parameters['spectrometer']['scan_parameters']['line']
                    scan_description = f"mono at Ein={scan_parameters['energy']} with Johann {aux_parameters['spectrometer']['scan_type']} at {element}-{line} line"
                else:
                    if spectrometer_is_vonhamos:
                        scan_key = 'von_hamos_xes'
                        scan_description = f"mono at Ein={scan_parameters['energy']} with Von Hamos x{scan_parameters['n_exposures']} for {scan_parameters['dwell_time']} s"
                    else:
                        scan_key = 'constant_e_johann'
                        spectrometer_energy = aux_parameters['spectrometer']['scan_parameters']['energy']
                        scan_description = f"mono at Ein={scan_parameters['energy']} with Johann at Eout={spectrometer_energy} x{scan_parameters['n_exposures']} for {scan_parameters['dwell_time']} s"

        aux_parameters['scan_key'] = scan_key
        aux_parameters['scan_description'] = scan_description

    def create_lightweight_trajectory(self, scan, plot_func):
        if scan['scan_type'] == 'fly scan':
            self.trajectory_creator.define_complete(scan['scan_parameters'], lightweight=True)
            energy = self.trajectory_creator.energy
            time = self.trajectory_creator.time
        elif scan['scan_type'] == 'step scan':
            energy, _, time = generate_energy_grid_from_dict(scan['scan_parameters'])
        elif scan['scan_type'] == 'constant energy':
            energy_value = scan['scan_parameters']['energy']
            energy = np.ones(101) * energy_value
            time = np.linspace(0, 1, energy.size)
        plot_func(time, energy)

    def add_spectrometer_grids_if_needed(self, aux_parameters):
        scan_key = aux_parameters['scan_key']
        if scan_key == 'johann_xes':
            energy_grid, time_grid = generate_emission_energy_grid_from_dict(aux_parameters['spectrometer']['scan_parameters'])
            aux_parameters['spectrometer']['scan_parameters']['time_grid'] = time_grid.tolist()
            aux_parameters['spectrometer']['scan_parameters']['energy_grid'] = energy_grid.tolist()
        elif scan_key == 'johann_rixs':
            energy_grid, _ = generate_emission_energy_grid_from_dict(aux_parameters['spectrometer']['scan_parameters'])
            aux_parameters['spectrometer']['scan_parameters']['energy_grid'] = energy_grid.tolist()

    def create_trajectory_file(self, scan, uid):
        filename = f'{uid}.txt'
        filepath = self.trajectory_path + filename
        if scan['scan_type'] == 'fly scan':
            self.trajectory_creator.define_complete(scan['scan_parameters'])
            self.trajectory_creator.save(filepath)
        elif scan['scan_type'] == 'step scan':
            energy, dwell_time, _ = generate_energy_grid_from_dict(scan['scan_parameters'])
            data = np.vstack((energy, dwell_time)).T
            element = scan['scan_parameters']['element']
            edge = scan['scan_parameters']['edge']
            e0 = scan['scan_parameters']['e0']
            if scan['scan_parameters']['revert'] : direction = 'backward'
            else: direction = 'forward'
            header = f'element: {element}, edge: {edge}, E0: {e0}, direction: {direction}'
            np.savetxt(filepath, data, header=header)
        elif scan['scan_type'] == 'constant energy':
            filename = ''

        self.scan_dict[uid]['scan_parameters']['filename'] = filename

    def parse_scan_to_plan(self, name, comment, scan_idx, sample_coordinates=None, metadata={}):
        scan_local = self.scan_list_local[scan_idx]
        scan_uid = scan_local['uid']
        metadata['monochromator_scan_uid'] = scan_uid
        scan = self.scan_dict[scan_uid]
        return self.parse_scan_to_plan_from_parameters(name,
                                                       comment,
                                                       scan,
                                                       scan_local['aux_parameters'],
                                                       sample_coordinates=sample_coordinates,
                                                       metadata=metadata)


    def parse_scan_to_plan_from_parameters(self, name, comment, scan, aux_parameters, sample_coordinates=None, metadata={}, rixs_file_name=None):
        scan_type = scan['scan_type']
        scan_parameters = scan['scan_parameters']

        scan_key = aux_parameters['scan_key']
        common_kwargs = {'name': name,
                         'comment': comment,
                         'detectors': aux_parameters['detectors'],
                         'mono_angle_offset': aux_parameters['offset'],
                         'metadata': metadata}

        output = []

        if type(sample_coordinates) == dict:
            plan_name = 'move_sample_stage_plan'
            plan_kwargs = {'sample_coordinates': sample_coordinates}
            output.append({'plan_name': plan_name,
                           'plan_kwargs': plan_kwargs,
                           'plan_description' : generate_plan_description(plan_name, plan_kwargs)})

        if scan_key == 'xas':
            if scan_type == 'step scan':
                plan_name = 'step_scan_plan'
            elif scan_type == 'fly scan':
                plan_name = 'fly_scan_plan'
            plan_kwargs = {'trajectory_filename': scan_parameters['filename'],
                           'element': scan_parameters['element'],
                           'edge': scan_parameters['edge'],
                           'e0': scan_parameters['e0']}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'constant_e':
            plan_name = 'collect_n_exposures_plan'
            plan_kwargs = {'n_exposures': scan_parameters['n_exposures'],
                           'dwell_time': scan_parameters['dwell_time'],
                           'mono_energy': scan_parameters['energy']}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'von_hamos_xes':
            plan_name = 'collect_von_hamos_xes_plan'
            plan_kwargs = {'n_exposures': scan_parameters['n_exposures'],
                           'dwell_time': scan_parameters['dwell_time'],
                           'mono_energy': scan_parameters['energy']}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'von_hamos_rixs':
            if scan_type == 'step scan':
                plan_name = 'step_scan_von_hamos_plan'
            elif scan_type == 'fly scan':
                plan_name = 'fly_scan_von_hamos_plan'
            plan_kwargs = {'trajectory_filename': scan_parameters['filename'],
                           'element': scan_parameters['element'],
                           'edge': scan_parameters['edge'],
                           'e0': scan_parameters['e0']}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'constant_e_johann':
            plan_name = 'collect_n_exposures_johann_plan'
            spectrometer_energy = aux_parameters['spectrometer']['scan_parameters']['energy']
            plan_kwargs = {'n_exposures': scan_parameters['n_exposures'],
                           'dwell_time': scan_parameters['dwell_time'],
                           'mono_energy': scan_parameters['energy'],
                           'spectrometer_energy': spectrometer_energy}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'johann_xes':
            plan_name = 'step_scan_johann_xes_plan'
            spectrometer_energy_grid = aux_parameters['spectrometer']['scan_parameters']['energy_grid']
            spectrometer_time_grid = aux_parameters['spectrometer']['scan_parameters']['time_grid']
            element = aux_parameters['spectrometer']['scan_parameters']['element']
            line = aux_parameters['spectrometer']['scan_parameters']['line']
            e0 = aux_parameters['spectrometer']['scan_parameters']['e0']
            plan_kwargs = {'mono_energy': scan_parameters['energy'],
                           'emission_energy_list': spectrometer_energy_grid,
                           'emission_time_list': spectrometer_time_grid,
                           'element': element,
                           'line': line,
                           'e0': e0}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'johann_herfd':
            if scan_type == 'step scan':
                plan_name = 'step_scan_johann_herfd_plan'
            elif scan_type == 'fly scan':
                plan_name = 'fly_scan_johann_herfd_plan'
            spectrometer_energy = aux_parameters['spectrometer']['scan_parameters']['energy']
            plan_kwargs = {'trajectory_filename': scan_parameters['filename'],
                           'element': scan_parameters['element'],
                           'edge': scan_parameters['edge'],
                           'e0': scan_parameters['e0'],
                           'spectrometer_energy': spectrometer_energy}
            if rixs_file_name is not None:
                plan_kwargs['rixs_file_name'] = rixs_file_name
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs},
                           'plan_description' : generate_plan_description(plan_name, {**plan_kwargs, **common_kwargs})})

        elif scan_key == 'johann_rixs':
            spectrometer_energy_grid = aux_parameters['spectrometer']['scan_parameters']['energy_grid']
            if type(sample_coordinates) == list:
                assert len(sample_coordinates) == len(spectrometer_energy_grid), 'number of positions on the sample must match the number of energy points on emission grid'
            else:
                sample_coordinates = [sample_coordinates] * len(spectrometer_energy_grid)

            _local_rixs_file_name = create_interp_file_name(name, '.rixs')

            for emission_energy, _local_sample_coordinates in zip(spectrometer_energy_grid, sample_coordinates):

                _local_name = f'{name} E={str(emission_energy)}'
                _local_comment = f'{comment} E={str(emission_energy)}'
                _local_spectrometer_parameters = {'kind' : 'johann',
                                                  'scan_type': 'constant energy',
                                                  'scan_parameters': {'energy': emission_energy}}
                _local_aux_parameters = copy.deepcopy(aux_parameters)
                _local_aux_parameters['spectrometer'] = _local_spectrometer_parameters
                _local_aux_parameters['scan_key'] = 'johann_herfd'
                _local_output = self.parse_scan_to_plan_from_parameters(_local_name,
                                                                        _local_comment,
                                                                        scan,
                                                                        _local_aux_parameters,
                                                                        sample_coordinates=_local_sample_coordinates,
                                                                        metadata=metadata,
                                                                        rixs_file_name=_local_rixs_file_name)
                output.extend(_local_output)

        return output

    def generate_plan_list(self, name, comment, repeat, delay, scan_idx, sample_coordinates=None):
        plans = []
        for indx in range(int(repeat)):
            name_n = '{} {:04d}'.format(name, indx + 1)
            plan_list_for_scan = self.parse_scan_to_plan(name_n, comment, scan_idx, sample_coordinates=sample_coordinates)
            plans.extend(plan_list_for_scan)
            if delay > 0:
                plans.append({'plan_name': 'sleep', 'plan_kwargs': {'delay': delay}})
        return plans

scan_manager = ScanManager()





class ScanProcessor():

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





scan_processor = ScanProcessor()











