

class FlyableEpicsMotor(Device): # device is needed to have Device status
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
        #              'durations': [t1_2, t2_3, t3_4]}
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


def test_flying_epics_motor():
    flying_motor_cr_main_roll =  FlyableEpicsMotor(johann_emission.motor_cr_main_roll, name='flying_motor_cr_main_roll')
    flying_motor_cr_aux2_roll = FlyableEpicsMotor(johann_emission.motor_cr_aux2_roll, name='flying_motor_cr_aux2_roll')
    flying_motor_cr_aux3_roll = FlyableEpicsMotor(johann_emission.motor_cr_aux3_roll, name='flying_motor_cr_aux3_roll')

    roll_center = 1500
    roll_delta1 = 1000
    roll_delta2 = 200
    traj_dict_main = {'positions': [roll_center - roll_delta1,
                                    roll_center - roll_delta2,
                                    roll_center + roll_delta2,
                                    roll_center + roll_delta1], 'durations': [5, 10, 5]}
    flying_motor_cr_main_roll.set_trajectory(traj_dict_main)
    flying_motor_cr_aux2_roll.set_trajectory(traj_dict_main)
    flying_motor_cr_aux3_roll.set_trajectory(traj_dict_main)

    prepare_st1 = flying_motor_cr_main_roll.prepare()
    prepare_st2 = flying_motor_cr_aux2_roll.prepare()
    prepare_st3 = flying_motor_cr_aux3_roll.prepare()

    combine_status_list([prepare_st1, prepare_st2, prepare_st3]).wait()

    st1 = flying_motor_cr_main_roll.kickoff()
    st2 = flying_motor_cr_aux2_roll.kickoff()
    st3 = flying_motor_cr_aux3_roll.kickoff()

    combine_status_list([st1, st2, st3]).wait()

    data1 = np.array(flying_motor_cr_main_roll.data)
    data2 = np.array(flying_motor_cr_aux2_roll.data)
    data3 = np.array(flying_motor_cr_aux3_roll.data)

    plt.figure(1, clear=True)
    plt.plot(data1[:, 0] - data1[0, 0], data1[:, 1], '.-')
    plt.plot(data2[:, 0] - data1[0, 0], data2[:, 1], '.-')
    plt.plot(data3[:, 0] - data1[0, 0], data3[:, 1], '.-')
