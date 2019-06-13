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
from time import sleep
import numpy as np
import os
import pyqtgraph as pg

from pymeasure.display.browser import BrowserItem
from pymeasure.display.curves import ResultsCurve # JM: only need to import another if we want a PlotterWindow equivalent
from pymeasure.display.manager import Manager, Experiment, ImageExperiment, ImageManager
from pymeasure.display.Qt import QtCore, QtGui
from pymeasure.display.widgets import PlotWidget, BrowserWidget, InputsWidget, LogWidget, ResultsDialog, ImageWidget
from pymeasure.experiment.results import Results

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
		self.tempcontrol = ThorlabsTC200USB('/dev/ttyUSB0')
		if tempcontrol.get_stat():
			self.tempcontrol.toggleenable()
		self.tempcontrol.set_mode('cycle')
		self.tempcontrol.set_cycle_num(1)
		self.tempcontrol.set_stop_temp(self.stop_temp)
		self.tempcontrol.set_ramp_time(self.ramp_time)
		self.tempcontrol.set_hold_time(self.hold_time)
		self.tempcontrol.toggleenable()
		self.duration = self.ramp_time + self.hold_time

	def execute(self):
		num_progress = np.floor(self.duration / 0.01)
		start_time = time.time()
		end_time = start_time + self.duration
		progress_iterator = 0

		while time.time() < end_time:
			self._update_parameters()
			self.emit("progress", int(100*progress_iterator/num_progress))
			progress_iterator += 1
			log.info("Recording results")
			self.emit('results', {
			"global_time": time.time(),
			"heating_time": time.time()-start_time,
			"temperature": self.tempcontrol.act_temp()                
			})
			if self.should_stop():
				log.warning("Caught stop flag in procedure.")
			break
			sleep(0.01)

	def shutdown(self):
		log.info("Finished with scan. Shutting down instruments.")
		if tempcontrol.get_stat():
			self.tempcontrol.toggleenable()

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

	def _setup_ui(self):
		self.log_widget = LogWidget()
		self.log.addHandler(self.log_widget.handler)  # needs to be in Qt context?
		log.info("ManagedWindow connected to logging")

		self.queue_button = QtGui.QPushButton('Queue', self)
		self.queue_button.clicked.connect(self.queue)

		self.abort_button = QtGui.QPushButton('Abort', self)
		self.abort_button.setEnabled(False)
		self.abort_button.clicked.connect(self.abort)

		#self.queue_button = QtGui.QPushButton('Set', self)
		#self.queue_button.clicked.connect(self.procedure.refresh_parameters())

		self.plot_widget = PlotWidget(self.procedure_class.DATA_COLUMNS, self.x_axis, self.y_axis)
		self.plot = self.plot_widget.plot

		self.browser_widget = BrowserWidget(
		self.procedure_class,
		self.displays,
		[self.x_axis, self.y_axis],
		parent=self
		)
		self.browser_widget.show_button.clicked.connect(self.show_experiments)
		self.browser_widget.hide_button.clicked.connect(self.hide_experiments)
		self.browser_widget.clear_button.clicked.connect(self.clear_experiments)
		self.browser_widget.open_button.clicked.connect(self.open_experiment)
		self.browser = self.browser_widget.browser

		self.browser.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.browser.customContextMenuRequested.connect(self.browser_item_menu)
		self.browser.itemChanged.connect(self.browser_item_changed)

		self.inputs = InputsWidget(
		self.procedure_class,
		self.inputs,
		parent=self
		)

		self.manager = Manager(self.plot, self.browser, log_level=self.log_level, parent=self)
		self.manager.abort_returned.connect(self.abort_returned)
		self.manager.queued.connect(self.queued)
		self.manager.running.connect(self.running)
		self.manager.finished.connect(self.finished)
		self.manager.log.connect(self.log.handle)

	def _layout(self):
		self.main = QtGui.QWidget(self)

		inputs_dock = QtGui.QWidget(self)
		inputs_vbox = QtGui.QVBoxLayout(self.main)

		hbox = QtGui.QHBoxLayout()
		hbox.setSpacing(10)
		hbox.setContentsMargins(-1, 6, -1, 6)
		hbox.addWidget(self.queue_button)
		hbox.addWidget(self.abort_button)
		hbox.addStretch()

		inputs_vbox.addWidget(self.inputs)
		inputs_vbox.addLayout(hbox)
		inputs_vbox.addStretch()
		inputs_dock.setLayout(inputs_vbox)

		dock = QtGui.QDockWidget('Input Parameters')
		dock.setWidget(inputs_dock)
		dock.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

		tabs = QtGui.QTabWidget(self.main)
		tabs.addTab(self.plot_widget, "Results Graph")
		tabs.addTab(self.log_widget, "Experiment Log")

		splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
		splitter.addWidget(tabs)
		splitter.addWidget(self.browser_widget)
		self.plot_widget.setMinimumSize(100, 200)

		vbox = QtGui.QVBoxLayout(self.main)
		vbox.setSpacing(0)
		vbox.addWidget(splitter)

		self.main.setLayout(vbox)
		self.setCentralWidget(self.main)
		self.main.show()
		self.resize(1000, 800)

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