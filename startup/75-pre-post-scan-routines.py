from datetime import datetime
import time

import numpy as np
from bluesky.plan_stubs import mv, mvr
from random import random
import json
from xas.ft_analysis import data_ft


def remove_pb_files(uid):
    run = db[uid]
    for i in run['descriptors']:
        if i['name'] != 'primary':
            os.remove(i['data_keys'][i['name']]['filename'])


def generate_tune_table(motor=hhm.energy, start_energy=5000, stop_energy=13000, step=100):
    table = []
    for energy in range(start_energy, stop_energy + 1, step):
        motor.move(energy)
        time.sleep(0.5)
        tune_mono_pitch(2, 0.025)
        tune_mono_y(0.5, 0.01)
        table.append([energy, hhm.pitch.read()['hhm_pitch']['value'], hhm.y.read()['hhm_y']['value']])
    return table



def set_reference_foil(element:str = 'Mn'):
    # Adding reference foil element list
    with open('/nsls2/xf08id/settings/json/foil_wheel.json') as fp:
        reference_foils = json.load(fp)
    elems = [item['element'] for item in reference_foils]


    if element is None:
        yield from mv(foil_wheel.wheel1, 0)
        yield from mv(foil_wheel.wheel2, 0)
    else:
        if element in elems:
            indx = elems.index(element)
            yield from mv(foil_wheel.wheel2, reference_foils[indx]['fw2'])
            yield from mv(foil_wheel.wheel1, reference_foils[indx]['fw1'])
        else:
            yield from mv(foil_wheel.wheel1, 0)
            yield from mv(foil_wheel.wheel2, 0)

        #yield from mv(foil_wheel.wheel2, reference[element]['foilwheel2'])
        #yield from mv(foil_wheel.wheel1, reference[element]['foilwheel1'])

def set_attenuator(thickness:int  = 0, **kwargs):
    # Adding reference foil element list
    with open('/nsls2/xf08id/settings/json/attenuator.json') as fp:
        attenuators_list = json.load(fp)
    thickness_list = [item['attenuator'] for item in attenuators_list]

    if thickness in thickness_list:
        indx = thickness_list.index(thickness)
        yield from mv(attenuator_motor.pos, attenuators_list[indx]['position'])
    else:
        yield from mv(attenuator_motor.pos,0)



def random_step(x: float = 0,y: float = 0, **kwargs):

    '''
    This plan will move the stage randomly by a random number between
    x/2 and x  and y/2 and y, sampling a donut around the original point
    '''
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    print_to_gui('Executing random move',sys.stdout)
    if  type(x) == str:
        x = float(x)
        y = float(y)
    if not 'motor_x' in kwargs.keys():
        motor_x = giantxy.x
    if not 'motor_y' in kwargs.keys():
        motor_y = giantxy.y
    random_x = 2 * x * (random()-0.5)
    random_x = random_x * 0.5 + 0.5 * np.sign(random_x)
    random_y = 2 * y*(random()-0.5)
    random_y = random_y * 0.5 + 0.5 * np.sign(random_y)
    yield from mvr(motor_x,random_x,motor_y,random_y)



