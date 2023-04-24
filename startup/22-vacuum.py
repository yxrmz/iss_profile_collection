print(ttime.ctime() + ' >>>> ' + __file__)


from ophyd.utils.errors import UnknownStatusFailure, InvalidState
from ophyd.status import Status
'''
 Terrible hack
'''

class ISSGateValve(TwoButtonShutterISS):
    RETRY_PERIOD = 3
    MAX_ATTEMPTS = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def set(self, val):
        st = super().set(val)
        try:
            st.wait()
        except UnknownStatusFailure:
            # this handling is done because ophyd cannot operate on ISS gatevalves properly
            st._finished(success=True)
        return st

    def custom_set(self, val):
        try:
            self.set(val)
            success = True
        except InvalidState:
             success = False
        return success

    def open(self):
        return self.custom_set('Open')

    def close(self):
        return self.custom_set('Close')




gv2 = ISSGateValve('FE:C08A-VA{GV:2}', name='gv2')
gv_fb = ISSGateValve('XF:08IDA-VA{Fltr:FB-GV:1}', name = 'gv_fb')
gv_cm = ISSGateValve('XF:08IDA-VA{Mir:1-CM-GV:1}', name = 'gv_cm' )
gv_hhm = ISSGateValve('XF:08IDA-VA{Mono:HHM-GV:1}', name = 'gv_hhm' )
gv_hrm = ISSGateValve('XF:08IDA-VA{Mono:HRM-GV:1}', name = 'gv_hrm')
gv_fm = ISSGateValve('XF:08IDA-VA{Mir:FM-GV:1}', name ='gv_fm')
gv_bt = ISSGateValve('XF:08IDB-VA{BT-GV:1}', name = 'gv_bt')

gate_valves = [gv2, gv_fb, gv_cm, gv_hhm, gv_hrm, gv_fm, gv_bt]

def check_gate_valves():
    is_open_list = []
    message = ''
    for gate_valve in gate_valves:
        gv_status = gate_valve.status.get().lower()
        if gv_status in ['close', 'closed', 'not open']:
            if gate_valve.name == 'gv2':
                message += '  Gate valve GV2 is closed. Contact control room at x2550.\n'
                is_open = False

            else:
                print_to_gui(f'({ttime.ctime()}) Attempting to open {gate_valve.name}.')
                is_open = gate_valve.open()
                if not is_open:
                    print_to_gui(f'({ttime.ctime()}) Failed to open {gate_valve.name}.')
                    message += f'  Gate valve {gate_valve.name} cannot be opened. Contact beamline staff for assistance.\n'
                else:
                    print_to_gui(f'({ttime.ctime()}) Successfully opened {gate_valve.name}.')
        else:
            is_open = True

        is_open_list.append(is_open)

    all_open = all(is_open_list)
    if all_open:
        if shutter_fe_2b.status.get() == shutter_fe_2b.close_val:
            print_to_gui(f'({ttime.ctime()}) Attempting to open FE shutter.')
            try:
                _status = shutter_fe_2b.set('Open')
                _status.wait()
                print_to_gui(f'({ttime.ctime()}) Successfully opened FE shutter.')
            except:
                print_to_gui(f'({ttime.ctime()}) Failed to open FE shutter.')
                message += f'  FE shutter cannot be opened. Contact beamline staff for assistance.\n'

            # print_to_gui(f'({ttime.ctime()}) All gate valves and/or shutters were successfully open')
    else:
        message = 'Gate valves cannot be opened. Reasons:\n' + message

    return all_open, message


def check_gate_valves_plan():
    foe_ready, err_msg = check_gate_valves()
    if not foe_ready:
        print_to_gui(err_msg)
        raise Exception(err_msg)
    yield from bps.null()

