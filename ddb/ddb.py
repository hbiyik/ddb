import binascii
import time
import struct
import sys
import argparse

import serial
from serial.tools import list_ports


s = serial.Serial(None, 
				baudrate=19200,
				bytesize=serial.EIGHTBITS,
				parity=serial.PARITY_EVEN,
				stopbits=serial.STOPBITS_ONE,
				rtscts=False,
				timeout=1,
				writeTimeout=2,
				xonxoff=True,
				dsrdtr=False,
				)

def portlist():
	return "Available Ports: " + " , ".join([port[0] for port in list_ports.comports()])
				

types = {
	"\x08": (10, 2, "h"), # integer
	"\x0b": (11, 2, "f"), # float but with some weird formatting
}
				
def endp(seq):
	return struct.pack("B",sum(bytearray(seq)) % 256) + b"\x16"


def readdb(ddb1, ddb2):
	prefix = b"\x68\x07\x07\x68"
	seq = b"\x7b\x01\x00\x07\x14"
	seq += binascii.unhexlify(ddb2 + ddb1)
	seq += endp(seq)
	return query(prefix + seq)

	
def init():
	prefix = b"\x68\x03\x03\x68"
	seq = b"\x40\x01\x00"
	seq += endp(seq)
	return query(prefix + seq)	
	
	
def write(d):
	print "---> write: %s" % binascii.hexlify(d)
	ret = s.write(d)
	return ret


def read():
	data = ""
	while True:
		ret = s.read(size=1)
		if ret == "":
			break
		data += ret
	print "<---- read: %s" % binascii.hexlify(data)
	typ = data[2]
	tmap = types.get(typ)
	if tmap:
		offset, end, fmt = tmap
		chunk = data[offset:-end]
		ret = struct.unpack(fmt, chunk)[0]
	else:
		ret = chunk = data[11:-3]
	print "<---- response: %s" % binascii.hexlify(chunk)
	return ret
	

def query(h):
	try:
		write(h)
		return read()
	except serial.SerialTimeoutException, e:
		print e.message


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("port", type=str, help="comport to use")
	parser.add_argument("ddb1", type=str, help="first ddb address")
	parser.add_argument("ddb2", type=str, help="second ddb address")
	parser.add_argument("data", type=str, help="ddb data, skip this if you want to read, set this if you want to write", nargs="*")
	parser.add_argument("-p", "--ports", help="list comports", default=False, action="version", version=portlist())
	args = parser.parse_args()
	try:
		s.port = args.port
		s.open()
	except serial.SerialException:
		print "Can not open port %s" % args.port
		sys.exit()
	init()
	if not len(args.data):
		try:
			print readdb(args.ddb1, args.ddb2)
		except TypeError:
			print "Wrong ddb numbers %s:%s" % (args.ddb1, args.ddb2)
