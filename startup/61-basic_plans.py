def print_message_plan(msg='', tag='', add_timestamp=False, ntabs=0):
    print_message(msg, tag='', add_timestamp=add_timestamp, ntabs=ntabs)
    yield from bps.null()

def move_bpm_fm_plan(action = 'insert'):
    yield from bps.mv(bpm_fm, action)

def put_bpm_fm_to_continuous_mode():
    # if hasattr(detector, 'image_mode'):
    yield from bps.mv(getattr(bpm_fm, 'image_mode'), 2)
    yield from bps.mv(getattr(bpm_fm, 'acquire'), 1)

def move_mono_energy(energy=-1):
    yield from bps.mv(hhm.energy, energy)

def set_hhm_feedback_plan(state=0):
    yield from bps.mv(hhm.fb_status, state)

