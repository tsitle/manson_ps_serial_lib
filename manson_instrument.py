#
# by TS, Dec 2020
#

from copy import deepcopy
from serial import Serial as pyser_Serial
from serial.serialutil import SerialException as pyser_SerialException
import time

try:
	from .mi_commands import *
	from .emulated_instrument_serial import EmulatedInstrumentSerial
	from .exceptions import CouldNotConnectError, \
			FunctionNotSupportedForModelError, InvalidModelError, \
			InvalidResponseError, NotConnectedError, UnsupportedModelError
	from .models import build_spec_dict as models_build_spec_dict, \
			get_hw_model_id as models_get_hw_model_id, \
			get_hw_specs as models_get_hw_specs, \
			MODEL_SERIES_ID_HCS, MODEL_SERIES_ID_NTP, MODEL_SERIES_ID_SSP, \
			MODEL_SUBSERIES_ID_SSP80, MODEL_SUBSERIES_ID_SSP81, MODEL_SUBSERIES_ID_SSP83, MODEL_SUBSERIES_ID_SSP90
	from .serializer import *
except (ModuleNotFoundError, ImportError):
	from mi_commands import *
	from emulated_instrument_serial import EmulatedInstrumentSerial
	from exceptions import CouldNotConnectError, \
			FunctionNotSupportedForModelError, InvalidModelError, \
			InvalidResponseError, NotConnectedError, UnsupportedModelError
	from models import build_spec_dict as models_build_spec_dict, \
			get_hw_model_id as models_get_hw_model_id, \
			get_hw_specs as models_get_hw_specs, \
			MODEL_SERIES_ID_HCS, MODEL_SERIES_ID_NTP, MODEL_SERIES_ID_SSP, \
			MODEL_SUBSERIES_ID_SSP80, MODEL_SUBSERIES_ID_SSP81, MODEL_SUBSERIES_ID_SSP83, MODEL_SUBSERIES_ID_SSP90
	from serializer import *

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

VIRTUAL_SERIAL_DEVICE = "VirtualComPort"

