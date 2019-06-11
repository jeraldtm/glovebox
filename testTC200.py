# import serial
# from pymeasure.instruments.instrument import Instrument
# from pymeasure.adapters.serial import SerialAdapter
# import time

# ser = serial.Serial('/dev/ttyUSB0', baudrate=115200)
# serAdap = SerialAdapter(ser)

# #serAdap.write('ens\r')
# serAdap.write('tact?\r')
# print(serAdap.read_custom_eol('\r'))
# print(serAdap.read_custom_eol('\r'))

from pymeasure.instruments.thorlabs import ThorlabsTC200USB
a = ThorlabsTC200USB('/dev/ttyUSB0')
a.adapter.connection.timeout = 0.1
a.adapter.write("tact?\r")
print(a.get_temp())
print(a.act_temp())

# a = ThorlabsTC200USB('ASRL/dev/ttyUSB0::INSTR')
# a.adapter.connection.baudrate = 115200
# a.adapter.connection.data_bits = 8
# a.adapter.connection.timeout = 1
# a.adapter.connection.write("ens", "\r")

()