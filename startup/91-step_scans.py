


def step_scan(name: str, comment: str, n_cycles: int = 1, delay: float = 0, reference=True, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    energy_grid = kwargs.pop('energy_grid', [])
    time_grid = kwargs.pop('time_grid', [])
    element = kwargs.pop('element', [])
    e0 = kwargs.pop('e0', [])
    edge = kwargs.pop('element', [])


    yield from bps.mv(adaq_pb_step.divide, 35)
    yield from step_scan_plan(name, comment, energy_grid, time_grid, element=element, e0=e0, edge=edge )







def xia_step_scan(name:str, comment:str, e0:int=8333, preedge_start:int=-200, xanes_start:int=-50, xanes_end:int=30, exafs_end:int=16, preedge_spacing:float=10, xanes_spacing:float=0.2, exafs_spacing:float=0.04, **kwargs):
    '''
    xia_step_scan - Runs the monochromator along the trajectory defined in the parameters. Gets data from the XIA and the ion chambers after each step.

    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
        Other parameters: TODO


    Returns
    -------
    uid : str
        Unique id of the scan

    interp_filename : str
    Filename where the interpolated data was stored


    See Also
    --------
    :func:`tscan`

    '''
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    energy_grid, time_grid = generate_energy_grid(e0, preedge_start, xanes_start, xanes_end, exafs_end, preedge_spacing, xanes_spacing, exafs_spacing)
    positions_grid = xray.energy2encoder(energy_grid) / 360000

    ax = kwargs.get('ax')
    if ax is not None:
        uid, = RE(step_list_plan([xia1, i0, it, iff, ir], hhm.theta, positions_grid, name), LivePlot(xia1.mca1.roi0.sum.name, hhm.theta.name, ax=ax))
    else:
        uid, = RE(step_list_plan([xia1, i0, it, iff, ir], hhm.theta, positions_grid, name))

    path = '/GPFS/xf08id/User Data/{}.{}.{}/'.format(db[uid]['start']['year'], db[uid]['start']['cycle'], db[uid]['start']['PROPOSAL'])
    filename = parse_xia_step_scan(uid, name, path)

    ax.cla()
    plot_xia_step_scan(uid, ax=ax)

    print('Done!')
    return uid


def parse(db, uid):
    dataset = pd.DataFrame()
    hdr = db[uid]

    detectors = [pba1.adc6, pba1.adc1, pba2.adc6, pba1.adc7]

    channels = ['iff', 'it', 'ir', 'i0']
    for detector, channel in zip(detectors, channels):
        indx = 0
        spectrum = [];
        print(f'Detector {detector.name}')
        data = list(hdr.data(detector.name, stream_name=detector.name))
        for point in data:

            indx +=1
            print(f'We are at {indx}')
            adc = point['adc']
            try:
                adc = adc.apply(lambda x: (int(x, 16) >> 8) - 0x40000 if (int(x, 16) >> 8) > 0x1FFFF else int(x,
                                                                                                          16) >> 8) * 7.62939453125e-05
                mean_val = np.mean(adc)
            except:
                mena_val = 1
            spectrum.append(mean_val)
        dataset[channel] = np.array(spectrum)

    energies = np.array(hdr.start['plan_pattern_args']['object'])
    dataset['energy']= energies
    return dataset

def save_dataset(dataset, name):
    dataset.to_csv()