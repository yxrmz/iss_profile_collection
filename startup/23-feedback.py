
from xas.pid import PID
from xas.image_analysis import determine_beam_position_from_fb_image
#

#
from piezo_feedback.piezo_fb import PiezoFeedback
from PyQt5.QtCore import QThread

machine_name = os.uname()[1]
if 'ws1' in machine_name:
    local_hostname = 'ws01'
elif 'ws2' in machine_name:
    local_hostname = 'ws02'
else:
    raise ValueError('This machine does not support local feedback')




class _PiezoFeedback(PiezoFeedback):
    def __init__(self):
        super().__init__(hhm,
                         bpm_es,
                         {shutter_fe.name: shutter_fe,
                          shutter_ph.name: shutter_ph},
                         local_hostname=local_hostname)


class PiezoFeedbackThread(QThread, _PiezoFeedback):
    def __init__(self):
        super().__init__()


hhm_feedback = PiezoFeedbackThread()
hhm_feedback.start()


