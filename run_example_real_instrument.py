#!/usr/bin/env python3

#
# by TS, Dec 2020
#

import argparse
from serial.tools.list_ports import comports as pyser_get_comports
import sys

from manson_instrument import MansonInstrument

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def _get_parsed_args():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
			description="Run an example for real hardware",
			epilog="")
	parser.add_argument("COMPORT", help="Serial port of real instrument (use 'list' to see available ports)")
	#
	args = parser.parse_args()
	args = vars(args)  # convert into dict
	#
	if args["COMPORT"] and (args["COMPORT"] == "h" or args["COMPORT"] == "help"):
		print("! Invalid Serial port '%s'" % args["COMPORT"], file=sys.stderr)
		sys.exit(1)
	if args["COMPORT"] and (args["COMPORT"] == "l" or args["COMPORT"] == "list"):
		args["list_com"] = True
	else:
		args["list_com"] = False
	if args["list_com"]:
		print("Serial Ports:")
		cpArr = pyser_get_comports(include_links=False)
		if not cpArr:
			print("  --none found--")
		for entryCp in cpArr:
			if entryCp.manufacturer is None and entryCp.vid is None:
				continue
			print("  " + entryCp.device + ":")
			print("    desc         = %s" % entryCp.description)
			print("    serial_number= %s" % entryCp.serial_number)
			print("    manufacturer = %s" % entryCp.manufacturer)
			print("    product      = %s" % entryCp.product)
			print("    interface    = %s" % entryCp.interface)
			#print("    hwid         = %s" % entryCp.hwid)
			if entryCp.vid is not None and entryCp.pid is not None:
				vidHex = "0x" + ("%02x" % int(entryCp.vid)).upper()
				pidHex = "0x" + ("%02x" % int(entryCp.pid)).upper()
				print("    vid/pid      = %s / %s (%s / %s)" % \
						(entryCp.vid, entryCp.pid, vidHex, pidHex))
		sys.exit(0)
	#
	if not args["COMPORT"]:
		print("! Missing serial port", file=sys.stderr)
		sys.exit(1)
	return args

if __name__ == "__main__":
	args = _get_parsed_args()
	#
	miObj = MansonInstrument()
	#
	print("Open serial port '%s'..." % args["COMPORT"])
	miObj.open_port(args["COMPORT"])
	#
	print("Output voltage: ", end="")
	tmpV = miObj.get_output_voltage()
	print("%.3fV" % tmpV)
	#
	print("Output current: ", end="")
	tmpC = miObj.get_output_current()
	print("%.3fA" % tmpC)
	#
	print("Close serial port")
	miObj.close_port()
