print(ttime.ctime() + ' >>>> ' + __file__)

class Potentiostat(EpicsSignalRO):
    def get(self):
        value = super().get()
        if value>10:
            return 0
        else:
            return value

potentiostatV = Potentiostat('XF:08IDB-CT{DIODE-Box_B1:13}InCh0:Data-I')
potentiostatI = Potentiostat('XF:08IDB-CT{DIODE-Box_B1:13}InCh1:Data-I')

sample_env_dict= {
'sample_heater_1_T_rb':         {'obj': EpicsSignalRO('XF:08IDB-CT{DIODE-Box_B2:5}InCh0:Data-I'),
                                 'human_readable_key': 'SampleHeater.temperature1.readback',
                                 'shortcut': 'Temperature 1'},
'sample_heater_2_T_rb':         {'obj': EpicsSignalRO('XF:08IDB-CT{DIODE-Box_B2:5}InCh1:Data-I'),
                                 'human_readable_key': 'SampleHeater.temperature2.readback',
                                 'shortcut': 'Temperature 2'},
}