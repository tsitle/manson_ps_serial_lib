#
# by TS, Dec 2020
#

from copy import deepcopy
import re

try:
	from .exceptions import InvalidInputDataError
	from .models import build_spec_dict as models_build_spec_dict
except (ModuleNotFoundError, ImportError):
	from exceptions import InvalidInputDataError
	from models import build_spec_dict as models_build_spec_dict

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

SZR_OUTP_MODE_CC = "CC"
SZR_OUTP_MODE_CV = "CV"
#
SZR_VTYPE_VOLT = "vt-volt"
SZR_VTYPE_SPECVOLT = "vt-specvolt"
SZR_VTYPE_VARVOLT = "vt-varvolt"
SZR_VTYPE_CURR = "vt-curr"
SZR_VTYPE_SPECCURR = "vt-speccurr"
SZR_VTYPE_VARCURR = "vt-varcurr"
SZR_VTYPE_IX = "vt-ix"
SZR_VTYPE_STATE = "vt-state"
SZR_VTYPE_MODEL = "vt-model"
SZR_VTYPE_VER = "vt-ver"
SZR_VTYPE_MODE = "vt-mode"
SZR_VTYPE_RANGE = "vt-range"
#
SZR_RESP_OK_SUFFIX = "OK@"
SZR_LEN_RESP_OK_SUFFIX = len(SZR_RESP_OK_SUFFIX)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class Serializer(object):
	def __init__(self):
		self._modelSpecs = models_build_spec_dict()

	# --------------------------------------------------------------------------

	def set_hw_specs(self, hwSpecs):
		""" Set hardware specs

		Parameters:
			hwSpecs (dict)
		"""
		assert isinstance(hwSpecs, dict), "hwSpecs needs to be dict"
		#
		self._modelSpecs = deepcopy(hwSpecs)

	def round_value(self, valFloat, isVolt):
		""" Round a Voltage/Current value with respect to the hardware's capabilities

		Parameters:
			valFloat (float): Value to round
			isVolt (bool): If True use valFloat as Voltage value, else as Current value
		Returns:
			float
		"""
		assert self._modelSpecs is not None, "call set_hw_specs() first"
		assert isinstance(valFloat, (float, int)), "valFloat needs to be float or int"
		assert isVolt == True or isVolt == False, "isVolt needs to be bool"
		#
		precVC = self._modelSpecs["precVolt" if isVolt else "precCurr"]
		return round(float(valFloat), precVC)

	def unserialize_data(self, valStr, listValueTypes):
		""" Decode input from hardware

		Parameters:
			valStr (str)
			listValueTypes (list)
		Returns:
			list
		Raises:
			InvalidInputDataError
		"""
		assert isinstance(valStr, str), "valStr needs to be string"
		assert isinstance(listValueTypes, list), "listValueTypes needs to be list"
		#
		if not valStr.endswith(SZR_RESP_OK_SUFFIX):
			raise InvalidInputDataError(valStr)
		valStr = valStr[:-SZR_LEN_RESP_OK_SUFFIX]
		#
		if len(listValueTypes) == 0 and valStr != "":
			raise InvalidInputDataError(valStr)
		resA = []
		if len(listValueTypes) == 0:
			return resA
		hwSpecs = self._modelSpecs
		#
		#print("  __ SZR.ud inp='%s' __  " % (valStr), end="")
		for entryVt in listValueTypes:
			entryVtOrg = entryVt
			if len(valStr) == 0:
				raise InvalidInputDataError(valStr, entryVtOrg)
			#
			#print("  __ SZR.ud '%s'[%s] __  " % (valStr, entryVt), end="")
			if entryVt == SZR_VTYPE_VARVOLT or entryVt == SZR_VTYPE_VARCURR:
				targetType = (SZR_VTYPE_VOLT if entryVt == SZR_VTYPE_VARVOLT \
						else SZR_VTYPE_CURR)
				targetLen = self._get_serialized_data_len(targetType)
				pos = valStr.find(";")
				if pos < 1:
					raise InvalidInputDataError(valStr, entryVtOrg)
				if pos > hwSpecs["totalDigits"] + 1:
					raise InvalidInputDataError(valStr, entryVtOrg)
				valStr = "0" * (targetLen - pos) + valStr
				entryVt = targetType
			#
			substrLen = self._get_serialized_data_len(entryVt)
			if substrLen < 0:
				resA.append({"vtype": entryVtOrg, "val": valStr})
				valStr = ""
				break
			if len(valStr) < substrLen:
				raise InvalidInputDataError(valStr, entryVtOrg)
			sstr = valStr[0:substrLen]
			valStr = valStr[substrLen:]
			if entryVtOrg == SZR_VTYPE_VARVOLT or entryVtOrg == SZR_VTYPE_VARCURR:
				valStr = valStr[1:]
			if entryVt == SZR_VTYPE_VOLT or entryVt == SZR_VTYPE_CURR or \
					entryVt == SZR_VTYPE_SPECVOLT or entryVt == SZR_VTYPE_SPECCURR:
				isVolt = (entryVt == SZR_VTYPE_VOLT or entryVt == SZR_VTYPE_SPECVOLT)
				precVC = hwSpecs["precVolt" if isVolt else "precCurr"]
				if entryVt == SZR_VTYPE_SPECVOLT or entryVt == SZR_VTYPE_SPECCURR:
					precVC = 2
				#
				pattern = re.compile(r"^[0-9]+$")
				match = pattern.match(sstr)
				if not match:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resF = int(sstr) * pow(10, -precVC)
				resF = self.round_value(resF, isVolt)
				resA.append({"vtype": entryVtOrg, "val": resF})
			elif entryVt == SZR_VTYPE_IX:
				pattern = re.compile(r"^[0-9]$")
				match = pattern.match(sstr)
				if not match:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resI = int(sstr)
				if resI >= hwSpecs["virtMemPresetLocations"]:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resA.append({"vtype": entryVtOrg, "val": resI})
			elif entryVt == SZR_VTYPE_STATE:
				if sstr != hwSpecs["charStateOn"] and sstr != hwSpecs["charStateOff"]:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resB = (sstr == hwSpecs["charStateOn"])
				resA.append({"vtype": entryVtOrg, "val": resB})
			elif entryVt == SZR_VTYPE_MODE:
				if sstr != hwSpecs["charModeCv"] and sstr != hwSpecs["charModeCc"]:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resS = (SZR_OUTP_MODE_CV if sstr == hwSpecs["charModeCv"] else SZR_OUTP_MODE_CC)
				resA.append({"vtype": entryVtOrg, "val": resS})
			elif entryVt == SZR_VTYPE_RANGE:
				pattern = re.compile(r"^[0-9]$")
				match = pattern.match(sstr)
				if not match:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resI = int(sstr)
				if resI >= hwSpecs["ranges"]:
					raise InvalidInputDataError(sstr, entryVtOrg)
				resA.append({"vtype": entryVtOrg, "val": resI})
		if valStr != "" and valStr != ";" and valStr != "@":
			raise InvalidInputDataError(valStr)
		return resA

	def serialize_data(self, valArr, listValueTypes):
		""" Encode data for hardware

		Parameters:
			valArr (list)
			listValueTypes (list)
		Returns:
			str
		Raises:
			ValueError
		"""
		assert isinstance(valArr, list), "valArr needs to be list"
		assert isinstance(listValueTypes, list), "listValueTypes needs to be list"
		#
		if len(valArr) != len(listValueTypes):
			raise ValueError("len of valArr does not match listValueTypes")
		resS = ""
		entryIx = 0
		hwSpecs = self._modelSpecs
		#
		for entryVal in valArr:
			entryVt = listValueTypes[entryIx]
			entryIx += 1
			#
			substrLen = self._get_serialized_data_len(entryVt)
			#
			if entryVt == SZR_VTYPE_VOLT or entryVt == SZR_VTYPE_CURR or \
					entryVt == SZR_VTYPE_SPECVOLT or entryVt == SZR_VTYPE_SPECCURR or \
					entryVt == SZR_VTYPE_VARVOLT or entryVt == SZR_VTYPE_VARCURR:
				if not isinstance(entryVal, (int, float)):
					raise ValueError("value needs to be int or float for ValueType " + entryVt)
				isVolt = (entryVt == SZR_VTYPE_VOLT or entryVt == SZR_VTYPE_SPECVOLT or entryVt == SZR_VTYPE_VARVOLT)
				self._validate_output_value(entryVal, isVolt)
				entryVal = self.round_value(entryVal, isVolt)
			#
			if entryVt == SZR_VTYPE_VARVOLT or entryVt == SZR_VTYPE_VARCURR:
				isVolt = (entryVt == SZR_VTYPE_VARVOLT)
				precVC = hwSpecs["precVolt" if isVolt else "precCurr"]
				# e.g. 1.2V --> "12"
				tmpF = float(entryVal * pow(10.0, precVC))
				tmpS = str(int(round(tmpF, 0)))
				resS += tmpS + ";"
			elif entryVt == SZR_VTYPE_VOLT or entryVt == SZR_VTYPE_CURR:
				isVolt = (entryVt == SZR_VTYPE_VOLT)
				precVC = hwSpecs["precVolt" if isVolt else "precCurr"]
				# e.g. 1.2V --> "012"
				tmpF = float(entryVal * pow(10.0, precVC))
				tmpS = str(int(round(tmpF, 0)))
				resS += ("0" * (substrLen - len(tmpS))) + tmpS
			elif entryVt == SZR_VTYPE_SPECVOLT or entryVt == SZR_VTYPE_SPECCURR:
				# e.g. 1.2V --> "0120", 0.2V --> "0020"
				if entryVal != 0.0:
					tmpF = float(entryVal * pow(10.0, 2))
					tmpS = str(int(round(tmpF, 0)))
				else:
					tmpS = "00"
				tmpS = ("0" * (substrLen - len(tmpS))) + tmpS
				resS += tmpS
			elif entryVt == SZR_VTYPE_IX:
				if not isinstance(entryVal, int):
					raise ValueError("value needs to be int for ValueType " + entryVt)
				if entryVal < 0 or entryVal >= hwSpecs["virtMemPresetLocations"]:
					raise ValueError("value needs to >=0 and <%d for ValueType %s" % \
							(hwSpecs["virtMemPresetLocations"], entryVt))
				resS += str(entryVal)
			elif entryVt == SZR_VTYPE_STATE:
				if not isinstance(entryVal, bool):
					raise ValueError("value needs to be bool for ValueType " + entryVt)
				resS += (hwSpecs["charStateOn"] if entryVal else hwSpecs["charStateOff"])
			elif entryVt == SZR_VTYPE_MODE:
				if not isinstance(entryVal, str):
					raise ValueError("value needs to be string for ValueType " + entryVt)
				if entryVal != SZR_OUTP_MODE_CV and entryVal != SZR_OUTP_MODE_CC:
					raise ValueError("value needs to be '%s' or '%s' for ValueType %s" % \
							(SZR_OUTP_MODE_CV, SZR_OUTP_MODE_CC, entryVt))
				resS += (hwSpecs["charModeCv"] if entryVal == SZR_OUTP_MODE_CV else hwSpecs["charModeCc"])
			elif entryVt == SZR_VTYPE_MODEL or entryVt == SZR_VTYPE_VER:
				if not isinstance(entryVal, str):
					raise ValueError("value needs to be string for ValueType " + entryVt)
				if len(entryVal) == 0:
					raise ValueError("value may not be empty for ValueType " + entryVt)
				resS += entryVal
			elif entryVt == SZR_VTYPE_RANGE:
				if not isinstance(entryVal, int):
					raise ValueError("value needs to be int for ValueType " + entryVt)
				if entryVal < 0 or entryVal >= hwSpecs["ranges"]:
					raise ValueError("value needs to >=0 and <%d for ValueType %s" % \
							(hwSpecs["ranges"], entryVt))
				resS += str(entryVal)
			else:
				raise ValueError("invalid valueType '%s'" % entryVt)
		return resS

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _validate_output_value(self, valFloat, isVolt):
		""" Validate output value for Voltage/Current

		Parameters:
			valFloat (float)
			isVolt (bool)
		Raises:
			ValueError
		"""
		assert isinstance(valFloat, (int, float)), "valFloat needs to be int or float"
		assert isVolt == True or isVolt == False, "isVolt needs to be bool"
		#
		valFloat = self.round_value(valFloat, isVolt)
		#
		valUnit = "V" if isVolt else "A"
		valName = "voltage" if isVolt else "current"
		#
		tmpMinMax = self._modelSpecs
		keyMin = ("minVolt" if isVolt else "minCurr")
		keyMax = ("maxVolt" if isVolt else "maxCurr")
		if valFloat < tmpMinMax[keyMin]:
			raise ValueError("{0:s} is out of range (min={1:.2f}{2:s})".format(
						valName, tmpMinMax[keyMin], valUnit
					))
		if valFloat > tmpMinMax[keyMax]:
			raise ValueError("{0:s} is out of range (max={1:.2f}{2:s})".format(
						valName, tmpMinMax[keyMax], valUnit
					))

	def _get_serialized_data_len(self, valueType):
		""" Get length of serialied data

		Parameters:
			valueType (str)
		Returns:
			int
		Raises:
			ValueError
		"""
		substrLen = 0
		hwSpecs = self._modelSpecs
		if valueType == SZR_VTYPE_VOLT or valueType == SZR_VTYPE_CURR:
			substrLen = hwSpecs["totalDigits"]
		elif valueType == SZR_VTYPE_SPECVOLT or valueType == SZR_VTYPE_SPECCURR:
			substrLen = 4
		elif valueType == SZR_VTYPE_IX or valueType == SZR_VTYPE_STATE or \
				valueType == SZR_VTYPE_MODE or valueType == SZR_VTYPE_RANGE:
			substrLen = 1
		elif valueType == SZR_VTYPE_MODEL or valueType == SZR_VTYPE_VER or \
				valueType == SZR_VTYPE_VARVOLT or valueType == SZR_VTYPE_VARCURR:
			substrLen = -1
		else:
			raise ValueError("invalid valueType '%s'" % valueType)
		#print(" ## SZR:gsdl vT='%s', l=%d ## " % (valueType, substrLen))
		return substrLen
