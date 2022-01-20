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
        scan_def = self.create_human_scan_def(scan, name)

        scan_local = {'uid' : uid, 'scan_def' : scan_def, 'aux_parameters' : aux_parameters}
        self.scan_list_local.append(scan_local)
        self.dump_local_scan_list()
        return uid

    def create_human_scan_def(self, scan, name):
        if scan['scan_type'] == 'constant energy':
            scan_str = name + ' mono at ' + str(scan['scan_parameters']['energy'])
            if 'dwell_time' in scan['scan_parameters'].keys():
                scan_str += f" x{scan['scan_parameters']['n_exposures']} {scan['scan_parameters']['dwell_time']} s"
        else:
            scan_str = name + f" {scan['scan_type']}"
            scan_str += f" at {scan['scan_parameters']['element']} - {scan['scan_parameters']['edge']} edge"

        return scan_str


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
        aux_parameters['scan_key'] = self.determine_scan_key(scan, aux_parameters)
        self.create_lightweight_trajectory(scan, plot_func)
        self.add_spectrometer_grids_if_needed(aux_parameters)

    def determine_scan_key(self, scan, aux_parameters):
        mono_is_moving = (scan['scan_type'] != 'constant energy')
        spectrometer_is_used = ('spectrometer' in aux_parameters.keys())

        if spectrometer_is_used:
            spectrometer_is_moving = (aux_parameters['spectrometer']['scan_type'] != 'constant energy')
            spectrometer_is_vonhamos = (aux_parameters['spectrometer']['kind'] == 'von_hamos')
        else: # redundant but why not
            spectrometer_is_moving = False
            spectrometer_is_vonhamos = False

        if mono_is_moving:
            if (not spectrometer_is_used):
                scan_key = 'xas'
            else:
                if spectrometer_is_moving:
                    scan_key = 'johann_rixs'
                else:
                    if spectrometer_is_vonhamos:
                        scan_key = 'von_hamos_rixs'
                    else:
                        scan_key = 'johann_herfd'
        else:
            if (not spectrometer_is_used):
                scan_key = 'constant_e'
            else:
                if spectrometer_is_moving:
                    scan_key = 'johann_xes'
                else:
                    if spectrometer_is_vonhamos:
                        scan_key = 'von_hamos_xes'
                    else:
                        scan_key = 'constant_e_johann'

        return scan_key

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
        scan = self.scan_dict[scan_uid]
        return self.parse_scan_to_plan_from_parameters(name,
                                                       comment,
                                                       scan,
                                                       scan_local['aux_parameters'],
                                                       sample_coordinates=sample_coordinates,
                                                       metadata=metadata)


    def parse_scan_to_plan_from_parameters(self, name, comment, scan, aux_parameters, sample_coordinates=None, metadata={}, rixs_log_name=None):
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
            plan_name = 'move_sample_stage'
            plan_kwargs = {'sample_coordinates': sample_coordinates}
            output.append({'plan_name': plan_name,
                           'plan_kwargs': plan_kwargs})

        if scan_key == 'xas':
            if scan_type == 'step scan':
                plan_name = 'step_scan_plan'
            elif scan_type == 'fly scan':
                plan_name = 'fly_scan_plan'
            plan_kwargs = {'trajectory_filename': scan_parameters['filename'],
                           'element': scan_parameters['element'],
                           'edge': scan_parameters['edge'],
                           'e0': scan_parameters['e0']}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs}})

        elif scan_key == 'von_hamos_xes':
            pass

        elif scan_key == 'von_hamos_rixs':
            pass

        elif scan_key == 'constant_e':
            plan_name = 'collect_n_exposures'
            plan_kwargs = {'n_exposures': scan_parameters['n_exposures'],
                           'dwell_time': scan_parameters['dwell_time'],
                           'energy': scan_parameters['energy']}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs}})

        elif scan_key == 'constant_e_johann':
            plan_name = 'collect_n_exposures_johann'
            spectrometer_energy = aux_parameters['spectrometer']['scan_parameters']['energy']
            plan_kwargs = {'n_exposures': scan_parameters['n_exposures'],
                           'dwell_time': scan_parameters['dwell_time'],
                           'energy': scan_parameters['energy'],
                           'spectrometer_energy': spectrometer_energy}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs}})

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
            if rixs_log_name is not None:
                plan_kwargs['rixs_log_name'] = rixs_log_name
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs}})

        elif scan_key == 'johann_xes':
            plan_name = 'step_scan_johann_xes_plan'
            spectrometer_energy_grid = aux_parameters['spectrometer']['scan_parameters']['energy_grid']
            spectrometer_time_grid = aux_parameters['spectrometer']['scan_parameters']['time_grid']
            plan_kwargs = {'mono_energy': scan_parameters['energy'],
                           'emission_energy_grid': spectrometer_energy_grid,
                           'emission_time_grid': spectrometer_time_grid}
            output.append({'plan_name': plan_name, 'plan_kwargs': {**plan_kwargs, **common_kwargs}})

        elif scan_key == 'johann_rixs':
            spectrometer_energy_grid = aux_parameters['spectrometer']['scan_parameters']['energy_grid']
            if type(sample_coordinates) == list:
                assert len(sample_coordinates) == len(spectrometer_energy_grid), 'number of positions on the sample must match the number of energy points on emission grid'
            else:
                sample_coordinates = [sample_coordinates] * len(spectrometer_energy_grid)

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
                                                                        rixs_log_name=name)
                output.extend(_local_output)

        return output

    def generate_plan_list(self, name, comment, repeat, delay, scan_idx, sample_coordinates=None):
        plans = []
        for indx in range(int(repeat)):
            name_n = '{} {:04d}'.format(name, indx + 1)
            plan_list_for_scan = self.parse_scan_to_plan(name_n, comment, scan_idx, sample_coordinates=sample_coordinates)
            plans.extend(plan_list_for_scan)
            if delay > 0:
                plans.append({'plan_name': 'sleep', 'plan_kwargs': {'time': delay}})
        return plans

scan_manager = ScanManager()





class ScanProcessor():

    def __init__(self):
        self.logger = self.get_logger()
        self.RE = RE
        self.scan_manager = scan_manager
        self.plan_list = []

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
        self.plan_list.extend(plans)

    def run(self):
        while len(self.plan_list) > 0:
            plan_dict = self.plan_list[0]
            plan = basic_plan_dict[plan_dict['plan_name']](**plan_dict['plan_kwargs'])
            print(f'{ttime.ctime()}   started doing plan {plan}')
            self.RE(plan)
            print(f'{ttime.ctime()}   done doing plan {plan}')
            self.plan_list.pop(0)
            # self.RE(plan)

scan_processor = ScanProcessor()











