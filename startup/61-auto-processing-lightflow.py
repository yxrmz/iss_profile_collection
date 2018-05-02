# Things for the ZMQ communication
import socket


from bluesky.callbacks import CallbackBase

# Needs the lightflow environment
from lightflow.config import Config
from lightflow.workflows import start_workflow

# set where the lightflow config file is
lightflow_config_file = "/home/xf08id/.config/lightflow/lightflow.cfg"

def submit_lightflow_job(uid):
    '''
        Submit an interpolation job to lightflow
        
        uid : the uid of the data set
    '''
    config = Config()
    config.load_from_file(lightflow_config_file)

    store_args = dict()
    store_args['uid'] = uid
    store_args['requester'] = socket.gethostname()
    job_id = start_workflow(name='interpolation', config=config,
                            store_args=store_args, queue='iss-workflow')
    print('Started workflow with ID', job_id)

job_submitter = submit_lightflow_job

class InterpolationRequester(CallbackBase):
    '''
        The interpolation requester

        On a stop doc, submits request to lightflow
    '''
    def stop(self, doc):
        uid = doc['run_start']
        submit_lightflow_job(uid)


interpolator = InterpolationRequester()
interpolation_subscribe_id = RE.subscribe(interpolator)
