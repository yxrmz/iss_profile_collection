import matplotlib
matplotlib.use("Agg")

import uuid


# TEST root
ISSANALYSISROOT = "/tmp"
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


md = dict(sample_name="foo", user="Julien", cycle="2018-1", proposal="00000")
# add more data
md['parent_uid'] = ""
md['plan_name'] = 'analysis'
md['name'] = 'analysis'

# test data
import pandas as pd
import h5py

df_dict = [
            dict(a=1, b=2, c=3),
            dict(a=2, b=2, c=3),
            dict(a=1, b=1, c=3),
            dict(a=1, b=2, c=4),
            ]

df = pd.DataFrame(df_dict)

df.to_hdf("foo.hd5", "df1")

data_dicts = [
        dict(primary=dict(interp_df=df))
        ]

doc_gen = ingest(data_dicts, md=md, external_writers=external_writers)

# rewriteing because there has been a refactor
from databroker import Broker
class ToDataBroker:
    '''
        This version is for *before* the asset refactor.
    '''
    def __init__(self, dbname, reg=None):
        '''
            Callback to write back into analysis store
        '''
        self.db = Broker.named(dbname)
        if reg is None:
            self.reg = self.db.reg

    def __call__(self, name, doc):
        getattr(self, name)(doc)

    def start(self, doc):
        self.db.insert('start', doc)

    def descriptor(self, doc):
        self.db.insert('descriptor', doc)

    def event(self, doc):
        self.db.insert('event', doc)

    def stop(self, doc):
        self.db.insert('stop', doc)

    def resource(self, doc):
        # TODO : After refactor, we can give a uid
        # For now, uid is mutated
        # TODO: Assumed that datums follow in order
        # make sure this is documented somewhere
        resource = dict(
            spec=doc['spec'],
            root=doc['root'],
            resource_path=doc['resource_path'],
            resource_kwargs=doc['resource_kwargs'],
        )
        self.resource_uid = self.db.reg.insert_resource(**resource)
        

    def datum(self, doc):
        datum_id = doc['datum_id']
        datum_kwargs = doc['datum_kwargs']
        # TODO Add this after the refactor
        #resource_id = doc['resource']
        # and replace self here
        self.db.reg.insert_datum(self.resource_uid, datum_id, datum_kwargs)

dbname = 'iss-analysis'
todb = ToDataBroker(dbname)
for nds in doc_gen:
    todb(*nds)

db_analysis = Broker.named("iss-analysis")
db_analysis.reg.register_handler(ISSANALYSISSPEC, HDF5DFHandler)
