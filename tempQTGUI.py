import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import sys
from pymeasure.log import console_log
from pymeasure.experiment import Results, unique_filename
from pymeasure.display.Qt import QtCore, QtGui, fromUi
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Procedure
from pymeasure.experiment import IntegerParameter, FloatParameter, BooleanParameter, Parameter
from pymeasure.adapters import DAQmxAdapter
from pymeasure.instruments.thorlabs import ThorlabsTC200USB
from time import sleep, time
import numpy as np
import os
import pyqtgraph as pg

from pymeasure.display.browser import BrowserItem
from pymeasure.display.curves import ResultsCurve # JM: only need to import another if we want a PlotterWindow equivalent
from pymeasure.display.manager import Manager, Experiment, ImageExperiment, ImageManager
from pymeasure.display.Qt import QtCore, QtGui
from pymeasure.display.widgets import PlotWidget, BrowserWidget, InputsWidget, LogWidget, ResultsDialog, ImageWidget
from pymeasure.experiment.results import Results
import serial

class tempProcedure(Procedure):
	sample_name = Parameter("Sample Name", default='undefined')
	save_dir = Parameter("Save Directory", default=r"\junk")
	stop_temp = FloatParameter("Target Temperature", units="C", default=20) 
	ramp_time = IntegerParameter("Ramp Time", units="min", default=1)
	hold_time = IntegerParameter("Hold Time", units="min", default=1)
	DATA_COLUMNS = ["global_time", "temperature", "heating_time"]

	def startup(self):
		log.info("Temp, Ramp, Hold: %.1f, %d, %d" % (self.stop_temp, self.ramp_time, self.hold_time))
		log.info("Connecting temperature controller")
		self.tempcontrol = ThorlabsTC200USB('COM3')
		if self.tempcontrol.get_stat():
			self.tempcontrol.toggleenable()
		self.tempcontrol.set_mode('cycle')
		self.tempcontrol.set_cycle_num(1)
		self.tempcontrol.set_stop_temp(self.stop_temp)
		self.tempcontrol.set_ramp_time(self.ramp_time)
		self.tempcontrol.set_hold_time(self.hold_time)
		self.tempcontrol.toggleenable()
		self.duration = (self.ramp_time + self.hold_time)*60.

	def execute(self):
		num_progress = np.floor(self.duration / 0.05)
		start_time = time()
		end_time = start_time + self.duration
		progress_iterator = 0

		while time() < end_time:
			self.emit("progress", int(100*progress_iterator/num_progress))
			progress_iterator += 1
			log.info("Recording results")
			self.emit('results', {
			"global_time": time(),
			"heating_time": time()-start_time,
			"temperature": self.tempcontrol.act_temp()                
			})
			if self.should_stop():
				log.warning("Caught stop flag in procedure.")
				break
			sleep(0.05)

	def shutdown(self):
		log.info("Finished with scan. Shutting down instruments.")
		if self.tempcontrol.get_stat():
			self.tempcontrol.toggleenable()
		self.tempcontrol.adapter.connection.close() #close serial port to avoid port already open error

class tempQTQUI(ManagedWindow):
	def __init__(self):
		super().__init__(
		procedure_class=tempProcedure,
		inputs=[
		'sample_name',
		'save_dir',
		'stop_temp',
		'ramp_time',
		'hold_time'
		],
		displays=['sample_name', 'stop_temp', 'ramp_time', 'hold_time'],
		x_axis='heating_time',
		y_axis='temperature'
		)
		self.setWindowTitle("Temperature Cycle")

	def queue(self):
		procedure = self.make_procedure()
		filename = unique_filename(procedure.save_dir, procedure.sample_name, '_temp_monitor_')
		results = Results(procedure, filename)
		experiment = self.new_experiment(results)
		self.manager.queue(experiment)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = tempQTQUI()
	window.show()
	sys.exit(app.exec_())

# 