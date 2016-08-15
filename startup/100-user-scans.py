def tscan(comment, prepare_traj=True, log_sel=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_trajectory(comment))
	write_html_log(-1, comment, log=log_sel)

def tscan_Rrep(comment, prepare_traj=True, log_sel=True):
	if (prepare_traj == True):
		prep_trajectory()

	RE(execute_trajectory(comment))
	write_html_log(-1, comment, log=log_sel)


def tloopscan(comment, prepare_traj=True, log_sel=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_loop_trajectory(comment))
	write_html_log(-1, comment, log=log_sel)

def tscanXia(comment, prepare_traj=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_trajectory(comment))
	write_html_log(-1, comment, log=log_sel)
