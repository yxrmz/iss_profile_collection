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
    # except FailedStatus:
    #     raise CannotActuateShutter(f'Error: Photon shutter failed to {state.lower()}.')
    except Exception as e:
        print_to_gui(f'{str(e)}', tag='SHUTTER DEBUG')
        yield from bps.null()

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


def check_photon_shutter_plan():
    if shutter_ph_2b.status.get() == shutter_ph_2b.close_val:
        print_to_gui(f'Attempting to open PH shutter.', add_timestamp=True, tag='Beamline')
        yield from actuate_photon_shutter_plan('Open')


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

    for ic_amp, val, hs in zip([ic for index, ic in enumerate(args) if index % 3 == 0],
                       [val for index, val in enumerate(args) if index % 3 == 1],
                       [hs for index, hs in enumerate(args) if index % 3 == 2]):
        yield from ic_amp.set_gain_plan(val, hs)

        if type(ic_amp) != ICAmplifier:
            raise Exception('Wrong type: {} - it should be ICAmplifier'.format(type(ic)))
        if type(val) != int:
            raise Exception('Wrong type: {} - it should be int'.format(type(val)))
        if type(hs) != bool:
            raise Exception('Wrong type: {} - it should be bool'.format(type(hs)))

        print_to_gui('set amplifier gain for {}: {}, {}'.format(ic_amp.name, val, hs))


def set_gains_plan(i0_gain: int = 5, it_gain: int = 5, ir_gain: int = 5, iff_gain: int = 5,
               hs: bool = False):
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    yield from general_set_gains_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs)
    yield from get_offsets_plan()


def prepare_trajectory_plan(trajectory_filename, offset=None):
    trajectory_stack.set_trajectory(trajectory_filename, offset=offset)
    yield from bps.null()

def prepare_scan_plan(scan_uid=None, aux_parameters=None):
    scan = scan_manager.scan_dict[scan_uid]
    if scan['scan_type'] == 'fly scan':
        mono_angle_offset = aux_parameters['offset']
        trajectory_filename = scan['scan_parameters']['filename']
        yield from prepare_trajectory_plan(trajectory_filename, offset=mono_angle_offset)


def optimize_gains_plan(n_tries=3, trajectory_filename=None, mono_angle_offset=None):
    # sys.stdout = kwargs.pop('stdout', sys.stdout)

    # if 'detector_names' not in kwargs:
    # detectors = [pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
    detectors = [apb_ave]
    channels = [ apb_ave.ch1,  apb_ave.ch2,  apb_ave.ch3,  apb_ave.ch4]
    # offsets = [apb.ch1_offset, apb.ch2_offset, apb.ch3_offset, apb.ch4_offset]

    if trajectory_filename is not None:
        yield from prepare_trajectory_plan(trajectory_filename, offset=mono_angle_offset)
        # trajectory_stack.set_trajectory(trajectory_filename, offset=mono_angle_offset)

    threshold_hi = 3.250
    threshold_lo = 0.250

    e_min, e_max = trajectory_manager.read_trajectory_limits()
    scan_positions = np.arange(e_max + 50, e_min - 50, -200).tolist()

    yield from actuate_photon_shutter_plan('Open')
    yield from shutter.open_plan()

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


