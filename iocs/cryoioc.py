from textwrap import dedent

from caproto import ChannelType
from caproto._dbr import _LongStringChannelType
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run
import time as ttime
import numpy as np
from ophyd import Component as Cpt, Device, EpicsSignalRO, Kind
from nslsii.devices import TwoButtonShutter

cryocooler_ps_level = EpicsSignalRO('XF:08IDA-UT{Cryo:1}PS-I', name='cryocooler_ps_level')
cryocooler_bath_level = EpicsSignalRO('XF:08IDA-UT{Cryo:1}LN2Bath-I', name='cryocooler_bath_level')
cryocooler_valve = TwoButtonShutter('XF:08IDA-UT{Cryo:1-Vlv}', name='cryocooler_valve')

cryocooler_bath_level_lo = 60
cryocooler_bath_level_hi = 70


print('#####################################################################')
print('###                    LAUNCHING CRYO WATCH IOC                   ###')
print('#####################################################################')


class CryoIOC(PVGroup):
    """
    An IOC for watching the ISS cryostat

    """
    heartbeat = pvproperty(
        value=0,
        doc='IOC heartbeat'
    )

    dwell_time = 5 # seconds

    @heartbeat.startup
    async def heartbeat(self, instance, async_lib):

        while True:
            await async_lib.sleep(self.dwell_time)
            await instance.write(value=int(not instance.value))
            try:
                cryocooler_bath_level_value = cryocooler_bath_level.get()
                print(f'{cryocooler_bath_level_value=:.3f}.', end=' ')

                if (cryocooler_bath_level_value > cryocooler_bath_level_hi) and (cryocooler_valve.status.get() == 'Open'):
                    print(f'REACHED THE HIGHER THRESHOLD. CLOSING THE VALVE.')
                    st = cryocooler_valve.set('Close')
                    st.wait()

                elif (cryocooler_bath_level_value <= cryocooler_bath_level_lo) and (cryocooler_valve.status.get() == 'Not Open'):
                    print('REACHED THE LOWER THRESHOLD. OPENING THE VALVE.')
                    st = cryocooler_valve.set('Open')
                    st.wait()

                else:
                    print(f'NORMAL OPERATIONS.')
            except Exception as e:
                print(f'Failed to act on the valve. Reason: {e}')




if __name__ == '__main__':
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='XF:08IDA-CryoWatch:',
        desc=dedent(CryoIOC.__doc__))
    ioc = CryoIOC(**ioc_options)
    run(ioc.pvdb, **run_options)