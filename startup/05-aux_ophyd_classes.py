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
        self.n_tries = 2
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


    def move(self, position, wait=True, **kwargs):
        position = self.check_position_vs_low_lim(position)
        for i in range(self.n_tries):
            status = super().move(position, wait=True, **kwargs)
            self.homing.put('1')
            ttime.sleep(self.dwell_time)
        return status


def combine_status_list(status_list):
    st_all = status_list[0]
    for st in status_list[1:]:
        st_all = st_all and st
    return st_all