def quick_optimize_gains_plan(n_tries=3, trajectory_filename=None, mono_angle_offset=None):
    # sys.stdout = kwargs.pop('stdout', sys.stdout)

    # if 'detector_names' not in kwargs:
    # detectors = [pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
    # detectors = [apb_ave]
    # channels = [ apb_ave.ch1,  apb_ave.ch2,  apb_ave.ch3,  apb_ave.ch4]
    channels = [apb.ch1, apb.ch2, apb.ch3, apb.ch4]
    # offsets = [apb.ch1_offset, apb.ch2_offset, apb.ch3_offset, apb.ch4_offset]

    if trajectory_filename is not None:
        yield from prepare_trajectory_plan(trajectory_filename, offset=mono_angle_offset)
        # trajectory_stack.set_trajectory(trajectory_filename, offset=mono_angle_offset)

    threshold_hi = 3.250
    threshold_lo = 0.250

    e_min, e_max = trajectory_manager.read_trajectory_limits()
    e_min -= 50
    e_max += 50
    # scan_positions = np.arange(e_max + 50, e_min - 50, -200).tolist()

    yield from actuate_photon_shutter_plan('Open')
    yield from shutter.open_plan()

    for jj in range(n_tries):

        # current_energy = hhm.energy.position
        # e1 = np.abs(current_energy - e_min), np.abs(current_energy - e_max)

        yield from bps.mv(hhm.energy, e_max)

        @return_NullStatus_decorator
        def _move_energy_plan():
            yield from move_mono_energy(e_min, step=200, beampos_tol=10)

        ramp_plan = ramp_plan_with_multiple_monitors(_move_energy_plan(), [hhm.energy] + channels, bps.null)
        yield from ramp_plan

        # plan = bp.list_scan(detectors, hhm.energy, scan_positions)
        # yield from plan
        table = process_monitor_scan(db, -1)

        all_gains_are_good = True

        for channel in channels:

            # if channel.polarity == 'neg':
            trace_extreme = table[channel.name].min()
            # else:
            #     trace_extreme = table[channel.name].max()

            trace_extreme = trace_extreme / 1000

            print_to_gui(f'Extreme value {trace_extreme} for detector {channel.name}')

            current_gain = channel.amp.get_gain()[0]
            if abs(trace_extreme) > threshold_hi:
                if current_gain > 3:
                    print_to_gui(f'Decreasing gain for detector {channel.name}')
                    yield from channel.amp.set_gain_plan(current_gain - 1, False)
                    all_gains_are_good = False
            elif abs(trace_extreme) <= threshold_hi and abs(trace_extreme) > threshold_lo:
                print_to_gui(f'Correct gain for detector {channel.name}')
            elif abs(trace_extreme) <= threshold_lo:
                if current_gain < 7:
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
    with open(f'{ROOT_PATH_SHARED}/settings/json/foil_wheel.json') as fp:
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

###########################
# Akhil Tayal added new code

