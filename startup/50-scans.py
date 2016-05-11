from bluesky import DeltaScanPlan, Count
from bluesky.callbacks import LiveTable, LivePlot

cm1.pitch.settle_time = 1  # time per point
# See http://nsls-ii.github.io/bluesky/plans.html#bluesky.plans.DeltaScanPlan
#scanning_plan = DeltaScanPlan([tc_mask2_4], cm1.pitch, -0.5, 0.5, 10)
#scanning_plan.subs = [LiveTable(['tc_mask2_4', 'cm1_pitch']), LivePlot('tc_mask2_4', 'cm1_pitch', marker='x')]

# To execute, interactively: RE(plan)

# http://nsls-ii.github.io/bluesky/plans.html#count
#average_plan = Count([tc_mask2_4], num=5, delay=1)  # num=None runs forever until Ctrl C
#average_plan.subs = [LiveTable(['tc_mask2_4'])]

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

def pb_scan(signal, motor, init_pos, final_pos, count):
    import filestore
    filestore.api.register_handler('PIZZABOX_FILE', PizzaBoxHandler, overwrite=True)
    scanning_plan = DeltaScanPlan([], motor, init_pos, final_pos, count)
    scanning_plan.flyers = signal
#    scanning_plan.subs=[LiveTable(x.name for x in signal)]
    RE(scanning_plan)
    if (motor.name[len(motor.name) - 5 : len(motor.name)] == 'pitch') and (len(signal) == 3):
        plot_pitch(signal[0].filepath.value[len(signal[0].filepath.value) - 8 : len(signal[0].filepath.value)], signal[1].filepath.value[len(signal[1].filepath.value) - 8 : len(signal[1].filepath.value)], signal[2].filepath.value[len(signal[2].filepath.value) - 8 : len(signal[2].filepath.value)])
    elif (motor.name[len(motor.name) - 4 : len(motor.name)] == 'roll') and (len(signal) == 2):
        plot_roll(signal[0].filepath.value[len(signal[0].filepath.value) - 8 : len(signal[0].filepath.value)], signal[1].filepath.value[len(signal[1].filepath.value) - 8 : len(signal[1].filepath.value)])
    elif (motor.name[len(motor.name) - 1 : len(motor.name)] == 'y') and (len(signal) == 3):
        plot_y(signal[0].filepath.value[len(signal[0].filepath.value) - 8 : len(signal[0].filepath.value)], signal[1].filepath.value[len(signal[1].filepath.value) - 8 : len(signal[1].filepath.value)], signal[2].filepath.value[len(signal[2].filepath.value) - 8 : len(signal[2].filepath.value)])

#    last_run = db[-1]
#    table = get_table(last_run)
#    for x in pizza_box_list:
#        getattr(eval(x), "ignoreAll")()
#    while(getattr(eval(current_pizza_box), "ignore" + last_encoder + "_rb.value") == 0):
#        pass
#    for x in pizza_box_list:
#        getattr(eval(x), "enabled")()


# DEMO WITH DAN:
def pizza_test():
    import filestore
    filestore.api.register_handler('PIZZABOX_FILE', PizzaBoxHandler, overwrite=True)
    from bluesky.plans import Count
    c = Count([], delay=5)  # give it some time for readings to accumulate
    c.flyers = [pb6.enc1]

    RE(c)
    get_table(db[-1])

#_____
# getting data from table:

# import datetime
# for x in range(11, 338689, 1000):
#     print('Encoder Pos =', str(table.loc[x, 'pb2_enc1'][2]), "(" + datetime.datetime.fromtimestamp(table.loc[x, 'pb2_enc1'][0]).strftime('%Y-%m-%d %H:%M:%S') + ":" + format(table.loc[x, 'pb2_enc1'][1], '09d') + ")")
