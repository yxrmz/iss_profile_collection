from bluesky.plan_patterns import spiral_square_pattern

from bluesky.plans import rel_spiral_square

def find_holder_fiducial():
    detector = it
    motor_x = motor_dictionary['giantxy_x']['object']
    motor_y = motor_dictionary['giantxy_y']['object']

    plan = rel_spiral_square([detector],motor_x,motor_y,5,5,20,20)

    if hasattr(detector, 'kickoff'):
        plan_with_flyers = bpp.fly_during_wrapper(plan, [detector])
    uid = (yield from plan_with_flyers)
    # table = db[uid].table()
    # row_num = table[detector.volt.name].idxmin()
    # x_pos = table['giantxy_x'][row_num]
    # y_pos = table['giantxy_y'][row_num]