def sleep(delay:float=1, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    yield from bps.sleep(float(delay))
    yield None


class CannotActuateShutter(Exception):
    pass


def get_offsets (time:int = 2, *args, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    try:
        yield from bps.mv(shutter_ph_2b, 'Close')
    except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to close.')
    detectors = [apb_ave]
    uid = (yield from get_offsets_plan(detectors, time))

    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        print('Error: Photon shutter failed to open')

    return uid



def record_offsets_plan(suffix=''):
    fpath = '/nsls2/xf08id/log/offsets/' + str(datetime.now()).replace(':', '-')[:-7] + suffix + '.dat'
    uid = (yield from get_offsets())
    table = db[uid].table()
    table.to_csv(fpath)


def record_offsets_for_all_gains_plan():
    amps = [i0_amp, it_amp, ir_amp, iff_amp]
    # set_gains_plan(*args)
    for gain_value in range(3, 8):

        for amp in amps:
            yield from amp.set_gain_plan(gain_value, bool(0))
        # ttime.sleep(0.5)

        # output = str(gain_value)
        # for amp in amps:
        #     output += ' ' + amp.name + ' ' + str(amp.get_gain())
        # print(output)
        suffix = f' gain-{gain_value}'

        yield from bps.sleep(60)
        yield from record_offsets_plan(suffix=suffix)


def get_adc_readouts(times: int = 20, *args, **kwargs):
    """
    Get Ion Chambers Offsets - Gets the offsets from the ion chambers and automatically subtracts from the acquired data in the next scans
    Parameters
    ----------
    num : int
        Number of points to acquire and average for each ion chamber

    Returns
    -------
    uid : list(str)
        List containing the unique id of the scan

    See Also
    --------
    :func:`tscan`
    """
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    adcs = list(args)
    if not len(adcs):
        adcs = [pba2.adc7, pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]

    old_avers = []
    for adc in adcs:
        old_avers.append(adc.averaging_points.get())
        adc.averaging_points.put(15)
    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to open.')
    uid = (yield from get_offsets_plan(adcs, num=int(times)))


    readouts = []
    df = db[uid].table()

    for index, adc in enumerate(adcs):
        key = '{}_volt'.format(adc.name)
        array = df[key]
        readout = np.mean(df[key][2:int(times)])

        readouts.append(readout)
        print('Channel readout for {}  is {} V'.format(adc.dev_name.get(), readout))
        adc.averaging_points.put(old_avers[index])

    remove_pb_files(uid)

    print('ADC readout complete!')





def adjust_ic_gains( **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    if 'detector_names' not in kwargs:
        # detectors = [pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
        detectors = [apb_ave]
        channels = [ apb_ave.ch1,  apb_ave.ch2,  apb_ave.ch3,  apb_ave.ch4]
        offsets = [apb.ch1_offset, apb.ch2_offset, apb.ch3_offset, apb.ch4_offset]

    e_min, e_max = trajectory_manager.read_trajectory_limits()
    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        print('ERROR: Photon shutter failed to open')
    yield from shutter.open_plan()
    scan_positions = np.arange(e_max + 50, e_min - 50, -200).tolist()

    # plan = bp.list_scan(detectors, hhm.energy, scan_positions)
    flyers = []
    # for detector in detectors:
    #     if hasattr(detector, 'kickoff'):
    #         flyers.append(detector)
    threshold_hi = 3.250
    threshold_lo = 0.250

    for jj in range(3):
    # for jj in range(2):
        plan = bp.list_scan(detectors, hhm.energy, scan_positions)
        yield from plan
        table = db[-1].table()

        all_gains_are_good = True
        # for channel, offset in zip(channels, offsets):
        for channel in channels:
            current_gain = channel.amp.get_gain()[0]
            if channel.polarity == 'neg':
                trace_extreme = table[channel.name].min()
            else:
                trace_extreme = table[channel.name].max()

            # trace_extreme = (trace_extreme - offset.get())/1000
            trace_extreme = trace_extreme  / 1000

            print(f'Extreme value {trace_extreme} for detector {channel.name}')
            if abs(trace_extreme) > threshold_hi:
                print(f'Decreasing gain for detector {channel.name}')
                yield from channel.amp.set_gain_plan(current_gain-1, False)
                all_gains_are_good = False
            elif abs(trace_extreme) <= threshold_hi and abs(trace_extreme) > threshold_lo:
                print(f'Correct gain for detector {channel.name}')
            elif abs(trace_extreme) <= threshold_lo:
                print(f'Increasing gain for detector {channel.name}')
                yield from channel.amp.set_gain_plan(current_gain + 1, False)
                all_gains_are_good = False

        if all_gains_are_good:
            print(f'Gains are correct. Taking offsets..')
            break

    yield from shutter.close_plan()
    yield from get_offsets()

def vibration_diagnostics(time=1):
    cur_divide_value = apb_ave.divide.value
    cur_sample_len = apb_ave.sample_len.value
    cur_wf_len = apb_ave.wf_len.value

    yield from bps.abs_set(apb_ave.divide, 36, wait=True)
    yield from bps.abs_set(apb_ave.sample_len, time*1e4, wait=True)
    yield from bps.abs_set(apb_ave.wf_len, time*1e4, wait=True)

    uid = (yield from bp.count([apb_ave], int(time), md={"plan_name": "vibration_diagnostics"}))

    table = db[uid].table()

    data = np.zeros((int(time * 1e4), 9))
    # print(data.shape)
    data[:, 0] = table['apb_ave_time_wf'][1]

    for i in range(8):
        col_name = 'apb_ave_ch' + str(i + 1) + '_wf'
        data[:, i + 1] = table[col_name][1]

    yield from bps.abs_set(apb_ave.divide, cur_divide_value, wait=True)
    yield from bps.abs_set(apb_ave.sample_len, cur_sample_len, wait=True)
    yield from bps.abs_set(apb_ave.wf_len, cur_wf_len, wait=True)

    data_ft(data)




from xas.energy_calibration import get_foil_spectrum
def validate_element_edge_in_db_proc(element, edge, error_message_func=None):
    try:
        get_foil_spectrum(element, edge, db_proc)
        return True
    except: # Denis, Oct 28, 2021: GUI breaks when error_message_func (the one opening the message box) is ran from exception, but this strange architecture works
        pass
    msg = f'Error: {element} {edge}-edge spectrum has not been added to the database yet'
    if error_message_func is not None:
        error_message_func(msg)
    print_to_gui(msg)
    return False



def calibrate_energy_plan(element, edge, dE=25, plot_func=None, error_message_func=None):
    # # check if current trajectory is good for this calibration
    success = validate_element_edge_in_db_proc(element, edge, error_message_func=error_message_func)
    if not success: return
    success = trajectory_manager.validate_element(element, edge, error_message_func=error_message_func)
    if not success: return
    yield from set_reference_foil(element)
    yield from bps.sleep(1)
    success = foil_camera.validate_barcode(element, error_message_func=error_message_func)
    if not success: return
    yield from adjust_ic_gains()
    name = f'{element} {edge} foil energy calibration'
    yield from fly_scan_with_apb(name, '')
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)
    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual-energy_nominal:.2f} eV')
    success = hhm.calibrate(energy_nominal, energy_actual, error_message_func=error_message_func)
    if not success: return
    trajectory_manager.reinit()
    yield from fly_scan_with_apb(name, '')
    energy_nominal, energy_actual = get_energy_offset(-1, db, db_proc, dE=dE, plot_fun=plot_func)
    print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy shift is {energy_actual - energy_nominal:.2f} eV')
    if np.abs(energy_actual - energy_nominal) < 0.1:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Completed')
    else:
        print_to_gui(f'{ttime.ctime()} [Energy calibration] Energy calibration error is > 0.1 eV. Check Manually.')



# plans for adjusting the roll
def scan_beam_position_vs_energy(camera=camera_sp2):
    camera.stats4.centroid_threshold.put(10)
    centers = []
    energies = np.linspace(6000, 14000, 11)
    for energy in energies:
        print (f'Energy is {energy}')
        hhm.energy.move(energy)
        ttime.sleep(3)
        camera.adjust_camera_exposure_time(target_max_counts=150, atol=10)
        # adjust_camera_exposure_time(camera)
        _centers = []
        for i in range(10):
            ttime.sleep(0.05)
            center = camera.stats4.centroid.x.get()
            _centers.append(center)
        centers.append(np.mean(_centers))
        print(f'Center is {np.mean(_centers)}')

    return energies, np.array(centers)



# def adjust_camera_exposure_time(camera, roi_index=1,
#                                 target_max_counts=150, atol=10,
#                                 max_exp_time_thresh=1,
#                                 min_exp_time_thresh=0.00002):
#     stats = getattr(camera, f'stats{roi_index}')
#     while True:
#         current_maximum = stats.max_value.get()
#         current_exp_time = camera.exp_time.get()
#         delta = np.abs(current_maximum - target_max_counts)
#         ratio = target_max_counts / current_maximum
#         new_exp_time = np.clip(current_exp_time * ratio, min_exp_time_thresh, max_exp_time_thresh)
#
#         if new_exp_time != current_exp_time:
#             if delta > atol:
#                 set_and_wait(camera.exp_time, new_exp_time)
#                 ttime.sleep(np.max((0.5, new_exp_time)))
#                 continue
#         break


# def adjust_camera_exposure_time(camera):
#     while True:
#         current_maximum = camera.stats1.max_value.get()
#         current_exp_time = camera.exp_time.get()
#         if current_maximum < 100:
#             camera.exp_time.put(current_exp_time * 2)
#             ttime.sleep(0.5)
#         elif current_maximum > 230:
#             camera.exp_time.put(current_exp_time / 2)
#             ttime.sleep(0.5)
#         else:
#             break

# data = RE(vibration_diagnostics())


# def get_offsets_plan(detectors = [apb_ave], time = 2):
#     for detector in detectors:
#         detector.divide_old = detector.divide.get()
#
#         yield from bps.abs_set(detector.divide,375) # set sampling to 1 kHz
#         yield from bps.abs_set(detector.sample_len, int(time)*1e3)
#         yield from bps.abs_set(detector.wf_len, int(time) * 1e3)
#
#     uid = (yield from bp.count(detectors,1, md={"plan_name": "get_offsets"}))
#
#     for detector in detectors:
#         yield from bps.abs_set(detector.divide, detector.divide_old)
#
#     table = db[uid].table()





