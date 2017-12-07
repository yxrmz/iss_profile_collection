import uuid
from databroker import Broker
import time
import os.path as op
import jsonschema
from event_model import DocumentNames, schemas
from databroker.assets.handlers_base import HandlerBase
from collections import namedtuple
import pandas as pd
import h5py

from pathlib import Path


def store_results_databroker(md, parent_uid, db, stream_name, filepath, root=None):
    ''' Save results to a databroker instance.
        Takes a streamdoc instance.

        md : the metadata
        parent_uid : the parent scan uid
        db : the databroker instance
        filename : the full filename of file you want to write
            needs to be an absolute path

        It is assumed everything here can be written with the same writer.
    '''

    # This part creates all the documents
    start_doc = dict()
    # update the start doc with the metadata
    start_doc.update(**md)
    start_doc['time'] = time.time()
    start_doc['uid'] = str(uuid.uuid4())
    start_doc['plan_name'] = 'analysis'
    start_doc['save_timestamp'] = time.time()
    # start_doc['parent_uid'] = parent_uid
    start_doc['name'] = stream_name

    # just make one descriptor and event document for now
    # initialize both event and descriptor
    descriptor_doc = dict()
    event_doc = dict()
    event_doc['data'] = dict()
    event_doc['timestamps'] = dict()
    descriptor_doc['data_keys'] = dict()
    descriptor_doc['time'] = time.time()
    descriptor_doc['uid'] = str(uuid.uuid4())
    descriptor_doc['run_start'] = start_doc['uid']
    descriptor_doc['name'] = stream_name

    full_path = Path(root) / Path(filepath)

    # Check if file exists
    if not op.exists(full_path):
        raise IOError(f'The requested file {full_path} does not exist.')

    chunk_size = 1024
    resource_uid = db_analysis.reg.register_resource(
        f'ISS-{stream_name}',
        root,
        filepath,
        {'chunk_size': chunk_size})

    # Get shape of HDF5 file
    f = h5py.File(full_path, mode='r')
    shape = [list(f.values())[0].shape[0], len(list(f.keys()))]
    linecount = list(f.values())[0].shape[0]
    f.close()

    now = time.time()

    events = []
    chunk_count = linecount // chunk_size + int(linecount % chunk_size != 0)
    for chunk_num in range(chunk_count):
        datum_uid = db_analysis.reg.register_datum(resource_uid,
                                                   {'chunk_num': chunk_num})
        data = {stream_name: datum_uid}
        events.append({'data': data,
                       'descriptor': descriptor_doc['uid'],
                       'filled': {stream_name: False},
                       'seq_num': chunk_num,
                       'time': now,
                       'timestamps': {key: now for key in data},
                       'uid': str(uuid.uuid4())})

    descriptor_doc['data_keys'][stream_name] = {
        'dtype': 'array',
        'external': 'FILESTORE:',
        'filename': str(full_path),
        'shape': shape,
        'source': f'iss-{stream_name}'
    }

    stop_doc = dict()
    stop_doc['time'] = time.time()
    stop_doc['uid'] = str(uuid.uuid4())
    stop_doc['run_start'] = start_doc['uid']
    stop_doc['exit_status'] = 'success'
    stop_doc['name'] = 'primary'

    # write the database results here to mongodb
    jsonschema.validate(start_doc, schemas[DocumentNames.start])
    jsonschema.validate(descriptor_doc, schemas[DocumentNames.descriptor])
    jsonschema.validate(stop_doc, schemas[DocumentNames.stop])
    db.insert('start', start_doc)
    db.insert('descriptor', descriptor_doc)
    for event_doc in events:
        jsonschema.validate(event_doc, schemas[DocumentNames.event])
        db.insert('event', event_doc)
    db.insert('stop', stop_doc)


class SpectroscopyInterpHandler(HandlerBase):
    def __init__(self, fpath, chunk_size):
        self.chunk_size = chunk_size

        f = h5py.File(fpath, mode='r')
        df = pd.DataFrame({key: value for key, value in zip(f.keys(), f.values())})
        keys = list(df.keys())
        linecount = len(df)
        f.close()

        if '1' in keys:
            keys[keys.index('1')] = 'Ones'
        self.row = namedtuple('row', keys)
        self.array = df.values

        # with open(fpath, 'r') as f:
        #    self.lines = np.array(list(f))[lines_header:]

    def __call__(self, chunk_num):
        cs = self.chunk_size
        return {field: val for field, val in
                zip(self.row._fields, self.array[chunk_num * cs:(chunk_num + 1) * cs, :].transpose())}


md = dict(sample_name = "foo", user="Bruno")
db_analysis = Broker.named("iss-analysis")
db_analysis.reg.register_handler('ISS-interpolated', SpectroscopyInterpHandler, overwrite=True)
rootpath = '/GPFS/xf08id'
filepath = 'User Data'

# parent_uid = 'bla'
#store_results_databroker(md,
#                         parent_uid,
#                         db_analysis,
#                         'interpolated',
#                         Path(filepath) / Path('2017.3.301954/SPS_Brow_Xcut_R12 28.hdf5'),
#                         root=rootpath)

# Retrieving data:
#hdr = db_analysis[-1]
#dd = [_['data'] for _ in db_analysis.get_events(hdr, stream_name='interpolated', fill=True)]
#result = {}
#for chunk in [chunk['interpolated'] for chunk in dd]:
#    for key in chunk.keys():
#        if key in result:
#            result[key] = np.concatenate((result[key], chunk[key]))
#            continue
#        result[key] = chunk[key]
#result_df = pd.DataFrame(result)
#result_df