import matplotlib
matplotlib.use("Agg")

import uuid
from databroker import Broker
import time
import os.path as op
import jsonschema
from event_model import DocumentNames, schemas
from databroker.assets.handlers_base import HandlerBase
from collections import namedtuple

from pathlib import Path

import pandas as pd
import h5py

'''
    Proposed Handler/Writer Scheme:

    1. The Handler:
        It works as usual: resource kwargs initialize the instance
        and datum kwargs retrieve data upon calling the instance.
    2. The Writer:
        The writer should write data that is eventually read by the handler.
        Therefore:
        I. The initialization should require the same exact kwargs that the
            handler's initialization requires. i.e. The information used to
            retrieve should be enough to write and vice versa.
        II. The call should receive a data dictionary and iterate over each
            key. This should then return the datum_kwargs necessary to re-read
            this data. i.e. When we send this data for writing, we need to know
            how to get it back.

    This scheme requires just two items for transforming data into a series of
    documents:
        1. data_dicts: a list of nested dicionaries:
            data_dicts[n][stream_name][key] gives one data element (number, np array etc)
            where n is just a number, stream_name the stream name and key the data_keyt
        2. md: metadata for the start document

    Optionally, one can pass a writers_dict. This is a dictionary of writers:
        writers_dict[data_key]
                        ['writer']
                        ['resource']
                            ['func'] : the funcition to create the resource
                                        of form f(docs, data_key, **additional_kwargs)
                            ['kwargs']  : the additional kwargs for the func above
                        ['root'] : the analysis root
                        ['spec'] : the spec id for the handler

        Here
            - 'data_key' is the key name of the data.
            - 'writer' is the writer
            - 'resource' is information on building theresrouce 
                -'func' is the function that builds the resource,
                    of form func(docs, data_key)
                        where docs is a dict of the documents (start, descriptor, event)
                        and data_key is the data key
                - 'kwargs' are additional kwargs for the func
            - 'root' : the root directory (for the resource)
            - 'spec' : the spec id for the handler that would read this


    This should be enough to submit documents to an analysis store.
                        
            

    Resources/similar work:
        CJ has written a library that takes data and tranforms it into a series of documents:
            https://github.com/xpdAcq/SHED/blob/master/shed/translation.py
        This does not write data to disk, or emit resource/datum documents.

'''
class HDF5DFHandler(HandlerBase):
    ''' Pandas dataframe handler
        
        The filename is all that is needed for initialization.

        To get data, one calls this initialized object with the corresponding
        key.
    '''
    def __init__(self, fpath):
        self._fpath = fpath

    def __call__(self, key):
        return pd.read_hdf(self._fpath, key)

class HDF5DFWriter(HandlerBase):
    ''' Pandas dataframe writer

        The resource is initialized with the same args as the file handler.

        A dictionary of data is supplied for writing.
        The call should return the arguments necessary for the file handler.
    '''
    def __init__(self, fpath):
        '''
            resource_func : callable
                returns resource kwargs for retrieval
        '''
        self.fpath = fpath

    def __call__(self, data_dict):
        '''
            Assumes data frames given.
        '''
        for key, df in data_dict.items():
            df.to_hdf(self.fpath, key, mode='a')
        return dict(key=key)


# the writers should have a function that creates a resource for them
import datetime
def make_resource_hdf5dfwriter(docs, data_key, root=""):
    '''
        Make a resource given documents
        docs : a dict of the documents
            start, descriptor, event
            (one for each, not list)
        data_key : the data_key in the event being written
    '''
    # just need the start to get the metadata
    # but could access the descriptors or other
    md = docs['start']
    now = datetime.datetime.now()
    fpath = root + "/" + md['cycle'] + "/" + md['proposal'] + "/"
    fpath = fpath + str(uuid.uuid4()) + ".h5"
    # check if exists and create
    directory = os.path.dirname(fpath)
    print("making sure {} exists".format(directory))
    os.makedirs(directory, exist_ok=True)
    print("file paht is {}".format(fpath))
    return dict(fpath=fpath)


ISSANALYSISROOT = "/home/xf08id/nsls2/data"
ISSANALYSISSPEC = 'ISS-hdf5-df'
# dict of key, writer, and callable to make resource args
external_writers = {'interp_df' : {'writer': HDF5DFWriter, 
                                    'resource': {'func': make_resource_hdf5dfwriter,
                                    'kwargs' : dict(root=ISSANALYSISROOT)},
                                    'root' : ISSANALYSISROOT,
                                    'spec' : ISSANALYSISSPEC,
                                    },
                    'bin_df' : {'writer': HDF5DFWriter, 
                                    'resource': {'func': make_resource_hdf5dfwriter,
                                    'kwargs' : dict(root=ISSANALYSISROOT)},
                                    'root' : ISSANALYSISROOT,
                                    'spec' : ISSANALYSISSPEC,
                                    },
                    }


