from xas.file_io import validate_file_exists
import time as ttime
from datetime import datetime
from ophyd.status import SubscriptionStatus



class FlyerAPBwithTrigger(FlyerAPB):

    def __init__(self, det, pbs, motor, trigger): #, xs_det):
        super().__init__( det, pbs, motor)
        self.trigger = trigger

    def kickoff(self, traj_duration=None):
        self.trigger.stage()
        st_super = super().kickoff(traj_duration=traj_duration)
        return st_super

    def complete(self):
        st_super = super().complete()
        def callback_motor():
            self.trigger.complete()

        self._motor_status.add_callback(callback_motor)
        return st_super & self._motor_status #& st_xs

    def describe_collect(self):
        dict_super = super().describe_collect()
        dict_trig = self.trigger.describe_collect()
        return {**dict_super, **dict_trig}#, **dict_xs}

    def collect_asset_docs(self):
        yield from super().collect_asset_docs()
        yield from self.trigger.collect_asset_docs()

    def collect(self):
        self.trigger.unstage()
        yield from super().collect()
        yield from self.trigger.collect()


flyer_apb_trigger = FlyerAPBwithTrigger(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger)



class FlyerXS(FlyerAPBwithTrigger):

    def __init__(self, det, pbs, motor, trigger, xs_det):
        super().__init__( det, pbs, motor, trigger)
        self.xs_det = xs_det

    def kickoff(self, traj_duration=None):
        traj_duration = get_traj_duration()
        acq_rate = self.trigger.freq.get()
        self.xs_det.stage(acq_rate, traj_duration)
        st_super = super().kickoff(traj_duration=traj_duration)
        return st_super

    def complete(self):
        st_super = super().complete()
        def callback_xs(value, old_value, **kwargs):
            if int(round(old_value)) == 1 and int(round(value)) == 0:
                self.xs_det.complete()
                return True
            else:
                return False

        saving_st = SubscriptionStatus(self.xs_det.hdf5.capture, callback_xs)
        return st_super & saving_st

    def describe_collect(self):
        dict_super = super().describe_collect()
        dict_xs = self.xs_det.describe_collect()
        return {**dict_super, **dict_xs}

    def collect_asset_docs(self):
        yield from super().collect_asset_docs()
        yield from self.xs_det.collect_asset_docs()

    def collect(self):
        self.xs_det.unstage()
        yield from super().collect()
        yield from self.xs_det.collect()


flyer_xs = FlyerXS(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger, xs_det=xs_stream)


class FlyerPilatus(FlyerAPBwithTrigger):

    def __init__(self, det, pbs, motor, trigger, pil_det):
        super().__init__( det, pbs, motor, trigger)
        self.pil_det = pil_det

    def kickoff(self, traj_duration=None):
        print(f'     !!!!! {datetime.now()} PIL100K KICKOFF')
        traj_duration = get_traj_duration()
        acq_rate = self.trigger.freq.get()
        self.pil_det.stage(acq_rate, traj_duration)

        st_pil = self.pil_det.trigger()
        st_super = super().kickoff(traj_duration=traj_duration)
        return st_super & st_pil

    def complete(self):
        print(f'     !!!!! {datetime.now()} PIL100K COMPLETE')
        st_super = super().complete()
        # def callback_pil(value, old_value, **kwargs):
        #     print(f'     !!!!! {datetime.now()} callback_pil100k_capture {value} --> {old_value}')
        #     if int(round(old_value)) == 1 and int(round(value)) == 0:
        #         print(f'     !!!!! {datetime.now()} callback_pil100k_capture')
        #         self.pil_det.complete()
        #         return True
        #     else:
        #         return False
        # saving_st = SubscriptionStatus(self.pil_det.tiff.capture, callback_pil)
        self.pil_det.complete()
        return st_super# & saving_st

    def describe_collect(self):
        print(f'     !!!!! {datetime.now()} PIL100K DESCRIBE COLLECT')
        dict_super = super().describe_collect()
        dict_pil = self.pil_det.describe_collect()
        return {**dict_super, **dict_pil}

    def collect_asset_docs(self):
        print(f'     !!!!! {datetime.now()} PIL100K COLLECT ASSET DOCS')
        yield from super().collect_asset_docs()
        yield from self.pil_det.collect_asset_docs()

    def collect(self):
        print(f'     !!!!! {datetime.now()} PIL100K COLLECT')
        self.pil_det.unstage()
        yield from super().collect()
        yield from self.pil_det.collect()


# flyer_pil = FlyerPilatus(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger_pil100k, pil_det=pil100k_stream)
flyer_pil = FlyerPilatus(det=apb_stream, pbs=[pb9.enc1], motor=hhm, trigger=apb_trigger_pil100k, pil_det=pil100k_hdf5_stream)


def execute_trajectory_apb_trigger(name, **metadata):
    md = get_md_for_scan(name,
                         'fly_scan',
                         'execute_trajectory_apb_trigger',
                         'fly_energy_scan_apb_trigger',
                         **metadata)
    yield from bp.fly([flyer_apb_trigger], md=md)





def execute_trajectory_xs(name, **metadata):
    md = get_md_for_scan(name,
                         'fly_scan',
                         'execute_trajectory_xs',
                         'fly_energy_scan_xs3',
                         **metadata)
    md['aux_detector'] = 'XSpress3'
    yield from bp.fly([flyer_xs], md=md)



def execute_trajectory_pil100k(name, **metadata):
    md = get_md_for_scan(name,
                         'fly_scan',
                         'execute_trajectory_pil100k',
                         'fly_energy_scan_pil100k',
                         **metadata)
    md['aux_detector'] = 'Pilatus100k'

    roi_data = [[pil100k.roi1.min_xyz.min_x.get(), pil100k.roi1.min_xyz.min_y.get(),
                 pil100k.roi1.size.x.get(),        pil100k.roi1.size.y.get()        ],
                [pil100k.roi2.min_xyz.min_x.get(), pil100k.roi2.min_xyz.min_y.get(),
                 pil100k.roi2.size.x.get(),        pil100k.roi2.size.y.get()        ],
                [pil100k.roi3.min_xyz.min_x.get(), pil100k.roi3.min_xyz.min_y.get(),
                 pil100k.roi3.size.x.get(),        pil100k.roi3.size.y.get()],
                [pil100k.roi4.min_xyz.min_x.get(), pil100k.roi4.min_xyz.min_y.get(),
                 pil100k.roi4.size.x.get(),        pil100k.roi4.size.y.get()]]
    md['roi'] = roi_data
    yield from bp.fly([flyer_pil], md=md)
