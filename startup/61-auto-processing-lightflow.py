# Things for the ZMQ communication
import socket


from bluesky.callbacks import CallbackBase

# Needs the lightflow environment
from lightflow.config import Config
from lightflow.workflows import start_workflow

# set where the lightflow config file is
lightflow_config_file = "/home/xf08id/.config/lightflow/lightflow.cfg"

import socket

def create_interp_request(uid):
    '''
        Create an interpolation request.

    '''
    data = dict()
    requester = str(socket.gethostname())
    request = {
            'uid': uid,
            'requester': requester,
            'type': 'spectroscopy',
            'processing_info': {
                'type': 'interpolate',
                'interp_base': 'i0'
            }
        }
    return request 


def submit_lightflow_job(request):
    '''
        Submit an interpolation job to lightflow
        
        uid : the uid of the data set
    '''
    config = Config()
    config.load_from_file(lightflow_config_file)

    store_args = dict()
    store_args['request'] = request
    job_id = start_workflow(name='interpolation', config=config,
                            store_args=store_args, queue='iss-workflow')
    print('Started workflow with ID', job_id)

# takes a request as argument
job_submitter = submit_lightflow_job

class InterpolationRequester(CallbackBase):
    '''
        The interpolation requester

        On a stop doc, submits request to lightflow
    '''
    def stop(self, doc):
        uid = doc['run_start']
        request = create_interp_request(uid)
        submit_lightflow_job(request)

import sys
sys.path.append("/home/xf08id/Repos/workflows")
class InterpolationRequesterNoLightFlow(CallbackBase):
    '''
        The interpolation requester

        On a stop doc, submits request to lightflow
    '''
    # NOTE : for testing ONLY
    def stop(self, doc):
        uid = doc['run_start']
        request = create_interp_request(uid)
        #submit_lightflow_job(request)
        store = dict()
        store['request'] = request
        data = dict()
        import interpolation
        interpolation.process_run_func(data, store, None, None)


#interpolator = InterpolationRequester()
interpolator = InterpolationRequesterNoLightFlow()
interpolation_subscribe_id = RE.subscribe(interpolator)
