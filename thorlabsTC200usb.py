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

    def write(self, command):
        self.adapter.write(command + '\r')
        time.sleep(0.5) #Wait for instrument to return command
        self.read_single_line()

    def get_stat(self):
        """
        Reads zeroth bit of status byte
        """
        self.write('stat?')
        return (int(self.read_single_line()[:2])%2)

    def toggleenable(self):
        self.write('ens')

    def act_temp(self):
        self.write("tact?")
        temp = self.read_single_line()
        return float(temp[:-2]) #Extract float from string e.g. 20.0 from '20.0 C' 

    def set_mode(self, mode):
        self.write('mode=' + mode + '')

    def set_cycle_num(self, cycle_num):
        self.write('cycle=%d' % cycle_num)

    def set_stop_temp(self, stop_temp):
        self.write('stop=%.1f' % stop_temp)

    def set_ramp_time(self, ramp_time):
        self.write('ramp=%d' % ramp_time)

    def set_hold_time(self, hold_time):
        self.write('hold=%d' % hold_time)

    def set_temp(self, temp):
        self.write('tset=%.1f' % temp)

    def read_single_line(self):
        """ Reads line from instrument ending in \r
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
            SerialAdapter(port, baudrate=115200, timeout=0.1), "Thorlabs TC200 Temperature Controller", **kwargs
        )

        # super(ThorlabsTC200USB, self).__init__(
        #     VISAAdapter(port), 'Thorlabs TC200 Temperature Controller', timeout=1)