from bluesky.plan_patterns import spiral_square_pattern
import numpy as np
from bluesky.plans import rel_spiral_square


# def sample_spiral_scan():
#     detectors = [apb_ave]
#
#     return general_spiral_scan(detectors, giantxy.x, giantxy.y, 15, 15, 15, 15, time_step=0.1)

    # channels = [apb_ave.ch1, apb_ave.ch2, apb_ave.ch3, apb_ave.ch4]
    # offsets = [apb.ch1_offset, apb.ch2_offset, apb.ch3_offset, apb.ch4_offset, ]

    # plan = rel_spiral_square(detectors, giantxy.x, giantxy.y, 15, 15, 15, 15)

    # time_step = 0.1
    # samples = 250 * (np.ceil(time_step * 10443 / 250))  # hn I forget what that does... let's look into the new PB OPI
    # yield from bps.abs_set(apb_ave.sample_len, time_step*1e3, wait=True)
    # yield from bps.abs_set(apb_ave.wf_len, time_step*1e3, wait=True)
    # yield from bps.abs_set(apb_ave.divide, 374, wait=True)

    # if hasattr(detector, 'kickoff'):
    # plan_with_flyers = bpp.fly_during_wrapper(plan, [detectors])
    # uid = (yield from plan)
    # table = db[uid].table()
    # row_num = table[detector.volt.name].idxmin()
    # x_pos = table['giantxy_x'][row_num]
    # y_pos = table['giantxy_y'][row_num]

def general_spiral_scan(detectors_list, *, motor1=giantxy.x, motor2=giantxy.y, motor1_range=15, motor2_range=15, motor1_nsteps=15, motor2_nsteps=15, time_step=0.1, **kwargs):

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    print(f'Dets {detectors_list}')
    print(f'Motors {motor1}, {motor2}')


    plan = rel_spiral_square(detectors_list, motor1, motor2,
                                        motor1_range, motor2_range, motor1_nsteps, motor2_nsteps,
                                        md={"plan_name": "spiral scan"})

    if apb_ave in detectors_list:
        print('Preparing pizzabox')
        cur_divide_value = apb_ave.divide.value
        cur_sample_len = apb_ave.sample_len.value
        cur_wf_len = apb_ave.wf_len.value

    print('[General Spiral Scan] Starting scan...')
    yield from bps.abs_set(apb_ave.divide, 374, wait=True)
    yield from bps.abs_set(apb_ave.sample_len, int(time_step * 1e3), wait=True)
    yield from bps.abs_set(apb_ave.wf_len, int(time_step * 1e3), wait=True)

    uid = (yield from plan)

    if apb_ave in detectors_list:
        print('Returning the pizzabox to its original state')
        yield from bps.abs_set(apb_ave.divide, cur_divide_value, wait=True)
        yield from bps.abs_set(apb_ave.sample_len, cur_sample_len, wait=True)
        yield from bps.abs_set(apb_ave.wf_len, cur_wf_len, wait=True)
    return uid






from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def get_mus():
    data = db[-1].table()
    x = data['giantxy_x']
    y = data['giantxy_y']

    mut = np.log(data['apb_ave_ch1_mean']/data['apb_ave_ch2_mean'])
    muf = data['apb_ave_ch4_mean']/data['apb_ave_ch1_mean']

    return x,y, mut, muf

def analyze_surface():
    x, y, mut, muf = get_mus()
    plot_xyz(x, y, mut)
    plot_xyz(x, y, muf)


def com(a_orig, w_orig, mask=None):
    a = a_orig.copy()
    w = w_orig.copy()
    if mask is not None:
        a = a[mask]
        w = w[mask]
    return np.sum(a * w)/np.sum(w)




def plot_xyz(x, y, z, r1=5, r2=(13.4/2-1)):
    fig = plt.figure()
    # ax = fig.gca(projection='3d')
    # ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True, cmap=plt.cm.Spectral)
    ax = fig.gca()

    x_im_center = x.iloc[0]
    y_im_center = y.iloc[0]
    # R = r1 #13.4/2-1
    xy_mask = (np.sqrt(np.abs(x - x_im_center)**2 +
                       np.abs(y - y_im_center)**2) < r1)

    x_ho_com = com(x, z.max() - z, ~xy_mask)
    y_ho_com = com(y, z.max() - z, ~xy_mask)

    xy_mask_recen = (np.sqrt(np.abs(x - x_ho_com) ** 2 +
                             np.abs(y - y_ho_com) ** 2) < r2)

    # x_max = x[xy_mask_recen][np.argmax(z[xy_mask_recen])]
    # y_max = y[xy_mask_recen][np.argmax(z[xy_mask_recen])]

    x_max = com(x, (z - z.min())**2, xy_mask_recen)
    y_max = com(y, (z - z.min())**2, xy_mask_recen)

    ax.tricontourf(x, y, z, 50)
    ax.plot(x_im_center, y_im_center, 'ro', ms=25)
    ax.plot(x_ho_com, y_ho_com, 'bx', ms=25, markeredgewidth=5)
    ax.plot(x_max, y_max, 'm+', ms=25, markeredgewidth=5)

    # plt.plot(x[xy_mask], y[xy_mask], 'g.', alpha=0.5)
    # plt.plot(x[~xy_mask], y[~xy_mask], 'r.', alpha=0.5)
    # plt.show()