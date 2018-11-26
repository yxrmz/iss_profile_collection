
import time as ttime
def prepare_bl_plan(energy: int = -1, move_cm_mirror = False):
    energy_ranges = [
        {
            'energy_start': 4500,
            'energy_end': 6000,
            'He_flow': 5,
            'N2_flow': 1,
            'IC_voltage': 1000,
            'HHRM': 0,
            'CM1':0,
            'Filtebox': 1,
        },
        {
            'energy_start': 6000,
            'energy_end': 10000,
            'He_flow': 5,
            'N2_flow': 3,
            'IC_voltage': 1700,
            'HHRM': 0,
            'CM1':0,
            'Filtebox': -69,
        },
        {
            'energy_start': 10000,
            'energy_end': 13000,
            'He_flow': 5,
            'N2_flow': 5,
            'IC_voltage': 1700,
            'HHRM': 8,
            'CM1':0,
            'Filtebox': -139,
        },
        {
            'energy_start': 13000,
            'energy_end': 17000,
            'He_flow': 5,
            'N2_flow': 5,
            'IC_voltage': 1700,
            'HHRM': 20,
            'CM1': 2,
            'Filtebox': -139,
        },
        {
            'energy_start': 17000,
            'energy_end': 35000,
            'He_flow': 2,
            'N2_flow': 5,
            'IC_voltage': 1900,
            'HHRM': 8,
            'CM1': 2,
            'Filtebox': -209,
        },
    ]


    He_flow_setter = gas_he.flow
    N2_flow_setter = gas_n2.flow
    high_voltage_setters = [wps1.hv302,wps1.hv303,wps1.hv305]
    safe_high_voltage = 900
    filter_box_setter = filterbox.y
    cm_setter = cm1.x
    hhrm_setter = hhrm.hor_translation

    energy_range = [e_range for e_range in energy_ranges if
                  e_range['energy_end'] > energy >= e_range['energy_start']][0]
    if not energy_range:
        print('ERROR: Energy is outside of the beamline energy range')
        return
    print(f'[Prepare BL] Setting up the beamline to {energy} eV')


    if move_cm_mirror == True:
        start_cm_position = cm_setter.position
        end_cm_position = energy_range['CM1']
        cm_motion_range = abs(end_cm_position-start_cm_position)

        moving_cm_mirror = cm_setter.set(end_cm_position)

    moving_hhrm = hhrm_setter.set(energy_range['HHRM'])

    hv_setter_values = []
    for high_voltage_setter in high_voltage_setters:
        hv_setter_values.append(high_voltage_setter)
        hv_setter_values.append(safe_high_voltage)


    yield from bps.mv(*hv_setter_values)

    start_time = ttime.time()

    yield from bps.mv(
                        He_flow_setter,energy_range['He_flow'],
                        N2_flow_setter,energy_range['N2_flow'],
                      )



    while not moving_hhrm.done:
        print('waiting')
        yield from bps.sleep(1)



    '''

    #close shutter before moving the filter

   try:
        yield from bps.mv(shutter_ph_2b, 'Close')
   except FailedStatus:
        raise CannotActuateShutter(f'Error: Photon shutter failed to close.')


    yield from bps.mv(filter_box_setter,energy_range['Filterbox'])
    shutter_fe_2b.open()

    while ttime.time < (start_time + 120):
        print(f'[Prepare Beamline] {int(120 - (ttime.time-start_time))} s left to settle the ion chamber gas flow')
        yield from bps.sleep(5)

    for high_voltage_setter in high_voltage_setters:
        yield from bps.mv(high_voltage_setter, energy_range['IC_voltage'])


    if move_cm_mirror == True:
        while moving_cm_mirror.done is False:
            motion_so_far = cm1.x.position
            percent_complete = int(abs(motion_so_far-start_cm_position)/cm_motion_range*100)
            print(f'[Prepare Beamline]CM1 motion is {percent_complete} % complete')

    print('[Prepare Beamline] Beamline preparation complete!')



























def prepare_bl_plan(energy: int = -1, print_messages=True, debug=False):
    if debug:
        print('[Prepare BL] Running Prepare Beamline in Debug Mode! (Not moving anything)')

    energy = int(energy)
    curr_energy = energy
    if energy < 0:
        ret = (yield from bps.read(hhm.energy))
        if ret is not None:
            curr_energy = ret[hhm.energy.name]['value']

    if print_messages:
        print('[Prepare BL] Setting up the beamline to {} eV'.format(curr_energy))

    curr_range = [ran for ran in prepare_bl_def[0] if
                  ran['energy_end'] > curr_energy >= ran['energy_start']]
    if not len(curr_range):
        print('Current energy is not valid. :( Aborted.')
        return

    curr_range = curr_range[0]
    pv_he = curr_range['pvs']['IC Gas He']['object']
    if print_messages:
        print('[Prepare BL] Setting HE to {}'.format(curr_range['pvs']['IC Gas He']['value']))
    if not debug:
        yield from bps.mv(pv_he, curr_range['pvs']['IC Gas He']['value'])

    pv_n2 = curr_range['pvs']['IC Gas N2']['object']
    if print_messages:
        print('[Prepare BL] Setting N2 to {}'.format(curr_range['pvs']['IC Gas N2']['value']))
    if not debug:
        yield from bps.mv(pv_n2, curr_range['pvs']['IC Gas N2']['value'])

    # If you go from less than 1000 V to more than 1400 V, you need a delay. 2 minutes
    # For now if you increase the voltage (any values), we will have the delay. 2 minutes

    pv_i0_volt = curr_range['pvs']['I0 Voltage']['object']
    ret = (yield from bps.read(pv_i0_volt))
    if ret is not None:
        old_i0 = ret[pv_i0_volt.name]['value']
    else:
        old_i0 = 0
    if print_messages:
        print('[Prepare BL] Old I0 Voltage: {} | New I0 Voltage: {}'.format(old_i0,
                                                                        curr_range['pvs']['I0 Voltage']['value']))

    pv_it_volt = curr_range['pvs']['It Voltage']['object']
    ret = (yield from bps.read(pv_it_volt))
    if ret is not None:
        old_it = ret[pv_it_volt.name]['value']
    else:
        old_it = 0
    if print_messages:
        print('[Prepare BL] Old It Voltage: {} | New It Voltage: {}'.format(old_it,
                                                                        curr_range['pvs']['It Voltage']['value']))

    pv_ir_volt = curr_range['pvs']['Ir Voltage']['object']
    ret = (yield from bps.read(pv_ir_volt))
    if ret is not None:
        old_ir = ret[pv_ir_volt.name]['value']
    else:
        old_ir = 0
    if print_messages:
        print('[Prepare BL] Old Ir Voltage: {} | New Ir Voltage: {}'.format(old_ir,
                                                                        curr_range['pvs']['Ir Voltage']['value']))

    # check if bpm_cm will move
    close_shutter = 0
    cm = [bpm for bpm in curr_range['pvs']['BPMs'] if bpm['name'] == bpm_cm.name][0]
    new_cm_value = cm['value']
    if new_cm_value == 'OUT':
        pv = cm['object'].switch_retract
    elif new_cm_value == 'IN':
        pv = cm['object'].switch_insert
    yield from bps.sleep(0.1)
    ret = (yield from bps.read(pv))
    if ret is not None:
        if ret[pv.name]['value'] == 0:
            close_shutter = 1

    # check if filtebox will move
    mv_fb = 0
    fb_value = prepare_bl_def[1]['FB Positions'][curr_range['pvs']['Filterbox Pos']['value'] - 1]
    pv_fb_motor = curr_range['pvs']['Filterbox Pos']['object']
    yield from bps.sleep(0.1)
    ret = (yield from bps.read(pv_fb_motor))
    if ret is not None:
        curr_fb_value = ret[pv_fb_motor.name]['value']
    else:
        curr_fb_value = -1

    if abs(fb_value - curr_fb_value) > 20 * (10 ** (-pv_fb_motor.precision)):
        close_shutter = 1
        mv_fb = 1

    def handler(signum, frame):
        print("[Prepare BL] Could not activate FE Shutter")
        raise Exception("Timeout")

    if close_shutter:
        if print_messages:
            print('[Prepare BL] Closing FE Shutter...')
        if not debug:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(12)
            try:
                yield from shutter_fe.close_plan()
            except Exception as exc:
                print('[Prepare BL] Timeout! Could not close FE Shutter. Aborting! (Try once again, maybe?)')
                return

            tries = 10
            ret = (yield from bps.read(shutter_fe.state))
            if ret is not None:
                while ret[shutter_fe.state.name]['value'] != 1:
                    yield from bps.sleep(0.1)
                    if tries:
                        yield from shutter_fe.close_plan()
                        tries -= 1
                    ret = (yield from bps.read(shutter_fe.state))

            signal.alarm(0)
        if print_messages:
            print('[Prepare BL] FE Shutter closed')

    yield from bps.sleep(0.1)
    fb_sts_pv = curr_range['pvs']['Filterbox Pos']['STS PVS'][curr_range['pvs']['Filterbox Pos']['value'] - 1]
    if mv_fb:
        if print_messages:
            print('[Prepare BL] Moving Filterbox to {}'.format(fb_value))
        if not debug:
            yield from bps.abs_set(pv_fb_motor, fb_value, group='prepare_bl')

    pv_hhrm_hor = curr_range['pvs']['HHRM Hor Trans']['object']
    yield from bps.sleep(0.1)
    if print_messages:
        print('[Prepare BL] Moving HHRM Horizontal to {}'.format(curr_range['pvs']['HHRM Hor Trans']['value']))
    if not debug:
        yield from bps.abs_set(pv_hhrm_hor, curr_range['pvs']['HHRM Hor Trans']['value'], group='prepare_bl')

    bpm_pvs = []
    for bpm in curr_range['pvs']['BPMs']:
        exposure_time = bpm['exposure_time']
        if bpm['value'] == 'IN':
            pv_set = bpm['object'].ins
            pv_read = bpm['object'].switch_insert
        elif bpm['value'] == 'OUT':
            pv_set = bpm['object'].ret
            pv_read = bpm['object'].switch_retract
        try:
            if pv:
                if print_messages:
                    print('[Prepare BL] Moving {} {}'.format(bpm['name'], bpm['value']))
                for i in range(3):
                    if not debug:
                        if exposure_time > 0:
                            yield from bps.abs_set(bpm['object'].exp_time, exposure_time)
                        yield from bps.abs_set(pv_set, 1)
                    yield from bps.sleep(0.1)
                bpm_pvs.append([pv_set, pv_read])
        except Exception as exp:
            print(exp)

    if close_shutter:
        yield from wait_filter_in_place(fb_sts_pv)
        #while fb_sts_pv.value != 1:
        #    pass
        if print_messages:
            print('[Prepare BL] Opening shutter...')
        if not debug:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(12)
            try:
                yield from shutter_fe.open_plan()
            except Exception as exc:
                print('[Prepare BL] Timeout! Could not open FE Shutter. Aborting! (Try once again, maybe?)')
                return

            tries = 10
            ret = (yield from bps.read(shutter_fe.state))
            if ret is not None:
                while ret[shutter_fe.state.name]['value'] != 0:
                    yield from bps.sleep(0.1)
                    if tries:
                        yield from shutter_fe.open_plan()
                        tries -= 1
                    ret = (yield from bps.read(shutter_fe.state))

            signal.alarm(0)
        if print_messages:
            print('[Prepare BL] FE Shutter open')

    if curr_range['pvs']['I0 Voltage']['value'] - old_i0 > 2 or \
            curr_range['pvs']['It Voltage']['value'] - old_it > 2 or \
            curr_range['pvs']['Ir Voltage']['value'] - old_ir > 2:
        old_time = ttime.time()
        wait_time = 120
        if print_messages:
            print('[Prepare BL] Waiting for gas ({}s)...'.format(wait_time))
        percentage = 0
        if not debug:
            while ttime.time() - old_time < wait_time:  # 120 seconds
                if ttime.time() - old_time >= percentage * wait_time:
                    print(
                        '[Prepare BL] {:3}% ({:.1f}s)'.format(int(np.round(percentage * 100)), percentage * wait_time))
                    percentage += 0.1
                yield from bps.sleep(0.1)
        print('[Prepare BL] 100% ({:.1f}s)'.format(wait_time))
        if print_messages:
            print('[Prepare BL] Done waiting for gas...')

    if print_messages:
        print('[Prepare BL] Setting i0 {}'.format(curr_range['pvs']['I0 Voltage']['value']))
        print('[Prepare BL] Setting it {}'.format(curr_range['pvs']['It Voltage']['value']))
        print('[Prepare BL] Setting ir {}'.format(curr_range['pvs']['Ir Voltage']['value']))
    if not debug:
        pv_i0_volt._put_complete = True
        pv_it_volt._put_complete = True
        pv_ir_volt._put_complete = True
        yield from bps.abs_set(pv_i0_volt, curr_range['pvs']['I0 Voltage']['value'])#, group='prepare_bl')
        yield from bps.abs_set(pv_it_volt, curr_range['pvs']['It Voltage']['value'])#, group='prepare_bl')
        yield from bps.abs_set(pv_ir_volt, curr_range['pvs']['Ir Voltage']['value'])#, group='prepare_bl')

    yield from bps.sleep(0.1)

    if print_messages:
        print('[Prepare BL] Waiting for everything to be in position...')
    if not debug:
        while abs(abs(pv_i0_volt.value) - abs(
                curr_range['pvs']['I0 Voltage']['value'])) > (10 ** -pv_i0_volt.precision) * 2000 or abs(
                        abs(pv_it_volt.value) - abs(
                        curr_range['pvs']['It Voltage']['value'])) > (10 ** -pv_it_volt.precision) * 2000 or abs(
                        abs(pv_ir_volt.value) - abs(
                        curr_range['pvs']['Ir Voltage']['value'])) > (10 ** -pv_ir_volt.precision) * 2000:
            yield from bps.sleep(0.1)
        yield from bps.wait(group='prepare_bl')
    if print_messages:
        print('[Prepare BL] Everything seems to be in position')
        print('[Prepare BL] Setting energy to {}'.format(curr_energy))

    if not debug:
        yield from bps.abs_set(hhm.energy, curr_energy, wait=True)

    if print_messages:
        print('[Prepare BL] Beamline preparation complete!')
'''