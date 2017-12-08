import os
import os.path as op
from subprocess import call
from pathlib import Path


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
    def __init__(self, gen_parser, xia_parser, db, beamline_gpfs_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gen_parser = gen_parser
        self.xia_parser = xia_parser
        self.db = db
        self.md = {}
        self.user_data_path = Path(beamline_gpfs_path) / Path('User Data')
        self.xia_data_path = Path(beamline_gpfs_path) / Path('xia_files')

    def start(self, doc):
        self.md = doc

    def stop(self, doc):
        self.process(self.md)

    def process(self, md={}):
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

        if 'xia_filename' not in md:
            self.process_tscan()
        else:
            self.process_tscanxia(md, current_filepath)

        division = self.gen_parser.interp_df['i0'].values / self.gen_parser.interp_df['it'].values
        division[division < 0] = 1

        self.gen_parser.export_trace_hdf5(current_filepath[:-5], '')
        self.gen_parser.export_trace(current_filepath[:-5], '')
        #store_results_databroker(md,
        #                         parent_uid,
        #                         db_analysis,
        #                         'interpolated',
        #                         Path(filepath) / Path('2017.3.301954/SPS_Brow_Xcut_R12 28.hdf5'),
        #                         root=rootpath)

    def process_tscan(self):
        interp_base = 'i0'
        self.gen_parser.interpolate(key_base=interp_base)

    def process_tscanxia(self, md, current_filepath):
        #TODO XIA
        pass

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