elements_dictonary = {'Sc': {'K': '4492', 'L-I': '498.0', 'L-2': '403.6', 'L-3': '398.7'},
                      'Ti': {'K': '4966', 'L-I': '560.9', 'L-2': '460.2', 'L-3': '453.8'},
                      'V': {'K': '5465', 'L-I': '626.7', 'L-2': '519.8', 'L-3': '512.1'},
                      'Cr': {'K': '5989', 'L-I': '696.0', 'L-2': '583.8', 'L-3': '574.1'},
                      'Mn': {'K': '6539', 'L-I': '769.1', 'L-2': '649.9', 'L-3': '638.7'},
                      'Fe': {'K': '7112', 'L-I': '844.6', 'L-2': '719.9', 'L-3': '706.8'},
                      'Co': {'K': '7709', 'L-I': '925.1', 'L-2': '793.2', 'L-3': '778.1'},
                      'Ni': {'K': '8333', 'L-I': '1008.6', 'L-2': '870.0', 'L-3': '852.7'},
                      'Cu': {'K': '8979', 'L-I': '1096.7', 'L-2': '952.3', 'L-3': '932.7'},
                      'Zn': {'K': '9659', 'L-I': '1196.2', 'L-2': '1044.9', 'L-3': '1021.8'},
                      'Ga': {'K': '10367', 'L-I': '1299.0', 'L-2': '1143.2', 'L-3': '1116.4'},
                      'Ge': {'K': '11103', 'L-I': '1414.6', 'L-2': '1248.1', 'L-3': '1217.0'},
                      'As': {'K': '11867', 'L-I': '1527.0', 'L-2': '1359.1', 'L-3': '1323.6'},
                      'Se': {'K': '12658', 'L-I': '1652.0', 'L-2': '1474.3', 'L-3': '1433.9'},
                      'Br': {'K': '13474', 'L-I': '1782', 'L-2': '1596', 'L-3': '1550'},
                      'Kr': {'K': '14326', 'L-I': '1921', 'L-2': '1730.9', 'L-3': '1678.4'},
                      'Rb': {'K': '15200', 'L-I': '2065', 'L-2': '1864', 'L-3': '1804'},
                      'Sr': {'K': '16105', 'L-I': '2216', 'L-2': '2007', 'L-3': '1940'},
                      'Y': {'K': '17038', 'L-I': '2373', 'L-2': '2156', 'L-3': '2080'},
                      'Zr': {'K': '17998', 'L-I': '2532', 'L-2': '2307', 'L-3': '2223'},
                      'Nb': {'K': '18986', 'L-I': '2698', 'L-2': '2465', 'L-3': '2371'},
                      'Mo': {'K': '20000', 'L-I': '2866', 'L-2': '2625', 'L-3': '2520'},
                      'Tc': {'K': '21044', 'L-I': '3043', 'L-2': '2793', 'L-3': '2677'},
                      'Ru': {'K': '22117', 'L-I': '3224', 'L-2': '2967', 'L-3': '2838'},
                      'Rh': {'K': '23220', 'L-I': '3412', 'L-2': '3146', 'L-3': '3004'},
                      'Pd': {'K': '24350', 'L-I': '3604', 'L-2': '3330', 'L-3': '3173'},
                      'Ag': {'K': '25514', 'L-I': '3806', 'L-2': '3524', 'L-3': '3351'},
                      'Cd': {'K': '26711', 'L-I': '4018', 'L-2': '3727', 'L-3': '3538'},
                      'In': {'K': '27940', 'L-I': '4238', 'L-2': '3938', 'L-3': '3730'},
                      'Sn': {'K': '29200', 'L-I': '4465', 'L-2': '4156', 'L-3': '3929'},
                      'Sb': {'K': '30491', 'L-I': '4698', 'L-2': '4380', 'L-3': '4132'},
                      'Te': {'K': '31814', 'L-I': '4939', 'L-2': '4612', 'L-3': '4341'},
                      'I': {'K': '33169', 'L-I': '5188', 'L-2': '4852', 'L-3': '4557'},
                      'Xe': {'K': '34561', 'L-I': '5453', 'L-2': '5107', 'L-3': '4786'},
                      'Cs': {'K': '35985', 'L-I': '5714', 'L-2': '5359', 'L-3': '5012'},
                      'Ba': {'K': '37441', 'L-I': '5989', 'L-2': '5624', 'L-3': '5247'},
                      'La': {'K': '38925', 'L-I': '6266', 'L-2': '5891', 'L-3': '5483'},
                      'Ce': {'K': '40443', 'L-I': '6548', 'L-2': '6164', 'L-3': '5723'},
                      'Pr': {'K': '41991', 'L-I': '6835', 'L-2': '6440', 'L-3': '5964'},
                      'Nd': {'K': '43569', 'L-I': '7126', 'L-2': '6722', 'L-3': '6208'},
                      'Pm': {'K': '45184', 'L-I': '7428', 'L-2': '7013', 'L-3': '6459'},
                      'Sm': {'K': '46834', 'L-I': '7737', 'L-2': '7312', 'L-3': '6716'},
                      'Eu': {'K': '48519', 'L-I': '8052', 'L-2': '7617', 'L-3': '6977'},
                      'Gd': {'K': '50239', 'L-I': '8376', 'L-2': '7930', 'L-3': '7243'},
                      'Tb': {'K': '51996', 'L-I': '8708', 'L-2': '8252', 'L-3': '7514'},
                      'Dy': {'K': '53789', 'L-I': '9046', 'L-2': '8581', 'L-3': '7790'},
                      'Ho': {'K': '55618', 'L-I': '9394', 'L-2': '8918', 'L-3': '8071'},
                      'Er': {'K': '57486', 'L-I': '9751', 'L-2': '9264', 'L-3': '8358'},
                      'Tm': {'K': '59390', 'L-I': '10116', 'L-2': '9617', 'L-3': '8648'},
                      'Yb': {'K': '61332', 'L-I': '10486', 'L-2': '9978', 'L-3': '8944'},
                      'Lu': {'K': '63314', 'L-I': '10870', 'L-2': '10349', 'L-3': '9244'},
                      'Hf': {'K': '65351', 'L-I': '11271', 'L-2': '10739', 'L-3': '9561'},
                      'Ta': {'K': '67416', 'L-I': '11682', 'L-2': '11136', 'L-3': '9881'},
                      'W': {'K': '69525', 'L-I': '12100', 'L-2': '11544', 'L-3': '10207'},
                      'Re': {'K': '71676', 'L-I': '12527', 'L-2': '11959', 'L-3': '10535'},
                      'Os': {'K': '73871', 'L-I': '12968', 'L-2': '12385', 'L-3': '10871'},
                      'Ir': {'K': '76111', 'L-I': '13419', 'L-2': '12824', 'L-3': '11215'},
                      'Pt': {'K': '78395', 'L-I': '13880', 'L-2': '13273', 'L-3': '11564'},
                      'Au': {'K': '80725', 'L-I': '14353', 'L-2': '13734', 'L-3': '11919'},
                      'Hg': {'K': '83102', 'L-I': '14839', 'L-2': '14209', 'L-3': '12284'},
                      'Tl': {'K': '85530', 'L-I': '15347', 'L-2': '14698', 'L-3': '12658'},
                      'Pb': {'K': '88005', 'L-I': '15861', 'L-2': '15200', 'L-3': '13035'},
                      'Bi': {'K': '90526', 'L-I': '16388', 'L-2': '15711', 'L-3': '13419'},
                      'Po': {'K': '93105', 'L-I': '16939', 'L-2': '16244', 'L-3': '13814'},
                      'At': {'K': '95730', 'L-I': '17493', 'L-2': '16785', 'L-3': '14214'},
                      'Rn': {'K': '98404', 'L-I': '18049', 'L-2': '17337', 'L-3': '14619'},
                      'Fr': {'K': '101137', 'L-I': '18639', 'L-2': '17907', 'L-3': '15031'},
                      'Ra': {'K': '103922', 'L-I': '19237', 'L-2': '18484', 'L-3': '15444'},
                      'Ac': {'K': '106755', 'L-I': '19840', 'L-2': '19083', 'L-3': '15871'},
                      'Th': {'K': '109651', 'L-I': '20472', 'L-2': '19693', 'L-3': '16300'},
                      'Pa': {'K': '112601', 'L-I': '21105', 'L-2': '20314', 'L-3': '16733'}}

