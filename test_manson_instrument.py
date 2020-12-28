#
# by TS, Dec 2020
#

import sys
import time
import traceback

try:
	from .exceptions import FunctionNotSupportedForModelError, InvalidModelError, \
			InvalidTestType, TestFailedError, UnsupportedModelError
	from .manson_instrument import MansonInstrument, \
			VIRTUAL_SERIAL_DEVICE, \
			RANGE_ID_0_16V0_5A0, RANGE_ID_1_27V0_3A0, RANGE_ID_2_36V0_2A2
	from .test_serializer_manson_instrument import TestSerializerMansonInstrument
except (ModuleNotFoundError, ImportError):
	from exceptions import FunctionNotSupportedForModelError, InvalidModelError, \
			InvalidTestType, TestFailedError, UnsupportedModelError
	from manson_instrument import MansonInstrument, \
			VIRTUAL_SERIAL_DEVICE, \
			RANGE_ID_0_16V0_5A0, RANGE_ID_1_27V0_3A0, RANGE_ID_2_36V0_2A2
	from test_serializer_manson_instrument import TestSerializerMansonInstrument

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

TEST_TYPE_KEY_ALL = "all"
TEST_TYPE_KEY_SER = "ser"
TEST_TYPE_KEY_SIMPLE = "sim"
TEST_TYPE_KEY_VOLT = "v"
TEST_TYPE_KEY_CURR = "c"
TEST_TYPE_KEY_MEMPRESET = "mp"

TEST_TYPES = {
		TEST_TYPE_KEY_ALL: "run all Test Types",
		TEST_TYPE_KEY_SER: "run Serializer tests",
		TEST_TYPE_KEY_SIMPLE: "run simple tests",
		TEST_TYPE_KEY_VOLT: "run Voltage tests",  # WARNING: potentially dangerous to connected load
		TEST_TYPE_KEY_CURR: "run Current tests",  # WARNING: potentially dangerous to connected load
		TEST_TYPE_KEY_MEMPRESET: "run Memory Preset tests"  # WARNING: potentially dangerous to connected load
	}

