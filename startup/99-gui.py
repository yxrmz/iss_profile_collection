from isstools import xlive

import atexit
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import time as ttime

# sample_stages = [{'x': giantxy.x.name, 'y': giantxy.y.name},
#                  {'x': samplexy.x.name, 'y': samplexy.y.name},
#                  {'x': huber_stage.z.name, 'y': huber_stage.y.name}]

xlive_gui = xlive.XliveGui(plan_funcs={

    'Fly scan (new PB)': fly_scan_with_apb,
    'Step scan': step_scan,
    'Step scan w/Pilatus': step_scan_w_pilatus,
    'Step scan w/Xspress 3': step_scan_w_xs,
    'Constant energy': constant_energy,
    'Spiral fly scan': fly_scan_over_spiral,
    'Fly scan with SDD': fly_scan_with_sdd,
    'Fly scan with Area Detector': fly_scan_with_camera,

},
    service_plan_funcs={
        'get_offsets': get_offsets,
        'sleep': sleep,
        'random_step': random_step,
        'set_gains': set_gains,
        'adjust_ic_gains': adjust_ic_gains,
        'prepare_beamline_plan': prepare_beamline_plan,
        'tune_beamline_plan': tune_beamline_plan,
        'optimize_beamline_plan': optimize_beamline_plan,
        'optimize_sample_plan': optimize_sample_plan,
        'xs_count': xs_count,
        'pil_count': pil_count,

    },
    aux_plan_funcs={
        'get_adc_readouts': get_adc_readouts,
        'prepare_traj_plan': prep_traj_plan,
        'general_scan': general_scan,
        'general_spiral_scan': general_spiral_scan,
        'set_reference_foil': set_reference_foil,

        'tuning_scan': tuning_scan,

    },
    RE=RE,
    db=db,
    accelerator=nsls_ii,
    hhm=hhm,
    sdd=xs,
    shutters_dict=shutter_dictionary,
    det_dict=detector_dictionary,
    motors_dict=motor_dictionary,
    camera_dict=camera_dictionary,
    sample_stage=giantxy,
    tune_elements=tune_elements,
    ic_amplifiers=ic_amplifiers,
    window_title="XLive @ISS/08-ID NSLS-II",
    apb=apb_ave
)

def xlive():
    xlive_gui.show()

xlive()
print(f'Startup complete at {ttime.ctime()}')


sys.stdout = xlive_gui.emitstream_out
sys.stderr = xlive_gui.emitstream_err


def cleaning():
   if xlive_gui.piezo_thread.isRunning():
       xlive_gui.toggle_piezo_fb(0)

atexit.register(cleaning)
