#
# by TS, Dec 2020
#

from copy import deepcopy
import re

try:
	from .mi_commands import *
	from .exceptions import InvalidModelError
	from .exceptions import UnsupportedModelError
except (ModuleNotFoundError, ImportError):
	from mi_commands import *
	from exceptions import InvalidModelError
	from exceptions import UnsupportedModelError

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# HW Model IDs

# HCS Series
##
MODEL_ID_HCS3100 = "HCS-3100"  # 1-18V 0-10A
MODEL_ID_HCS3102 = "HCS-3102"  # 1-36V 0-5A
MODEL_ID_HCS3104 = "HCS-3104"  # 1-60V 0-2.5A
MODEL_ID_HCS3150 = "HCS-3150"  # 1-18V 0-15A
##
MODEL_ID_HCS3200 = "HCS-3200"  # 1-18V 0-20A (a.k.a B&K Precision 1688B)
MODEL_ID_HCS3202 = "HCS-3202"  # 1-36V 0-10A (a.k.a B&K Precision 1687B)
MODEL_ID_HCS3204 = "HCS-3204"  # 1-60V 0-5A (a.k.a B&K Precision 1685B)
##
MODEL_ID_HCS3300 = "HCS-3300"  # 1-16V 0-30A
MODEL_ID_HCS3302 = "HCS-3302"  # 1-32V 0-15A
MODEL_ID_HCS3304 = "HCS-3304"  # 1-60V 0-8A
##
MODEL_ID_HCS3400 = "HCS-3400"  # 1-16V 0-40A (a.k.a Peaktech 1565)
MODEL_ID_HCS3402 = "HCS-3402"  # 1-32V 0-20A (a.k.a Peaktech 1575)
MODEL_ID_HCS3404 = "HCS-3404"  # 1-60V 0-10A
##
MODEL_ID_HCS3600 = "HCS-3600"  # 1-16V 0-60A (a.k.a B&K Precision 1900B, Peaktech 1570)
MODEL_ID_HCS3602 = "HCS-3602"  # 1-32V 0-30A (a.k.a B&K Precision 1901B, Peaktech 1580)
MODEL_ID_HCS3604 = "HCS-3604"  # 1-60V 0-15A (a.k.a B&K Precision 1902B, Peaktech 1585)

MODEL_LIST_HCS31XX = [MODEL_ID_HCS3100, MODEL_ID_HCS3102, MODEL_ID_HCS3104, MODEL_ID_HCS3150]
MODEL_LIST_HCS32XX = [MODEL_ID_HCS3200, MODEL_ID_HCS3202, MODEL_ID_HCS3204]
MODEL_LIST_HCS33XX = [MODEL_ID_HCS3300, MODEL_ID_HCS3302, MODEL_ID_HCS3304]
MODEL_LIST_HCS34XX = [MODEL_ID_HCS3400, MODEL_ID_HCS3402, MODEL_ID_HCS3404]
MODEL_LIST_HCS36XX = [MODEL_ID_HCS3600, MODEL_ID_HCS3602, MODEL_ID_HCS3604]

MODEL_LIST_SERIES_HCS = []
MODEL_LIST_SERIES_HCS += MODEL_LIST_HCS31XX
MODEL_LIST_SERIES_HCS += MODEL_LIST_HCS32XX
MODEL_LIST_SERIES_HCS += MODEL_LIST_HCS33XX
MODEL_LIST_SERIES_HCS += MODEL_LIST_HCS34XX
MODEL_LIST_SERIES_HCS += MODEL_LIST_HCS36XX

MODEL_SERIES_ID_HCS = "HCS"

# NTP Series
##
MODEL_ID_NTP6521 = "NTP-6521"  # 1-20V 0.25-5A  (a.k.a Multicomp MP710079)
MODEL_ID_NTP6531 = "NTP-6531"  # 1-36V 0.25-3A  (a.k.a Multicomp MP710080)
MODEL_ID_NTP6561 = "NTP-6561"  # 1-60V 0.25-1.6A  (a.k.a Multicomp MP710081)
##
MODEL_ID_NTP6621 = "NTP-6621"  # 1-20V 0.25-5A
MODEL_ID_NTP6631 = "NTP-6631"  # 1-36V 0.25-3A
MODEL_ID_NTP6661 = "NTP-6661"  # 1-60V 0.25-1.6A
##
MODEL_LIST_NTP65XX = [MODEL_ID_NTP6521, MODEL_ID_NTP6531, MODEL_ID_NTP6561]
MODEL_LIST_NTP66XX = [MODEL_ID_NTP6621, MODEL_ID_NTP6631, MODEL_ID_NTP6661]

