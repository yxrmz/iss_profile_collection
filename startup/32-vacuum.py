from ophyd.utils.errors import UnknownStatusFailure
from ophyd.status import Status
'''
 Terrible hack
'''
class GateValve(TwoButtonShutterISS):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set(self, val):
        st = super().set(val)
        try:
            st.wait()
        except UnknownStatusFailure:
            st._finished(success=True)
        return st

gv_fm = GateValve('XF:08IDA-VA{Mir:FM-GV:1}', name = 'gv_fm')




# gv2 = TwoButtonShutterISS('FE:C08A-VA{GV:2}', name='gv2')
# gv_fb = TwoButtonShutterISS('XF:08IDA-VA{Fltr:FB-GV:1}', name = 'gv_fb')
# gv_cm = TwoButtonShutterISS('XF:08IDA-VA{Mir:1-CM-GV:1}', name = 'gv_cm' )
# gv_hhm = EPSTwoStateDevice('XF:08IDA-VA{Mono:HHM-GV:1}', name = 'gv_hhm' )
# gv_hrm = EPSTwoStateDevice('XF:08IDA-VA{Mono:HRM-GV:1}', name = 'gv_hrm')
gv_fm = GateValve('XF:08IDA-VA{Mir:FM-GV:1}', name = 'gv_fm')
# gv_bt = EPSTwoStateDevice('XF:08IDB-VA{BT-GV:1}', name = 'gv_bt')
#
#
# gate_valves = [gv2,gv_fb, gv_cm, gv_hhm, gv_hrm, gv_fm, gv_bt]

# def is_gate_valves_open():
#     message_stub = 'Gate valves cannot be opened:'
#     for gate_valve in gate_valves:
#         if gate_valve.status.get() =='Close':
#             if gate_valve.name == 'gv2':
#                 message = 'Gate Valve GV2 is closed. Contact control room at x2550'
#             else:
#                 pass


