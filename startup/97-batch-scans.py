from xas.trajectory import trajectory, trajectory_manager
from bluesky.plan_stubs import mv


def batch_parse_and_run(hhm,sample_stage,batch,plans_dict ):
    tm = trajectory_manager(hhm)
    for ii in range(batch.rowCount()):
        experiment = batch.item(ii)
        print(experiment.item_type)
        repeat=experiment.repeat
        print(repeat)
        for jj in range(experiment.rowCount()):
            child = experiment.child(jj)
            print(child.item_type)
            if child.item_type == 'sample':
                print('  ' + sample.name)
                print('  ' + str(sample.x))
                print('  ' + str(sample.y))
                yield from mv(sample_stage.x, sample.x, sample_stage.y, sample.y)
                for kk in range(sample.rowCount()):
                    scan = sample.child(kk)
                    traj_index= scan.trajectory
                    print('      ' + scan.scan_type)
                    plan = plans_dict[scan.scan_type]
                    kwargs = {'name': sample.name,
                              'comment': '',
                              'delay': 0,
                              'n_cycles': repeat}
                    tm.init(traj_index+1)
                    yield from plan(**kwargs)
            elif child.item_type == 'service':
                    print(child.service_plan)

# summarize_plan(parse_and_execute())