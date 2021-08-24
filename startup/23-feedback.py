
from xas.pid import PID
from xas.image_analysis import determine_beam_position_from_fb_image
#
class PiezoFeedback:

    def __init__(self, hhm, bpm_es, sample_time = 0.01):

        self.hhm = hhm
        self.bpm_es = bpm_es


        P = 0.004 * 1
        I = 0  # 0.02
        D = 0  # 0.01
        self.pid = PID(P, I, D)
        self.pid.windup_guard = 3
        self.pid.setSampleTime(sample_time)

        self.go = 0
        self.should_print_diagnostics = True
        self.truncate_data = False

        self.read_piezo_analysis_parameters()


    def set_piezo_analysis_parameters(self, line, center, n_lines, n_measures, pcoeff):
        self.hhm.fb_line.put(line)
        self.hhm.fb_center.put(center)
        self.hhm.fb_nlines.put(n_lines)
        self.hhm.fb_nmeasures.put(n_measures)
        self.hhm.fb_pcoeff.put(pcoeff)
        self.read_piezo_analysis_parameters()


    def read_piezo_analysis_parameters(self):
        self.line = self.hhm.fb_line.get()
        self.center = self.hhm.fb_center.get()
        self.n_lines = self.hhm.fb_nlines.get()
        self.n_measures = self.hhm.fb_nmeasures.get()
        self.pid.Kp = self.hhm.fb_pcoeff.get()



    def determine_beam_position_from_image(self):
        try:

            image = self.bpm_es.image.array_data.read()['bpm_es_image_array_data']['value'].reshape((960,1280))

        except Exception as e:
            print(f"Exception: {e}\nPlease, check the max retries value in the piezo feedback IOC or maybe the network load (too many cameras).")
            return
        beam_position = determine_beam_position_from_fb_image(image,
                                                              line=self.line,
                                                              center_point=self.center,
                                                              n_lines=self.n_lines,
                                                              truncate_data=self.truncate_data,
                                                              should_print_diagnostics=self.should_print_diagnostics)
        return beam_position


    def gaussian_piezo_feedback(self):

        current_position = self.determine_beam_position_from_image()

        if current_position:
            self.pid.SetPoint = 960 - self.center_point
            self.pid.update(current_position)
            deviation = self.pid.output
            # deviation = -(coeff[1] - center_point)
            piezo_diff = deviation  # * 0.0855

            curr_value = self.gui.hhm.pitch.read()['hhm_pitch']['value']
            # print(f"{ttime.ctime()} curr_value: {curr_value}, piezo_diff: {piezo_diff}, delta: {curr_value - piezo_diff}")
            try:
                self.gui.hhm.pitch.move(curr_value - piezo_diff)
                self.should_print_diagnostics = True
            except:
                if self.should_print_diagnostics:
                    print('failed to correct pitch due to controller bug (DSSI works on it)')  # TODO: Denis 5/25/2021
                    self.should_print_diagnostics = False
        else:
            self.should_print_diagnostics = False

    def adjust_center_point(self, line=420, center_point=655, n_lines=1, n_measures=10):
        # getting center:
        centers = []
        #print(f'center_point INITIALLY is {center_point}')
        for i in range(n_measures):
            current_position = self.determine_beam_position_from_image(line=line, center_point=center_point,
                                                                       n_lines=n_lines)
            if current_position:
                centers.append(960 - current_position)
        # print('Centers: {}'.format(centers))
        # print('Old Center Point: {}'.format(center_point))
        if len(centers) > 0:
            center_point = np.mean(centers)
            print(f'center_point DETERMINED is {center_point}')
            self.gui.settings.setValue('piezo_center', center_point)
            self.gui.piezo_center = center_point
            self.gui.hhm.fb_center.put(self.gui.piezo_center)
            # print('New Center Point: {}'.format(center_point))

    def run(self)
        self.go = 1
        # self.adjust_center_point(line = self.gui.piezo_line, center_point = self.gui.piezo_center, n_lines = self.gui.piezo_nlines, n_measures = self.gui.piezo_nmeasures)

        while (self.go):
            # print("Here all the time? 1")
            if len([self.gui.shutter_dictionary[shutter] for shutter in self.gui.shutter_dictionary if
                    self.gui.shutter_dictionary[shutter].shutter_type != 'SP' and
                                    self.gui.shutter_dictionary[shutter].state.read()['{}_state'.format(shutter)][
                                        'value'] != 0]) == 0:
                self.gaussian_piezo_feedback(line=self.gui.piezo_line, center_point=self.gui.piezo_center,
                                             n_lines=self.gui.piezo_nlines, n_measures=self.gui.piezo_nmeasures)
                # print("Here all the time? 4")
                ttime.sleep(self.sampleTime)
                # print("Here all the time? 5")
            else:
                # print("Here all the time? Not here!")
                ttime.sleep(self.sampleTime)
#


from PyQt5.QtCore import QThread
class PiezoFeedbackThread(QThread, PiezoFeedback):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)




