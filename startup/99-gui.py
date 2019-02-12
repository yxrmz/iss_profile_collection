from isstools import xlive
import collections
import atexit
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)




# sample_stages = [{'x': giantxy.x.name, 'y': giantxy.y.name},
#                  {'x': samplexy.x.name, 'y': samplexy.y.name},
#                  {'x': huber_stage.z.name, 'y': huber_stage.y.name}]




shutter_dictionary = collections.OrderedDict([(shutter_fe.name, shutter_fe),
                                         (shutter_ph.name, shutter_ph),
                                         (shutter.name, shutter)])

ic_amplifiers = {'i0_amp': i0_amp,
                 'it_amp': it_amp,
                 'ir_amp': ir_amp,
                 'iff_amp': iff_amp}

xlive_gui = xlive.XliveGui(plan_funcs={
                                'Fly scan':       fly_scan,
                                'Fly scan with SDD':    fly_scan_with_sdd,
                                'Fly scan with Area Detector':    fly_scan_with_camera,
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
                           window_title="XLive @ISS/08-ID NSLS-II Development",
                           )


def xlive():
    xlive_gui.show()

#xview_gui = xview.XviewGui(hhm.pulses_per_deg, db=db)

#def xview():
    #xview_gui.show()

xlive()
print('Startup complete')

sys.stdout = xlive_gui.emitstream_out
sys.stderr = xlive_gui.emitstream_err


#def cleaning():
#    if xlive_gui.piezo_thread.isRunning():
#        xlive_gui.toggle_piezo_fb(0)

#atexit.register(cleaning)

#def cleaning():
#    if xlive_gui.piezo_thread.isRunning():
#        xlive_gui.toggle_piezo_fb(0)

#atexit.register(cleaning)


#
# def load():
#     uid = db[-1]['start']['uid']
#     aa = xasdata_load_dataset_from_files(db, uid)
#     print(f'took {timer()-start}')
#     return aa





