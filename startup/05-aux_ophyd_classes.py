from ophyd import (EpicsMotor, Device, Kind, Component as Cpt,
                   EpicsSignal)


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
                    print(f'[Debug message]: {ttime.ctime()}: {self.name} motor got stuck ... unstucking it')
                    self.stop()
                    self.move(cur_sp, wait=True, **kwargs)
                else:
                    old_pos = new_pos


    def move(self, position, wait=True, **kwargs):
        cid = self.motor_is_moving.subscribe(self._stuck_check)
        status = super().move(position, wait=True, **kwargs)
        self.motor_is_moving.unsubscribe(cid)
        return status




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