MODEL_LIST_SERIES_NTP = []
MODEL_LIST_SERIES_NTP += MODEL_LIST_NTP65XX
MODEL_LIST_SERIES_NTP += MODEL_LIST_NTP66XX

MODEL_SERIES_ID_NTP = "NTP"

# SSP Series
##
MODEL_ID_SSP8080 = "SSP-8080"  # 0-16V 0-5A (not produced anymore)
##
MODEL_ID_SSP8160 = "SSP-8160"  # 0-42V 0-10A
MODEL_ID_SSP8162 = "SSP-8162"  # 0-84V 0-5A
##
MODEL_ID_SSP8320 = "SSP-8320"  # 0-42V 0-20A
MODEL_ID_SSP8322 = "SSP-8322"  # 0-84V 0-10A
##
MODEL_ID_SSP9081 = "SSP-9081"  # 0.5-36V 0-5A  (a.k.a Multicomp MP710083)

MODEL_LIST_SSP80XX = [MODEL_ID_SSP8080]
MODEL_LIST_SSP81XX = [MODEL_ID_SSP8160, MODEL_ID_SSP8162]
MODEL_LIST_SSP83XX = [MODEL_ID_SSP8320, MODEL_ID_SSP8322]
MODEL_LIST_SSP90XX = [MODEL_ID_SSP9081]

MODEL_LIST_SERIES_SSP = []
MODEL_LIST_SERIES_SSP += MODEL_LIST_SSP80XX
MODEL_LIST_SERIES_SSP += MODEL_LIST_SSP81XX
MODEL_LIST_SERIES_SSP += MODEL_LIST_SSP83XX
MODEL_LIST_SERIES_SSP += MODEL_LIST_SSP90XX

MODEL_SERIES_ID_SSP = "SSP"

MODEL_SUBSERIES_ID_SSP80 = "SSP80"
MODEL_SUBSERIES_ID_SSP81 = "SSP81"
MODEL_SUBSERIES_ID_SSP83 = "SSP83"
MODEL_SUBSERIES_ID_SSP90 = "SSP90"

# ------------------------------------------------------------------------------

MODEL_LIST_SERIES_ALL = []
MODEL_LIST_SERIES_ALL += MODEL_LIST_SERIES_HCS
MODEL_LIST_SERIES_ALL += MODEL_LIST_SERIES_NTP
MODEL_LIST_SERIES_ALL += MODEL_LIST_SERIES_SSP

# ------------------------------------------------------------------------------

TEST_MODEL_LIST = []
TEST_MODEL_LIST.append(MODEL_ID_HCS3100)  # precV=1, precC=1
TEST_MODEL_LIST.append(MODEL_ID_HCS3102)  # precV=1, precC=2
TEST_MODEL_LIST.append(MODEL_ID_HCS3404 + "-USB")  # precV=1, precC=1
TEST_MODEL_LIST.append(MODEL_ID_NTP6521)  # precV=2, precC=3
TEST_MODEL_LIST.append(MODEL_ID_NTP6661.replace("NTP-", ""))  # precV=2, precC=3
TEST_MODEL_LIST.append(MODEL_ID_SSP8080)  # precV=2, precC=3
TEST_MODEL_LIST.append(MODEL_ID_SSP8160)  # precV=2, precC=2
TEST_MODEL_LIST.append(MODEL_ID_SSP8320)  # precV=2, precC=2
TEST_MODEL_LIST.append(MODEL_ID_SSP9081)  # precV=2, precC=3

# ------------------------------------------------------------------------------

