


def move_sample_stage_plan(sample_coordinates : dict = {}):
    for motor_key, position in sample_coordinates.items():
        motor = getattr(sample_stage, motor_key)
        yield from bps.mv(motor, position)



def random_step(x: float = 0,y: float = 0, **kwargs):

    '''
    This plan will move the stage randomly by a random number between
    x/2 and x  and y/2 and y, sampling a donut around the original point
    '''
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    print_to_gui('Executing random move',sys.stdout)
    if  type(x) == str:
        x = float(x)
        y = float(y)
    if not 'motor_x' in kwargs.keys():
        motor_x = giantxy.x
    if not 'motor_y' in kwargs.keys():
        motor_y = giantxy.y
    random_x = 2 * x * (random()-0.5)
    random_x = random_x * 0.5 + 0.5 * np.sign(random_x)
    random_y = 2 * y*(random()-0.5)
    random_y = random_y * 0.5 + 0.5 * np.sign(random_y)
    yield from mvr(motor_x,random_x,motor_y,random_y)

