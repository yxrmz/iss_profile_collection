from ophyd import EpicsMotor, Device, Component as Cpt


class Mirror(Device):
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')
    roll = Cpt(EpicsMotor, '-Ax:R}Mtr')
    xd = Cpt(EpicsMotor, '-Ax:XD}Mtr')  # downstream
    xu = Cpt(EpicsMotor, '-Ax:XU}Mtr')  # upstream
    x = Cpt(EpicsMotor, '-Ax:X}Mtr')
    ydi = Cpt(EpicsMotor, '-Ax:YDI}Mtr')  # downstream inboard
    ydo = Cpt(EpicsMotor, '-Ax:YDO}Mtr')  # downstream outboard
    yu = Cpt(EpicsMotor, '-Ax:YU}Mtr')
    yaw = Cpt(EpicsMotor, '-Ax:Yaw}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y}Mtr')


mir1 = Mirror('XF:08IDA-OP{Mir:1-CM', name='mir1')
mir2 = Mirror('XF:08IDA-OP{Mir:2-CM', name='mir2')
fm = Mirror('XF:08IDA-OP{Mir:FM', name='fm')


class HHM(Device):
    "high heat load monochrometer"
    pitch = Cpt(EpicsMotor, '-Ax:P}Mtr')
    roll = Cpt(EpicsMotor, '-Ax:R}Mtr')
    theta = Cpt(EpicsMotor, '-Ax:Th}Mtr')
    y = Cpt(EpicsMotor, '-Ax:Y2}Mtr')

hhm = HHM('Mono:HHM', name='hhm')