ISS_foils= {'Sc': {'K': '4492', 'L-I': '498.0', 'L-2': '403.6', 'L-3': '398.7'},
            'Ti': {'K': '4966', 'L-I': '560.9', 'L-2': '460.2', 'L-3': '453.8'},
            'V': {'K': '5465', 'L-I': '626.7', 'L-2': '519.8', 'L-3': '512.1'},
            'Cr': {'K': '5989', 'L-I': '696.0', 'L-2': '583.8', 'L-3': '574.1'},
            'Mn': {'K': '6539', 'L-I': '769.1', 'L-2': '649.9', 'L-3': '638.7'},
            'Fe': {'K': '7112', 'L-I': '844.6', 'L-2': '719.9', 'L-3': '706.8'},
            'Co': {'K': '7709', 'L-I': '925.1', 'L-2': '793.2', 'L-3': '778.1'},
            'Ni': {'K': '8333', 'L-I': '1008.6', 'L-2': '870.0', 'L-3': '852.7'},
            'Cu': {'K': '8979', 'L-I': '1096.7', 'L-2': '952.3', 'L-3': '932.7'},
            'Zn': {'K': '9659', 'L-I': '1196.2', 'L-2': '1044.9', 'L-3': '1021.8'},
            'Se': {'K': '12658', 'L-I': '1652.0', 'L-2': '1474.3', 'L-3': '1433.9'},
            'Y': {'K': '17038', 'L-I': '2373', 'L-2': '2156', 'L-3': '2080'},
            'Zr': {'K': '17998', 'L-I': '2532', 'L-2': '2307', 'L-3': '2223'},
            'Nb': {'K': '18986', 'L-I': '2698', 'L-2': '2465', 'L-3': '2371'},
            'Mo': {'K': '20000', 'L-I': '2866', 'L-2': '2625', 'L-3': '2520'},
            'Ru': {'K': '22117', 'L-I': '3224', 'L-2': '2967', 'L-3': '2838'},
            'Rh': {'K': '23220', 'L-I': '3412', 'L-2': '3146', 'L-3': '3004'},
            'Pd': {'K': '24350', 'L-I': '3604', 'L-2': '3330', 'L-3': '3173'},
            'Ag': {'K': '25514', 'L-I': '3806', 'L-2': '3524', 'L-3': '3351'},
            'Cd': {'K': '26711', 'L-I': '4018', 'L-2': '3727', 'L-3': '3538'},
            'In': {'K': '27940', 'L-I': '4238', 'L-2': '3938', 'L-3': '3730'},
            'Sn': {'K': '29200', 'L-I': '4465', 'L-2': '4156', 'L-3': '3929'},
            'Ta': {'K': '67416', 'L-I': '11682', 'L-2': '11136', 'L-3': '9881'},
            'Re': {'K': '71676', 'L-I': '12527', 'L-2': '11959', 'L-3': '10535'},
            'Ir': {'K': '76111', 'L-I': '13419', 'L-2': '12824', 'L-3': '11215'},
            'Pt': {'K': '78395', 'L-I': '13880', 'L-2': '13273', 'L-3': '11564'},
            'Au': {'K': '80725', 'L-I': '14353', 'L-2': '13734', 'L-3': '11919'},
            'Pb': {'K': '88005', 'L-I': '15861', 'L-2': '15200', 'L-3': '13035'},
            }

