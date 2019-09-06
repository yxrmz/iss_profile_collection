from isstools import xlive

import atexit
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# sample_stages = [{'x': giantxy.x.name, 'y': giantxy.y.name},
#                  {'x': samplexy.x.name, 'y': samplexy.y.name},
#                  {'x': huber_stage.z.name, 'y': huber_stage.y.name}]

xlive_gui = xlive.XliveGui(plan_funcs={
                                    'Fly scan':                     fly_scan,
                                    'Step scan':                    step_scan,
                                    'Constant energy' :             constant_energy,
                                    'Spiral fly scan':              fly_scan_over_spiral,
                                    'Fly scan with SDD':            fly_scan_with_sdd,
                                    'Fly scan with Area Detector':  fly_scan_with_camera,

                           },
                           service_plan_funcs={
                                'get_adc_offsets':  get_adc_offsets,
                                'sleep':                   sleep,
                                'random_step':          random_step,
                                'set_gains':        set_gains,
                                'adjust_ic_gains': adjust_ic_gains,
                                'prepare_beamline_plan': prepare_beamline_plan,

                           },
                           aux_plan_funcs ={
                               'get_adc_readouts': get_adc_readouts,
                               'prepare_traj_plan': prep_traj_plan,
                               'general_scan': general_scan,
                               'set_reference_foil': set_reference_foil,
                               'write_html_log':     write_html_log,
                               'tuning_scan': tuning_scan,


                           },
                           RE = RE,
                           db = db,
                           accelerator = nsls_ii,
                           hhm = hhm,
                           shutters_dict =shutter_dictionary,
                           det_dict=detector_dictionary,
                           motors_dict=motor_dictionary,
                           sample_stage = giantxy,
                           tune_elements = tune_elements,
                           ic_amplifiers = ic_amplifiers,
                           window_title="XLive @ISS/08-ID NSLS-II",
                           )

# # jlynch 2019/9/5
# # XIA debugging
# from bluesky.utils import ts_msg_hook
# RE.msg_hook = ts_msg_hook
# # jlynch 2019/9/5


def xlive():
    xlive_gui.show()

xlive()
print('Startup complete')

sys.stdout = xlive_gui.emitstream_out
sys.stderr = xlive_gui.emitstream_err


#def cleaning():
#    if xlive_gui.piezo_thread.isRunning():
#        xlive_gui.toggle_piezo_fb(0)

#atexit.register(cleaning)







