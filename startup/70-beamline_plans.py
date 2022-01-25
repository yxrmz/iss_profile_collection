


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



def bender_scan():
    bender_current_position = bender.pos.user_readback.get()
    bender_positions = bender_current_position + np.arange(-15, 20, 5)
    for bender_position in bender_positions:
        yield from bps.mv(bender.pos, bender_position)
        yield from bps.sleep(3)
        loading = bender.load_cell.get()
        fname = f'Bender scan - {loading} N - {bender_position} um'

        yield from fly_scan_with_apb(fname,'')
    yield from bps.mv(bender.pos, bender_current_position)

    def scan_beam_position_vs_energy(camera=camera_sp2):
        camera.stats4.centroid_threshold.put(10)
        centers = []
        energies = np.linspace(6000, 14000, 11)
        for energy in energies:
            print(f'Energy is {energy}')
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
