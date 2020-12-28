#
# by TS, Dec 2020
#

try:
	from .exceptions import InvalidInputDataError, TestFailedError
	from .models import get_hw_model_id as models_get_hw_model_id, \
			get_hw_specs as models_get_hw_specs
	from .serializer import *
except (ModuleNotFoundError, ImportError):
	from exceptions import InvalidInputDataError, TestFailedError
	from models import get_hw_model_id as models_get_hw_model_id, \
			get_hw_specs as models_get_hw_specs
	from serializer import *

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class TestSerializerMansonInstrument(object):
	_TEST_ALL = True
	_TEST_INV_TYPES = False
	_TEST_IX = False
	_TEST_ST = False
	_TEST_MODEL = False
	_TEST_VER = False
	_TEST_VOLT = False
	_TEST_CURR = False
	_TEST_SPECVOLT = False
	_TEST_SPECCURR = False
	_TEST_VARVOLT = False
	_TEST_VARCURR = False
	_TEST_VARVOLTCURRMODE = False
	_TEST_VOLTCURR = False
	_TEST_RANGE = True

	def __init__(self, modelId):
		""" Constructor

		Parameters:
			modelId (str): Hardware Model to simulate
		"""
		modelId = models_get_hw_model_id(modelId)
		#
		self._modelId = modelId
		self._hwSpecs = models_get_hw_specs(modelId)
		#
		self._szrObj = Serializer()
		self._szrObj.set_hw_specs(self._hwSpecs)

	def test_unserialize(self):
		""" Test decoding input from hardware

		Raises:
			TestFailedError
		"""
		hwSpecs = self._hwSpecs
		print("Test Unserializing Data (Model '%s'):" % self._modelId)
		#
		if self._TEST_ALL or self._TEST_INV_TYPES:
			print("  IT #a: ", end="")
			valStr = "asd" + SZR_RESP_OK_SUFFIX
			try:
				resA = self._szrObj.unserialize_data(valStr, [])
				if len(resA) != 0:
					raise TestFailedError("! unexpected result")
			except InvalidInputDataError:
				print("OK")
			#
			print("  IT #b: ", end="")
			valStr = "asd" + SZR_RESP_OK_SUFFIX
			try:
				resA = self._szrObj.unserialize_data(valStr, ["xylo"])
				if len(resA) != 0:
					raise TestFailedError("! unexpected result")
				raise TestFailedError("! unexpected success")
			except ValueError:
				print("OK")
			#
			print("  IT #c: ", end="")
			valStr = "0" + SZR_RESP_OK_SUFFIX
			try:
				resA = self._szrObj.unserialize_data(valStr, [SZR_VTYPE_IX, SZR_VTYPE_IX])
				if len(resA) != 0:
					raise TestFailedError("! unexpected result")
				raise TestFailedError("! unexpected success")
			except InvalidInputDataError:
				print("OK")
		#
		if self._TEST_ALL or self._TEST_IX:
			self._test_unserialize_ix_1("a", "asd" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_ix_1("b", "" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_ix_1("c", str(hwSpecs["virtMemPresetLocations"] - 1))
			self._test_unserialize_ix_1("d", str(hwSpecs["virtMemPresetLocations"]) + SZR_RESP_OK_SUFFIX)
			#
			if hwSpecs["virtMemPresetLocations"] > 0:
				self._test_unserialize_ix_2("e", hwSpecs["virtMemPresetLocations"] - 1)
		#
		if self._TEST_ALL or self._TEST_ST:
			self._test_unserialize_state_1("a", "asd" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_state_1("b", "" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_state_1("c", "a" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_state_1("d", "2" + SZR_RESP_OK_SUFFIX)
			#
			self._test_unserialize_state_2("e", True)
			self._test_unserialize_state_2("f", False)
		#
		if self._TEST_ALL or self._TEST_MODEL:
			listValueTypes = [SZR_VTYPE_MODEL]
			#
			print("  ML #a: ", end="")
			valStr = "" + SZR_RESP_OK_SUFFIX
			try:
				self._szrObj.unserialize_data(valStr, listValueTypes)
				raise TestFailedError("! unexpected success")
			except InvalidInputDataError:
				print("OK (expected failure)")
			#
			print("  ML #b: ", end="")
			expV = "themodel"
			valStr = expV + SZR_RESP_OK_SUFFIX
			resA = self._szrObj.unserialize_data(valStr, listValueTypes)
			if len(resA) == 1 and resA[0]["val"] == expV:
				print("OK")
			else:
				raise TestFailedError("! unexpected value")
		#
		if self._TEST_ALL or self._TEST_VER:
			listValueTypes = [SZR_VTYPE_VER]
			#
			print("  VE #a: ", end="")
			valStr = "" + SZR_RESP_OK_SUFFIX
			try:
				self._szrObj.unserialize_data(valStr, listValueTypes)
				raise TestFailedError("! unexpected success")
			except InvalidInputDataError:
				print("OK (expected failure)")
			#
			print("  VE #b: ", end="")
			expV = "theversion"
			valStr = expV + SZR_RESP_OK_SUFFIX
			resA = self._szrObj.unserialize_data(valStr, listValueTypes)
			if len(resA) == 1 and resA[0]["val"] == expV:
				print("OK")
			else:
				raise TestFailedError("! unexpected value")
		#
		if self._TEST_ALL or self._TEST_VOLT:
			self._test_unserialize_volt_or_curr_1(True, "a", "" + SZR_RESP_OK_SUFFIX)
			#
			valStr = "0" * (hwSpecs["totalDigits"] - 1)
			valStr += "1" + SZR_RESP_OK_SUFFIX
			expV = 1.0 * pow(10, -hwSpecs["precVolt"])
			self._test_unserialize_volt_or_curr_2(True, "b", valStr, expV)
			#
			valStr = "0" * (hwSpecs["totalDigits"] - 2)
			valStr += "12" + SZR_RESP_OK_SUFFIX
			expV = 12.0 * pow(10, -hwSpecs["precVolt"])
			self._test_unserialize_volt_or_curr_2(True, "c", valStr, expV)
			#
			valStr = "0" * (hwSpecs["totalDigits"] - 3)
			valStr += "123" + SZR_RESP_OK_SUFFIX
			expV = 123.0 * pow(10, -hwSpecs["precVolt"])
			self._test_unserialize_volt_or_curr_2(True, "d", valStr, expV)
			#
			if hwSpecs["totalDigits"] > 3:
				valStr = "0" * (hwSpecs["totalDigits"] - 4)
				valStr += "1234" + SZR_RESP_OK_SUFFIX
				expV = 1234.0 * pow(10, -hwSpecs["precVolt"])
				self._test_unserialize_volt_or_curr_2(True, "e", valStr, expV)
		#
		if self._TEST_ALL or self._TEST_CURR:
			self._test_unserialize_volt_or_curr_1(False, "a", "" + SZR_RESP_OK_SUFFIX)
			#
			valStr = "0" * (hwSpecs["totalDigits"] - 1)
			valStr += "1" + SZR_RESP_OK_SUFFIX
			expV = 1.0 * pow(10, -hwSpecs["precCurr"])
			self._test_unserialize_volt_or_curr_2(False, "b", valStr, expV)
			#
			valStr = "0" * (hwSpecs["totalDigits"] - 2)
			valStr += "12" + SZR_RESP_OK_SUFFIX
			expV = 12.0 * pow(10, -hwSpecs["precCurr"])
			self._test_unserialize_volt_or_curr_2(False, "c", valStr, expV)
			#
			valStr = "0" * (hwSpecs["totalDigits"] - 3)
			valStr += "123" + SZR_RESP_OK_SUFFIX
			expV = 123.0 * pow(10, -hwSpecs["precCurr"])
			self._test_unserialize_volt_or_curr_2(False, "d", valStr, expV)
			#
			if hwSpecs["totalDigits"] > 3:
				valStr = "0" * (hwSpecs["totalDigits"] - 4)
				valStr += "1234" + SZR_RESP_OK_SUFFIX
				expV = 1234.0 * pow(10, -hwSpecs["precCurr"])
				self._test_unserialize_volt_or_curr_2(False, "e", valStr, expV)
		#
		if self._TEST_ALL or self._TEST_SPECVOLT:
			self._test_unserialize_specvolt_or_speccurr_1(True, "a", "" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_specvolt_or_speccurr_1(True, "b", "111" + SZR_RESP_OK_SUFFIX)
			#
			valStr = "1239" + SZR_RESP_OK_SUFFIX
			expV = 12.39
			self._test_unserialize_specvolt_or_speccurr_2(True, "c", valStr, expV)
		#
		if self._TEST_ALL or self._TEST_SPECCURR:
			self._test_unserialize_specvolt_or_speccurr_1(False, "a", "" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_specvolt_or_speccurr_1(False, "b", "111" + SZR_RESP_OK_SUFFIX)
			#
			valStr = "1239" + SZR_RESP_OK_SUFFIX
			expV = 12.39
			self._test_unserialize_specvolt_or_speccurr_2(False, "c", valStr, expV)
		#
		if self._TEST_ALL or self._TEST_VARVOLT:
			self._test_unserialize_varvolt_or_varcurr_1(True, "a", "" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_varvolt_or_varcurr_1(True, "b", "0" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_varvolt_or_varcurr_1(True, "c", ";" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_varvolt_or_varcurr_1(True, "d", "a;" + SZR_RESP_OK_SUFFIX)
			#
			self._test_unserialize_varvolt_or_varcurr_2(True, "e", 12.39)
			self._test_unserialize_varvolt_or_varcurr_2(True, "f", 1.39)
			self._test_unserialize_varvolt_or_varcurr_2(True, "g", 0.07)
		#
		if self._TEST_ALL or self._TEST_VARCURR:
			self._test_unserialize_varvolt_or_varcurr_1(False, "a", "" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_varvolt_or_varcurr_1(False, "b", "0" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_varvolt_or_varcurr_1(False, "c", ";" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_varvolt_or_varcurr_1(False, "d", "a;" + SZR_RESP_OK_SUFFIX)
			#
			self._test_unserialize_varvolt_or_varcurr_2(False, "e", 1.39)
			self._test_unserialize_varvolt_or_varcurr_2(False, "f", 0.2)
			self._test_unserialize_varvolt_or_varcurr_2(False, "g", 0.05)
		#
		if self._TEST_ALL or self._TEST_VARVOLTCURRMODE:
			self._test_unserialize_vvcm_1("a", "1;1;1")
			self._test_unserialize_vvcm_1("b", "1;1;1;")
			self._test_unserialize_vvcm_1("c", "12345;1;1" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_vvcm_1("d", "1;12345;1" + SZR_RESP_OK_SUFFIX)
			self._test_unserialize_vvcm_1("e", "1;1;12" + SZR_RESP_OK_SUFFIX)
			#
			expV1 = 1.39
			expV2 = 0.42
			expV3Co = SZR_OUTP_MODE_CV
			self._test_unserialize_vvcm_2("f", expV1, expV2, expV3Co)
			#
			expV1 = 12.34
			expV2 = 0.01
			expV3Co = SZR_OUTP_MODE_CC
			self._test_unserialize_vvcm_2("g", expV1, expV2, expV3Co)
		#
		if self._TEST_ALL or self._TEST_RANGE:
			self._test_unserialize_range_1("a", "x")
			self._test_unserialize_range_1("b", str(hwSpecs["ranges"]))
			#
			if hwSpecs["ranges"] > 0:
				self._test_unserialize_range_2("c", 0)
				self._test_unserialize_range_2("d", hwSpecs["ranges"] - 1)

	def test_serialize(self):
		""" Test encoding output for hardware

		Raises:
			TestFailedError
		"""
		hwSpecs = self._hwSpecs
		print("Test Serializing Data (Model '%s'):" % self._modelId)
		#
		if self._TEST_ALL or self._TEST_INV_TYPES:
			listValueTypes = []
			#
			print("  IT #a: ", end="")
			valArr = []
			resS = self._szrObj.serialize_data(valArr, listValueTypes)
			if len(resS) != 0:
				raise TestFailedError("! unexpected result")
			print("OK")
			#
			listValueTypes = ["xylo"]
			#
			print("  IT #b: ", end="")
			valArr = ["asd"]
			try:
				resS = self._szrObj.serialize_data(valArr, listValueTypes)
				if len(resS) != 0:
					raise TestFailedError("! unexpected result")
				raise TestFailedError("! unexpected success")
			except ValueError:
				print("OK")
			#
			listValueTypes = [SZR_VTYPE_IX, SZR_VTYPE_IX]
			#
			print("  IT #c: ", end="")
			valArr = ["0"]
			try:
				resS = self._szrObj.serialize_data(valArr, listValueTypes)
				if len(resS) != 0:
					raise TestFailedError("! unexpected result")
				raise TestFailedError("! unexpected success")
			except ValueError:
				print("OK")
		#
		if self._TEST_ALL or self._TEST_IX:
			self._test_serialize_ix_1("a", "asd")
			self._test_serialize_ix_1("b", "")
			self._test_serialize_ix_1("c", -1)
			self._test_serialize_ix_1("d", hwSpecs["virtMemPresetLocations"])
			#
			if hwSpecs["virtMemPresetLocations"] > 0:
				self._test_serialize_ix_2("e", hwSpecs["virtMemPresetLocations"] - 1)
		#
		if self._TEST_ALL or self._TEST_ST:
			self._test_serialize_state_1("a", "asd")
			self._test_serialize_state_1("b", "")
			self._test_serialize_state_1("c", "a")
			self._test_serialize_state_1("d", "2")
			#
			self._test_serialize_state_2("e", True)
			self._test_serialize_state_2("f", False)
		#
		if self._TEST_ALL or self._TEST_MODEL:
			listValueTypes = [SZR_VTYPE_MODEL]
			#
			print("  ML #a: ", end="")
			valArr = [""]
			try:
				self._szrObj.serialize_data(valArr, listValueTypes)
				raise TestFailedError("! unexpected success")
			except ValueError:
				print("OK (expected failure)")
			#
			print("  ML #b: ", end="")
			expV = "themodel"
			valArr = [expV]
			resS = self._szrObj.serialize_data(valArr, listValueTypes)
			if resS == expV:
				print("OK")
			else:
				raise TestFailedError("! unexpected value (is='%s', exp='%s')" % (resS, expV))
		#
		if self._TEST_ALL or self._TEST_VER:
			listValueTypes = [SZR_VTYPE_VER]
			#
			print("  VE #a: ", end="")
			valArr = [""]
			try:
				self._szrObj.serialize_data(valArr, listValueTypes)
				raise TestFailedError("! unexpected success")
			except ValueError:
				print("OK (expected failure)")
			#
			print("  VE #b: ", end="")
			expV = "theversion"
			valArr = [expV]
			resS = self._szrObj.serialize_data(valArr, listValueTypes)
			if resS == expV:
				print("OK")
			else:
				raise TestFailedError("! unexpected value")
		#
		if self._TEST_ALL or self._TEST_VOLT:
			self._test_serialize_volt_or_curr_1(True, "a", "")
			self._test_serialize_volt_or_curr_1(True, "b", hwSpecs["minVolt"] - 0.1)
			self._test_serialize_volt_or_curr_1(True, "c", hwSpecs["maxVolt"] + 0.1)
			#
			self._test_serialize_volt_or_curr_2(True, "d", hwSpecs["minVolt"])
			self._test_serialize_volt_or_curr_2(True, "e", hwSpecs["maxVolt"])
		#
		if self._TEST_ALL or self._TEST_CURR:
			self._test_serialize_volt_or_curr_1(False, "a", "")
			self._test_serialize_volt_or_curr_1(False, "b", hwSpecs["minCurr"] - 0.1)
			self._test_serialize_volt_or_curr_1(False, "c", hwSpecs["maxCurr"] + 0.1)
			#
			self._test_serialize_volt_or_curr_2(False, "d", hwSpecs["minCurr"])
			self._test_serialize_volt_or_curr_2(False, "e", hwSpecs["maxCurr"])
		#
		if self._TEST_ALL or self._TEST_SPECVOLT:
			self._test_serialize_specvolt_or_speccurr_1(True, "a", "")
			self._test_serialize_specvolt_or_speccurr_1(True, "b", 111111)
			#
			self._test_serialize_specvolt_or_speccurr_2(True, "c", hwSpecs["minVolt"])
			self._test_serialize_specvolt_or_speccurr_2(True, "d", hwSpecs["minVolt"] + 0.1)
			self._test_serialize_specvolt_or_speccurr_2(True, "e", (hwSpecs["maxVolt"] - hwSpecs["minVolt"]) / 3.333)
			self._test_serialize_specvolt_or_speccurr_2(True, "f", hwSpecs["maxVolt"])
		#
		if self._TEST_ALL or self._TEST_SPECCURR:
			self._test_serialize_specvolt_or_speccurr_2(False, "a", hwSpecs["minCurr"])
			self._test_serialize_specvolt_or_speccurr_2(False, "b", hwSpecs["minCurr"] + 0.1)
			self._test_serialize_specvolt_or_speccurr_2(False, "c", (hwSpecs["maxCurr"] - hwSpecs["minCurr"]) / 3.333)
			self._test_serialize_specvolt_or_speccurr_2(False, "d", hwSpecs["maxCurr"])
		#
		if self._TEST_ALL or self._TEST_VARVOLT:
			self._test_serialize_varvolt_or_varcurr_2(True, "a", hwSpecs["minVolt"])
			self._test_serialize_varvolt_or_varcurr_2(True, "b", hwSpecs["minVolt"] + 0.1)
			self._test_serialize_varvolt_or_varcurr_2(True, "c", (hwSpecs["maxVolt"] - hwSpecs["minVolt"]) / 3.333)
			self._test_serialize_varvolt_or_varcurr_2(True, "d", hwSpecs["maxVolt"])
		#
		if self._TEST_ALL or self._TEST_VARCURR:
			self._test_serialize_varvolt_or_varcurr_2(False, "a", hwSpecs["minCurr"])
			self._test_serialize_varvolt_or_varcurr_2(False, "b", hwSpecs["minCurr"] + 0.1)
			self._test_serialize_varvolt_or_varcurr_2(False, "c", (hwSpecs["maxCurr"] - hwSpecs["minCurr"]) / 3.333)
			self._test_serialize_varvolt_or_varcurr_2(False, "d", hwSpecs["maxCurr"])
		#
		if self._TEST_ALL or self._TEST_VARVOLTCURRMODE:
			expV1 = hwSpecs["minVolt"]
			expV2 = hwSpecs["minCurr"]
			expV3Ch = hwSpecs["charModeCv"]
			self._test_serialize_vvcm("a", expV1, expV2, expV3Ch)
			#
			expV1 = (hwSpecs["maxVolt"] - hwSpecs["minVolt"]) / 7.33333
			expV2 = (hwSpecs["maxCurr"] - hwSpecs["minCurr"]) / 7.33333
			expV3Ch = hwSpecs["charModeCc"]
			self._test_serialize_vvcm("b", expV1, expV2, expV3Ch)
			#
			expV1 = hwSpecs["maxVolt"]
			expV2 = hwSpecs["maxCurr"]
			expV3Ch = hwSpecs["charModeCc"]
			self._test_serialize_vvcm("c", expV1, expV2, expV3Ch)
		#
		if self._TEST_ALL or self._TEST_VOLTCURR:
			expV1 = hwSpecs["minVolt"]
			expV2 = hwSpecs["minCurr"]
			self._test_serialize_vc("a", expV1, expV2)
			#
			expV1 = (hwSpecs["maxVolt"] - hwSpecs["minVolt"]) / 7.73333
			expV2 = (hwSpecs["maxCurr"] - hwSpecs["minCurr"]) / 7.73333
			self._test_serialize_vc("b", expV1, expV2)
			#
			expV1 = hwSpecs["maxVolt"]
			expV2 = hwSpecs["maxCurr"]
			self._test_serialize_vc("c", expV1, expV2)
		#
		if self._TEST_ALL or self._TEST_RANGE:
			self._test_serialize_range_1("a", "x")
			self._test_serialize_range_1("b", hwSpecs["ranges"])
			#
			if hwSpecs["ranges"] > 0:
				self._test_serialize_range_2("c", 0)
				self._test_serialize_range_2("d", hwSpecs["ranges"] - 1)

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _test_unserialize__exp_fail(self, listValueTypes, testId, testIx, testStr):
		print("  %s #%s: " % (testId, testIx), end="")
		try:
			self._szrObj.unserialize_data(testStr, listValueTypes)
			raise TestFailedError("! unexpected success")
		except InvalidInputDataError:
			print("OK (expected failure)")

	def _test_unserialize_ix_1(self, testIx, testStr):
		listValueTypes = [SZR_VTYPE_IX]
		self._test_unserialize__exp_fail(listValueTypes, "IX", testIx, testStr)

	def _test_unserialize_ix_2(self, testIx, expV1):
		listValueTypes = [SZR_VTYPE_IX]
		#
		print("  IX #%s: " % testIx, end="")
		valStr = str(expV1) + SZR_RESP_OK_SUFFIX
		resA = self._szrObj.unserialize_data(valStr, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK")
		else:
			raise TestFailedError("! unexpected value")

	def _test_unserialize_state_1(self, testIx, testStr):
		listValueTypes = [SZR_VTYPE_STATE]
		self._test_unserialize__exp_fail(listValueTypes, "ST", testIx, testStr)

	def _test_unserialize_state_2(self, testIx, expV1):
		listValueTypes = [SZR_VTYPE_STATE]
		#
		print("  ST #%s: " % testIx, end="")
		valStr = (self._hwSpecs["charStateOn"] if expV1 else self._hwSpecs["charStateOff"]) + SZR_RESP_OK_SUFFIX
		resA = self._szrObj.unserialize_data(valStr, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK")
		else:
			raise TestFailedError("! unexpected value")

	def _test_unserialize_volt_or_curr_1(self, isVolt, testIx, testStr):
		listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
		self._test_unserialize__exp_fail(listValueTypes, "VOLT" if isVolt else "CURR", testIx, testStr)

	def _test_unserialize_volt_or_curr_2(self, isVolt, testIx, testStr, expV1):
		listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
		#
		print("  %s #%s: " % ("VOLT" if isVolt else "CURR", testIx), end="")
		expV1 = self._szrObj.round_value(expV1, isVolt=isVolt)
		resA = self._szrObj.unserialize_data(testStr, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%.3f)" % expV1)
		else:
			raise TestFailedError("! unexpected value (is=%.3f, exp=%.3f)" % (resA[0]["val"], expV1))

	def _test_unserialize_specvolt_or_speccurr_1(self, isVolt, testIx, testStr):
		listValueTypes = [SZR_VTYPE_SPECVOLT if isVolt else SZR_VTYPE_SPECCURR]
		self._test_unserialize__exp_fail(listValueTypes, "SPECV" if isVolt else "SPECC", testIx, testStr)

	def _test_unserialize_specvolt_or_speccurr_2(self, isVolt, testIx, testStr, expV1):
		listValueTypes = [SZR_VTYPE_SPECVOLT if isVolt else SZR_VTYPE_SPECCURR]
		#
		print("  %s #%s: " % ("SPECV" if isVolt else "SPECC", testIx), end="")
		expV1 = self._szrObj.round_value(expV1, isVolt=isVolt)
		expV1 = round(expV1, 2)  # extra round because of SPECVOLT/SPECCURR which has only 2 dec digits
		resA = self._szrObj.unserialize_data(testStr, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%.3f)" % expV1)
		else:
			raise TestFailedError("! unexpected value (is=%.3f, exp=%.3f)" % (resA[0]["val"], expV1))

	def _test_unserialize_varvolt_or_varcurr_1(self, isVolt, testIx, testStr):
		listValueTypes = [SZR_VTYPE_VARVOLT if isVolt else SZR_VTYPE_VARCURR]
		self._test_unserialize__exp_fail(listValueTypes, "VARV" if isVolt else "VARC", testIx, testStr)

	def _test_unserialize_varvolt_or_varcurr_2(self, isVolt, testIx, expV1):
		listValueTypes = [SZR_VTYPE_VARVOLT if isVolt else SZR_VTYPE_VARCURR]
		#
		print("  %s #%s: " % ("VARV" if isVolt else "VARC", testIx), end="")
		expV1 = self._szrObj.round_value(expV1, isVolt=isVolt)
		precVC = (self._hwSpecs["precVolt"] if isVolt else self._hwSpecs["precCurr"])
		valStr = str(int(expV1 * pow(10, precVC)))+ ";" + SZR_RESP_OK_SUFFIX
		resA = self._szrObj.unserialize_data(valStr, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%.3f)" % expV1)
		else:
			raise TestFailedError("! unexpected value (is=%.3f, exp=%.3f)" % (resA[0]["val"], expV1))

	def _test_unserialize_vvcm_1(self, testIx, testStr):
		listValueTypes = [SZR_VTYPE_VARVOLT, SZR_VTYPE_VARCURR, SZR_VTYPE_MODE]
		self._test_unserialize__exp_fail(listValueTypes, "VVCM", testIx, testStr)

	def _test_unserialize_vvcm_2(self, testIx, expV1, expV2, expV3Co):
		listValueTypes = [SZR_VTYPE_VARVOLT, SZR_VTYPE_VARCURR, SZR_VTYPE_MODE]
		#
		print("  VVCM #%s: " % testIx, end="")
		expV1 = self._szrObj.round_value(expV1, isVolt=True)
		expV2 = self._szrObj.round_value(expV2, isVolt=False)
		valStr = str(int(expV1 * pow(10, self._hwSpecs["precVolt"]))) + ";"
		valStr += str(int(expV2 * pow(10, self._hwSpecs["precCurr"]))) + ";"
		valStr += (self._hwSpecs["charModeCv"] if expV3Co == SZR_OUTP_MODE_CV else self._hwSpecs["charModeCc"]) + ";"
		valStr += SZR_RESP_OK_SUFFIX
		resA = self._szrObj.unserialize_data(valStr, listValueTypes)
		if len(resA) == 3 and resA[0]["val"] == expV1 and resA[1]["val"] == expV2 and \
				resA[2]["val"] == expV3Co:
			print("OK (=%.3f / %.3f / %s)" % (expV1, expV2, "CV" if expV3Co == SZR_OUTP_MODE_CV else "CC"))
		else:
			errMsg = "! unexpected value ("
			errMsg += "is1=%.3f, exp1=%.3f, " % (resA[0]["val"], expV1)
			errMsg += "is2=%.3f, exp2=%.3f, " % (resA[1]["val"], expV2)
			errMsg += "is3=%s, exp3=%s)" % ("CV" if resA[2]["val"] == SZR_OUTP_MODE_CV else "CC", "CV" if expV3Co == SZR_OUTP_MODE_CV else "CC")
			raise TestFailedError(errMsg)

	def _test_unserialize_range_1(self, testIx, testStr):
		listValueTypes = [SZR_VTYPE_RANGE]
		self._test_unserialize__exp_fail(listValueTypes, "RA", testIx, testStr)

	def _test_unserialize_range_2(self, testIx, expV1):
		listValueTypes = [SZR_VTYPE_RANGE]
		#
		print("  RA #%s: " % testIx, end="")
		valStr = str(expV1) + SZR_RESP_OK_SUFFIX
		resA = self._szrObj.unserialize_data(valStr, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK")
		else:
			raise TestFailedError("! unexpected value")

	# --------------------------------------------------------------------------

	def _test_serialize__exp_fail(self, listValueTypes, testId, testIx, testValMixed):
		print("  %s #%s: " % (testId, testIx), end="")
		valArr = [testValMixed]
		try:
			self._szrObj.serialize_data(valArr, listValueTypes)
			raise TestFailedError("! unexpected success")
		except ValueError:
			print("OK (expected failure)")

	def _test_serialize_ix_1(self, testIx, testValMixed):
		listValueTypes = [SZR_VTYPE_IX]
		self._test_serialize__exp_fail(listValueTypes, "IX", testIx, testValMixed)

	def _test_serialize_ix_2(self, testIx, expV1):
		listValueTypes = [SZR_VTYPE_IX]
		#
		print("  IX #%s: " % testIx, end="")
		expS = str(expV1)
		valArr = [expV1]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		if len(resS) == 1 and resS == expS:
			print("OK")
		else:
			raise TestFailedError("! unexpected value")

	def _test_serialize_state_1(self, testIx, testStr):
		listValueTypes = [SZR_VTYPE_STATE]
		self._test_serialize__exp_fail(listValueTypes, "ST", testIx, testStr)

	def _test_serialize_state_2(self, testIx, expV1):
		listValueTypes = [SZR_VTYPE_STATE]
		#
		print("  ST #%s: " % testIx, end="")
		expS = (self._hwSpecs["charStateOn"] if expV1 else self._hwSpecs["charStateOff"])
		valArr = [expV1]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		if len(resS) == 1 and resS == expS:
			print("OK")
		else:
			raise TestFailedError("! unexpected value")

	def _test_serialize_volt_or_curr_1(self, isVolt, testIx, testValMixed):
		listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
		self._test_serialize__exp_fail(listValueTypes, "VOLT" if isVolt else "CURR", testIx, testValMixed)

	def _test_serialize_volt_or_curr_2(self, isVolt, testIx, expV1):
		listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
		#
		print("  %s #%s: " % ("VOLT" if isVolt else "CURR", testIx), end="")
		expV1 = self._szrObj.round_value(expV1, isVolt=isVolt)
		valArr = [expV1]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		resA = self._szrObj.unserialize_data(resS + SZR_RESP_OK_SUFFIX, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%s)" % resS)
		else:
			raise TestFailedError("! unexpected value (is=%.3f, exp=%.3f)" % (resA[0]["val"], expV1))

	def _test_serialize_specvolt_or_speccurr_1(self, isVolt, testIx, testValMixed):
		listValueTypes = [SZR_VTYPE_SPECVOLT if isVolt else SZR_VTYPE_SPECCURR]
		self._test_serialize__exp_fail(listValueTypes, "SPECV" if isVolt else "SPECC", testIx, testValMixed)

	def _test_serialize_specvolt_or_speccurr_2(self, isVolt, testIx, expV1):
		listValueTypes = [SZR_VTYPE_SPECVOLT if isVolt else SZR_VTYPE_SPECCURR]
		#
		print("  %s #%s: " % ("SPECV" if isVolt else "SPECC", testIx), end="")
		expV1 = round(expV1, 2)  # extra round because of SPECVOLT/SPECCURR which has only 2 dec digits
		valArr = [expV1]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		resA = self._szrObj.unserialize_data(resS + SZR_RESP_OK_SUFFIX, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%s)" % resS)
		else:
			raise TestFailedError("! unexpected value (is=%.3f ('%s'), exp=%.3f)" % (resA[0]["val"], resS, expV1))

	def _test_serialize_varvolt_or_varcurr_1(self, isVolt, testIx, testValMixed):
		listValueTypes = [SZR_VTYPE_VARVOLT if isVolt else SZR_VTYPE_VARCURR]
		self._test_serialize__exp_fail(listValueTypes, "VARV" if isVolt else "VARC", testIx, testValMixed)

	def _test_serialize_varvolt_or_varcurr_2(self, isVolt, testIx, expV1):
		listValueTypes = [SZR_VTYPE_VARVOLT if isVolt else SZR_VTYPE_VARCURR]
		#
		print("  %s #%s: " % ("VARV" if isVolt else "VARC", testIx), end="")
		expV1 = self._szrObj.round_value(expV1, isVolt=isVolt)
		valArr = [expV1]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		resA = self._szrObj.unserialize_data(resS + SZR_RESP_OK_SUFFIX, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%s)" % resS)
		else:
			raise TestFailedError("! unexpected value (is=%.3f ('%s'), exp=%.3f)" % (resA[0]["val"], resS, expV1))

	def _test_serialize_vvcm(self, testIx, expV1, expV2, expV3Ch):
		listValueTypes = [SZR_VTYPE_VARVOLT, SZR_VTYPE_VARCURR, SZR_VTYPE_MODE]
		#
		print("  VVCM #%s: " % testIx, end="")
		hwSpecs = self._hwSpecs
		if expV1 < hwSpecs["minVolt"]:
			expV1 += hwSpecs["minVolt"]
		if expV2 < hwSpecs["minCurr"]:
			expV2 += hwSpecs["minCurr"]
		expV1 = self._szrObj.round_value(expV1, isVolt=True)
		expV2 = self._szrObj.round_value(expV2, isVolt=False)
		expV3Co = SZR_OUTP_MODE_CV if expV3Ch == self._hwSpecs["charModeCv"] else SZR_OUTP_MODE_CC
		valArr = [expV1, expV2, expV3Co]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		resA = self._szrObj.unserialize_data(resS + SZR_RESP_OK_SUFFIX, listValueTypes)
		if len(resA) == 3 and resA[0]["val"] == expV1 and resA[1]["val"] == expV2 and \
				resA[2]["val"] == expV3Co:
			print("OK (=%.3f / %.3f / %s)" % (expV1, expV2, "CV" if expV3Co == SZR_OUTP_MODE_CV else "CC"))
		else:
			errMsg = "! unexpected value ("
			errMsg += "is1=%.3f, exp1=%.3f, " % (resA[0]["val"], expV1)
			errMsg += "is2=%.3f, exp2=%.3f, " % (resA[1]["val"], expV2)
			errMsg += "is3=%s, exp3=%s)" % ("CV" if resA[2]["val"] == SZR_OUTP_MODE_CV else "CC", "CV" if expV3Co == SZR_OUTP_MODE_CV else "CC")
			raise TestFailedError(errMsg)

	def _test_serialize_vc(self, testIx, expV1, expV2):
		listValueTypes = [SZR_VTYPE_VOLT, SZR_VTYPE_CURR]
		#
		print("  VC #%s: " % testIx, end="")
		hwSpecs = self._hwSpecs
		if expV1 < hwSpecs["minVolt"]:
			expV1 += hwSpecs["minVolt"]
		if expV2 < hwSpecs["minCurr"]:
			expV2 += hwSpecs["minCurr"]
		expV1 = self._szrObj.round_value(expV1, isVolt=True)
		expV2 = self._szrObj.round_value(expV2, isVolt=False)
		valArr = [expV1, expV2]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		resA = self._szrObj.unserialize_data(resS + SZR_RESP_OK_SUFFIX, listValueTypes)
		if len(resA) == 2 and resA[0]["val"] == expV1 and resA[1]["val"] == expV2:
			print("OK (=%.3f / %.3f)" % (expV1, expV2))
		else:
			errMsg = "! unexpected value ("
			errMsg += "is1=%.3f, exp1=%.3f, " % (resA[0]["val"], expV1)
			errMsg += "is2=%.3f, exp2=%.3f)" % (resA[1]["val"], expV2)
			raise TestFailedError(errMsg)

	def _test_serialize_range_1(self, testIx, testStr):
		listValueTypes = [SZR_VTYPE_RANGE]
		self._test_serialize__exp_fail(listValueTypes, "RA", testIx, testStr)

	def _test_serialize_range_2(self, testIx, expV1):
		listValueTypes = [SZR_VTYPE_RANGE]
		#
		print("  RA #%s: " % testIx, end="")
		valArr = [expV1]
		resS = self._szrObj.serialize_data(valArr, listValueTypes)
		resA = self._szrObj.unserialize_data(resS + SZR_RESP_OK_SUFFIX, listValueTypes)
		if len(resA) == 1 and resA[0]["val"] == expV1:
			print("OK (=%d)" % (expV1))
		else:
			errMsg = "! unexpected value ("
			errMsg += "is1=%d, exp1=%d)" % (resA[0]["val"], expV1)
			raise TestFailedError(errMsg)
