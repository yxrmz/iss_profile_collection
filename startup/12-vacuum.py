from nslsii.devices import TwoButtonShutter

gv2 = TwoButtonShutter('FE:C08A-VA{GV:2}Pos-Sts', name='gv2')
gv_fb = TwoButtonShutter('XF:08IDA-VA{Fltr:FB-GV:1}', name = 'gv_fb')
gv_cm = TwoButtonShutter('XF:08IDA-VA{Mir:1-CM-GV:1}', name = 'gv_cm' )
gv_hhm = TwoButtonShutter('XF:08IDA-VA{Mono:HHM-GV:1}', name = 'gv_hhm' )
gv_hrm = TwoButtonShutter('XF:08IDA-VA{Mono:HRM-GV:1}', name = 'gv_hrm')
gv_fm = TwoButtonShutter('XF:08IDA-VA{Mir:FM-GV:1}', name = 'gv_fm')
gv_bt = TwoButtonShutter('XF:08IDB-VA{BT-GV:1}', name = 'gv_bt')


gate_valves = [gv2,gv_fb, gv_cm, gv_hhm, gv_hrm, gv_fm, gv_bt]

# def is_gate_valves_open():
#     message_stub = 'Gate valves cannot be opened:'
#     for gate_valve in gate_valves:
#         if gate_valve.status.get() =='Close':
#             if gate_valve.name == 'gv2':
#                 message = 'Gate Valve GV2 is closed. Contact control room at x2550'
#             else:
#                 pass


def force_gv_open(gvs):
    to_open = []
    for valve in gvs:
        state = yield from bps.rd(valve)
        if state != 'open':   # or what ever they return in the "right" state
            to_open.extend([valve, "open"])
    if len(to_open):
        yield from bps.mv(*to_open)
    failed = []
    for valve in gvs:
        state = yield from bps.rd(valve)
        if state is not None and state != 'open':
            failed.append(valve)
    if len(failed):
        raise RuntimeError(f"Failed to open {[v.name for v in failed]}, please open manually")