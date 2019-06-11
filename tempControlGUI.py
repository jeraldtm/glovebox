import logging
import os
from time import sleep, time, strftime
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import numpy as np
from pymeasure.experiment import FloatParameter, IntegerParameter, Parameter
from pymeasure.log import console_log
from pymeasure.experiment import Procedure
from pymeasure.instruments.thorlabs import ThorlabsTC200USB

from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Results, unique_filename
import sys
from pymeasure.log import console_log
from pymeasure.display.Qt import QtCore, QtGui, fromUi

class tempControlProcedure(Procedure):
    """
    Procedure for calibrating the voltage to field strength relationship
    on Daedalus. Assumes that the center calibration has already ran.
    """

    # control parameters
    calib_name = Parameter("Calibration Name", default='')
    temp_start = FloatParameter("Temperature start", units="C", default=-30.)
    temp_stop = FloatParameter("Temperature stop", units="C", default=100.)
    temp_step = FloatParameter("Temperature step", units="C", default=0.1)
    #heating_time = FloatParameter("Heating time", units="s", default=60.)
    #queued_time = Parameter("Queued Time")

    DATA_COLUMNS = ["set_temp","act_temp","elapsed_time"]

    def startup(self):
        log.info("Connecting and configuring the instruments")
        self.heatcontrol = ThorlabsTC200USB('/dev/ttyUSB0')
        self.heatcontrol.toggleenable()
        
    def execute(self):
        start_time = time()
        temp_points = np.arange(self.temp_start, self.temp_stop, self.temp_step)
        if self.temp_stop not in temp_points:
            temp_points = np.append(temp_points, self.temp_stop)

        temp_points = np.concatenate((temp_points, temp_points[::-1]))
        num_progress = temp_points.size

        for progress_iterator, t in enumerate(temp_points):
            log.info("Setting temperature %f C"%t)
            self.heatcontrol.set_temp = t
            sleep(1)
            self.emit('progress', int(100*progress_iterator/num_progress))
            self.emit('results',
                      {
                          "set_temp": self.heatcontrol.get_temp(),
                          "act_temp": self.heatcontrol.act_temp(),
                          "elapsed_time": time()-start_time
                      })
            if self.should_stop():
                log.warning("Caught stop flag in procedure.")
                break

    def shutdown(self):
        log.info("Done with scan. Shutting down instruments")
        self.heatcontrol.toggleenable()

class tempControlGUI(ManagedWindow):
    def __init__(self):
        super().__init__(
            procedure_class=tempControlProcedure,
            displays=[
                ],
            x_axis='elapsed_time',
            y_axis='set_temp',
        )
        self.setWindowTitle('Temperature Control GUI')

    def _layout(self):
        self.main = QtGui.QWidget(self)

        inputs_dock = QtGui.QWidget(self)
        inputs_vbox = QtGui.QVBoxLayout(self.main)

        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.setContentsMargins(-1, 6, -1, 6)
        hbox.addWidget(self.queue_button)
        hbox.addWidget(self.abort_button)
        hbox.addWidget(self.stop_button)
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

    def _setup_ui(self):
        """
        Loads custom QT UI for center calibration
        """
        super()._setup_ui()
        self.stop_button = QtGui.QPushButton('Stop', self)
        self.queue_button.clicked.connect(self.stop)

        self.inputs.hide()
        self.run_directory = os.path.dirname(os.path.realpath(__file__))
        self.inputs = fromUi(os.path.join(self.run_directory,
                                          'temp_control_gui.ui'))

    def stop(self):
        self.abort()
        self.resume()

    def make_procedure(self):
        procedure = tempControlProcedure()
        procedure.temp_start = self.inputs.temp_start.value()
        procedure.temp_stop = self.inputs.temp_stop.value()
        procedure.temp_step = self.inputs.temp_step.value()
        # procedure.heating_time = self.inputs.heating_time.value()
        return procedure

    def queue(self):
        fname = unique_filename(
            self.inputs.save_dir.text(),
            dated_folder=True,
            prefix=self.inputs.calib_name.text() + '_temperature_record_',
            suffix=''
        )
        procedure = self.make_procedure()
        results = Results(procedure, fname)
        experiment = self.new_experiment(results)
        self.manager.queue(experiment)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = tempControlGUI()
    window.show()
    sys.exit(app.exec_())
