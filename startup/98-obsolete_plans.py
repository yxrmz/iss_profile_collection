

'''

def set_gains_and_offsets(i0_gain:int=5, it_gain:int=5, iff_gain:int=6,
                          ir_gain:int=5, hs:bool=False):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    RE(set_gains_and_offsets_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs))

def set_gains(i0_gain:int=5, it_gain:int=5, iff_gain:int=5,
                          ir_gain:int=5, hs:bool=False, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    i0_gain = int(i0_gain)
    it_gain = int(it_gain)
    iff_gain = int(iff_gain)
    ir_gain = int(ir_gain)
    if type(hs) == str:
        hs = hs == 'True'

    yield from set_gains_plan(i0_amp, i0_gain, hs, it_amp, it_gain, hs, iff_amp, iff_gain, hs, ir_amp, ir_gain, hs)


def tune_mono_pitch(scan_range, step, retries=1, ax=None):
    aver = pba1.adc7.averaging_points.get()
    pba1.adc7.averaging_points.put(10)
    num_points = int(round(scan_range / step) + 1)
    over = 0

    while (not over):
        RE(tune([pba1.adc7], hhm.pitch, -scan_range / 2, scan_range / 2, num_points, ''),
           LivePlot('pba1_adc7_volt', 'hhm_pitch', ax=ax))
        last_table = db.get_table(db[-1])
        min_index = np.argmin(last_table['pba1_adc7_volt'])
        hhm.pitch.move(last_table['hhm_pitch'][min_index])
        print(hhm.pitch.position)

        run = db[-1]
        os.remove(run['descriptors'][0]['data_keys'][run['descriptors'][0]['name']]['filename'])
        # for i in run['descriptors']:
        #        if 'devname' in i['data_keys'][i['name']]

        # os.remove(db[-1]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
        if (num_points >= 10):
            if (((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    pba1.adc7.averaging_points.put(aver)
    print('Pitch tuning complete!')


def tune_mono_pitch_encoder(scan_range, step, retries=1, ax=None):
    aver = pba1.adc7.averaging_points.get()
    pba1.adc7.averaging_points.put(10)
    num_points = int(round(scan_range / step) + 1)
    over = 0

    start_position = pb2.enc3.pos_I.value

    while (not over):
        RE(tune([pba1.adc7, pb2.enc3], hhm.pitch, -scan_range / 2, scan_range / 2, 2, ''))

        enc = xasdata.XASdataAbs.loadENCtrace('', '', db[-1]['descriptors'][0]['data_keys']['pb2_enc3']['filename'])
        i0 = xasdata.XASdataAbs.loadADCtrace('', '', db[-1]['descriptors'][1]['data_keys']['pba1_adc7']['filename'])

        min_timestamp = np.array([i0[0, 0], enc[0, 0]]).max()
        max_timestamp = np.array([i0[len(i0) - 1, 0], enc[len(enc) - 1, 0]]).min()
        interval = i0[1, 0] - i0[0, 0]
        timestamps = np.arange(min_timestamp, max_timestamp, interval)
        enc_interp = np.array([timestamps, np.interp(timestamps, enc[:, 0], enc[:, 1])]).transpose()
        i0_interp = np.array([timestamps, np.interp(timestamps, i0[:, 0], i0[:, 1])]).transpose()
        len_to_erase = int(np.round(0.015 * len(i0_interp)))
        enc_interp = enc_interp[len_to_erase:]
        i0_interp = i0_interp[len_to_erase:]

        xas_abs.data_manager.process_equal(i0_interp[:, 0],
                                           enc_interp[:, 1],
                                           i0_interp[:, 1],
                                           i0_interp[:, 1],
                                           i0_interp[:, 1],
                                           10)

        xas_abs.data_manager.en_grid = xas_abs.data_manager.en_grid[5:-5]
        xas_abs.data_manager.i0_interp = xas_abs.data_manager.i0_interp[5:-5]
        # plt.plot(enc_interp[:,1], i0_interp[:,1]) #not binned

        plt.plot(xas_abs.data_manager.en_grid, xas_abs.data_manager.i0_interp)  # binned
        minarg = np.argmin(xas_abs.data_manager.i0_interp)
        enc_diff = xas_abs.data_manager.en_grid[minarg] - start_position

        pitch_pos = enc_diff / 204  # Enc to pitch convertion
        print('Delta Pitch = {}'.format(pitch_pos))
        # convert enc_diff to position (need to know the relation)
        # then move to the new position

        print(hhm.pitch.position)
        # os.remove(db[-1]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
        over = 1

    pba1.adc7.averaging_points.put(aver)
    print('Pitch tuning complete!')


def tune_mono_y(scan_range, step, retries=1, ax=None):
    aver = pba1.adc7.averaging_points.get()
    pba1.adc7.averaging_points.put(10)
    num_points = int(round(scan_range / step) + 1)
    over = 0

    while (not over):
        RE(tune([pba1.adc7], hhm.y, -scan_range / 2, scan_range / 2, num_points, ''),
           LivePlot('pba1_adc7_volt', 'hhm_y', ax=ax))
        last_table = db.get_table(db[-1])
        min_index = np.argmin(last_table['pba1_adc7_volt'])
        hhm.y.move(last_table['hhm_y'][min_index])
        print('New position: {}'.format(hhm.y.position))
        run = db[-1]
        os.remove(run['descriptors'][0]['data_keys'][run['descriptors'][0]['name']]['filename'])
        # os.remove(db[-1]['descriptors'][0]['data_keys']['pba1_adc7']['filename'])
        if (num_points >= 10):
            if (((min_index > 0.2 * num_points) and (min_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    pba1.adc7.averaging_points.put(aver)
    print('Y tuning complete!')


def tune_mono_y_bpm(scan_range, step, retries=1, ax=None):
    num_points = int(round(scan_range / step) + 1)
    over = 0

    while (not over):
        RE(tune([bpm_fm], hhm.y, -scan_range / 2, scan_range / 2, num_points, ''),
           LivePlot('bpm_fm_stats1_total', 'hhm_y', ax=ax))
        last_table = db.get_table(db[-1])
        max_index = np.argmax(last_table['bpm_fm_stats1_total'])
        hhm.y.move(last_table['hhm_y'][max_index])
        print('New position: {}'.format(hhm.y.position))
        if (num_points >= 10):
            if (((max_index > 0.2 * num_points) and (max_index < 0.8 * num_points)) or retries == 1):
                over = 1
            if retries > 1:
                retries -= 1
        else:
            over = 1

    print('Y tuning complete!')

'''