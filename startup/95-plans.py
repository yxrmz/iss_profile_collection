import bluesky as bs
import bluesky.plans as bp
import time as ttime
import PyQt4.QtCore


def energy_scan(start, stop, num, flyers=[pb9.enc1, pba2.adc6, pba2.adc7], comment='', **metadata):
	"""
	Example
	-------
	>>> RE(energy_scan(11350, 11450, 2))
	"""
	def inner():
		md = {'plan_args': {}, 'plan_name': 'step scan', 'comment': comment}
		md.update(**metadata)
		yield from bp.open_run(md=md)

	# Start with a step scan.
	plan = bp.scan([hhm_en.energy], hhm_en.energy, start, stop, num, md={'comment': comment})
	# Wrap it in a fly scan with the Pizza Box.
	plan = bp.fly_during_wrapper(plan, flyers)
	# Working around a bug in fly_during_wrapper, stage and unstage the pizza box manually.

	for flyer in flyers:
		yield from bp.stage(flyer)
	yield from bp.stage(hhm)

	plan = bp.pchain(plan)

	yield from plan


def energy_multiple_scans(start, stop, repeats, comment='', **metadata):
	"""
	Example
	-------
	>>> RE(energy_scan(11350, 11450, 2))
	"""
	flyers = [pb9.enc1, pba2.adc6, pba2.adc7]
	def inner():
		md = {'plan_args': {}, 'plan_name': 'energy_multiple_scans', 'comment': comment}
		md.update(**metadata)
		yield from bp.open_run(md=md)

		for i in range(0, repeats):
			print('Run:', i+1)
			hhm_en.energy.move(start)
			ttime.sleep(2)
			while (hhm_en.energy.moving == True):
				ttime.sleep(.1)
			hhm_en.energy.move(stop)
			ttime.sleep(2)
			while (hhm_en.energy.moving == True):
				ttime.sleep(.1)

		yield from bp.close_run()


	for flyer in flyers:
		yield from bp.stage(flyer)
	yield from bp.stage(hhm)

	yield from bp.fly_during_wrapper(inner(), flyers)

	yield from bp.unstage(hhm)
	for flyer in flyers:
		yield from bp.unstage(flyer)



def tune(detectors, motor, start, stop, num, comment='', **metadata):
	"""
	Example
	-------
	>>> RE(tune([pba2.adc7],-2, 2, 5, ''), LivePlot('pba2_adc7_volt', 'hhm_pitch'))
	"""

	flyers = detectors 

	plan = bp.relative_scan(flyers, motor, start, stop, num, md={'plan_name': 'tune ' + motor.name, 'comment': comment})
	plan = bp.fly_during_wrapper(plan, flyers)

	plan = bp.pchain(plan)
	yield from plan


def prep_trajectory(delay = 1):
	hhm.prepare_trajectory.put("1")
	while (hhm.trajectory_ready.value == 0):
		ttime.sleep(.1)
	while (hhm.trajectory_ready.value == 1):
		ttime.sleep(.1)
	ttime.sleep(delay)


def execute_trajectory(comment='', **metadata):
	flyers = [pb9.enc1, pba1.adc1, pba2.adc6, pba2.adc7]
	def inner():
		md = {'plan_args': {}, 'plan_name': 'execute_trajectory','experiment': 'transmission', 'comment': comment}
		md.update(**metadata)
		yield from bp.open_run(md=md)

		# TODO Replace this with actual status object logic.
		
		shutter.open()
		hhm.enable_loop.put("0")
		hhm.start_trajectory.put("1")
		while(hhm.trajectory_running.value == 0):
			ttime.sleep(.1)
		finished = 0
		while (hhm.trajectory_running.value == 1 or finished == 0):
			finished = 0
			ttime.sleep(.05)
			if (hhm.trajectory_running.value == 0):
				ttime.sleep(.05)
				finished = 1

		shutter.close()

		yield from bp.close_run()


	for flyer in flyers:
		yield from bp.stage(flyer)
	yield from bp.stage(hhm)

	yield from bp.fly_during_wrapper(inner(), flyers)

	yield from bp.unstage(hhm)
	for flyer in flyers:
		yield from bp.unstage(flyer)


def execute_xia_trajectory(comment='', **metadata):
	flyers = [pb9.enc1, pba1.adc1, pba2.adc7, pb4.di]
	def inner():
		md = {'plan_args': {}, 'plan_name': 'execute_xia_trajectory','experiment': 'fluorescence_sdd', 'comment': comment}
		md.update(**metadata)
		yield from bp.open_run(md=md)

		# TODO Replace this with actual status object logic.
	   
		shutter.open()
		xia1.start_mapping_scan()
		hhm.enable_loop.put("0")
		hhm.start_trajectory.put("1")
		while(hhm.trajectory_running.value == 0):
			ttime.sleep(.1)
		finished = 0
		while (hhm.trajectory_running.value == 1 or finished == 0):
			finished = 0
			ttime.sleep(.1)
			if (hhm.trajectory_running.value == 0):
				ttime.sleep(.5)
				finished = 1

		xia1.stop_scan()
		shutter.close()

		yield from bp.close_run()


	for flyer in flyers:
		yield from bp.stage(flyer)
	yield from bp.stage(hhm)
	#yield from bp.stage(xia1)

	yield from bp.fly_during_wrapper(inner(), flyers)

	#yield from bp.unstage(xia1)
	yield from bp.unstage(hhm)
	for flyer in flyers:
		yield from bp.unstage(flyer)


def execute_loop_trajectory(comment='', **metadata):

	flyers = [pb9.enc1, pba2.adc6, pba2.adc7]
	def inner():
		md = {'plan_args': {}, 'plan_name': 'execute_trajectory', 'comment': comment}
		md.update(**metadata)
		yield from bp.open_run(md=md)

		# TODO Replace this with actual status object logic.
		shutter.open()
		hhm.enable_loop.put("1")
		ttime.sleep(2)
		while (hhm.theta.moving == True or hhm.enable_loop_rbv.value == 1):
			ttime.sleep(.1)

		shutter.close()

		yield from bp.close_run()


	for flyer in flyers:
		yield from bp.stage(flyer)
	yield from bp.stage(hhm)

	yield from bp.fly_during_wrapper(inner(), flyers)

	yield from bp.unstage(hhm)
	for flyer in flyers:
		yield from bp.unstage(flyer)