# TODO : allow one more level in data_dicts?
#  (data_dicts[i][stream_name][key] etc)
# currently it's
#  (data_dicts[i][key])
def ingest(data_dicts, md={}, external_writers={}):
    ''' Save results to a databroker instance.
        Takes a streamdoc instance.

        md : the metadata
        data_dicts : list of data dictionaries

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
    start_doc['save_timestamp'] = time.time()
    jsonschema.validate(start_doc, schemas[DocumentNames.start])
    yield ('start', start_doc)


    # just make one descriptor and event document for now
    # initialize both event and descriptor
    descriptor_docs = dict()
    event_doc = dict()
    event_doc['data'] = dict()
    event_doc['timestamps'] = dict()


    for i, data_stream_dict in enumerate(data_dicts):
        for stream_name, data_dict in data_stream_dict.items():
            if descriptor_docs.get(stream_name, None) is None:
                # make descriptor
                descriptor_docs[stream_name] = dict()

                descriptor_doc = descriptor_docs[stream_name]
                descriptor_doc['data_keys'] = dict()
                descriptor_doc['time'] = time.time()
                descriptor_doc['uid'] = str(uuid.uuid4())
                descriptor_doc['run_start'] = start_doc['uid']
                descriptor_doc['name'] = stream_name
                for key, data in data_dict.items():
                    descriptor_doc['data_keys'][key] = {
                        # TODO : how to define a df here?
                        'dtype': 'array',
                        'external': 'FILESTORE:',
                        'shape': None,
                        'source': f'iss-{stream_name}'
                        }
                jsonschema.validate(descriptor_doc, schemas[DocumentNames.descriptor])
                yield ('descriptor', descriptor_doc)

            descriptor_doc = descriptor_docs[stream_name]
            if list(descriptor_doc['data_keys'].keys()) != list(data_dict.keys()):
                raise ValueError("Keys don't match")

            now = time.time()
            # create event
            event_doc = {'data': data_dict,
                     'descriptor': descriptor_doc['uid'],
                     'seq_num': i,
                     'time': now,
                     'timestamps': {key: now for key in data_dict},
                     'uid': str(uuid.uuid4()),
                     'filled' : {key : True for key in data_dict}
                     }
            # now save events to filestore if requested
            # (don't unfill)
            for key, data in data_dict.items():
                if key in external_writers:
                    print("Found key {} in writers".format(key))
                    writer_dict = external_writers[key]
                    writer = writer_dict['writer']
    
                    # the function that creates the resource
                    writer_resource_func = writer_dict['resource']['func']
                    writer_resource_func_kwargs = writer_dict['resource'].get('kwargs', {})
                    docs= dict(start=start_doc, descriptor=descriptor_doc, event=event_doc)
                    resource_kwargs = writer_resource_func(docs=docs, data_key=key, **writer_resource_func_kwargs)
                    print("got resource kwargs {}".format(resource_kwargs))
                    resource_path = resource_kwargs.get('fpath', '')
                    print("got file path : {}".format(resource_path))
    
                    writer_spec = writer_dict['spec']
                    writer_root = writer_dict['root'] 
    
                    # writer and handler share same resource kwargs
                    writer_instance = writer(**resource_kwargs)
                    # write the data dictionary, get datum kwargs
                    # the actual writing is done here
                    print("Writing data key {}".format(key))
                    datum_kwargs = writer_instance(dict(key=data))
                    print("Done")
                    resource_uid = str(uuid.uuid4())
                    resource = {'id': resource_uid,
                             'path_semantics': 'posix',
                              'resource_kwargs': resource_kwargs,
                              'resource_path' : resource_path,
                              'root': writer_root,
                              'spec': writer_spec,
                              'uid': resource_uid}
    
                    datum_uid = str(uuid.uuid4())
                    datum = {'datum_id': datum_uid,
                             'datum_kwargs': datum_kwargs,
                             'resource': resource_uid}
    
                    event_doc['filled'][key] = False
                    event_doc['data'][key] = datum_uid
    
                    yield ('resource', resource)
                    yield ('datum', datum)
    
                    #datum_uid = db_analysis.reg.register_datum(resource_uid,
                                                       #{'chunk_num': chunk_num})
            jsonschema.validate(event_doc, schemas[DocumentNames.event])
            yield ('event', event_doc)

    # write the database results here to mongodb

    stop_doc = dict()
    stop_doc['time'] = time.time()
    stop_doc['uid'] = str(uuid.uuid4())
    stop_doc['run_start'] = start_doc['uid']
    stop_doc['exit_status'] = 'success'
    stop_doc['name'] = 'primary'
    jsonschema.validate(stop_doc, schemas[DocumentNames.stop])
    yield ('stop', stop_doc)


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
