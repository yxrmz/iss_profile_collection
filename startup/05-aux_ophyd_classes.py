from ophyd import (EpicsMotor, Device, Kind, Component as Cpt,
                   EpicsSignal, EpicsSignalRO, Kind, set_and_wait,
                   PseudoPositioner, PseudoSingle, SoftPositioner)
from ophyd.sim import NullStatus

from ophyd.pseudopos import (pseudo_position_argument,
                             real_position_argument)

from bluesky.preprocessors import monitor_during_wrapper


class StuckingEpicsMotor(EpicsMotor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stuck_check_delay = 2

    def _stuck_check(self, value, old_value, **kwargs):
        if value == 1: # here value == self.motor_is_moving
            cur_sp = self.user_setpoint.get()
            old_pos = self.user_readback.get()

            while self.motor_is_moving.get() == 1:
                ttime.sleep(self._stuck_check_delay)
                new_pos = self.user_readback.get()
                if new_pos == old_pos:
                    print_to_gui(f'[Debug message]: {ttime.ctime()}: {self.name} motor got stuck ... unstucking it')
                    self.stop()
                    self.move(cur_sp, wait=True, **kwargs)
                else:
                    old_pos = new_pos


    def move(self, position, wait=True, **kwargs):
        cid = self.motor_is_moving.subscribe(self._stuck_check)
        status = super().move(position, wait=wait, **kwargs)
        self.motor_is_moving.unsubscribe(cid)
        return status


class StuckingEpicsMotorThatFlies(StuckingEpicsMotor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flying = None

    def append_flying_status_pv(self, pv):
        self.flying = pv

    def _stuck_check(self, value, old_value, **kwargs):
        if value == 1:  # here value == self.motor_is_moving
            cur_sp = self.user_setpoint.get()
            old_pos = self.user_readback.get()
            if self.flying is not None:
                is_flying = bool(self.flying.get())
            else:
                is_flying = False

            while self.motor_is_moving.get() == 1:
                ttime.sleep(self._stuck_check_delay)
                new_pos = self.user_readback.get()
                if new_pos == old_pos and (not is_flying):
                    print(f'[Debug message]: {ttime.ctime()}: {self.name} motor got stuck ... unstucking it')
                    self.stop()
                    self.move(cur_sp, wait=True, **kwargs)
                else:
                    old_pos = new_pos


class InfirmStuckingEpicsMotor(StuckingEpicsMotor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dwell_time = 2
        self.n_tries = 5
        self.low_lim = None

    def set_low_lim(self, low_lim=8.5):
        self.low_lim = low_lim

    def check_position_vs_low_lim(self, position):
        if self.low_lim is not None:
            if position < self.low_lim:
                position = self.low_lim
        return position


    def append_homing_pv(self, homing):
        self.homing = homing

    def one_move_attempt(self, position, wait=True, attempt_num=None, **kwargs):
        print_to_gui(f'(attempt_num={attempt_num}) moving hhm_y_precise to {position}', add_timestamp=True, tag='Debug')
        status = super().move(position, wait=wait, **kwargs)
        status.wait()
        print_to_gui(f'(attempt_num={attempt_num}) user readback value of hhm_y_precise before homing is {self.user_readback.value}', add_timestamp=True, tag='Debug')
        self.homing.put('1')
        ttime.sleep(self.dwell_time)
        print_to_gui(f'(attempt_num={attempt_num}) user readback value of hhm_y_precise after homing is {self.user_readback.value}', add_timestamp=True, tag='Debug')
        # self.user_setpoint.set(self.position)

        return status

    def move(self, new_position, wait=True, max_attempts=20, **kwargs):
        wait=True
        new_position = self.check_position_vs_low_lim(new_position)

        for idx in range(20):
            status = self.one_move_attempt(new_position, wait=wait, attempt_num=idx, **kwargs)
            if abs(new_position - self.position) < 0.0075:
                break
            if idx == 19:
                print('exceeded the maximum number of attempts (20) to bring the motor to requested position')
        ttime.sleep(1)
        return status

    def set(self, *args, **kwargs):
        if 'wait' in kwargs.keys():
            print_to_gui(f'{self.name} set kwargs = {kwargs}', add_timestamp=True, tag='Debug')
            kwargs.pop('wait')
        return super().set(*args, wait=True, **kwargs)

def combine_status_list(status_list):
    st_all = status_list[0]
    for st in status_list[1:]:
        st_all = st_all and st
    return st_all



def compose_bulk_datum(*, resource_uid, counter, datum_kwargs, validate=True):
    # print_message_now(datum_kwargs)
    # any_column, *_ = datum_kwargs
    # print_message_now(any_column)
    N = len(datum_kwargs)
    # print_message_now(N)
    doc = {'resource': resource_uid,
           'datum_ids': ['{}/{}'.format(resource_uid, next(counter)) for _ in range(N)],
           'datum_kwarg_list': datum_kwargs}
    # if validate:
    #     schema_validators[DocumentNames.bulk_datum].validate(doc)
    return doc


def return_NullStatus_decorator(plan):
    def wrapper(*args, **kwargs):
        yield from plan(*args, **kwargs)
        return NullStatus()
    return wrapper


# def ramp_plan_fixed(go_plan, monitor_sig, inner_plan_func,
#                     take_pre_data=True, timeout=None, period=None, md=None):
#
#     @return_NullStatus_decorator
#     def _go_plan():
#         yield from go_plan
#
#     yield from bp.ramp_plan(_go_plan, monitor_sig, inner_plan_func,
#                             take_pre_data=take_pre_data, timeout=timeout, period=period, md=md)


def ramp_plan_with_multiple_monitors(go_plan, monitor_list, inner_plan_func,
                                     take_pre_data=True, timeout=None, period=None, md=None):
    mon1 = monitor_list[0]
    mon_rest = monitor_list[1:]
    ramp_plan = bp.ramp_plan(go_plan, mon1, inner_plan_func,
                                take_pre_data=take_pre_data, timeout=timeout, period=period, md=md)
    yield from monitor_during_wrapper(ramp_plan, mon_rest)


from ophyd.utils import AlarmSeverity

class EpicsMotorThatCannotReachTheTargetProperly(EpicsMotor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tolerated_alarm =  AlarmSeverity.MAJOR


    def set(self, new_position, atol=5e-3, max_tries=500, **kwargs):
        for i in range(max_tries):
            # print(i)
            st = super().set(new_position, **kwargs)
            st.wait()
            if np.isclose(self.position, new_position, atol=atol):
                return st
        print('Achieved the maximum motion attempts; exiting')
        return st



# sample_stage_z = EpicsMotorThatCannotReachTheTargetProperly('XF:08IDB-OP{Misc-Ax:2}Mtr', name='sample_stage_z')
# sample_stage_z.tolerated_alarm =  AlarmSeverity.MAJOR
#
# RE(bps.mv(sample_stage_z, -3.5, wait=True))



