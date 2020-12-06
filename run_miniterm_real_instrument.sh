#!/bin/bash

#
# by TS, Dec 2020
#

function printUsage() {
	echo "Usage: $(basename "$0") [-h|--help] COMPORT" >>/dev/stderr
	echo >>/dev/stderr
	echo "Use 'list' for COMPORT to see available ports" >>/dev/stderr
	echo >>/dev/stderr
	echo "Examples: ./$(basename "$0") list" >>/dev/stderr
	echo "          ./$(basename "$0") /dev/ttyUSB0" >>/dev/stderr
	exit 1
}

if [ $# -eq 0 -o $# -gt 1 -o "$1" = "-h" -o "$1" = "--help" ]; then
	printUsage
fi

if [ "$1" = "l" -o "$1" = "list" ]; then
	python3 run_test_real_instrument.py list
	exit 0
fi

python3 -m serial.tools.miniterm --eol CR "$1" 9600
