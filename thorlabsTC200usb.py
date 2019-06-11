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
from pymeasure.instruments import Instrument
from pymeasure.adapters import SerialAdapter, VISAAdapter

class ThorlabsTC200USB(Instrument):

    def toggleenable(self):
        self.adapter.write('ens\r')

    def set_temp(self, temp):
        self.adapter.write("tset=%.1f\r" % temp)   
    
    def get_temp(self):
        temp = self.read_temp("tset?\r")
        return temp

    def act_temp(self):
        temp = self.read_temp("tact?\r")
        return temp

    def read_temp(self, command):
        """
        Parse multiple output lines for temperature.
        """
        self.adapter.write(command)
        output_list = []
        while True:
            output_line = self.read_single_line()
            if output_line == '':
                break
            output_list.append(output_line  )
        return float(output_list[-2][:5])

    def read_single_line(self):
        """ Reads line
        :returns: String ASCII response of instrument
        """
        eol = '\r'
        eolbyte = eol.encode()
        leneol = len(eol)
        line = bytearray()
        while True:
            c = self.adapter.connection.read(1)
            if c:
                line += c
                if line[-leneol:] == eolbyte:
                    break
            else:
                break
        return bytes(line).decode()

    def __init__(self, port, rw_delay=None, **kwargs):
        super(ThorlabsTC200USB, self).__init__(
            SerialAdapter(serial.Serial(port, baudrate=115200, timeout=0.11)), "Thorlabs TC200 Temperature Controller", **kwargs
        )

        # super(ThorlabsTC200USB, self).__init__(
        #     VISAAdapter(port), 'Thorlabs TC200 Temperature Controller', timeout=1)