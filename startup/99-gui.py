import isstools.gui

xlive_gui = isstools.gui.ScanGui([tscan, tscan_N, tscanxia, get_offsets], [tune_mono_pitch , tune_mono_y], prep_traj_plan, RE, db, hhm, {'xia':xia1, 'pba1':pba1, 'pba2':pba2})

def xlive():
    xlive_gui.show()