def get_hw_model_id(modelId):
	""" Get valid HW Model ID

	Parameters:
		modelId (str): e.g. '3202'
	Returns:
		str: HW Model ID, e.g. MODEL_ID_HCS3202
	Raises:
		UnsupportedModelError
		InvalidModelError
	"""
	assert isinstance(modelId, str), "modelId needs to be str"
	#
	if modelId in MODEL_LIST_SERIES_ALL:
		return modelId
	#
	modelIdOrg = modelId
	if modelId.endswith("-USB") or modelId.endswith(" USB") or modelId.endswith("_USB"):
		modelId = modelId[:-4]
	elif modelId.endswith("USB"):
		modelId = modelId[:-3]
	# e.g. "HCS-3202":
	pattern = re.compile(r"^[A-Z]{3}-\d{4}$")
	match = pattern.match(modelId)
	if match:
		resS = match.group()
		if not resS in MODEL_LIST_SERIES_ALL:
			raise UnsupportedModelError(resS)
		return resS
	# e.g. "3202":
	pattern = re.compile(r"^\d{4}$")
	match = pattern.match(modelId)
	if match:
		resS = match.group()
		resS = "-" + resS
		#if not any(resS in s for s in  MODEL_LIST_SERIES_ALL):
		#	raise UnsupportedModelError(modelId)
		matching = [s for s in MODEL_LIST_SERIES_ALL if resS in s]
		if len(matching) != 1:
			raise UnsupportedModelError(modelId)
		resS = matching[0]
		return resS
	#
	raise InvalidModelError(modelIdOrg)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# HW Model Specs

MODEL_SPECS = {}

def get_hw_specs(modelId):
	""" Get HW Specifications

	Parameters:
		modelId (str): e.g. '3202' or MODEL_ID_HCS3202
	Returns:
		dict
	"""
	assert isinstance(modelId, str), "modelId needs to be str"
	#
	modelId = get_hw_model_id(modelId)
	return deepcopy(MODEL_SPECS[modelId])

def build_spec_dict(mnv=0.0, mxv=0.0, mnc=0.0, mxc=0.0, pv=0, pc=0, virtMpl=0, realMpl=0, td=0, charStateOn="", charStateOff="", rg=0, modelSeries="", modelSubSeries=""):
	""" Build HW Specifications dictionary

	Returns:
		dict
	"""
	return {
			"minVolt": mnv,  # e.g. 1.0
			"maxVolt": mxv,  # e.g. 16.0
			"minCurr": mnc,  # e.g. 0.25
			"maxCurr": mxc,  # e.g. 40.0
			"precVolt": pv,  # decimal digits for Volt values, e.g. 2 ^= values will have the format [x]x.yy
			"precCurr": pc,  # decimal digits for Current values, e.g. 3 ^= values will have the format [x]x.yyy
			"virtMemPresetLocations": virtMpl,  # virtual memory preset locations, e.g. 4
			"realMemPresetLocations": realMpl,  # real memory preset locations, e.g. 3
			"totalDigits": td,  # total amount of digits that Volt/Current values can have, e.g. 4 ^= values will have the format x.yyy or xx.yy or xxx.y
			"charStateOn": charStateOn,  # char that represents the output enable state "on"
			"charStateOff": charStateOff,  # char that represents the output enable state "off"
			"charModeCv": "0",  # char that represents the mode "CV"
			"charModeCc": "1",  # char that represents the mode "CC"
			"ranges": rg,  # amount of available Voltage/Current ranges
			"modelSeries": modelSeries,
			"modelSubSeries": modelSubSeries,
			"hwCmdSupp": _build_hwcmdsupp_dict_for_model(modelSeries, modelSubSeries)
		}

