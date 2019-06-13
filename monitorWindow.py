import logging

import os
import pyqtgraph as pg

from .browser import BrowserItem
from .curves import ResultsCurve # JM: only need to import another if we want a PlotterWindow equivalent
from .manager import Manager, Experiment, ImageExperiment, ImageManager
from .Qt import QtCore, QtGui
from .widgets import PlotWidget, BrowserWidget, InputsWidget, LogWidget, ResultsDialog, ImageWidget
from ..experiment.results import Results

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


lass MonitorWindow(QtGui.QMainWindow):
	    """
    Abstract base class.

    The ManagedWindow provides an interface for inputting experiment
    parameters, running several experiments
    (:class:`~pymeasure.experiment.procedure.Procedure`), plotting
    result curves, and listing the experiments conducted during a session.

    The ManagedWindow uses a Manager to control Workers in a Queue,
    and provides a simple interface. The :meth:`~.queue` method must be
    overridden by the child class.

    .. seealso::

        Tutorial :ref:`tutorial-managedwindow`
            A tutorial and example on the basic configuration and usage of ManagedWindow.

    .. attribute:: plot

        The `pyqtgraph.PlotItem`_ object for this window. Can be
        accessed to further customise the plot view programmatically, e.g.,
        display log-log or semi-log axes by default, change axis range, etc.

    .. _pyqtgraph.PlotItem: http://www.pyqtgraph.org/documentation/graphicsItems/plotitem.html


    """

    EDITOR = 'gedit'

    def __init__(self, procedure_class, inputs=(), displays=(), x_axis=None, y_axis=None,
                 log_channel='', log_level=logging.INFO, parent=None):
        super().__init__(parent)
        app = QtCore.QCoreApplication.instance()
        app.aboutToQuit.connect(self.quit)
        self.procedure_class = procedure_class
        self.inputs = inputs
        self.displays = displays
        self.log = logging.getLogger(log_channel)
        self.log_level = log_level
        log.setLevel(log_level)
        self.log.setLevel(log_level)
        self.x_axis, self.y_axis = x_axis, y_axis
        self._setup_ui()
        self._layout()
        self.setup_plot(self.plot)

    def _setup_ui(self):
        self.log_widget = LogWidget()
        self.log.addHandler(self.log_widget.handler)  # needs to be in Qt context?
        log.info("ManagedWindow connected to logging")

        self.queue_button = QtGui.QPushButton('Queue', self)
        self.queue_button.clicked.connect(self.queue)

        self.abort_button = QtGui.QPushButton('Abort', self)
        self.abort_button.setEnabled(False)
        self.abort_button.clicked.connect(self.abort)

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






