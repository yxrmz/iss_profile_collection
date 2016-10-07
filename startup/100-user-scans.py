def tscan(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_trajectory(comment))
	uid, interp_filename = write_html_log(-1, comment, absorp=absorp)
	print('Done!')
	return uid, interp_filename


def tscan_N(comment, prepare_traj=True, absorp=True, n_cycles=1, delay=0):
	for indx in range(0, n_cycles): 
		comment_n = comment + ' ' + str(indx + 1)
		print(comment_n) 
		if (prepare_traj == True):
			prep_trajectory()
		RE(execute_trajectory(comment_n))
		uid, interp_filename = write_html_log(-1, comment_n, absorp=absorp)
		time.sleep(delay)
	print('Done!')
	return uid, interp_filename


def tscan_Rrep(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()

	RE(execute_trajectory(comment))
	uid, interp_filename = write_html_log(-1, comment, absorp=absorp)
	print('Done!')
	return uid, interp_filename


def tloopscan(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_loop_trajectory(comment))
	uid, interp_filename = write_html_log(-1, comment, absorp=absorp)
	print('Done!')
	return uid, interp_filename


def tscanxia(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_xia_trajectory(comment))
	print('Done!')
	#write_html_log(-1, comment, absorp=absorp)
