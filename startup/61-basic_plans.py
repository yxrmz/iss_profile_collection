def print_message_plan(msg='', tag='', add_timestamp=False, ntabs=0):
    print_to_gui(msg, tag=tag, add_timestamp=add_timestamp, ntabs=ntabs)
    yield from bps.null()

def sleep_plan(delay : float = 1.0):
    yield from bps.sleep(float(delay))

def move_bpm_fm_plan(action = 'insert'):
    yield from bps.mv(bpm_fm, action)

def put_bpm_fm_to_continuous_mode():
    # if hasattr(detector, 'image_mode'):
    yield from bps.mv(getattr(bpm_fm, 'image_mode'), 2)
    yield from bps.mv(getattr(bpm_fm, 'acquire'), 1)



def set_hhm_feedback_plan(state=0, update_center=False):
    if update_center:
        hhm_feedback.update_center()
        yield from sleep_plan(delay=0.3)
    yield from bps.mv(hhm.fb_status, state)

def move_motor_plan(motor_attr='', based_on='description', position=None):
    motor_device = get_motor_device(motor_attr, based_on=based_on)
    yield from bps.mv(motor_device, position)

def move_mono_energy(energy=-1):
    yield from move_motor_plan(motor_attr=hhm.energy.name, based_on='object_name', position=energy)
