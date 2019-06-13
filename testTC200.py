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
a.set_temp(20.0)

# if a.get_stat:
# 	a.toggleenable()
# a.set_mode('cycle')
# a.set_cycle_num(1)
# a.set_stop_temp(50)
# a.set_ramp_time(5)
# a.set_hold_time(5)
# a.toggleenable()

# a.adapter.connection.timeout = 1
# a.adapter.write('mode=cycle\r')
# a.adapter.write('cycle=1\r')
# a.adapter.write('stop=40.0\r')
# a.adapter.write('ramp=1\r')
# a.adapter.write('hold=1\r')
# a.adapter.write('cycles?\r')
# a.adapter.write('ens\r')
# a.adapter.write('stat?\r')
# a.read_single_line()
# output = a.adapter.connection.read(2)
# print(int(output)%2)
# print(output)
# binary = bin(int(output, 16))[2:].zfill(8)
# print(binary)

# a.adapter.connection.timeout = 0.1
# a.adapter.write("tact?\r")
# print(a.get_temp())
# print(a.act_temp())

# a = ThorlabsTC200USB('ASRL/dev/ttyUSB0::INSTR')
# a.adapter.connection.baudrate = 115200
# a.adapter.connection.data_bits = 8
# a.adapter.connection.timeout = 1
# a.adapter.connection.write("ens", "\r")

# if a.get_stat():
# 	print('enabled')
# else:
# 	print('disabled')

