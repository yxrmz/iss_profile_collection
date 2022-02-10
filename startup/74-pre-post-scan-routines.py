from datetime import datetime
import time

import numpy as np
from bluesky.plan_stubs import mv, mvr
from random import random
import json
from xas.ft_analysis import data_ft





# def sleep(delay : int=1, **kwargs):
#     sys.stdout = kwargs.pop('stdout', sys.stdout)
#     print_to_gui(f'Pausing for {delay} seconds....',sys.stdout)
#     yield from (bps.sleep(int(delay)))
#     print_to_gui(f'Resuming', sys.stdout)

class CannotActuateShutter(Exception):
    pass


# def get_offsets(time:int = 2, *args, **kwargs):
#     sys.stdout = kwargs.pop('stdout', sys.stdout)
#
#     try:
#         yield from bps.mv(shutter_ph_2b, 'Close')
#     except FailedStatus:
#         raise CannotActuateShutter(f'Error: Photon shutter failed to close.')
#     detectors = [apb_ave]
#     uid = (yield from get_offsets_plan(detectors, time))
#
#     try:
#         yield from bps.mv(shutter_ph_2b, 'Open')
#     except FailedStatus:
#         print('Error: Photon shutter failed to open')
#
#     return uid


def actuate_photon_shutter_plan(state):
    try:
        yield from bps.mv(shutter_ph_2b, state)
    except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to {state.lower()}.')

def get_offsets_plan(time : float = 2):
    apb_ave.save_current_status()
    prepare_detectors_for_exposure_plan([apb_ave], n_exposures=1)
    set_detector_exposure_time_plan([apb_ave], time)

    yield from actuate_photon_shutter_plan('Close')
    uid = (yield from bp.count([apb_ave], 1, md={"plan_name": "get_offsets_plan"}))
    yield from actuate_photon_shutter_plan('Open')

    yield from apb_ave.restore_to_saved_status()

    table = db[uid].table()

    for i in range(0,8):
        mean =  float(table[f'apb_ave_ch{i+1}_mean'])
        print_to_gui(f'Mean {(mean)}')
        ch_offset = getattr(apb_ave, f'ch{i+1}_offset')
        yield from bps.abs_set(ch_offset, mean)



# def record_offsets_plan(suffix=''):
#     fpath = '/nsls2/xf08id/log/offsets/' + str(datetime.now()).replace(':', '-')[:-7] + suffix + '.dat'
#     uid = (yield from get_offsets())
#     table = db[uid].table()
#     table.to_csv(fpath)


# def record_offsets_for_all_gains_plan():
#     amps = [i0_amp, it_amp, ir_amp, iff_amp]
#     # set_gains_plan(*args)
#     for gain_value in range(3, 8):
#
#         for amp in amps:
#             yield from amp.set_gain_plan(gain_value, bool(0))
#         # ttime.sleep(0.5)
#
#         # output = str(gain_value)
#         # for amp in amps:
#         #     output += ' ' + amp.name + ' ' + str(amp.get_gain())
#         # print(output)
#         suffix = f' gain-{gain_value}'
#
#         yield from bps.sleep(60)
#         yield from record_offsets_plan(suffix=suffix)


def general_set_gains_plan(*args):
    """
    Parameters
    ----------
    Groups of three parameters: amplifier, gain, hs

    Example: set_gains_and_offsets(i0_amp, 5, False, it_amp, 4, False, iff_amp, 5, True)
    """

    mod = len(args) % 3
    if mod:
        args = args[:-mod]

    for ic, val, hs in zip([ic for index, ic in enumerate(args) if index % 3 == 0],
                       [val for index, val in enumerate(args) if index % 3 == 1],
                       [hs for index, hs in enumerate(args) if index % 3 == 2]):
        yield from ic.set_gain_plan(val, hs)

        if type(ic) != ICAmplifier:
            raise Exception('Wrong type: {} - it should be ICAmplifier'.format(type(ic)))
        if type(val) != int:
            raise Exception('Wrong type: {} - it should be int'.format(type(val)))
        if type(hs) != bool:
            raise Exception('Wrong type: {} - it should be bool'.format(type(hs)))

        print_to_gui('set amplifier gain for {}: {}, {}'.format(ic.par.dev_name.get(), val, hs))


def set_gains_plan(i0_gain: int = 5, it_gain: int = 5, iff_gain: int = 5,
              ir_gain: int = 5, hs: bool = False):
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    yield from general_set_gains_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs)




def optimize_gains_plan(n_tries=3):
    # sys.stdout = kwargs.pop('stdout', sys.stdout)

    # if 'detector_names' not in kwargs:
    # detectors = [pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
    detectors = [apb_ave]
    channels = [ apb_ave.ch1,  apb_ave.ch2,  apb_ave.ch3,  apb_ave.ch4]
    # offsets = [apb.ch1_offset, apb.ch2_offset, apb.ch3_offset, apb.ch4_offset]

    yield from actuate_photon_shutter_plan('Open')
    yield from shutter.open_plan()

    e_min, e_max = trajectory_manager.read_trajectory_limits()
    scan_positions = np.arange(e_max + 50, e_min - 50, -200).tolist()

    threshold_hi = 3.250
    threshold_lo = 0.250

    for jj in range(n_tries):

        plan = bp.list_scan(detectors, hhm.energy, scan_positions)
        yield from plan
        table = db[-1].table()

        all_gains_are_good = True

        for channel in channels:
            current_gain = channel.amp.get_gain()[0]
            if channel.polarity == 'neg':
                trace_extreme = table[channel.name].min()
            else:
                trace_extreme = table[channel.name].max()

            trace_extreme = trace_extreme / 1000

            print_to_gui(f'Extreme value {trace_extreme} for detector {channel.name}')
            if abs(trace_extreme) > threshold_hi:
                print_to_gui(f'Decreasing gain for detector {channel.name}')
                yield from channel.amp.set_gain_plan(current_gain - 1, False)
                all_gains_are_good = False
            elif abs(trace_extreme) <= threshold_hi and abs(trace_extreme) > threshold_lo:
                print_to_gui(f'Correct gain for detector {channel.name}')
            elif abs(trace_extreme) <= threshold_lo:
                print(f'Increasing gain for detector {channel.name}')
                yield from channel.amp.set_gain_plan(current_gain + 1, False)
                all_gains_are_good = False

        if all_gains_are_good:
            print(f'Gains are correct. Taking offsets..')
            break

    yield from shutter.close_plan()
    yield from get_offsets_plan()



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





