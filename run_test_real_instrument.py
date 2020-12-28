#!/usr/bin/env python3

#
# by TS, Dec 2020
#

import argparse
from serial.tools.list_ports import comports as pyser_get_comports
import sys

from test_manson_instrument import TestMansonInstrument, \
		TEST_TYPE_KEY_ALL, TEST_TYPE_KEY_SER, TEST_TYPE_KEY_SIMPLE, TEST_TYPES, \
		ALL_TEST_TYPE_KEYS

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def _get_parsed_args():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
			description="Run tests for real hardware",
			epilog="")
	parser.add_argument("--tt", help="Type of test to run (see --list-tt), default=" + TEST_TYPE_KEY_SIMPLE)
	parser.add_argument("--list-tt", action="store_true", help="List options for --tt")
	parser.add_argument("COMPORT", help="Serial port of real instrument (use 'list' to see available ports)")
	#
	args = parser.parse_args()
	args = vars(args)  # convert into dict
	#
	if args["tt"] and (args["tt"] == "h" or args["tt"] == "help"):
		args["list_tt"] = True
	if args["COMPORT"] and (args["COMPORT"] == "h" or args["COMPORT"] == "help"):
		print("! Invalid Serial port '%s'" % args["COMPORT"], file=sys.stderr)
		sys.exit(1)
	if args["COMPORT"] and (args["COMPORT"] == "l" or args["COMPORT"] == "list"):
		args["list_com"] = True
	else:
		args["list_com"] = False
	if args["list_tt"]:
		print("Test Types (for --tt):")
		for entryTt in ALL_TEST_TYPE_KEYS:
			if entryTt == TEST_TYPE_KEY_SER:
				continue
			print("  %3s: %s" % (entryTt, TEST_TYPES[entryTt]))
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
	if args["list_tt"] or args["list_com"]:
		sys.exit(0)
	#
	if args["tt"]:
		if args["tt"] == TEST_TYPE_KEY_ALL or \
				args["tt"] == TEST_TYPE_KEY_SER or args["tt"] not in ALL_TEST_TYPE_KEYS:
			print("! Invalid Test Type '%s'" % args["tt"], file=sys.stderr)
			sys.exit(1)
	else:
		args["tt"] = TEST_TYPE_KEY_SIMPLE
	if not args["COMPORT"]:
		print("! Missing serial port", file=sys.stderr)
		sys.exit(1)
	return args

if __name__ == "__main__":
	args = _get_parsed_args()
	#
	print("-" * 60)
	print("++ TEST '%s' ++++" % (args["tt"]))
	print("")
	tmiObj = TestMansonInstrument()
	isOk = tmiObj.runtest(args["tt"], args["COMPORT"])
	sys.exit(0 if isOk else 1)
