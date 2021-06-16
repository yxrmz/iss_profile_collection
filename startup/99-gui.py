# from PyQt5.QtWidgets import QApplication
import atexit
import requests
import os
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import time as ttime

# sample_stages = [{'x': giantxy.x.name, 'y': giantxy.y.name},
#                  {'x': samplexy.x.name, 'y': samplexy.y.name},
#                  {'x': huber_stage.z.name, 'y': huber_stage.y.name}]


#app = QApplication(sys.argv)

if not os.environ.get('AZURE_TESTING'):
    from isstools import xlive

    plan_funcs = {

        'Fly scan (new PB)': fly_scan_with_apb,
        'Fly scan w/Xspress 3': fly_scan_with_xs3,
        'Fly scan w/Pilatus100k': fly_scan_with_pil100k,
        'fly scan Johann RIXS w/Pilatus': fly_scan_rixs_w_pilatus,
        'Step scan': step_scan,
        'Step scan w/Pilatus': step_scan_w_pilatus,
        'Step scan w/Xspress 3': step_scan_w_xs,
        # 'Constant energy': constant_energy,
        # 'Spiral fly scan': fly_scan_over_spiral,
        'Step scan Johann Emission w/Pilatus': step_scan_emission_w_pilatus,
        'Step scan Johann RIXS w/Pilatus': step_scan_rixs_w_pilatus,
    }

    service_plan_funcs = {
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
        'johann_calibration_scan_plan' : johann_calibration_scan_plan,
        'n_pil100k_exposures_plan' : n_pil100k_exposures_plan,
    }


    aux_plan_funcs = {
        'get_adc_readouts': get_adc_readouts,
        'prepare_traj_plan': prep_traj_plan,
        'general_scan': general_scan,
        'general_spiral_scan': general_spiral_scan,
        'set_reference_foil': set_reference_foil,
        'tuning_scan': tuning_scan,
    }

    xlive_gui = xlive.XliveGui(plan_funcs=plan_funcs,
        service_plan_funcs=service_plan_funcs,
        aux_plan_funcs=aux_plan_funcs,
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
    #sys.exit(app.exec_())

    sys.stdout = xlive_gui.emitstream_out
    sys.stderr = xlive_gui.emitstream_err


    def cleaning():
       if xlive_gui.piezo_thread.isRunning():
           xlive_gui.toggle_piezo_fb(0)

    atexit.register(cleaning)