# Ranges for SSP-80XX Series only
RANGE_ID_0_16V0_5A0 = "0"
RANGE_ID_1_27V0_3A0 = "1"
RANGE_ID_2_36V0_2A2 = "2"

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class MansonInstrument(object):
	_BAUDRATE = 9600

	def __init__(self):
		self._pyserObj = None
		self._modelId = None
		self._modelVers = None
		self._modelSpecs = None
		self._modelSeries = None
		self._modelSubSeries = None
		self._modelHwCmdSupp = None
		self._hwMin = None
		self._hwMax = None
		self._memPresets = None
		self._enableMemPresetsCache = False
		self._szrObj = Serializer()
		self._isEmulated = False

	# --------------------------------------------------------------------------

	def open_port(self, comPort, emulateModel=None):
		""" Init serial connection

		Parameters:
			comPort (str): Serial device (e.g. "/dev/tty.SLAB_USBtoUART")
			emulateModel (str|None): optional Model ID for hardware emulation
		Raises:
			CouldNotConnectError
		"""
		assert isinstance(comPort, str), "comPort needs to be string"
		assert comPort != VIRTUAL_SERIAL_DEVICE or emulateModel is not None, "for VIRTUAL_SERIAL_DEVICE emulateModel needs to be != None"
		#
		haveSerialErr = False
		try:
			if comPort != VIRTUAL_SERIAL_DEVICE:
				self._pyserObj = pyser_Serial(comPort, baudrate=self._BAUDRATE, bytesize=8, parity="N", stopbits=1, timeout=0.1)
				self._enableMemPresetsCache = True
			else:
				self._pyserObj = EmulatedInstrumentSerial(emulateModel)
				self._isEmulated = True
			self._pyserObj.flushInput()
			self._pyserObj.flushOutput()
		except pyser_SerialException:
			haveSerialErr = True
		if haveSerialErr:
			raise CouldNotConnectError("comPort='%s', baud=%d" % (comPort, self._BAUDRATE))
		#
		self.get_hw_model()
		self.get_hw_specs()
		self._szrObj.set_hw_specs(self._modelSpecs)
		if comPort == VIRTUAL_SERIAL_DEVICE:
			self._pyserObj.update_model_id(self._modelId)

	def close_port(self):
		""" Close serial connection """
		if self._pyserObj is None:
			return
		self._pyserObj.close()
		self._pyserObj = None

	def round_value(self, valFloat, isVolt):
		""" Round a Voltage/Current value with respect to the hardware's capabilities

		Parameters:
			valFloat (float): Value to round
			isVolt (bool): If True use valFloat as Voltage value, else as Current value
		Returns:
			float
		Raises:
			NotConnectedError
		"""
		if self._pyserObj is None:
			raise NotConnectedError()
		return self._szrObj.round_value(valFloat, isVolt)

	def get_hw_specs(self, modelId=""):
		""" Get min/max values for Voltage and Current
		and precision of Voltage/Current values
		as defined in Specifications

		Parameters:
			modelId (str): Optional Model ID
		Returns:
			dict: {"minVolt": float, "maxVolt": float, "minCurr": float, "maxCurr": float, "precVolt": int, "precCurr": int}
		"""
		assert modelId is None or isinstance(modelId, str), "modelId needs to be string or None"
		#
		modelIdOrg = modelId
		if modelId == "" or modelId is None:
			if self._modelSpecs is not None:
				return deepcopy(self._modelSpecs)
			modelId = self._modelId
		#
		hwSpecs = models_build_spec_dict()
		if modelId is not None:
			try:
				hwSpecs = models_get_hw_specs(modelId)
			except (InvalidModelError, UnsupportedModelError):
				pass
		if modelIdOrg == "" or modelIdOrg is None:
			self._modelSpecs = deepcopy(hwSpecs)
			self._modelSeries = self._modelSpecs["modelSeries"]
			self._modelSubSeries = self._modelSpecs["modelSubSeries"]
			self._modelHwCmdSupp = deepcopy(self._modelSpecs["hwCmdSupp"])
		return deepcopy(hwSpecs)

	# --------------------------------------------------------------------------
	# All Series

	def get_hw_model(self):
		""" Get hardware model

		Returns:
			str
		"""
		if self._modelId is not None:
			return self._modelId
		response = self._lowlev_send_get_cmd(MICMD_GMOD)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_MODEL])
		if tmpUd[0]["val"].endswith("@"):
			tmpUd[0]["val"] = tmpUd[0]["val"][:-1]
		resS = models_get_hw_model_id(tmpUd[0]["val"])
		self._modelId = resS
		return resS

	def get_hw_version(self):
		""" Get hardware version

		Returns:
			str
		"""
		if self._modelVers is not None:
			return self._modelVers
		response = self._lowlev_send_get_cmd(MICMD_GVER)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_VER])
		tmpVer = tmpUd[0]["val"]
		if tmpVer.endswith("@"):
			tmpVer = tmpVer[:-1]
		self._modelVers = tmpVer
		return tmpVer

	def get_output_voltage(self):
		""" Get PS display value of Voltage

		Returns:
			float
		"""
		tmpD = self._get_output_volt_curr_mode()
		return tmpD["volt"]

	def get_output_current(self):
		""" Get PS display value of Current

		Returns:
			float
		"""
		tmpD = self._get_output_volt_curr_mode()
		return tmpD["curr"]

	def get_is_output_mode_cv(self):
		""" Is PS in Constant Voltage mode?

		Returns:
			bool
		"""
		tmpD = self._get_output_volt_curr_mode()
		return (tmpD["mode"] == SZR_OUTP_MODE_CV)

	def get_is_output_mode_cc(self):
		""" Is PS in Constant Current mode?

		Returns:
			bool
		"""
		tmpD = self._get_output_volt_curr_mode()
		return (tmpD["mode"] == SZR_OUTP_MODE_CC)

	def get_output_state(self):
		""" Get whether output of PS is on/off

		Returns:
			bool: True if on, False if off
		"""
		response = self._lowlev_send_get_cmd(MICMD_GOUT)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_STATE])
		tmpState = tmpUd[0]["val"]
		return tmpState

	def set_output_state(self, state):
		""" Switch the output of PS on/off

		Parameters:
			state (bool): If True switch output on, else off
		"""
		assert state == True or state == False, "state needs to be bool"
		#
		cmd = MICMD_SOUT
		self._check_hwCmdSupp(cmd)
		#
		cargs = self._szrObj.serialize_data([state], [SZR_VTYPE_STATE])
		self._lowlev_send_set_cmd(cmd, cargs)

	# --------------------------------------------------------------------------
	# All Series but HCS Series

	def get_overvoltage_protection_value(self):
		""" Get Overvoltage Protection Value from PS

		Returns:
			float
		"""
		cmd = ""
		if self._modelSeries == MODEL_SERIES_ID_NTP:
			cmd = MICMD_GVSH
		else:
			cmd = MICMD_GOVP
		response = self._lowlev_send_get_cmd(cmd)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_VOLT])
		tmpV = tmpUd[0]["val"]
		return tmpV

	def set_overvoltage_protection_value(self, volt):
		""" Set Overvoltage Protection Value of PS

		Parameters:
			volt (float): Voltage value
		"""
		cmdAndCargs = self._get_cmd_set_ovp_or_ocp(volt, "volt", isVolt=True)
		self._lowlev_send_set_cmd(cmdAndCargs["cmd"], cmdAndCargs["cargs"])

	def get_overcurrent_protection_value(self):
		""" Get Overcurrent Protection Value from PS

		Returns:
			float
		"""
		cmd = ""
		if self._modelSeries == MODEL_SERIES_ID_NTP:
			cmd = MICMD_GISH
		else:
			cmd = MICMD_GOCP
		response = self._lowlev_send_get_cmd(cmd)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_CURR])
		tmpC = tmpUd[0]["val"]
		return tmpC

	def set_overcurrent_protection_value(self, curr):
		""" Set Overcurrent Protection Value of PS

		Parameters:
			curr (float): Current value
		"""
		cmdAndCargs = self._get_cmd_set_ovp_or_ocp(curr, "curr", isVolt=False)
		self._lowlev_send_set_cmd(cmdAndCargs["cmd"], cmdAndCargs["cargs"])

	# --------------------------------------------------------------------------
	# All Series but NTP Series

	def set_userinput_allowed(self, state):
		""" Allow/Disallow user input via knobs and buttons on hardware of PS

		Parameters:
			state (bool): If True allow user input, else disallow
		"""
		assert state == True or state == False, "state needs to be bool"
		#
		self._lowlev_send_set_cmd(MICMD_ENDS if state else MICMD_SESS, "")

	def load_memory_preset(self, index):
		""" Load saved Voltage and Current values from PS memory locations

		Parameters:
			index (int): Index of memory location to load
		Returns:
			dict: {"volt": value, "curr": value}
		"""
		assert isinstance(index, int), "index needs to be int"
		hwSpecs = self.get_hw_specs()
		assert index >= 0 and index < hwSpecs["realMemPresetLocations"], "index out of range (0..%d)" % (hwSpecs["realMemPresetLocations"] - 1)
		#
		tmpA = self._load_all_memory_presets()
		return tmpA[index]

	def apply_memory_preset(self, index):
		""" Apply saved Voltage and Current values from PS memory locations

		Parameters:
			index (int): Index of memory location to apply
		"""
		assert isinstance(index, int), "index needs to be int"
		hwSpecs = self.get_hw_specs()
		assert index >= 0 and index < hwSpecs["realMemPresetLocations"], "index out of range (0..%d)" % (hwSpecs["realMemPresetLocations"] - 1)
		#
		if self._modelSeries == MODEL_SERIES_ID_SSP:
			if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
				index += 1  # on SSP-90XX the preset #0 is the "Normal Mode"
			cmd = MICMD_SABC
		else:
			cmd = MICMD_RUNM
		self._check_hwCmdSupp(cmd)
		#
		cargs = self._szrObj.serialize_data([index], [SZR_VTYPE_IX])
		self._lowlev_send_set_cmd(cmd, cargs)

	def save_memory_preset(self, index, volt, curr):
		""" Save Voltage and Current values into PS memory locations

		Parameters:
			index (int): Index of memory location to save to
			volt (float): Voltage value
			curr (float): Current value
		Returns:
			bool: True if memory preset was changed, False if not
		"""
		assert isinstance(index, int), "index needs to be int"
		hwSpecs = self.get_hw_specs()
		assert index >= 0 and index < hwSpecs["realMemPresetLocations"], "index out of range (0..%d)" % (hwSpecs["realMemPresetLocations"] - 1)
		assert isinstance(volt, (float, int)), "volt needs to be float or int"
		assert isinstance(curr, (float, int)), "curr needs to be float or int"
		#
		memPresets = self._load_all_memory_presets()
		#
		volt = self.round_value(volt, isVolt=True)
		curr = self.round_value(curr, isVolt=False)
		#
		if self._enableMemPresetsCache and memPresets[index]["volt"] == volt and memPresets[index]["curr"] == curr:
			return False
		#print("  __ MI.smp old=%.3f/%.3f new=%.3f/%.3f __ " % (memPresets[index]["volt"], memPresets[index]["curr"], volt, curr))
		memPresets[index]["volt"] = volt
		memPresets[index]["curr"] = curr
		#
		if self._modelSeries == MODEL_SERIES_ID_SSP:
			cmd = MICMD_SETD
			self._check_hwCmdSupp(cmd)
			#
			if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
				index += 1  # on SSP-90XX the preset #0 is the "Normal Mode"
			cargs = self._szrObj.serialize_data([index, volt, curr], [SZR_VTYPE_IX, SZR_VTYPE_VOLT, SZR_VTYPE_CURR])
		else:
			cmd = MICMD_PROM
			self._check_hwCmdSupp(cmd)
			#
			valArr = []
			vtArr = []
			for ix in range(hwSpecs["realMemPresetLocations"]):
				valArr.append(memPresets[ix]["volt"])
				vtArr.append(SZR_VTYPE_VOLT)
				valArr.append(memPresets[ix]["curr"])
				vtArr.append(SZR_VTYPE_CURR)
			cargs = self._szrObj.serialize_data(valArr, vtArr)
		#
		self._lowlev_send_set_cmd(cmd, cargs, extraWait=True)
		self._memPresets = memPresets
		return True

	# --------------------------------------------------------------------------
	# All Series but SSP Series

	def get_max_values_from_hw(self):
		""" Get PS maximum Voltage and Current values

		Returns:
			dict: {"maxVolt": float, "maxCurr": float}
		"""
		if self._hwMax is not None:
			return deepcopy(self._hwMax)
		response = self._lowlev_send_get_cmd(MICMD_GMAX)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_VOLT, SZR_VTYPE_CURR])
		tmpV = tmpUd[0]["val"]
		tmpC = tmpUd[1]["val"]
		self._hwMax = {"maxVolt": tmpV, "maxCurr": tmpC}
		return deepcopy(self._hwMax)

	# --------------------------------------------------------------------------
	# All Series but SSP-80XX Series

	def get_preset_voltage_current(self):
		""" Get PS preset Voltage and Current values

		Returns:
			dict: {"volt": float, "curr": float}
		Raises:
			FunctionNotSupportedForModelError
		"""
		if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP80:
			raise FunctionNotSupportedForModelError()
		cmd = MICMD_GETS
		self._check_hwCmdSupp(cmd)
		#
		if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP81 or self._modelSubSeries == MODEL_SUBSERIES_ID_SSP83:
			cargs = self._szrObj.serialize_data([3], [SZR_VTYPE_IX])
		elif self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
			cargs = self._szrObj.serialize_data([0], [SZR_VTYPE_IX])
		else:
			cargs = ""
		response = self._lowlev_send_get_cmd(cmd, cargs)
		#
		if self._modelSeries == MODEL_SERIES_ID_NTP or self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
			vt1 = SZR_VTYPE_VARVOLT
			vt2 = SZR_VTYPE_VARCURR
		else:
			vt1 = SZR_VTYPE_VOLT
			vt2 = SZR_VTYPE_CURR
		tmpUd = self._szrObj.unserialize_data(response, [vt1, vt2])
		tmpV = tmpUd[0]["val"]
		tmpC = tmpUd[1]["val"]
		return {"volt": tmpV, "curr": tmpC}

	def set_preset_voltage_current(self, volt, curr):
		""" Set PS preset Voltage and Current values

		Parameters:
			volt (float): Voltage value
			curr (float): Current value
		Raises:
			FunctionNotSupportedForModelError
		"""
		assert isinstance(volt, (int, float)), "volt needs to be int or float"
		assert isinstance(curr, (int, float)), "curr needs to be int or float"
		#
		if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP80:
			raise FunctionNotSupportedForModelError()
		#
		if self._modelSeries == MODEL_SERIES_ID_NTP:
			cmd = MICMD_SETD
			self._check_hwCmdSupp(cmd)
			#
			cargs = self._szrObj.serialize_data([volt, curr], [SZR_VTYPE_VOLT, SZR_VTYPE_CURR])
			self._lowlev_send_set_cmd(cmd, cargs)
		else:
			self.set_preset_voltage(volt)
			self.set_preset_current(curr)

	def set_preset_voltage(self, volt):
		""" Set PS preset Voltage value

		Parameters:
			volt (float): Voltage value
		Raises:
			FunctionNotSupportedForModelError
		"""
		if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP80:
			raise FunctionNotSupportedForModelError()
		#
		cmdAndCargs = self._get_cmd_set_volt_or_curr(volt, "volt", isVolt=True)
		self._lowlev_send_set_cmd(cmdAndCargs["cmd"], cmdAndCargs["cargs"])

	def set_preset_current(self, curr):
		""" Set PS preset Current value

		Parameters:
			curr (float): Current value
		Raises:
			FunctionNotSupportedForModelError
		"""
		if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP80:
			raise FunctionNotSupportedForModelError()
		#
		cmdAndCargs = self._get_cmd_set_volt_or_curr(curr, "curr", isVolt=False)
		self._lowlev_send_set_cmd(cmdAndCargs["cmd"], cmdAndCargs["cargs"])

	# --------------------------------------------------------------------------
	# NTP Series only

	def get_min_values_from_hw(self):
		""" Get PS minimum Voltage and Current values

		Returns:
			dict: {"maxVolt": float, "maxCurr": float}
		"""
		if self._hwMin is not None:
			return deepcopy(self._hwMin)
		response = self._lowlev_send_get_cmd(MICMD_GMIN)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_VOLT, SZR_VTYPE_CURR])
		tmpV = tmpUd[0]["val"]
		tmpC = tmpUd[1]["val"]
		self._hwMin = {"minVolt": tmpV, "minCurr": tmpC}
		return deepcopy(self._hwMin)

	# --------------------------------------------------------------------------
	# SSP-80XX Series only

	def get_selected_range(self):
		""" Get selected Voltage/Current range of PS

		Returns:
			str: Range ID (one of RANGE_ID_0_16V0_5A0, RANGE_ID_1_27V0_3A0, RANGE_ID_2_36V0_2A2)
		Raises:
			ValueError
		"""
		response = self._lowlev_send_get_cmd(MICMD_GCHA)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_RANGE])
		rangeId = str(tmpUd[0]["val"])
		if rangeId not in [RANGE_ID_0_16V0_5A0, RANGE_ID_1_27V0_3A0, RANGE_ID_2_36V0_2A2]:
			raise ValueError("invalid rangeId read from device")
		return rangeId

	def set_selected_range(self, rangeId):
		""" Set selected Voltage/Current range of PS

		Parameters:
			rangeId (str): Range ID (one of RANGE_ID_0_16V0_5A0, RANGE_ID_1_27V0_3A0, RANGE_ID_2_36V0_2A2)
		Raises:
			ValueError
		"""
		if rangeId not in [RANGE_ID_0_16V0_5A0, RANGE_ID_1_27V0_3A0, RANGE_ID_2_36V0_2A2]:
			raise ValueError("rangeId needs to be one of RANGE_ID_*")
		#
		cmd = MICMD_SCHA
		self._check_hwCmdSupp(cmd)
		#
		cargs = self._szrObj.serialize_data([int(rangeId)], [SZR_VTYPE_RANGE])
		self._lowlev_send_set_cmd(cmd, cargs)

	# --------------------------------------------------------------------------
	# SSP Series only

	def get_selected_preset(self):
		""" Get selected preset of PS (Preset A/B/C == 0/1/2)

		Returns:
			int
		"""
		response = self._lowlev_send_get_cmd(MICMD_GABC)
		#
		tmpUd = self._szrObj.unserialize_data(response, [SZR_VTYPE_IX])
		tmpIx = tmpUd[0]["val"]
		if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
			tmpIx -= 1  # on SSP-90XX the preset #0 is the "Normal Mode"
		return tmpIx

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _check_hwCmdSupp(self, cmd):
		""" Check if command is supported by the current hardware

		Parameters:
			cmd (str)
		Raises:
			FunctionNotSupportedForModelError, ValueError
		"""
		assert isinstance(cmd, str), "cmd needs to be string"
		#
		if self._modelHwCmdSupp is None:
			if cmd != MICMD_GMOD and cmd != MICMD_GVER:
				raise ValueError("need to call get_hw_specs(modelId=None) first")
		elif not self._modelHwCmdSupp[cmd]:
			raise FunctionNotSupportedForModelError()

	def _lowlev_send_cmd(self, cmd, cargs, extraWait=False):
		""" Send command to hardware and return response

		Parameters:
			cmd (str)
			cargs (str)
			extraWait (bool)
		Returns:
			str
		Raises:
			NotConnectedError
		"""
		assert isinstance(cmd, str), "cmd needs to be string"
		assert isinstance(cargs, str), "cargs needs to be string"
		assert extraWait == True or extraWait == False, "extraWait needs to be bool"
		#
		self._check_hwCmdSupp(cmd)
		#
		if self._pyserObj is None:
			raise NotConnectedError()
		if cmd.endswith("\r"):
			cmd = cmd[0:-1]
		cmd += cargs + "\r"
		#print("-- S: '%s' --" % cmd.replace("\r", "@"))
		self._pyserObj.write(cmd.encode("ascii"))
		if not self._isEmulated:
			time.sleep(0.1 + (0.9 if extraWait else 0.0))
		resS = self._pyserObj.readline().decode("ascii")
		resS = resS.replace("\r", "@")
		#print("R: '%s'" % resS)
		if not self._isEmulated:
			time.sleep(0.1)
		return resS

	def _lowlev_send_get_cmd(self, cmd, cargs="", extraWait=False):
		""" Send GET command to hardware and return response

		Parameters:
			cmd (str)
			cargs (str)
			extraWait (bool)
		"""
		return self._lowlev_send_cmd(cmd, cargs, extraWait=extraWait)

	def _lowlev_send_set_cmd(self, cmd, cargs, extraWait=False):
		""" Send SET command to hardware and validate response

		Parameters:
			cmd (str)
			cargs (str)
			extraWait (bool)
		"""
		response = self._lowlev_send_cmd(cmd, cargs, extraWait=extraWait)
		self._szrObj.unserialize_data(response, [])

	def _get_cmd_set_volt_or_curr(self, valFloat, varName, isVolt):
		""" Get raw command for setting Voltage/Current

		Parameters:
			valFloat (float)
			varName (str)
			isVolt (bool)
		Returns:
			dict: {"cmd": str, "cargs": str}
		"""
		assert isinstance(valFloat, (int, float)), "%s needs to be int or float" % varName
		assert isinstance(varName, str), "varName needs to be string"
		assert isVolt == True or isVolt == False, "isVolt needs to be bool"
		#
		cmd = MICMD_VOLT if isVolt else MICMD_CURR
		self._check_hwCmdSupp(cmd)
		#
		valArr = []
		vtArr = []
		if self._modelSeries == MODEL_SERIES_ID_SSP:
			valArr.append(0 if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90 else 3)
			vtArr.append(SZR_VTYPE_IX)
		valArr.append(valFloat)
		vtArr.append(SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR)
		cargs = self._szrObj.serialize_data(valArr, vtArr)
		return {"cmd": cmd, "cargs": cargs}

	def _get_cmd_set_ovp_or_ocp(self, valFloat, varName, isVolt):
		""" Get raw command for setting OVP/OCP

		Parameters:
			valFloat (float)
			varName (str)
			isVolt (bool)
		Returns:
			dict: {"cmd": str, "cargs": str}
		"""
		assert isinstance(valFloat, (int, float)), "%s needs to be int or float" % varName
		assert isinstance(varName, str), "varName needs to be string"
		assert isVolt == True or isVolt == False, "isVolt needs to be bool"
		#
		if self._modelSeries == MODEL_SERIES_ID_NTP:
			cmd = MICMD_SVSH if isVolt else MICMD_SISH
		else:
			cmd = MICMD_SOVP if isVolt else MICMD_SOCP
		self._check_hwCmdSupp(cmd)
		#
		cargs = self._szrObj.serialize_data([valFloat], [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR])
		return {"cmd": cmd, "cargs": cargs}

	def _get_output_volt_curr_mode(self):
		""" Get raw PS display value of Voltage/Current/Mode

		Returns:
			dict: {"volt": float, "curr": float, "mode": str}
		"""
		response = self._lowlev_send_get_cmd(MICMD_GETD)
		#
		if self._modelSeries == MODEL_SERIES_ID_NTP or self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
			vt1 = SZR_VTYPE_VARVOLT
			vt2 = SZR_VTYPE_VARCURR
		else:
			isHcsSeries = self._modelSeries == MODEL_SERIES_ID_HCS
			vt1 = (SZR_VTYPE_SPECVOLT if isHcsSeries else SZR_VTYPE_VOLT)
			vt2 = (SZR_VTYPE_SPECCURR if isHcsSeries else SZR_VTYPE_CURR)
		tmpUd = self._szrObj.unserialize_data(response, [vt1, vt2, SZR_VTYPE_MODE])
		return {"volt": tmpUd[0]["val"], "curr": tmpUd[1]["val"], "mode": tmpUd[2]["val"]}

	def _load_all_memory_presets(self):
		""" Load all saved Voltage and Current values from PS memory locations

		Returns:
			list: [{"volt": value, "curr": value}, ...]
		"""
		if self._enableMemPresetsCache and self._memPresets is not None:
			return deepcopy(self._memPresets)
		#
		self._memPresets = []
		hwSpecs = self.get_hw_specs()
		if self._modelSeries == MODEL_SERIES_ID_SSP:
			if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
				vtArr = [SZR_VTYPE_VARVOLT, SZR_VTYPE_VARCURR]
			else:
				vtArr = [SZR_VTYPE_VOLT, SZR_VTYPE_CURR]
			#
			cmd = MICMD_GETS
			self._check_hwCmdSupp(cmd)
			#
			for ix in range(hwSpecs["realMemPresetLocations"]):
				tmpIx = ix
				if self._modelSubSeries == MODEL_SUBSERIES_ID_SSP90:
					tmpIx += 1  # on SSP-90XX the preset #0 is the "Normal Mode"
				cargs = self._szrObj.serialize_data([tmpIx], [SZR_VTYPE_IX])
				response = self._lowlev_send_get_cmd(cmd, cargs)
				tmpUd = self._szrObj.unserialize_data(response, vtArr)
				tmpV = tmpUd[0]["val"]
				tmpC = tmpUd[1]["val"]
				self._memPresets.append({"volt": tmpV, "curr": tmpC})
		else:
			response = self._lowlev_send_get_cmd(MICMD_GETM)
			#
			vtArr = []
			for ix in range(hwSpecs["realMemPresetLocations"]):
				vtArr.append(SZR_VTYPE_VOLT)
				vtArr.append(SZR_VTYPE_CURR)
			tmpUd = self._szrObj.unserialize_data(response, vtArr)
			#
			udIx = 0
			for ix in range(hwSpecs["realMemPresetLocations"]):
				tmpV = tmpUd[udIx]["val"]
				udIx += 1
				tmpC = tmpUd[udIx]["val"]
				udIx += 1
				self._memPresets.append({"volt": tmpV, "curr": tmpC})
		return deepcopy(self._memPresets)
