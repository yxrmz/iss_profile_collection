from ophyd import (EpicsMotor, Device, Kind, Component as Cpt,
                   EpicsSignal)
from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, Kind, set_and_wait
from ophyd.sim import NullStatus

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