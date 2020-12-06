#!/usr/bin/env python3

#
# by TS, Dec 2020
#

import argparse
from os import linesep
import sys

from exceptions import InvalidModelError
from exceptions import UnsupportedModelError
from models import get_hw_model_id
from models import TEST_MODEL_LIST
from models import MODEL_LIST_SERIES_ALL
from test_manson_instrument import TestMansonInstrument
from test_manson_instrument import TEST_TYPE_KEY_ALL
from test_manson_instrument import TEST_TYPES
from test_manson_instrument import ALL_TEST_TYPE_KEYS

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def _get_parsed_args():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
			description="Run tests for emulated hardware",
			epilog="Default hardware models to test:{0:s}  {1}".format(linesep, TEST_MODEL_LIST))
	parser.add_argument("--tt", help="Type of test to run (see --list-tt), default=" + TEST_TYPE_KEY_ALL)
	parser.add_argument("--list-tt", action="store_true", help="List options for --tt")
	parser.add_argument("--mod", help="HW Model to emulate (e.g. '%s') (see --list-mod)" % TEST_MODEL_LIST[0])
	parser.add_argument("--list-mod", action="store_true", help="List available HW Models")
	#
	args = parser.parse_args()
	args = vars(args)  # convert into dict
	#
	if args["tt"] and (args["tt"] == "h" or args["tt"] == "help" or \
			args["tt"] == "l" or args["tt"] == "list"):
		args["list_tt"] = True
	if args["mod"] and (args["mod"] == "h" or args["mod"] == "help" or \
			args["mod"] == "l" or args["mod"] == "list"):
		args["list_mod"] = True
	if args["list_tt"]:
		print("Test Types (for --tt):")
		print("  " + TEST_TYPE_KEY_ALL + ": " + TEST_TYPES[TEST_TYPE_KEY_ALL])
		for entryTt in ALL_TEST_TYPE_KEYS:
			print("  %3s: %s" % (entryTt, TEST_TYPES[entryTt]))
	if args["list_mod"]:
		print("Hardware Models (for --mod):")
		print("  all")
		for entryMod in MODEL_LIST_SERIES_ALL:
			print("  " + entryMod)
	if args["list_tt"] or args["list_mod"]:
		sys.exit(0)
	#
	if args["tt"]:
		if args["tt"] != TEST_TYPE_KEY_ALL and args["tt"] not in ALL_TEST_TYPE_KEYS:
			print("! Invalid Test Type '%s'" % args["tt"], file=sys.stderr)
			sys.exit(1)
	else:
		args["tt"] = TEST_TYPE_KEY_ALL
	#
	if args["mod"] and args["mod"] != "all":
		try:
			get_hw_model_id(args["mod"])
		except (InvalidModelError, UnsupportedModelError):
			print("! Warning: Unknown HW Model '%s'" % args["mod"], file=sys.stderr)
	return args

if __name__ == "__main__":
	args = _get_parsed_args()
	#
	isOk = False
	modelList = []
	if not args["mod"]:
		modelList = TEST_MODEL_LIST
	elif args["mod"] == "all":
		modelList = MODEL_LIST_SERIES_ALL
	else:
		modelList.append(args["mod"])
	for entryModel in modelList:
		print("")
		print("-" * 80)
		print("++ MODEL '%s' ++" % entryModel)
		print("")
		tmiObj = TestMansonInstrument()
		testTypeList = []
		if args["tt"] == TEST_TYPE_KEY_ALL:
			testTypeList = ALL_TEST_TYPE_KEYS
		else:
			testTypeList.append(args["tt"])
		for entryTt in testTypeList:
			print("")
			print("-" * 60)
			print("++++ MODEL '%s' - TEST '%s' ++++" % (entryModel, entryTt))
			print("")
			isOk = tmiObj.runtest(entryTt, serialDevice=None, emulateModel=entryModel)
			if not isOk:
				break
		if not isOk:
			break
	#
	sys.exit(0 if isOk else 1)
