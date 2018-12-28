
import time as ttime
import sys

def prepare_beamline_plan(energy: int = -1, move_cm_mirror = False):
    energy_ranges = [
        {
            'energy_start': 4500,
            'energy_end': 6000,
            'He_flow': 5,
            'N2_flow': 1,
            'IC_voltage': 1000,
            'HHRM': 0,
            'CM1':0,
            'Filterbox': 1,
        },
        {
            'energy_start': 6000,
            'energy_end': 10000,
            'He_flow': 5,
            'N2_flow': 3,
            'IC_voltage': 1700,
            'HHRM': 0,
            'CM1':0,
            'Filterbox': -69,
        },
        {
            'energy_start': 10000,
            'energy_end': 13000,
            'He_flow': 5,
            'N2_flow': 5,
            'IC_voltage': 1700,
            'HHRM': 8,
            'CM1':0,
            'Filterbox': -139,
        },
        {
            'energy_start': 13000,
            'energy_end': 17000,
            'He_flow': 5,
            'N2_flow': 5,
            'IC_voltage': 1700,
            'HHRM': 80,
            'CM1': 40,
            'Filterbox': -139,
        },
        {
            'energy_start': 17000,
            'energy_end': 35000,
            'He_flow': 2,
            'N2_flow': 5,
            'IC_voltage': 1900,
            'HHRM': 80,
            'CM1': 40,
            'Filterbox': -209,
        },
    ]


    He_flow_setter = gas_he.flow
    N2_flow_setter = gas_n2.flow
    high_voltage_setters = [wps1.hv302,wps1.hv303,wps1.hv305]
    safe_high_voltage = 580
    filter_box_setter = filterbox.y
    cm_setter = cm1.x
    hhrm_setter = hhrm.hor_translation

    energy_range = [e_range for e_range in energy_ranges if
                  e_range['energy_end'] > energy >= e_range['energy_start']][0]
    if not energy_range:
        print('ERROR: Energy is outside of the beamline energy range')
        return
    print(f'[Prepare Beamline] Setting up the beamline to {energy} eV')

    print('[Prepare Beamline] Starting...')
    if move_cm_mirror == True:
        start_cm_position = cm_setter.position
        end_cm_position = energy_range['CM1']
        cm_motion_range = abs(end_cm_position-start_cm_position)
        moving_cm = cm_setter.set(end_cm_position)

    start_hhrm_position = hhrm_setter.position
    end_hhrm_position = energy_range['HHRM']
    hhrm_motion_range = abs(start_hhrm_position-end_hhrm_position)
    moving_hhrm = hhrm_setter.set(end_hhrm_position)



    hv_setter_values = []
    for high_voltage_setter in high_voltage_setters:
        hv_setter_values.append(high_voltage_setter)
        hv_setter_values.append(safe_high_voltage)
    yield from bps.mv(*hv_setter_values)
    print('[Prepare Beamline] High voltage supply is set to safe values')


    start_time = ttime.time()

    yield from bps.mv(
                        He_flow_setter,energy_range['He_flow'],
                        N2_flow_setter,energy_range['N2_flow'],
                      )
    print('[Prepare Beamline] Ion chamber gas composition set', flush = True)

    print('[Prepare Beamline] Closing frontend shutter before selecting filter  ')
    #close shutter before moving the filter
    try:
        yield from bps.mv(shutter_fe_2b, 'Close')
    except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to close.')

    yield from bps.mv(filter_box_setter,energy_range['Filterbox'])

    print('[Prepare Beamline] Filter set')

    while ttime.time() < (start_time + 120):
        print(f'[Prepare Beamline] {int(120 - (ttime.time()-start_time))} s left to settle the ion chamber gas flow')
        yield from bps.sleep(10)

    hv_setter_values = []
    for high_voltage_setter in high_voltage_setters:
        hv_setter_values.append(high_voltage_setter)
        hv_setter_values.append(energy_range['IC_voltage'])
    yield from bps.mv(*hv_setter_values)
    print('[Prepare Beamline] High voltage values set', flush = True)

    while not moving_hhrm.done:
        motion_so_far = hhrm_setter.position
        percent_complete = int(abs(motion_so_far - start_hhrm_position) / hhrm_motion_range * 100)
        print(f'[Prepare Beamline] HHRM motion is {percent_complete} % complete')
        yield from bps.sleep(10)

    print('[Prepare Beamline] High harmonics rejection mirror position set')


    if move_cm_mirror == True:
        while not moving_cm.done:
            motion_so_far = cm_setter.position
            percent_complete = int(abs(motion_so_far - start_cm_position) / cm_motion_range * 100)
            print(f'[Prepare Beamline] CM1 motion is {percent_complete} % set')
            yield from bps.sleep(10)

    print('[Prepare Beamline] CM1 mirror position set', flush = True)

    print('[Prepare Beamline] Beamline preparation is complete')