def _build_hwcmdsupp_dict_for_model(modelSeries, modelSubSeries):
	""" Build HW Command Support dictionary

	Returns:
		dict
	"""
	resD = {
			MICMD_GMOD: True,
			MICMD_GVER: True,
			MICMD_GOUT: True,
			MICMD_SOUT: True,
			MICMD_ENDS: (modelSeries == MODEL_SERIES_ID_HCS or modelSeries == MODEL_SERIES_ID_SSP),
			MICMD_SESS: False,
			MICMD_VOLT: (modelSubSeries != MODEL_SUBSERIES_ID_SSP80),
			MICMD_CURR: False,
			MICMD_GETD: True,
			MICMD_GETS: True,
			MICMD_GMIN: (modelSeries == MODEL_SERIES_ID_NTP),
			MICMD_GMAX: (modelSeries == MODEL_SERIES_ID_HCS or modelSeries == MODEL_SERIES_ID_NTP),
			MICMD_GETM: (modelSeries == MODEL_SERIES_ID_HCS),
			MICMD_PROM: False,
			MICMD_RUNM: False,
			MICMD_SABC: (modelSeries == MODEL_SERIES_ID_SSP),
			MICMD_GABC: False,
			MICMD_SOVP: (modelSeries == MODEL_SERIES_ID_SSP),
			MICMD_SOCP: False,
			MICMD_GOVP: False,
			MICMD_GOCP: False,
			MICMD_SVSH: (modelSeries == MODEL_SERIES_ID_NTP),
			MICMD_SISH: False,
			MICMD_GVSH: False,
			MICMD_GISH: False,
			MICMD_SETD: (modelSeries == MODEL_SERIES_ID_SSP or modelSeries == MODEL_SERIES_ID_NTP),
			MICMD_GCHA: (modelSubSeries == MODEL_SUBSERIES_ID_SSP80),
			MICMD_SCHA: False
		}
	#
	resD[MICMD_SESS] = resD[MICMD_ENDS]
	#
	resD[MICMD_CURR] = resD[MICMD_VOLT]
	#
	resD[MICMD_PROM] = resD[MICMD_GETM]
	resD[MICMD_RUNM] = resD[MICMD_GETM]
	#
	resD[MICMD_GABC] = resD[MICMD_SABC]
	#
	resD[MICMD_SOCP] = resD[MICMD_SOVP]
	resD[MICMD_GOVP] = resD[MICMD_SOVP]
	resD[MICMD_GOCP] = resD[MICMD_SOVP]
	#
	resD[MICMD_SISH] = resD[MICMD_SVSH]
	resD[MICMD_GVSH] = resD[MICMD_SVSH]
	resD[MICMD_GISH] = resD[MICMD_SVSH]
	#
	resD[MICMD_SCHA] = resD[MICMD_GCHA]
	#
	return resD

def _add_specs(id, mnv, mxv, mnc, mxc):
	global MODEL_SPECS

	tmpPrecV = 0
	tmpPrecC = 0
	tmpVirtMpl = 0
	tmpRealMpl = 0
	tmpTotDigits = 0
	tmpCharStateOn = ""
	tmpCharStateOff = ""
	tmpRanges = 0
	tmpModelSeries = ""
	tmpModelSubSeries = ""
	#
	if id in MODEL_LIST_SERIES_HCS:
		tmpModelSeries = MODEL_SERIES_ID_HCS
	elif id in MODEL_LIST_SERIES_NTP:
		tmpModelSeries = MODEL_SERIES_ID_NTP
	elif id in MODEL_LIST_SERIES_SSP:
		tmpModelSeries = MODEL_SERIES_ID_SSP
		if id in MODEL_LIST_SSP80XX:
			tmpModelSubSeries = MODEL_SUBSERIES_ID_SSP80
		elif id in MODEL_LIST_SSP81XX:
			tmpModelSubSeries = MODEL_SUBSERIES_ID_SSP81
		elif id in MODEL_LIST_SSP83XX:
			tmpModelSubSeries = MODEL_SUBSERIES_ID_SSP83
		elif id in MODEL_LIST_SSP90XX:
			tmpModelSubSeries = MODEL_SUBSERIES_ID_SSP90
	#
	if id in [MODEL_ID_HCS3100, MODEL_ID_HCS3150, MODEL_ID_HCS3200, MODEL_ID_HCS3202] or \
			id in MODEL_LIST_HCS33XX or \
			id in MODEL_LIST_HCS34XX or \
			id in MODEL_LIST_HCS36XX:
		tmpPrecV = 1
		tmpPrecC = 1
	elif id in [MODEL_ID_HCS3102, MODEL_ID_HCS3104, MODEL_ID_HCS3204]:
		tmpPrecV = 1
		tmpPrecC = 2
	elif tmpModelSeries == MODEL_SERIES_ID_NTP:
		tmpPrecV = 2
		tmpPrecC = 3
	elif tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP80 or \
			tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP90:
		tmpPrecV = 2
		tmpPrecC = 3
	elif tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP81 or \
			tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP83:
		tmpPrecV = 2
		tmpPrecC = 2
	#
	if tmpModelSeries == MODEL_SERIES_ID_HCS or \
			tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP80:
		tmpVirtMpl = 3
		tmpRealMpl = 3
	elif tmpModelSeries == MODEL_SERIES_ID_NTP:
		tmpVirtMpl = 0
	elif tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP81 or \
			tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP83 or \
			tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP90:
		tmpVirtMpl = 4
		tmpRealMpl = 3
	#
	if tmpModelSeries == MODEL_SERIES_ID_HCS:
		tmpTotDigits = 3
	else:
		tmpTotDigits = 4
	#
	if tmpModelSeries == MODEL_SERIES_ID_HCS:
		tmpCharStateOn = "0"
		tmpCharStateOff = "1"
	else:
		tmpCharStateOn = "1"
		tmpCharStateOff = "0"
	#
	if tmpModelSubSeries == MODEL_SUBSERIES_ID_SSP80:
		tmpRanges = 3
	#
	MODEL_SPECS[id] = build_spec_dict(mnv, mxv, mnc, mxc,
			tmpPrecV, tmpPrecC,
			tmpVirtMpl, tmpRealMpl,
			tmpTotDigits,
			tmpCharStateOn, tmpCharStateOff,
			tmpRanges,
			tmpModelSeries, tmpModelSubSeries)

