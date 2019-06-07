#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2017 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import time
import serial
from pymeasure.instruments import Instruments

class TC200(Instrument):
    enabled = Instrument.control(
        "stat?", "ens"
        """ Returns status of instrument"""
        )

    set_temp = Instrument.control(
        "tset?", "tget%.1f",
        """A floating point property that controls the set temperature """
        )

    temp = Instrument.measurement(
        "tact?"
        """ Returns actual temperature"""
        )

    def __init__(self, port, rw_delay=None, **kwargs):
        super(TC200, self).__init__(
            serial.Serial(port, 115200), "Thorlabs TC200 Temperature Controller", **kwargs
        )
        self.rw_delay = rw_delay

    def values(self, command):
        self.write(command)
        if self.rw_delay is not None:
            time.sleep(self.rw_delay)
        return self.read()