def tscan(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_trajectory(comment))
	write_html_log(-1, comment, absorp=absorp)
	print('Done!')

def tscan_N(comment, prepare_traj=True, absorp=True, n_cycles=1, delay=0):
	for indx in range(0, n_cycles): 
		comment_n = comment + ' ' + str(indx + 1)
		print(comment_n) 
		if (prepare_traj == True):
			prep_trajectory()
		RE(execute_trajectory(comment_n))
		write_html_log(-1, comment_n, absorp=absorp)
		time.sleep(delay)
	print('Done!')



def tscan_Rrep(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()

	RE(execute_trajectory(comment))
	write_html_log(-1, comment, absorp=absorp)
	print('Done!')


def tloopscan(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_loop_trajectory(comment))
	write_html_log(-1, comment, absorp=absorp)
	print('Done!')

def tscanxia(comment, prepare_traj=True, absorp=True):
	if (prepare_traj == True):
		prep_trajectory()
	RE(execute_xia_trajectory(comment))
	print('Done!')
	#write_html_log(-1, comment, absorp=absorp)
