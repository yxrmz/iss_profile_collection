def tscan(comment, prepare_traj=True, log_sel=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_trajectory(comment))
	write_html_log(-1, comment, log=log_sel)

def tscan_N(comment, prepare_traj=True, log_sel=True,n_cycles=1):
	for indx in range(0, n_cycles): 
		comment_n = comment + ' ' + str(indx + 1)
		print(comment_n) 
		if (prepare_traj == True):
			prep_trajectory()
		RE(execute_trajectory(comment_n))
		write_html_log(-1, comment_n, log=log_sel)



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

def tscanxia(comment, prepare_traj=True, log_sel=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_xia_trajectory(comment))
	#write_html_log(-1, comment, log=log_sel)
