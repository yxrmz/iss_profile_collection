import numpy as np
import matplotlib.pyplot as plt
import math

class XASdata:
	def __init__(self, **kwargs):
		self.energy = np.array([])
		self.data = np.array([])
		self.encoder_file = ''
		self.i0_file = ''
		self.it_file = ''

	def loadADCtrace(self, filename = '', filepath = '/GPFS/xf08id/pizza_box_data/'):
		array_out=[]
		with open(filepath + str(filename)) as f:
			for line in f:
				current_line = line.split()
				current_line[3] = int(current_line[3],0) >> 8
				if current_line[3] > 0x1FFFF:
					current_line[3] -= 0x40000
				current_line[3] = float(current_line[3]) * 7.62939453125e-05
				array_out.append(
						[int(current_line[0])+1e-9*int(current_line[1]), current_line[3], int(current_line[2])])
		return np.array(array_out)

	def loadENCtrace(self, filename = '', filepath = '/GPFS/xf08id/pizza_box_data/'):
		array_out = []
		with open(filepath + str(filename)) as f:
			for line in f:  # read rest of lines
				current_line = line.split()
				array_out.append([int(current_line[0])+1e-9*int(current_line[1]), int(current_line[2]), int(current_line[3])])
		return np.array(array_out)

	def loadTRIGtrace(self, filename = '', filepath = '/GPFS/xf08id/pizza_box_data/'):
		array_out = []
		with open(filepath + str(filename)) as f:
			for line in f:  # read rest of lines
				current_line = line.split()
				if(int(current_line[4]) != 0):
					array_out.append([int(current_line[0])+1e-9*int(current_line[1]), int(current_line[3])])
		return np.array(array_out)

class XASdataAbs(XASdata):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#super(XASdata, self).__init__()
		self.i0 = np.array([])
		self.it = np.array([])

	def process(self, encoder_trace = '', i0trace = '', ittrace = ''):
		self.load(encoder_trace, i0trace, ittrace)
		self.interpolate()
		self.plot()

	def load(self, encoder_trace = '', i0trace = '', ittrace = ''):
		self.encoder_file = encoder_trace
		self.i0_file = i0trace
		self.it_file = ittrace
		self.encoder = self.loadENCtrace(encoder_trace)
		self.energy = self.encoder
		for i in range(len(self.encoder)):
			self.energy[i, 1] = -12400 / (2 * 3.1356 * math.sin(math.radians((self.encoder[i, 1]/360000)+0.134)))
		self.i0 = self.loadADCtrace(i0trace)
		self.it = self.loadADCtrace(ittrace)

	def interpolate(self):
		min_timestamp = np.array([self.i0[0,0], self.it[0,0], self.encoder[0,0]]).max()
		max_timestamp = np.array([self.i0[len(self.i0)-1,0], self.it[len(self.it)-1,0], self.encoder[len(self.encoder)-1,0]]).min()
		interval = self.i0[1,0] - self.i0[0,0]
		#interval = 0.001
		timestamps = np.arange(min_timestamp, max_timestamp, interval)
		self.i0_interp = np.array([timestamps, np.interp(timestamps, self.i0[:,0], self.i0[:,1])]).transpose()
		self.it_interp = np.array([timestamps, np.interp(timestamps, self.it[:,0], self.it[:,1])]).transpose()
		self.energy_interp = np.array([timestamps, np.interp(timestamps, self.energy[:,0], self.energy[:,1])]).transpose()

	def plot(self, color='r'):
		result_chambers = np.copy(self.i0_interp)
		result_chambers[:,1] = np.log(self.i0_interp[:,1] / self.it_interp[:,1])
		plt.plot(self.energy_interp[:,1], result_chambers[:,1], color)
		plt.xlabel('Energy (eV)')
		plt.ylabel('log(i0 / it)')
		plt.grid(True)

	def export_trace(self, filename, filepath = '/GPFS/xf08id/Sandbox/'):
		np.savetxt(filepath + filename + '-interp.txt', np.array([self.energy_interp[:,0], self.energy_interp[:,1], self.i0_interp[:,1], self.it_interp[:,1]]).transpose(), fmt='%17.6f %8.2f %f %f', delimiter=" ", header ='Timestamp (s)   En. (eV) 	i0 (V)	  it(V)')

class XASdataFlu(XASdata):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.i0 = np.array([])
		self.trigger = np.array([])
		self.iflu = np.array([])
		self.it = np.copy(self.iflu)
		self.trig_file = ''

	def process(self, encoder_trace = '', i0trace = '', iflutrace = '', trigtrace = ''):
		self.load(encoder_trace, i0trace, iflutrace, trigtrace)
		self.interpolate()
		self.plot()

	def load(self, encoder_trace = '', i0trace = '', iflutrace = '', trigtrace = ''):
		self.encoder_file = encoder_trace
		self.i0_file = i0trace
		self.it_file = iflutrace
		self.trig_file = trigtrace
		self.encoder = self.loadENCtrace(encoder_trace)
		self.energy = self.encoder
		for i in range(len(self.encoder)):
			self.energy[i, 1] = -12400 / (2 * 3.1356 * math.sin(math.radians((self.encoder[i, 1]/360000)+0.134)))
		self.i0 = self.loadADCtrace(i0trace)
		#self.trigger = self.loadTRIGtrace(trigtrace)
		self.iflu = self.loadADCtrace(iflutrace)
		self.it = np.copy(self.iflu)

	def interpolate(self):
		min_timestamp = np.array([self.i0[0,0], self.it[0,0], self.encoder[0,0]]).max()
		max_timestamp = np.array([self.i0[len(self.i0)-1,0], self.it[len(self.it)-1,0], self.encoder[len(self.encoder)-1,0]]).min()
		interval = self.i0[1,0] - self.i0[0,0]
		timestamps = np.arange(min_timestamp, max_timestamp, interval)

		#timestamps = self.trigger[:,0]
		self.i0_interp = np.array([timestamps, np.interp(timestamps, self.i0[:,0], self.i0[:,1])]).transpose()
		self.iflu_interp = np.array([timestamps, np.interp(timestamps, self.iflu[:,0], self.iflu[:,1])]).transpose()
		self.it_interp = np.copy(self.iflu_interp)
		self.energy_interp = np.array([timestamps, np.interp(timestamps, self.energy[:,0], self.energy[:,1])]).transpose()

	def plot(self, color='r'):
		result_chambers = self.i0_interp
		result_chambers[:,1] = (self.iflu_interp[:,1] / self.i0_interp[:,1])
		plt.plot(self.energy_interp[:,1], result_chambers[:,1], color)
		plt.xlabel('Energy (eV)')
		plt.ylabel('(iflu / i0)')
		plt.grid(True)

	def export_trace(self, filename, filepath = '/GPFS/xf08id/Sandbox/'):
		np.savetxt(filepath + filename + '-interp.txt', np.array([self.energy_interp[:,0], self.energy_interp[:,1], self.i0_interp[:,1], self.iflu_interp[:,1]]).transpose(), fmt='%17.6f %8.2f %f %f', delimiter=" ", header ='Timestamp (s)   En. (eV) 	i0 (V)	  if(V)')

	def export_trig_trace(self, filename, filepath = '/GPFS/xf08id/Sandbox/'):
		np.savetxt(filepath + filename + '-interp.txt', self.energy_interp[:,1], fmt='%f', delimiter=" ")
