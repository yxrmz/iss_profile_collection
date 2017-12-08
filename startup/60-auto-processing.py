import os
import os.path as op
from subprocess import call
from pathlib import Path
from isstools.xiaparser import xiaparser
from isstools.xasdata import xasdata

# Things for the ZMQ communication
import json
import pandas as pd
import numpy as np
import zmq
import socket

context = zmq.Context()
sender = context.socket(zmq.PUB)
sender.bind("tcp://*:5562")

def create_ret(scan_type, uid, process_type, data, requester):
    ret = {'type':scan_type,
           'uid': uid,
           'processing_ret':{
                             'type':process_type,
                             'data':data
                            }
          }

    return (requester + json.dumps(ret)).encode()


class CallbackBase:
    def __call__(self, name, doc):
        "Dispatch to methods expecting particular doc types."
        return getattr(self, name)(doc)

    def event(self, doc):
        pass

    def bulk_events(self, doc):
        pass

    def descriptor(self, doc):
        pass

    def start(self, doc):
        pass

    def stop(self, doc):
        pass


class ScanProcessor(CallbackBase):
    def __init__(self, gen_parser, xia_parser, db, beamline_gpfs_path, zmq_sender, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gen_parser = gen_parser
        self.xia_parser = xia_parser
        self.db = db
        self.md = {}
        self.user_data_path = Path(beamline_gpfs_path) / Path('User Data')
        self.xia_data_path = Path(beamline_gpfs_path) / Path('xia_files')
        self.sender = zmq_sender

    def start(self, doc):
        pass

    def stop(self, doc):
        self.md = self.db[doc['run_start']]['start']
        self.process(self.md)

    def process(self, md={}):
        print('starting processing!')
        if md == {}:
            md = self.md
        current_path = self.create_user_dirs(self.user_data_path,
                                             md['year'],
                                             md['cycle'],
                                             md['PROPOSAL'])
        current_filepath = Path(current_path) / Path(md['name'])
        current_filepath = ScanProcessor.get_new_filepath(str(current_filepath) + '.hdf5')
        current_uid = md['uid']
        self.gen_parser.load(current_uid)

        if 'plan_name' in md:
            if md['plan_name'] == 'get_offsets':
                pass
            elif md['plan_name'] == 'execute_trajectory':
                if 'xia_filename' not in md:
                    self.process_tscan()
                else:
                    self.process_tscanxia(md, current_filepath)

                division = self.gen_parser.interp_df['i0'].values / self.gen_parser.interp_df['it'].values
                division[division < 0] = 1

                self.gen_parser.export_trace_hdf5(current_filepath[:-5], '')
                self.gen_parser.export_trace(current_filepath[:-5], '')

                requester = socket.gethostname()
                ret = create_ret('spectroscopy', current_uid, 'interpolate', self.gen_parser.interp_df.to_json(),
                                 requester)
                self.sender.send(ret)
                print('Done with the interpolation!')

                e0 = int(md['e0'])
                bin_df = self.gen_parser.bin(e0, e0 - 30, e0 + 50, 10, 0.2, 0.04)
                self.gen_parser.data_manager.export_dat(current_filepath[:-5]+'.hdf5')
                ret = create_ret('spectroscopy', current_uid, 'bin', bin_df.to_json(), requester)
                self.sender.send(ret)
                print('Done with the binning!')

                #store_results_databroker(md,
                #                         parent_uid,
                #                         db_analysis,
                #                         'interpolated',
                #                         Path(filepath) / Path('2017.3.301954/SPS_Brow_Xcut_R12 28.hdf5'),
                #                         root=rootpath)
            elif md['plan_name'] == 'relative_scan':
                pass

    def process_tscan(self):
        interp_base = 'i0'
        self.gen_parser.interpolate(key_base=interp_base)

    def process_tscanxia(self, md, current_filepath):
        # Parse xia
        xia_filename = md['xia_filename']
        xia_filepath = 'smb://xf08id-nas1/xia_data/{}'.format(xia_filename)
        xia_destfilepath = '{}{}'.format(self.xia_data_path, xia_filename)
        smbclient = xiaparser.smbclient(xia_filepath, xia_destfilepath)
        try:
            smbclient.copy()
        except Exception as exc:
            if exc.args[1] == 'No such file or directory':
                print('*** File not found in the XIA! Check if the hard drive is full! ***')
            else:
                print(exc)
            print('Abort current scan processing!\nDone!')
            return

        interp_base = 'xia_trigger'
        self.gen_parser.interpolate(key_base=interp_base)
        xia_parser = self.xia_parser
        xia_parser.parse(xia_filename, self.xia_data_path)
        xia_parsed_filepath = current_filepath[0: current_filepath.rfind('/') + 1]
        xia_parser.export_files(dest_filepath=xia_parsed_filepath, all_in_one=True)

        try:
            if xia_parser.channelsCount():
                length = min(xia_parser.pixelsCount(0), len(self.gen_parser.interp_arrays['energy']))
                if xia_parser.pixelsCount(0) != len(self.gen_parser.interp_arrays['energy']):
                    len_xia = xia_parser.pixelsCount(0)
                    len_pb = len(self.gen_parser.interp_arrays['energy'])
                    raise Exception('XIA Pixels number ({}) != '
                                    'Pizzabox Trigger number ({})'.format(len_xia, len_pb))
            else:
                raise Exception("Could not find channels data in the XIA file")
        except Exception as exc:
            print('***', exc, '***')

        mcas = []
        if 'xia_rois' in md:
            xia_rois = md['xia_rois']
            if 'xia_max_energy' in md:
                xia_max_energy = md['xia_max_energy']
            else:
                xia_max_energy = 20

            for mca_number in range(1, xia_parser.channelsCount() + 1):
                if '{}_mca{}_roi0_high'.format(xia1.name, mca_number) in xia_rois:
                    rois_array = []
                    roi_numbers = [roi_number for roi_number in
                                   [roi.split('mca{}_roi'.format(mca_number))[1].split('_high')[0] for roi in
                                   xia_rois if len(roi.split('mca{}_roi'.format(mca_number))) > 1] if
                                   len(roi_number) <= 3]
                    for roi_number in roi_numbers:
                        rois_array.append(
                            [xia_rois['{}_mca{}_roi{}_high'.format(xia1.name, mca_number, roi_number)],
                             xia_rois['{}_mca{}_roi{}_low'.format(xia1.name, mca_number, roi_number)]])
                    mcas.append(xia_parser.parse_roi(range(0, length), mca_number, rois_array, xia_max_energy))
                else:
                    mcas.append(xia_parser.parse_roi(range(0, length), mca_number, [
                        [xia_rois['xia1_mca1_roi0_low'], xia_rois['xia1_mca1_roi0_high']]], xia_max_energy))

            for index_roi, roi in enumerate([[i for i in zip(*mcas)][ind] for ind, k in enumerate(roi_numbers)]):
                xia_sum = [sum(i) for i in zip(*roi)]
                if len(self.gen_parser.interp_arrays['energy']) > length:
                    xia_sum.extend([xia_sum[-1]] * (len(self.gen_parser.interp_arrays['energy']) - length))
                roi_label = ''
                #roi_label = getattr(self.parent_gui.widget_sdd_manager, 'edit_roi_name_{}'.format(roi_numbers[index_roi])).text()
                if not len(roi_label):
                    roi_label = 'XIA_ROI{}'.format(roi_numbers[index_roi])

                self.gen_parser.interp_arrays[roi_label] = np.array(
                    [self.gen_parser.interp_arrays['energy'][:, 0], xia_sum]).transpose()
                #self.figure.ax.plot(self.gen_parser.interp_arrays['energy'][:, 1], -(
                #    self.gen_parser.interp_arrays[roi_label][:, 1] / self.gen_parser.interp_arrays['i0'][:, 1]))

    def create_user_dirs(self, user_data_path, year, cycle, proposal):
        current_user_dir = Path(f"{year}.{cycle}.{proposal}")

        user_data_path = Path(user_data_path) / current_user_dir
        ScanProcessor.create_dir(user_data_path)

        log_path = user_data_path / Path('log')
        ScanProcessor.create_dir(log_path)

        snapshots_path = log_path / Path('snapshots')
        ScanProcessor.create_dir(snapshots_path)

        return user_data_path

    def get_new_filepath(filepath):
        if op.exists(Path(filepath)):
            if filepath[-5:] == '.hdf5':
                filepath = filepath[:-5]
            iterator = 2

            while True:
                new_filepath = f'{filepath}-{iterator}.hdf5'
                if not op.isfile(new_filepath):
                    return new_filepath
                iterator += 1
        return filepath

    def create_dir(path):
        if not op.exists(path):
            os.makedirs(path)
            call(['setfacl', '-m', 'g:iss-staff:rwx', path])
            call(['chmod', '770', path])


gen_parser = xasdata.XASdataGeneric(hhm.pulses_per_deg, db, db_analysis)
xia_parser = xiaparser.xiaparser()

processor = ScanProcessor(gen_parser, xia_parser, db, '/GPFS/xf08id/', sender)
processor_subscribe_id = RE.subscribe(processor)
