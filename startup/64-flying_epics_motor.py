

class FlyableEpicsMotor(Device):
    '''
    This class mimics hhm behavior that is used in the standard HHM ISS flyer
    '''

    def __init__(self, motor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.motor = motor
        self.traj_dict = None
        self.flying_status = None

    def set_trajectory(self, traj_dict):
        # traj_dict = {'positions': [point1, point2, point3, point4],
        #              'velocities': [v1_2, v2_3 ,v3_4]}
        self.traj_dict = traj_dict

    def prepare(self):
        return self.motor.move(self.traj_dict['positions'][0], wait=False)

    def kickoff(self):
        self.flying_status = DeviceStatus(self)
        thread = threading.Thread(target=self.execute_motion, daemon=True)
        thread.start()
        return self.flying_status

    def execute_motion(self):
        self.data = []
        def write_data_callback(value, timestamp, **kwargs):
            self.data.append([timestamp, value])
        cid = self.motor.user_readback.subscribe(write_data_callback)

        pre_fly_velocity = self.motor.velocity.get()
        for prev_position, next_position, duration in zip(self.traj_dict['positions'][:-1],
                                                          self.traj_dict['positions'][1:],
                                                          self.traj_dict['durations']):
            velocity = abs(next_position - prev_position) / duration
            self.motor.velocity.set(velocity).wait()
            self.motor.move(next_position).wait()
        self.flying_status.set_finished()

        self.motor.velocity.set(pre_fly_velocity).wait()
        self.motor.user_readback.unsubscribe(cid)

    def complete(self):
        self.flying_status = None
        self.traj_dict = None

    @property
    def current_trajectory_duration(self):
        return sum(self.traj_dict['durations'])


