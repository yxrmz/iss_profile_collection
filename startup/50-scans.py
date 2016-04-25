from bluesky import DeltaScanPlan, Count
from bluesky.callbacks import LiveTable, LivePlot

cm1.pitch.settle_time = 1  # time per point
# See http://nsls-ii.github.io/bluesky/plans.html#bluesky.plans.DeltaScanPlan
scanning_plan = DeltaScanPlan([tc_mask2_4], cm1.pitch, -0.5, 0.5, 10)
scanning_plan.subs = [LiveTable(['tc_mask2_4', 'cm1_pitch']), LivePlot('tc_mask2_4', 'cm1_pitch', marker='x')]

# To execute, interactively: RE(plan)

# http://nsls-ii.github.io/bluesky/plans.html#count
average_plan = Count([tc_mask2_4], num=5, delay=1)  # num=None runs forever until Ctrl C
average_plan.subs = [LiveTable(['tc_mask2_4'])]

def ct_ave(signal, num, delay):
    plan=Count(signal, num, delay)
    plan.subs=[LiveTable(x.name for x in signal)]
    RE(plan)
    last_run = db[-1]
    table = get_table(last_run)	

    for x in range(len(signal)):	
        print("Mean (" + signal[x].name +  ") =", table[signal[x].name].mean())

#def ct_ave(signal, num, delay):
#    plan=Count([signal], num, delay)
#    plan.subs=[LiveTable([signal.name])]
#    RE(plan)
#    last_run = db[-1]
#    table = get_table(last_run)

#    print("Mean (" + signal.name +  ") =", table[signal.name].mean())

