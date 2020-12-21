from bluesky.plan_patterns import spiral_square_pattern
import time as ttime
import numpy as np
import bluesky.plans as bp
from bluesky.plans import rel_spiral_square
from ophyd.sim import NullStatus


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


class SnakeFlyer():
    def __init__(self, det, pbs, motor_stage):
        self.name = 'snake_flyer'
        self.parent = None
        self.det = det
        self.pbs = pbs  # a list of passed pizza-boxes
        self.motor_stage = motor_stage
        self._motor_status = None
        self.traj = None

    def _motor_snaker(self, motor_x=None, range_x=None, motor_y=None, range_y=None):
        """Snake tragectory for flyer.

        :param motor_x: ophyd object for motor
        :param range_x: range in motor units
        :param motor_y: ophyd object for motor
        :param range_y: range in motor units
        :return: None
        """

        # Read start positions.
        start_pos_x = motor_x.user_readback.get()
        start_pos_y = motor_y.user_readback.get()

        step = 1

        # We need the grid scan here to get the tragectory.
        plan = bp.rel_grid_scan([], motor_y, -range_y / 2, range_y / 2, (range_y / step + 1),
                                motor_x, -range_x / 2, range_x / 2, 2,
                                True  # snake=True
                                )

        # This is adapted from plot_raster_scan in bluesky.
        cur_x = cur_y = None
        self.traj = []
        for msg in plan:
            cmd = msg.command
            if cmd == 'set':
                if msg.obj.name == motor_x.name:
                    cur_x = msg.args[0]
                if msg.obj.name == motor_y.name:
                    cur_y = msg.args[0]
            elif cmd == 'save':
                self.traj.append((cur_x, cur_y))

        # Move motors along the trajectory.
        for (x, y) in self.traj:
            print(x, y)
            if abs(motor_x.user_readback.get() - x) > 5e-3:
                print(f"Moving {motor_x.name}")
                # .move blocks the operation, and waits until the motor arrives to the target position.
                motor_x.move(x)
            if abs(motor_y.user_readback.get() - y) > 5e-3:
                print(f"Moving {motor_y.name}")
                # .move blocks the operation, and waits until the motor arrives to the target position.
                motor_y.move(y)

        # Move back to the original position both motors simultaneously.
        self._motor_status = motor_x.set(start_pos_x)
        self._motor_status &= motor_y.set(start_pos_y)

    def kickoff(self, *args, **kwargs):
        for pb in self.pbs:
            pb.stage()
            pb.kickoff()

        self.det.stage()
        # Start apb after encoder pizza-boxes, which will trigger the motor.
        self.det.stream.set(1)

        self._motor_snaker(motor_x=self.motor_stage.x, range_x=10, motor_y=self.motor_stage.y, range_y=4)

        print(f"Motor status in kickoff: {self._motor_status}")

        return NullStatus()

    def complete(self):
        print(f"Motor status in complete: {self._motor_status}")

        def callback_det(value, old_value, **kwargs):
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                print(f'callback_det {ttime.ctime()}')
                return True
            else:
                return False
        streaming_st = SubscriptionStatus(self.det.streaming, callback_det)

        def callback_motor():
            print(f'callback_motor {ttime.ctime()}')

            for pb in self.pbs:
                pb.complete()

            # TODO: see if this set is still needed (also called in self.det.unstage())
            self.det.stream.put(0)
            self.det.complete()

        self._motor_status.add_callback(callback_motor)

        # Jdun!
        return streaming_st & self._motor_status

    def describe_collect(self):
        return_dict = {self.det.name:
                        {f'{self.det.name}': {'source': 'APB',
                                              'dtype': 'array',
                                              'shape': [-1, -1],
                                              'filename_bin': self.det.filename_bin,
                                              'filename_txt': self.det.filename_txt,
                                              'external': 'FILESTORE:'}}}
        # Also do it for all pizza-boxes
        for pb in self.pbs:
            return_dict[pb.name] = pb.describe_collect()[pb.name]

        # Add a stream for the motor positions.
        return_dict[self.motor_stage.name] = {f'{self.motor_stage.x.name}': {'source': 'SNAKE',
                                                                             'dtype': 'number',
                                                                             'shape': []},
                                              f'{self.motor_stage.y.name}': {'source': 'SNAKE',
                                                                             'dtype': 'number',
                                                                             'shape': []}
                                              }
        return return_dict

    def collect_asset_docs(self):
        yield from self.det.collect_asset_docs()
        for pb in self.pbs:
            yield from pb.collect_asset_docs()

    def collect(self):
        print(f"Motor status in collect: {self._motor_status}")

        self.det.unstage()
        for pb in self.pbs:
            pb.unstage()

        def collect_all():
            for pb in self.pbs:
                yield from pb.collect()
            yield from self.det.collect()

            # Collect docs for motor positions.
            now = ttime.time()
            for (x, y) in self.traj:
                data = {f"{self.motor_stage.x.name}": x,
                        f"{self.motor_stage.y.name}": y}

                yield {'data': data,
                       'timestamps': {key: now for key in data}, 'time': now,
                       'filled': {key: False for key in data}}

        return collect_all()



snake_flyer = SnakeFlyer(det=apb_stream, pbs=[pb4.enc3, pb4.enc4], motor_stage=giantxy)