
from xas.pid import PID
from xas.image_analysis import determine_beam_position_from_fb_image
#

#
from piezo_feedback.piezo_fb import PiezoFeedback
from PyQt5.QtCore import QThread


class _PiezoFeedback(PiezoFeedback):
    def __init__(self):
        super().__init__(hhm,
                         bpm_es,
                         {shutter_fe.name: shutter_fe,
                          shutter_ph.name: shutter_ph},
                         host='local')


class PiezoFeedbackThread(QThread, _PiezoFeedback):
    def __init__(self):
        super().__init__()


hhm_feedback = PiezoFeedbackThread()


