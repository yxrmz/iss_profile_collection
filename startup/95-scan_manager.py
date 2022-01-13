
import json
import uuid

import numpy as np
from PyQt5 import QtGui
from xas.trajectory import TrajectoryCreator
from xas.xray import generate_energy_grid_from_dict, generate_emission_energy_grid
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

    def create_lightweight_spectrometer_trajectory(self, scan, plot_func):
        if scan['scan_type'] == 'step scan':
            energy, _, time = generate_emission_energy_grid_from_dict(scan['scan_parameters'])
        elif scan['scan_type'] == 'constant energy':
            energy_value = scan['scan_parameters']['energy']
            energy = np.ones(101) * energy_value
            time = np.linspace(0, 1, energy.size)
        plot_func(time, energy)


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
        scan_type = scan['scan_type']
        scan_parameters = scan['scan_parameters']
        aux_parameters = scan_local['aux_parameters']
        common_kwargs = {'name': name,
                         'comment': comment,
                         'detectors': aux_parameters['detectors'],
                         'mono_angle_offset': aux_parameters['offset'],
                         'metadata' : metadata}

        output = []

        # fixing the hhm energy if needed
        hhm_fixed = scan_type == 'constant energy'
        if hhm_fixed:
            output = []
            plan_name = 'set_hhm_energy'
            plan_kwargs = {'energy': scan_parameters['energy']}
            output.append({'plan_name': plan_name,
                           'plan_kwargs': plan_kwargs})

        # fixing the spectrometer energy if needed
        use_spectrometer = 'spectrometer' in aux_parameters.keys()
        spectrometer_fixed = True # if it is not used, we still think of it as fixed
        if use_spectrometer:
            spectrometer_scan_type = aux_parameters['spectrometer']['scan_type']
            spectrometer_scan_parameters = aux_parameters['spectrometer']['scan_parameters']
            spectrometer_fixed = spectrometer_scan_type == 'constant energy'
            if spectrometer_fixed:
                plan_name = 'set_spectrometer_energy'
                plan_kwargs = {'energy': spectrometer_scan_parameters['energy']}
                output.append({'plan_name': plan_name,
                               'plan_kwargs': plan_kwargs})

        # deal with sample_positioning if needed
        if sample_coordinates is not None:
            plan_name = 'move_sample_stage'
            plan_kwargs = {'sample_coordinates': sample_coordinates}
            output.append({'plan_name': plan_name,
                           'plan_kwargs': plan_kwargs})

        # dealing with hhm scanning
        if scan_type == 'step scan':
            plan_name = 'step_scan_plan'
            plan_kwargs = {'trajectory_filename' : scan_parameters['filename'],
                           'element': scan_parameters['element'],
                           'edge': scan_parameters['edge'],
                           'e0': scan_parameters['e0'],
                           }

        elif scan_type == 'fly scan':
            plan_name = 'fly_scan_plan'
            plan_kwargs = {'trajectory_filename': scan_parameters['filename'],
                           'element': scan_parameters['element'],
                           'edge': scan_parameters['edge'],
                           'e0': scan_parameters['e0'],
                           }

        elif scan_type == 'constant energy':

            if spectrometer_fixed:
                plan_name = 'expose_n_times'
                plan_kwargs = {'n_exposures' : scan_parameters['n_exposures'], 'dwell_time' : scan_parameters['dwell_time']}
            else:
                plan_name = 'johann_emission_scan'
                time_grid, energy_grid = generate_emission_energy_grid(scan_parameters['e0'],
                                                                       scan_parameters['preline_start'],
                                                                       scan_parameters['mainline_start'],
                                                                       scan_parameters['mainline_end'],
                                                                       scan_parameters['postline_end'],
                                                                       scan_parameters['preline_stepsize'],
                                                                       scan_parameters['mainline_stepsize'],
                                                                       scan_parameters['postline_stepsize'],
                                                                       scan_parameters['preline_dwelltime'],
                                                                       scan_parameters['mainline_dwelltime'],
                                                                       scan_parameters['postline_dwelltime'])
                plan_kwargs = {#'trajectory_filename': scan_parameters['filename'],
                               #'element': scan_parameters['element'],
                               #'line': scan_parameters['edge'],
                               #'e0': scan_parameters['e0'],
                               'energy_grid' : energy_grid,
                               'time_grid' : time_grid}



        else:
            raise NotImplementedError(f'Scan type "{scan_type}" is not implemented!')

        output.append({'plan_name' : plan_name, 'plan_kwargs' : {**plan_kwargs, **common_kwargs}})
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











