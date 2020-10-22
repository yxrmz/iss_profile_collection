import matplotlib.pyplot as plt
from datetime import datetime
from subprocess import call
import time
from scipy.optimize import curve_fit
from bluesky.plan_stubs import mv, mvr
import bluesky.preprocessors as bpp
from random import random
from xas.trajectory import trajectory_manager
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



def set_reference_foil(element = None):
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

# def get_adc_offsets(times: int = 20, *args, **kwargs):
#     """
#        Get Ion Chambers Offsets - Gets the offsets from the ion chambers and automatically subtracts from the acquired data in the next scans
#
#        Parameters
#        ----------
#        num : int
#            Number of points to acquire and average for each ion chamber
#
#
#        Returns
#        -------
#        uid : list(str)
#            List containing the unique id of the scan
#
#
#        See Also
#        --------
#        :func:`tscan`
#        """
#     sys.stdout = kwargs.pop('stdout', sys.stdout)
#
#     adcs = list(args)
#     if not len(adcs):
#         adcs = [pba2.adc7, pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
#
#     old_avers = []
#     for adc in adcs:
#         old_avers.append(adc.averaging_points.get())
#         adc.averaging_points.put(10)
#
#     try:
#         yield from bps.mv(shutter_ph_2b, 'Close')
#     except FailedStatus:
#         raise CannotActuateShutter(f'Error: Photon shutter failed to close.')
#
#     uid = (yield from get_offsets_plan(adcs, num=int(times)))
#
#     try:
#         yield from bps.mv(shutter_ph_2b, 'Open')
#     except FailedStatus:
#         print('Error: Photon shutter failed to open')
#
#
#     print('Updating values...')
#
#     arrays = []
#     offsets = []
#     df = db[uid].table()
#
#     for index, adc in enumerate(adcs):
#         key = '{}_volt'.format(adc.name)
#         array = df[key]
#         offset = np.mean(df[key][2:int(times)])
#
#         arrays.append(array)
#         offsets.append(offset)
#         adc.offset.put(offset)
#         print('{}\n New offset for {}) is  {}'.format(array, adc.dev_name.value, offset))
#         adc.averaging_points.put(old_avers[index])
#     print('[Offsets recorded] Complete\n')
#     remove_pb_files(uid)


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
        print('Channel readout for {}  is {} V'.format(adc.dev_name.value, readout))
        adc.averaging_points.put(old_avers[index])

    remove_pb_files(uid)

    print('ADC readout complete!')

def adjust_ic_gains( **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    if 'detector_names' not in kwargs:
        # detectors = [pba1.adc7, pba2.adc6, pba1.adc1, pba1.adc6]
        detectors = [apb_ave]
        channels = [ apb_ave.ch1,  apb_ave.ch2,  apb_ave.ch3,  apb_ave.ch4]
        offsets = [apb.ch1_offset, apb.ch2_offset,apb.ch3_offset,apb.ch4_offset,]


    current_lut = int(hhm.lut_number_rbv.value)
    traj_manager = trajectory_manager(hhm)
    info = traj_manager.read_info(silent=True)
    if 'max' not in info[str(current_lut)] or 'min' not in info[str(current_lut)]:
        raise Exception(
            'Could not find max or min information in the trajectory.'
            ' Try sending it again to the controller.')

    e_min = int(info[str(current_lut)]['min'])
    e_max = int(info[str(current_lut)]['max'])

    try:
        yield from bps.mv(shutter_ph_2b, 'Open')
    except FailedStatus:
        print('ERROR: Photon shutter failed to open')
    shutter.open()
    scan_positions = np.arange(e_max + 50, e_min - 50, -100)

    # plan = bp.list_scan(detectors, hhm.energy, scan_positions)
    flyers = []
    # for detector in detectors:
    #     if hasattr(detector, 'kickoff'):
    #         flyers.append(detector)
    for jj in range(2):
        plan = bp.list_scan(detectors, hhm.energy, scan_positions)
        yield from plan
        table = db[-1].table()
        for channel, offset in zip(channels, offsets):
            current_gain = channel.amp.get_gain()[0]
            if channel.polarity == 'neg':
                trace_extreme = table[channel.name].min()
            else:
                trace_extreme = table[channel.name].max()

            trace_extreme = (trace_extreme - offset.get())/1000

            print(f'Extreme value {trace_extreme} for detector {channel.name}')
            if abs(trace_extreme) > 3.4:
                print(f'Decreasing gain for detector {channel.name}')
                yield from channel.amp.set_gain_plan(current_gain-1, False)

            elif abs(trace_extreme) <= 3.4 and abs(trace_extreme) > 0.34:
                print(f'Correct gain for detector {channel.name}')
            elif abs(trace_extreme) <= 0.34:
                print(f'Increasing gain for detector {channel.name}')
                yield from channel.amp.set_gain_plan(current_gain + 1, False)

            #     #print(f'F2>>>>>>>>>>> {flyers}\n D2>>>>>>>>>>>>>>>>.{detectors}')
            #     yield from bps.sleep(2)
            # shutter.close()
            # print('[Adjust Gain] Complete\n')
            # remove_pb_files(uid)

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