element_edge_itsvalue = {}
for element in elements_dictonary.keys():
    for edge in elements_dictonary[element].keys():
        element_edge_itsvalue[element+"-"+edge] = float(elements_dictonary[element][edge])
element_edge_itsvalue_sorted = dict(sorted(element_edge_itsvalue.items(), key=lambda item: item[1]))

ISS_element_edge_itsvalue = {}
for element in ISS_foils.keys():
    for edge in ISS_foils[element].keys():
        ISS_element_edge_itsvalue[element+"-"+edge] = float(elements_dictonary[element][edge])
ISS_element_edge_itsvalue_sorted = dict(sorted(ISS_element_edge_itsvalue.items(), key=lambda item: item[1]))

ISS_foils_edges = dict([(key, value) for key,value in ISS_element_edge_itsvalue_sorted.items() if value>4500 and value<30000])

l3_edge = ["L3", "l3", "LIII", "L-III", "l-III", "L-3", "l-3"]
l2_edge = ["L2", "l2", "LII", "L-II", "l-II",  "L-2", "l-2"]
l1_edge = ["L1", "l1", "LI", "L-I", "l-I",  "L-1", "l-1"]
k_edge = ['k', "K"]

def find_correct_foil(element='Cu', edge="K"):
    """
    The function place the correct foil according to the element and Edge user wants to measure
    ----------
    Example: ind_correct_foil(element = "Os", edge="L-3")
    """

    if edge in l3_edge:
        edge = "L-3"
    elif edge in l2_edge:
        edge = "L-2"
    elif edge in l1_edge:
        edge = "L-I"
    elif edge in k_edge:
        edge = "K"

    foils_options = dict([(key, value) for key,value in ISS_foils_edges.items() if element_edge_itsvalue_sorted[element+"-"+edge]>value-200 and element_edge_itsvalue_sorted[element+"-"+edge]<value+1000])
    foils_options = [(key, value) for key, value in foils_options.items()]

    if len(foils_options)==1:
        print(foils_options[0][0].split('-')[0])
    elif len(foils_options)==0:
        print("No foil available going to empty foil")
    else:
        print(foils_options[1][0].split('-')[0])

    element = foils_options[1][0].split('-')[0]

    with open(f'{ROOT_PATH_SHARED}/settings/json/foil_wheel.json') as fp:
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


