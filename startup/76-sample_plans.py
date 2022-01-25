


def move_sample_stage_plan(sample_coordinates : dict = {}):
    for motor_key, position in sample_coordinates.items():
        motor = getattr(sample_stage, motor_key)
        yield from bps.mv(motor, position)

def move_rel_sample_stage_plan(sample_coordinates : dict = {}):
    for motor_key, shift in sample_coordinates.items():
        motor = getattr(sample_stage, motor_key)
        yield from bps.mvr(motor, shift)

def random_donut_shift(v):
    random_v = 2 * v * (random() - 0.5)
    random_v = random_v * 0.5 + 0.5 * np.sign(random_v)
    return random_v

def move_sample_by_random_xy_step(x: float = 0, y: float = 0):

    '''
    This plan will move the stage randomly by a random number between
    x/2 and x  and y/2 and y, sampling a donut around the original point
    '''
    # sys.stdout = kwargs.pop('stdout', sys.stdout)
    print_to_gui('Executing random move')


    random_x = random_donut_shift(x)
    random_y = random_donut_shift(y)
    yield from move_rel_sample_stage_plan({'x' : random_x, 'y' : random_y})
    # yield from mvr(motor_x,random_x,motor_y,random_y)