# HCS Series
##
_add_specs(MODEL_ID_HCS3100, 1.0, 18.0, 0.0, 10.0)
_add_specs(MODEL_ID_HCS3102, 1.0, 36.0, 0.0, 5.0)
_add_specs(MODEL_ID_HCS3104, 1.0, 60.0, 0.0, 2.5)
_add_specs(MODEL_ID_HCS3150, 1.0, 18.0, 0.0, 15.0)
##
_add_specs(MODEL_ID_HCS3200, 1.0, 18.0, 0.0, 20.0)
_add_specs(MODEL_ID_HCS3202, 1.0, 36.0, 0.0, 10.0)
_add_specs(MODEL_ID_HCS3204, 1.0, 60.0, 0.0, 5.0)
##
_add_specs(MODEL_ID_HCS3300, 1.0, 16.0, 0.0, 30.0)
_add_specs(MODEL_ID_HCS3302, 1.0, 32.0, 0.0, 15.0)
_add_specs(MODEL_ID_HCS3304, 1.0, 60.0, 0.0, 8.0)
##
_add_specs(MODEL_ID_HCS3400, 1.0, 16.0, 0.0, 40.0)
_add_specs(MODEL_ID_HCS3402, 1.0, 32.0, 0.0, 20.0)
_add_specs(MODEL_ID_HCS3404, 1.0, 60.0, 0.0, 10.0)
##
_add_specs(MODEL_ID_HCS3600, 1.0, 16.0, 0.0, 60.0)
_add_specs(MODEL_ID_HCS3602, 1.0, 32.0, 0.0, 30.0)
_add_specs(MODEL_ID_HCS3604, 1.0, 60.0, 0.0, 15.0)

# NTP Series
##
_add_specs(MODEL_ID_NTP6521, 1.0, 20.0, 0.25, 5.0)
_add_specs(MODEL_ID_NTP6531, 1.0, 36.0, 0.25, 3.0)
_add_specs(MODEL_ID_NTP6561, 1.0, 60.0, 0.25, 1.6)
##
_add_specs(MODEL_ID_NTP6621, 1.0, 20.0, 0.25, 5.0)
_add_specs(MODEL_ID_NTP6631, 1.0, 36.0, 0.25, 3.0)
_add_specs(MODEL_ID_NTP6661, 1.0, 60.0, 0.25, 1.6)

# SSP Series
##
_add_specs(MODEL_ID_SSP8080, 0.0, 16.0, 0.0, 5.0)
##
_add_specs(MODEL_ID_SSP8160, 0.0, 42.0, 0.0, 10.0)
_add_specs(MODEL_ID_SSP8162, 0.0, 84.0, 0.0, 5.0)
##
_add_specs(MODEL_ID_SSP8320, 0.0, 42.0, 0.0, 20.0)
_add_specs(MODEL_ID_SSP8322, 0.0, 84.0, 0.0, 10.0)
##
_add_specs(MODEL_ID_SSP9081, 0.5, 36.0, 0.0, 5.0)