ALL_TEST_TYPE_KEYS = [
		TEST_TYPE_KEY_SER,
		TEST_TYPE_KEY_SIMPLE,
		TEST_TYPE_KEY_VOLT,
		TEST_TYPE_KEY_CURR,
		TEST_TYPE_KEY_MEMPRESET
	]

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class TestMansonInstrument(object):
	def __init__(self):
		self._miCtrl = MansonInstrument()
		self._hwSpecs = None
		self._isEmulated = False

	# --------------------------------------------------------------------------

	def runtest(self, testType, serialDevice=None, emulateModel=None):
		if not testType in ALL_TEST_TYPE_KEYS:
			raise InvalidTestType(testType)
		miCtrl = self._miCtrl
		openedSerial = False
		#
		try:
			if serialDevice is None and emulateModel is None:
				raise ValueError("serialDevice and emulateModel may not both be None")
			if serialDevice is not None and serialDevice != VIRTUAL_SERIAL_DEVICE and emulateModel is not None:
				raise ValueError("for emulating a hardware model serialDevice needs to be VIRTUAL_SERIAL_DEVICE")
			if serialDevice is None and emulateModel is not None:
				serialDevice = VIRTUAL_SERIAL_DEVICE
			self._isEmulated = (serialDevice == VIRTUAL_SERIAL_DEVICE)
			if serialDevice is not None:
				print("Open Serial Port '%s'" % serialDevice)
				miCtrl.open_port(serialDevice, emulateModel)
				openedSerial = True
		except InvalidModelError as err:
			print("! Invalid model %s" % str(err), file=sys.stderr)
			return False
		except UnsupportedModelError as err:
			print("! Unsupported model %s" % str(err), file=sys.stderr)
			return False
		except Exception:
			print("")
			print("! An Exception has occured", file=sys.stderr)
			print("-" * 60, file=sys.stderr)
			traceback.print_exc(file=sys.stderr)
			print("-" * 60, file=sys.stderr)
			return False
		#
		resB = True
		try:
			if testType == TEST_TYPE_KEY_SER:
				self._ttype_serializer()
			else:
				print("Model: '%s', Version: '%s'" % (miCtrl.get_hw_model(), miCtrl.get_hw_version()))
				self._hwSpecs = miCtrl.get_hw_specs()
				if testType == TEST_TYPE_KEY_SIMPLE:
					self._ttype_simple()
				else:
					if not self._isEmulated:
						print("-" * 16)
						if testType == TEST_TYPE_KEY_MEMPRESET or testType == TEST_TYPE_KEY_VOLT:
							print("YOU -MAY- CONNECT AN ELECTRONIC LOAD TO THE POWER SUPPLY")
							print("AND SET IT IN CONSTANT CURRENT MODE WITH A CURRENT == 0.1A.")
							print("OR SIMPLY DISCONNECT ANY LOAD FROM THE POWER SUPPLY")
						elif testType == TEST_TYPE_KEY_CURR:
							print("YOU -NEED TO- CONNECT AN ELECTRONIC LOAD TO THE POWER SUPPLY")
							print("AND SET IT IN CONSTANT CURRENT MODE WITH A CURRENT == YOUR PS's MAXIMUM (e.g. 5A)")
						print("-" * 16)
					#
					if testType == TEST_TYPE_KEY_MEMPRESET:
						self._ttype_mempreset()
					elif testType == TEST_TYPE_KEY_VOLT:
						self._ttype_volt()
					elif testType == TEST_TYPE_KEY_CURR:
						self._ttype_curr()
			print("-" * 32)
		except TestFailedError as err:
			print("")
			print("! TEST FAILED", file=sys.stderr)
			print("! Error message: %s" % str(err), file=sys.stderr)
			resB = False
		except Exception:
			print("")
			print("! An error has occured", file=sys.stderr)
			print("-" * 60, file=sys.stderr)
			traceback.print_exc(file=sys.stderr)
			print("-" * 60, file=sys.stderr)
			resB = False
		finally:
			if openedSerial:
				if not self._isEmulated:
					#self._test_set_outp_state(state=False, doTest=False)
					try:
						print("Allow user input: ", end="")
						miCtrl.set_userinput_allowed(True)
						print("OK")
					except FunctionNotSupportedForModelError:
						print("(not supported)")
				#
				print("Close Serial Port")
				miCtrl.close_port()
		return resB

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _ttype_serializer(self):
		miCtrl = self._miCtrl
		#
		print("-" * 32)
		#
		tsmiCtrl = TestSerializerMansonInstrument(miCtrl.get_hw_model())
		tsmiCtrl.test_unserialize()
		tsmiCtrl.test_serialize()

	def _ttype_simple(self):
		miCtrl = self._miCtrl
		#
		print("-" * 32)
		print("Test Simple Commands (mostly read-only):")
		#
		try:
			print("Disallow user input: ", end="")
			miCtrl.set_userinput_allowed(False)
			print("OK")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		#
		hwSpecs = self._hwSpecs
		hwSpecsMaxVolt = hwSpecs["maxVolt"]
		hwSpecsMaxCurr = hwSpecs["maxCurr"]
		hwSpecsMpl = hwSpecs["realMemPresetLocations"]
		print("Specs: Voltage [%.3f..%.3fV] / Current [%.3f..%.3fA]" %
				(hwSpecs["minVolt"], hwSpecsMaxVolt, hwSpecs["minCurr"], hwSpecsMaxCurr))
		#
		try:
			print("HW min: ", end="")
			mnvc = miCtrl.get_min_values_from_hw()
			print("Voltage %.3fV / Current %.3fA" % (mnvc["minVolt"], mnvc["minCurr"]))
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		try:
			print("HW max: ", end="")
			mxvc = miCtrl.get_max_values_from_hw()
			print("Voltage %.3fV / Current %.3fA" % (mxvc["maxVolt"], mxvc["maxCurr"]))
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		#
		print("Preset: ", end="")
		try:
			presetVC = miCtrl.get_preset_voltage_current()
			print("%.3fV / %.3fA" % (presetVC["volt"], presetVC["curr"]))
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		#
		self._test_get_volt()
		self._test_get_curr()
		# set values
		# - otherwise the PS might be stuck at a "Upper Voltage/Current Limit" error
		self._test_set_volt_ignunsupported(hwSpecs["minVolt"] + 1.0)
		self._test_set_curr_ignunsupported(hwSpecs["minCurr"] + 0.1)
		#
		self._test_set_outp_state(state=False, doTest=True)
		self._test_set_outp_state(state=True, doTest=True)
		#
		print("Enable output: ", end="")
		miCtrl.set_output_state(True)
		print("OK")
		if not self._isEmulated:
			time.sleep(1)
		#
		print("Output state: ", end="")
		tmpB = miCtrl.get_output_state()
		print("on" if tmpB else "off")
		if not tmpB:
			raise TestFailedError("! unexpected state")
		#
		print("Output Mode: ", end="")
		tmpIsCv = miCtrl.get_is_output_mode_cv()
		tmpIsCc = not tmpIsCv and miCtrl.get_is_output_mode_cc()
		if not (tmpIsCv or tmpIsCc):
			raise TestFailedError("! unexpected mode")
		print("CV" if tmpIsCv else "CC")
		#
		if hwSpecsMpl == 0:
			print("(Mem presets not available)")
		else:
			for psIx in range(hwSpecsMpl):
				self._test_load_mempreset(psIx)
		#
		isSupp = self._test_set_ovp_ignunsupported(hwSpecs["minVolt"] + 2.0)
		if isSupp:
			tmpF = self._test_get_ovp()
			if tmpF != hwSpecs["minVolt"] + 2.0:
				raise TestFailedError("! unexpected value")
			self._test_set_ovp_ignunsupported(hwSpecsMaxVolt)
			tmpF = self._test_get_ovp()
			if tmpF != hwSpecsMaxVolt:
				raise TestFailedError("! unexpected value")
			#
			self._test_set_ocp(hwSpecs["minCurr"] + 0.2)
			tmpF = self._test_get_ocp()
			if tmpF != hwSpecs["minCurr"] + 0.2:
				raise TestFailedError("! unexpected value")
			self._test_set_ocp(hwSpecsMaxCurr)
			tmpF = self._test_get_ocp()
			if tmpF != hwSpecsMaxCurr:
				raise TestFailedError("! unexpected value")
		#
		isSupp = self._test_set_range_ignunsupported(RANGE_ID_0_16V0_5A0)
		if isSupp:
			tmpS = self._test_get_range()
			if tmpS != RANGE_ID_0_16V0_5A0:
				raise TestFailedError("! unexpected value")
			#
			self._test_set_range_ignunsupported(RANGE_ID_1_27V0_3A0)
			tmpS = self._test_get_range()
			if tmpS != RANGE_ID_1_27V0_3A0:
				raise TestFailedError("! unexpected value")
			#
			self._test_set_range_ignunsupported(RANGE_ID_2_36V0_2A2)
			tmpS = self._test_get_range()
			if tmpS != RANGE_ID_2_36V0_2A2:
				raise TestFailedError("! unexpected value")
			#
			try:
				self._test_set_range_ignunsupported("x")
				raise TestFailedError("! unexpected success")
			except ValueError:
				print("OK (expected failure)")

	def _ttype_volt(self):
		miCtrl = self._miCtrl
		hwSpecsMinVolt = self._hwSpecs["minVolt"]
		hwSpecsMaxVolt = self._hwSpecs["maxVolt"]
		hwSpecsMaxCurr = self._hwSpecs["maxCurr"]
		#
		print("-" * 32)
		print("Test Voltage Commands:")
		self._test_set_curr_ignunsupported(hwSpecsMaxCurr)
		#
		self._test_set_volt_expfail(hwSpecsMinVolt - 0.1)
		self._test_set_volt_expfail(hwSpecsMaxVolt + 0.1)
		#
		steps = 5
		for x in range(steps):
			tmpV = (hwSpecsMaxVolt / (steps + 1)) * (x + 1)
			tmpV = miCtrl.round_value(tmpV, isVolt=True)
			#
			try:
				self._test_set_volt(tmpV)
				if not self._isEmulated:
					time.sleep(4)  # give power supply and load some time to adjust
			except FunctionNotSupportedForModelError:
				print("(not supported)")
				return
			#
			res = self._test_get_volt()
			if res != tmpV:
				raise TestFailedError("! unexpected value")
		# reset output
		self._test_set_volt_ignunsupported(5.0)

	def _ttype_curr(self):
		miCtrl = self._miCtrl
		hwSpecsMinCurr = self._hwSpecs["minCurr"]
		hwSpecsMaxCurr = self._hwSpecs["maxCurr"]
		#
		print("-" * 32)
		print("Test Current Commands:")
		if not self._test_set_curr_ignunsupported(hwSpecsMinCurr + 0.1):
			return
		self._test_set_volt_ignunsupported(5.0)
		self._test_set_curr(hwSpecsMinCurr)
		if not self._isEmulated:
			time.sleep(5)  # give power supply and load some time to adjust
		#
		self._test_set_curr_expfail(hwSpecsMinCurr - 0.1)
		self._test_set_curr_expfail(hwSpecsMaxCurr + 0.1)
		#
		steps = 5
		for x in range(steps):
			tmpC = (hwSpecsMaxCurr / (steps + 1)) * (x + 1)
			tmpC = miCtrl.round_value(tmpC, isVolt=False)
			#
			self._test_set_curr(tmpC)
			if not self._isEmulated:
				time.sleep(5)  # give power supply and load some time to adjust
			#
			res = self._test_get_curr()
			if res < tmpC - 0.1 or res > tmpC + 0.1:
				raise TestFailedError("! unexpected value")
		# reset output
		self._test_set_curr(hwSpecsMinCurr + 0.1)

	def _ttype_mempreset(self):
		miCtrl = self._miCtrl
		hwSpecsMinVolt = self._hwSpecs["minVolt"]
		hwSpecsMaxVolt = self._hwSpecs["maxVolt"]
		hwSpecsMinCurr = self._hwSpecs["minCurr"]
		hwSpecsMaxCurr = self._hwSpecs["maxCurr"]
		hwSpecsMpl = self._hwSpecs["realMemPresetLocations"]
		#
		print("-" * 32)
		print("Test Memory Preset Commands:")
		#
		setVolt = miCtrl.round_value(hwSpecsMinVolt + 1.0, isVolt=True)
		setCurr = miCtrl.round_value(hwSpecsMaxCurr, isVolt=False)
		setVcSupp = self._test_set_voltcurr_ignunsupported(setVolt, setCurr)
		#
		self._test_save_mempreset_expfail(-1, 1.0, 1.0)
		self._test_save_mempreset_expfail(hwSpecsMpl, 1.0, 1.0)
		self._test_save_mempreset_expfail(0, hwSpecsMaxVolt + 0.1, 1.0)
		self._test_save_mempreset_expfail(0, 1.0, hwSpecsMaxCurr + 0.1)
		#
		self._test_load_mempreset_expfail(-1)
		self._test_load_mempreset_expfail(hwSpecsMpl)
		#
		self._test_apply_mempreset_expfail(-1)
		self._test_apply_mempreset_expfail(hwSpecsMpl)
		#
		for psIx in range(hwSpecsMpl):
			tmpV = (hwSpecsMaxVolt / (hwSpecsMpl + 1)) * (psIx + 1)
			tmpC = (hwSpecsMaxCurr / (hwSpecsMpl + 1)) * (psIx + 1)
			tmpV = miCtrl.round_value(tmpV, isVolt=True)
			setVolt = tmpV
			tmpC = miCtrl.round_value(tmpC, isVolt=False)
			#
			self._test_save_mempreset(psIx, tmpV, tmpC)
			#
			res = miCtrl.load_memory_preset(psIx)
			if res["volt"] != tmpV or res["curr"] != tmpC:
				raise TestFailedError("! unexpected value")
		#
		for psIx in range(hwSpecsMpl):
			self._test_apply_mempreset(psIx)
			if not self._isEmulated:
				time.sleep(5)  # give power supply and load some time to adjust
			try:
				print("Selected preset << ", end="")
				selIx = miCtrl.get_selected_preset()
				print("#%d " % selIx, end="")
				if selIx != psIx:
					raise TestFailedError("! unexpected value")
				print("OK")
			except FunctionNotSupportedForModelError:
				print("(not supported)")
		#
		if setVcSupp:
			isVolt = self._test_get_volt()
			if isVolt != setVolt:
				raise TestFailedError("! unexpected value")
			self._test_get_curr()
		# reset output
		self._test_set_curr_ignunsupported(hwSpecsMinCurr + 0.1)
		self._test_set_volt_ignunsupported(5.0)

	# --------------------------------------------------------------------------

	def _test_set_outp_state(self, state, doTest=True):
		miCtrl = self._miCtrl
		#
		print("Output state  >  " + ("on" if state else "off") + ": ", end="")
		miCtrl.set_output_state(state)
		print("OK")
		if not self._isEmulated:
			time.sleep(1)
		#
		if not doTest:
			return
		print("Output state < : ", end="")
		tmpB = miCtrl.get_output_state()
		print("on" if tmpB else "off")
		if tmpB != state:
			raise TestFailedError("! unexpected state")

	def _test_get_volt(self):
		miCtrl = self._miCtrl
		#
		print("Voltage < < : ", end="")
		curVolt = miCtrl.get_output_voltage()
		print("{0:6.3f}".format(curVolt))
		return curVolt

	def _test_set_volt_expfail(self, val):
		try:
			self._test_set_volt(val)
			raise TestFailedError("! unexpected success")
		except ValueError:
			print("OK (expected failure)")
		except FunctionNotSupportedForModelError:
			print("(not supported)")

	def _test_set_volt_ignunsupported(self, val):
		try:
			self._test_set_volt(val)
		except FunctionNotSupportedForModelError:
			print("(not supported)")
			return False
		return True

	def _test_set_volt(self, val):
		miCtrl = self._miCtrl
		#
		print("Voltage  > >  {0:6.3f}: ".format(val), end="")
		miCtrl.set_preset_voltage(val)
		print("OK")

	def _test_get_curr(self):
		miCtrl = self._miCtrl
		#
		print("Current < < : ", end="")
		curCurr = miCtrl.get_output_current()
		print("{0:6.3f}".format(curCurr))
		return curCurr

	def _test_set_curr_expfail(self, val):
		try:
			self._test_set_curr(val)
			raise TestFailedError("! unexpected success")
		except ValueError:
			print("OK (expected failure)")
		except FunctionNotSupportedForModelError:
			print("(not supported)")

	def _test_set_curr_ignunsupported(self, val):
		try:
			self._test_set_curr(val)
		except FunctionNotSupportedForModelError:
			print("(not supported)")
			return False
		return True

	def _test_set_curr(self, val):
		miCtrl = self._miCtrl
		#
		print("Current  > >  {0:6.3f}: ".format(val), end="")
		miCtrl.set_preset_current(val)
		print("OK")

	def _test_set_voltcurr_ignunsupported(self, volt, curr):
		try:
			miCtrl = self._miCtrl
			#
			print("Voltage/Current  > > {0:.3f}/{1:.3f}: ".format(volt, curr), end="")
			miCtrl.set_preset_voltage_current(volt, curr)
			print("OK")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
			return False
		return True

	def _test_load_mempreset_expfail(self, psIx):
		try:
			self._test_load_mempreset(psIx, autoReject=False)
			raise TestFailedError("! unexpected success")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		except AssertionError:
			print("OK (expected failure)")

	def _test_load_mempreset(self, psIx, autoReject=True):
		miCtrl = self._miCtrl
		hwSpecsMpl = self._hwSpecs["realMemPresetLocations"]
		#
		if autoReject and psIx >= hwSpecsMpl:
			return
		print("Mem preset #%2d <   <: " % psIx, end="")
		tmpD = miCtrl.load_memory_preset(psIx)
		print("{:6.3f}V / {:6.3f}A".format(tmpD["volt"], tmpD["curr"]))

	def _test_apply_mempreset_expfail(self, psIx):
		try:
			self._test_apply_mempreset(psIx, autoReject=False)
			raise TestFailedError("! unexpected success")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		except AssertionError:
			print("OK (expected failure)")

	def _test_apply_mempreset(self, psIx, autoReject=True):
		miCtrl = self._miCtrl
		hwSpecsMpl = self._hwSpecs["realMemPresetLocations"]
		#
		if autoReject and psIx >= hwSpecsMpl:
			return
		print("Mem preset #%2d apply: " % psIx, end="")
		miCtrl.apply_memory_preset(psIx)
		print("OK")

	def _test_save_mempreset_expfail(self, psIx, volt, curr):
		try:
			self._test_save_mempreset(psIx, volt, curr, autoReject=False)
			raise TestFailedError("! unexpected success")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
		except AssertionError:
			print("OK (expected failure)")
		except ValueError:
			print("OK (expected failure)")

	def _test_save_mempreset(self, psIx, volt, curr, autoReject=True):
		miCtrl = self._miCtrl
		hwSpecsMpl = self._hwSpecs["realMemPresetLocations"]
		#
		if autoReject and psIx >= hwSpecsMpl:
			return
		print("Mem preset #%2d  > > : %6.3fV / %6.3fA: " % (psIx, volt, curr), end="")
		changed = miCtrl.save_memory_preset(psIx, volt, curr)
		print("OK%s" % ("" if changed else " (unchanged)"))

	def _test_get_ovp(self):
		miCtrl = self._miCtrl
		#
		print("OVP < < : ", end="")
		curVolt = miCtrl.get_overvoltage_protection_value()
		print("{0:6.3f}".format(curVolt))
		return curVolt

	def _test_set_ovp_ignunsupported(self, val):
		try:
			miCtrl = self._miCtrl
			#
			print("OVP  > >  {0:6.3f}: ".format(val), end="")
			miCtrl.set_overvoltage_protection_value(val)
			print("OK")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
			return False
		return True

	def _test_get_ocp(self):
		miCtrl = self._miCtrl
		#
		print("OCP < < : ", end="")
		curCurr = miCtrl.get_overcurrent_protection_value()
		print("{0:6.3f}".format(curCurr))
		return curCurr

	def _test_set_ocp(self, val):
		miCtrl = self._miCtrl
		#
		print("OCP  > >  {0:6.3f}: ".format(val), end="")
		miCtrl.set_overcurrent_protection_value(val)
		print("OK")

	def _test_get_range(self):
		miCtrl = self._miCtrl
		#
		print("Range < < : ", end="")
		curRa = miCtrl.get_selected_range()
		print("{0:s}".format(curRa))
		return curRa

	def _test_set_range_ignunsupported(self, val):
		try:
			miCtrl = self._miCtrl
			#
			print("Range  > >  {0:s}: ".format(val), end="")
			miCtrl.set_selected_range(val)
			print("OK")
		except FunctionNotSupportedForModelError:
			print("(not supported)")
			return False
		return True
