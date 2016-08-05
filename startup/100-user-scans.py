def tscan(comment='', prepare_traj=True):
	RE(execute_trajectory(comment, prepare_traj))
	write_html_log(-1, comment)
