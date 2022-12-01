
def get_vh_metadata(plan_kwargs, scan_for_calibration_purpose=False, create_rixs_filename=False):
    metadata = plan_kwargs.pop('metadata')
    vh_metadata = {'spectrometer': 'von_hamos',
                   'spectrometer_config': von_hamos_geometry.short_config,
                   'scan_for_calibration_purpose': scan_for_calibration_purpose}

    if create_rixs_filename:
        name = plan_kwargs['name']
        rixs_file_name = create_interp_file_name(name, '.rixs')
        vh_metadata['rixs_file_name'] = rixs_file_name

    return {**vh_metadata, **metadata}

def _update_vh_spectrometer_calibration():
    calibration_uid = db[-1].uid
    von_hamos_geometry.set_spectrometer_calibration(calibration_uid)

def collect_von_hamos_xes_plan(**kwargs):
    ensure_pilatus_is_in_detector_list(kwargs['detectors'])
    metadata = get_vh_metadata(kwargs)
    yield from collect_n_exposures_plan(**kwargs, metadata=metadata)

def step_scan_von_hamos_plan(**kwargs):
    ensure_pilatus_is_in_detector_list(kwargs['detectors'])

    scan_for_calibration_purpose = kwargs.pop('scan_for_calibration_purpose')
    metadata = get_vh_metadata(kwargs,
                               scan_for_calibration_purpose=scan_for_calibration_purpose,
                               create_rixs_filename=True)
    yield from step_scan_plan(**kwargs, metadata=metadata)

    if scan_for_calibration_purpose:
        _update_vh_spectrometer_calibration()


def fly_scan_von_hamos_plan(**kwargs):
    ensure_pilatus_is_in_detector_list(kwargs['detectors'])

    scan_for_calibration_purpose = kwargs.pop('scan_for_calibration_purpose')
    metadata = get_vh_metadata(kwargs,
                               scan_for_calibration_purpose=scan_for_calibration_purpose,
                               create_rixs_filename=True)
    yield from fly_scan_plan(**kwargs, metadata=metadata)

    if scan_for_calibration_purpose:
        _update_vh_spectrometer_calibration()

# def test_plan():
#     yield from bps.null()
#     _update_vh_spectrometer_calibration()
#
# RE(test_plan())

# print(f'BEFORE: {BLA=}')
# RE(test_plan())
# print(f'AFTER: {BLA=}')

# def calibration_scan_w_pilatus(name: str, comment: str, n_cycles: int = 1, delay: float = 0,
#                                energy_down: bool = True,
#                                energy_min: float = 6460,
#                                energy_max: float = 6480,
#                                energy_step: float = 2,
#                                exposure_time: float = 1,
#                                 **kwargs):
#
#     sys.stdout = kwargs.pop('stdout', sys.stdout)
#
#
#     # energy_grid = kwargs.pop('energy_grid', [])
#     energy_grid = np.arange(energy_min, energy_max + energy_step, energy_step)
#     time_grid = np.ones(energy_grid.size) * exposure_time
#     if energy_down:
#         energy_grid = energy_grid[::-1]
#         time_grid = time_grid[::-1]
#
#     for indx in range(int(n_cycles)):
#         name_n = '{} {:04d}'.format(name, indx + 1)
#         yield from shutter.open_plan()
#         yield from step_scan_plan(name_n, comment, energy_grid, time_grid, [apb_ave, pil100k, hhm.enc.pos_I])
#         yield from shutter.close_plan()
#         yield from bps.sleep(float(delay))




#
#
#
# def point_scan_w_pilatus(name: str, comment: str, n_cycles: int = 1, delay: float = 0,
#                                energy: float = 7000,
#                                exposure_time: float = 1,
#                                use_sample_registry: bool = False,
#                                 **kwargs):
#
#     sys.stdout = kwargs.pop('stdout', sys.stdout)
#
#
#     # energy_grid = kwargs.pop('energy_grid', [])
#     energy_grid = np.array([energy])
#     time_grid = np.ones(energy_grid.size) * exposure_time
#
#     for indx in range(int(n_cycles)):
#         name_n = '{} {:04d}'.format(name, indx + 1)
#         if use_sample_registry:
#             if sample_registry.position_list is not None:
#                 yield from sample_registry.goto_unexposed_point_plan()
#
#         yield from shutter.open_plan()
#         yield from step_scan_plan(name_n, comment, energy_grid, time_grid, [apb_ave, pil100k, hhm.enc.pos_I])
#         yield from shutter.close_plan()
#         yield from bps.sleep(float(delay))
#         if use_sample_registry:
#             if sample_registry.position_list is not None:
#                 sample_registry.set_current_point_exposed()
#                 yield from sample_registry.goto_next_point_plan()
#                 sample_registry.dump_data()


# def last_dataset(spec_num, x_min,x_max, ):
#    hdr = db[spec_num]
#    t = hdr.table(fill=True)
#    im = t['pil100k_image'][1]
#    a=np.sum(im[x_min:x_max,:], axis=0)
#    plt.figure()
#    plt.plot(a)
#    return a
#
#
#
# def last_dataset_im():
#     hdr = db[-1]
#     t = hdr.table(fill=True)
#     im = t['pil100k_image'][1]
#     plt.figure()
#     plt.imshow(im,vmax=100)