# find_correct_foil2(element='Eu', edge='L1')


###########################

def set_attenuator(thickness:int  = 0, **kwargs):
    # Adding reference foil element list
    with open(f'{ROOT_PATH_SHARED}/settings/json/attenuator.json') as fp:
        attenuators_list = json.load(fp)
    thickness_str_list = [item['attenuator'] for item in attenuators_list]
    thickness_str = str(thickness)
    if thickness_str in thickness_str_list:
        indx = thickness_str_list.index(thickness_str)
        yield from mv(attenuator_motor.pos, attenuators_list[indx]['position'])
    else:
        yield from mv(attenuator_motor.pos, 0)



def scan_beam_center(camera=camera_sp1, emin=10000, emax=20000, nsteps=10, roll_range=5, roll_nsteps=6):

    original_roll = hhm.roll.position
    hhm_rolls = np.linspace(original_roll-roll_range/2, original_roll+roll_range/2, roll_nsteps+1)
    energies = np.linspace(emin, emax, nsteps+1).tolist()

    yield from bps.open_run()

    for hhm_roll in hhm_rolls:
        yield from bps.mv(hhm.roll, hhm_roll)
        for energy in energies:
            # yield from bps.mv(hhm.energy, energy)
            yield from move_mono_energy(energy, step=500, beampos_tol=10)
            camera.adjust_camera_exposure_time(percentile=100)
            yield from bps.trigger_and_read([hhm.energy, hhm.roll, camera.stats1.centroid, bpm_es.stats4.centroid])

    yield from bps.close_run()

    yield from bps.mv(hhm.roll, original_roll)



def plot_beam_center_scan(db, uid):
    t = db[uid].table()

    plt.figure(1, clear=True)

    roll = np.unique(t.hhm_roll_user_setpoint.values)
    energy = np.unique(t.hhm_energy_user_setpoint.values)
    x_cam_sp1 = np.zeros((energy.size, roll.size))
    x_bpm_es = np.zeros((energy.size, roll.size))

    for i, _roll in enumerate(roll):
        mask = t.hhm_roll_user_setpoint == _roll
        x_cam_sp1[:, i] = t.camera_sp1_stats1_centroid_x[mask].values
        x_bpm_es[:, i] = t.bpm_es_stats4_centroid_x[mask].values


    plt.subplot(221)
    for i in range(roll.size):
        plt.plot(energy, x_cam_sp1[:, i])
        plt.text(energy[-1]+500, x_cam_sp1[-1, i], f'{roll[i]:0.3f}')

    plt.subplot(222)
    for i in range(roll.size):
        plt.plot(energy, x_bpm_es[:, i])
        plt.text(energy[-1] + 500, x_bpm_es[-1, i], f'{roll[i]:0.3f}')

    plt.subplot(223)
    plt.plot(roll, np.ptp(x_cam_sp1, axis=0))

    plt.subplot(224)
    plt.plot(roll, np.ptp(x_bpm_es, axis=0))

# plot_beam_center_scan(db, -1)




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





