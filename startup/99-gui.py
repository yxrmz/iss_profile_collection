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

    xlive_gui = xlive.XliveGui(service_plan_funcs=service_plan_funcs,
                               aux_plan_funcs=aux_plan_funcs,
                               scan_manager=scan_manager,
                               plan_processor=plan_processor,
                               RE=RE,
                               db=db,
                               db_proc=db_proc,
                               accelerator=nsls_ii,
                               hhm=hhm,
                               hhm_encoder=hhm_encoder,
                               hhm_feedback=hhm_feedback,
                               trajectory_manager=trajectory_manager,
                               johann_spectrometer_motor=johann_spectrometer_motor,
                               sdd=xs,
                               pil100k=pil100k,
                               apb=apb_ave,
                               apb_trigger_xs=apb_trigger,
                               apb_trigger_pil100k=apb_trigger_pil100k,
                               detector_dict=detector_dictionary,
                               shutter_dict=shutter_dictionary,
                               motor_dict=motor_dictionary,
                               camera_dict=camera_dictionary,
                               sample_stage=giantxy,
                               tune_elements=tune_elements,
                               ic_amplifiers=ic_amplifiers,
                               window_title="XLive @ISS/08-ID NSLS-II")


    def xlive():
        xlive_gui.show()

    xlive()

    print(f'Startup complete at {ttime.ctime()}')
    #sys.exit(app.exec_())

    sys.stdout = xlive_gui.emitstream_out
    sys.stderr = xlive_gui.emitstream_err


    # def cleaning():
    #    if xlive_gui.widget_beamline_setup.piezo_thread.isRunning():
    #        xlive_gui.widget_beamline_setup.toggle_piezo_fb(0)
    #
    # atexit.register(cleaning)
