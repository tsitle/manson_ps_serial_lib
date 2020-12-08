#
# by TS, Dec 2020
#

try:
	from .mi_commands import *
	from .exceptions import InvalidModelError
	from .exceptions import NotConnectedError
	from .exceptions import UnknownCommandError
	from .exceptions import UnsupportedModelError
	from .models import build_spec_dict
	from .models import get_hw_model_id
	from .models import get_hw_specs
	from .models import MODEL_LIST_SERIES_HCS
	from .models import MODEL_LIST_SERIES_NTP
	from .models import MODEL_LIST_SERIES_SSP
	from .models import MODEL_LIST_SSP80XX
	from .models import MODEL_LIST_SSP81XX
	from .models import MODEL_LIST_SSP83XX
	from .models import MODEL_LIST_SSP90XX
	from .serializer import *
except (ModuleNotFoundError, ImportError):
	from mi_commands import *
	from exceptions import InvalidModelError
	from exceptions import NotConnectedError
	from exceptions import UnknownCommandError
	from exceptions import UnsupportedModelError
	from models import build_spec_dict
	from models import get_hw_model_id
	from models import get_hw_specs
	from models import MODEL_LIST_SERIES_HCS
	from models import MODEL_LIST_SERIES_NTP
	from models import MODEL_LIST_SERIES_SSP
	from models import MODEL_LIST_SSP80XX
	from models import MODEL_LIST_SSP81XX
	from models import MODEL_LIST_SSP83XX
	from models import MODEL_LIST_SSP90XX
	from serializer import *

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class EmulatedInstrumentSerial(object):
	def __init__(self, modelId=""):
		self._isopen = True
		self._bufferIn = None
		self._bufferOut = None
		self.flushInput()
		self.flushOutput()
		#
		self._inpCmdStr = None
		self._inpCargsStr = None
		#
		self._szrObj = Serializer()
		#
		self._states = {
				"preset_volt": 5.1,
				"preset_curr": 0.6,
				"disp_volt": 5.1,
				"disp_curr": 0.6,
				"over_volt_prot": 5.0,
				"over_curr_prot": 1.0,
				"output_mode": SZR_OUTP_MODE_CV,
				"outp_enabled": True,
				"active_preset": 0,
				"active_range": 0,
				"mem_presets": [
						{"volt": 3.3, "curr": 0.2},
						{"volt": 5.0, "curr": 0.3},
						{"volt": 12.0, "curr": 0.4},
					]
			}
		#
		self._hwSpecs = None
		self._modelId = None
		self.update_model_id(modelId)

	# --------------------------------------------------------------------------

	def update_model_id(self, modelId):
		self._modelId = modelId
		self._hwSpecs = build_spec_dict()
		if modelId is not None:
			try:
				modelId = get_hw_model_id(modelId)
				self._hwSpecs = get_hw_specs(modelId)
			except (InvalidModelError, UnsupportedModelError):
				pass
		self._szrObj.set_hw_specs(self._hwSpecs)
		#
		self._update_state_minmax("preset_volt", "minVolt", "maxVolt")
		self._update_state_minmax("preset_curr", "minCurr", "maxCurr")
		self._update_state_minmax("disp_volt", "minVolt", "maxVolt")
		self._update_state_minmax("disp_curr", "minCurr", "maxCurr")
		self._update_state_minmax("over_volt_prot", "minVolt", "maxVolt")
		self._update_state_minmax("over_curr_prot", "minCurr", "maxCurr")
		for ix in range(self._hwSpecs["realMemPresetLocations"]):
			self._update_mempreset_state_minmax(ix, True, "minVolt", "maxVolt")
			self._update_mempreset_state_minmax(ix, False, "minCurr", "maxCurr")

	# --------------------------------------------------------------------------

	def flushInput(self):
		self._bufferIn = bytes("", encoding="utf-8")

	def flushOutput(self):
		self._bufferOut = bytes("", encoding="utf-8")

	def close(self):
		self._isopen = False

	def write(self, data):
		if not self._isopen:
			raise NotConnectedError()
		if self._modelId is None:
			raise ValueError("no modelId has been set")
		self._bufferIn += data
		self._handle_input()

	def readline(self):
		if not self._isopen:
			raise NotConnectedError()
		resBy = self._bufferOut
		self.flushOutput()
		#print(" -> EIS.rl '%s' -- " % resBy.decode("ascii").replace("\r", "*"))
		return resBy

	# --------------------------------------------------------------------------
	# --------------------------------------------------------------------------

	def _update_state_minmax(self, sid, dictKeyMin, dictKeyMax):
		hwSpecs = self._hwSpecs
		cval = self._get_state(sid)
		if cval > hwSpecs[dictKeyMax]:
			self._set_state(sid, hwSpecs[dictKeyMax])
		elif cval < hwSpecs[dictKeyMin]:
			self._set_state(sid, hwSpecs[dictKeyMin])

	def _update_mempreset_state_minmax(self, ix, isVolt, dictKeyMin, dictKeyMax):
		hwSpecs = self._hwSpecs
		cvalD = self._get_mempreset_state(ix)
		cvalVC = cvalD["volt" if isVolt else "curr"]
		nvalV = cvalD["volt"]
		nvalC = cvalD["curr"]
		needsUpdate = False
		if cvalVC > hwSpecs[dictKeyMax]:
			if isVolt:
				nvalV = hwSpecs[dictKeyMax]
			else:
				nvalC = hwSpecs[dictKeyMax]
			needsUpdate = True
		elif cvalVC < hwSpecs[dictKeyMin]:
			if isVolt:
				nvalV = hwSpecs[dictKeyMin]
			else:
				nvalC = hwSpecs[dictKeyMin]
			needsUpdate = True
		if needsUpdate:
			self._set_mempreset_state(ix, nvalV, nvalC)

	def _get_state(self, sid):
		val = self._states[sid]
		#print("  _< EIS:gs(%s=%s) __ " % (sid, str(val)))
		return val

	def _set_state(self, sid, val):
		#print("  _> EIS:ss(%s=%s) __ " % (sid, str(val)))
		self._states[sid] = val

	def _get_mempreset_state(self, ix):
		valD = self._states["mem_presets"][ix]
		#print("  _< EIS:gMPs(%d=%.3f/%.3f) __ " % (ix, valD["volt"], valD["curr"]))
		return valD

	def _set_mempreset_state(self, ix, valVolt, valCurr):
		#print("  _> EIS:sMPs(%d=%.3f/%.3f) __ " % (ix, valVolt, valCurr))
		self._states["mem_presets"][ix]["volt"] = valVolt
		self._states["mem_presets"][ix]["curr"] = valCurr

	def _handle_input(self):
		""" Hande input command

		Raises:
			UnknownCommandError
		"""
		inpStr = self._bufferIn.decode("ascii")
		self.flushInput()
		if not inpStr.endswith("\r"):
			return
		inpStr = inpStr[:-1]
		if "\r" in inpStr:
			return
		cmdStr = inpStr[0:4]
		self._inpCmdStr = cmdStr
		self._inpCargsStr = inpStr[4:] + SZR_RESP_OK_SUFFIX
		#print(" <- EIS.hi '%s:%s' -- " % (cmdStr, self._inpCargsStr))
		if cmdStr == MICMD_GMOD:
			self._cmd_gmod()
		elif cmdStr == MICMD_GVER:
			self._cmd_gver()
		elif cmdStr == MICMD_ENDS or cmdStr == MICMD_SESS:
			self._cmd_ends_or_sess()
		elif cmdStr == MICMD_VOLT or cmdStr == MICMD_CURR:
			self._cmd_volt_or_curr()
		elif cmdStr == MICMD_GETD:
			self._cmd_getd()
		elif cmdStr == MICMD_GETS:
			self._cmd_gets()
		elif cmdStr == MICMD_GMIN or cmdStr == MICMD_GMAX:
			self._cmd_gmin_or_gmax()
		elif cmdStr == MICMD_SOUT:
			self._cmd_sout()
		elif cmdStr == MICMD_GOUT:
			self._cmd_gout()
		elif cmdStr == MICMD_GETM:
			self._cmd_getm()
		elif cmdStr == MICMD_PROM:
			self._cmd_prom()
		elif cmdStr == MICMD_GABC:
			self._cmd_gabc()
		elif cmdStr == MICMD_RUNM or cmdStr == MICMD_SABC:
			self._cmd_runm_or_sabc()
		elif cmdStr == MICMD_SOVP or cmdStr == MICMD_SOCP:
			self._cmd_sovp_or_socp()
		elif cmdStr == MICMD_GOVP or cmdStr == MICMD_GOCP:
			self._cmd_govp_or_gocp()
		elif cmdStr == MICMD_SVSH or cmdStr == MICMD_SISH:
			self._cmd_svsh_or_sish()
		elif cmdStr == MICMD_GVSH or cmdStr == MICMD_GISH:
			self._cmd_gvsh_or_gish()
		elif cmdStr == MICMD_SETD:
			self._cmd_setd()
		elif cmdStr == MICMD_GCHA:
			self._cmd_gcha()
		elif cmdStr == MICMD_SCHA:
			self._cmd_scha()
		else:
			raise UnknownCommandError(cmdStr)

	def _append_output(self, outpStr):
		self._bufferOut += bytes(outpStr + "OK\r", encoding="utf-8")

	def _cmd_gmod(self):
		self._szrObj.unserialize_data(self._inpCargsStr, [])
		self._append_output(self._modelId + "\r")

	def _cmd_gver(self):
		self._szrObj.unserialize_data(self._inpCargsStr, [])
		self._append_output("PSEUDO-V1.0" + "\r")

	def _cmd_ends_or_sess(self):
		if self._modelId in MODEL_LIST_SERIES_NTP:
			return
		self._szrObj.unserialize_data(self._inpCargsStr, [])
		self._append_output("")

	def _cmd_volt_or_curr(self):
		if self._modelId in MODEL_LIST_SSP80XX:
			return
		try:
			listValueTypes = []
			valVcIx = 0
			if self._modelId in MODEL_LIST_SERIES_SSP:
				listValueTypes.append(SZR_VTYPE_IX)
				valVcIx = 1
			isVolt = (self._inpCmdStr == MICMD_VOLT)
			listValueTypes.append(SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR)
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			self._set_state("preset_" + ("volt" if isVolt else "curr"), valArr[valVcIx]["val"])
			self._set_state("disp_" + ("volt" if isVolt else "curr"), valArr[valVcIx]["val"])
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_getd(self):
		outpStr = ""
		valVolt = self._get_state("disp_volt")
		valCurr = self._get_state("disp_curr")
		valMode = self._get_state("output_mode")
		listValueTypes = []
		if self._modelId in MODEL_LIST_SERIES_HCS:
			listValueTypes.append(SZR_VTYPE_SPECVOLT)
			listValueTypes.append(SZR_VTYPE_SPECCURR)
		elif self._modelId in MODEL_LIST_SSP80XX or self._modelId in MODEL_LIST_SSP81XX or \
				self._modelId in MODEL_LIST_SSP83XX:
			listValueTypes.append(SZR_VTYPE_VOLT)
			listValueTypes.append(SZR_VTYPE_CURR)
		elif self._modelId in MODEL_LIST_SERIES_NTP or self._modelId in MODEL_LIST_SSP90XX:
			listValueTypes.append(SZR_VTYPE_VARVOLT)
			listValueTypes.append(SZR_VTYPE_VARCURR)
		else:
			return
		listValueTypes.append(SZR_VTYPE_MODE)
		outpStr = self._szrObj.serialize_data([valVolt, valCurr, valMode], listValueTypes)
		self._append_output(outpStr)

	def _cmd_gets(self):
		psIx = -1
		try:
			if self._modelId in MODEL_LIST_SERIES_SSP:
				valArr = self._szrObj.unserialize_data(self._inpCargsStr, [SZR_VTYPE_IX])
				psIx = valArr[0]["val"]
		except InvalidInputDataError:
			return
		#
		outpStr = ""
		valVolt = 0.0
		valCurr = 0.0
		listValueTypes = []
		if self._modelId in MODEL_LIST_SERIES_HCS or \
				((self._modelId in MODEL_LIST_SSP81XX or self._modelId in MODEL_LIST_SSP83XX) and psIx == 3):
			listValueTypes.append(SZR_VTYPE_VOLT)
			listValueTypes.append(SZR_VTYPE_CURR)
			valVolt = self._get_state("preset_volt")
			valCurr = self._get_state("preset_curr")
		elif self._modelId in MODEL_LIST_SSP80XX or \
				self._modelId in MODEL_LIST_SSP81XX or self._modelId in MODEL_LIST_SSP83XX:
			listValueTypes.append(SZR_VTYPE_VOLT)
			listValueTypes.append(SZR_VTYPE_CURR)
			valStateD = self._get_mempreset_state(psIx)
			valVolt = valStateD["volt"]
			valCurr = valStateD["curr"]
		elif self._modelId in MODEL_LIST_SSP90XX and psIx > 0:
			listValueTypes.append(SZR_VTYPE_VARVOLT)
			listValueTypes.append(SZR_VTYPE_VARCURR)
			valStateD = self._get_mempreset_state(psIx - 1)
			valVolt = valStateD["volt"]
			valCurr = valStateD["curr"]
		elif self._modelId in MODEL_LIST_SERIES_NTP or self._modelId in MODEL_LIST_SSP90XX:
			listValueTypes.append(SZR_VTYPE_VARVOLT)
			listValueTypes.append(SZR_VTYPE_VARCURR)
			valVolt = self._get_state("preset_volt")
			valCurr = self._get_state("preset_curr")
		else:
			return
		outpStr = self._szrObj.serialize_data([valVolt, valCurr], listValueTypes)
		self._append_output(outpStr)

	def _cmd_gmin_or_gmax(self):
		isGmin = (self._inpCmdStr == MICMD_GMIN)
		if isGmin and self._modelId not in MODEL_LIST_SERIES_NTP:
			return
		if not isGmin and not (self._modelId in MODEL_LIST_SERIES_HCS or \
				self._modelId in MODEL_LIST_SERIES_NTP):
			return
		outpStr = ""
		valVolt = self._hwSpecs[("min" if isGmin else "max") + "Volt"]
		valCurr = self._hwSpecs[("min" if isGmin else "max") + "Curr"]
		listValueTypes = [SZR_VTYPE_VOLT, SZR_VTYPE_CURR]
		outpStr = self._szrObj.serialize_data([valVolt, valCurr], listValueTypes)
		self._append_output(outpStr)

	def _cmd_sout(self):
		try:
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, [SZR_VTYPE_STATE])
			self._set_state("outp_enabled", valArr[0]["val"])
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_gout(self):
		valState = self._get_state("outp_enabled")
		outpStr = self._szrObj.serialize_data([valState], [SZR_VTYPE_STATE])
		self._append_output(outpStr)

	def _cmd_getm(self):
		if self._modelId not in MODEL_LIST_SERIES_HCS:
			return
		outpStr = ""
		for ix in range(self._hwSpecs["realMemPresetLocations"]):
			valStateD = self._get_mempreset_state(ix)
			outpStr += self._szrObj.serialize_data([valStateD["volt"], valStateD["curr"]],
					[SZR_VTYPE_VOLT, SZR_VTYPE_CURR])
		self._append_output(outpStr)

	def _cmd_prom(self):
		if self._modelId not in MODEL_LIST_SERIES_HCS:
			return
		try:
			listValueTypes = []
			for ix in range(self._hwSpecs["realMemPresetLocations"]):
				listValueTypes.append(SZR_VTYPE_VOLT)
				listValueTypes.append(SZR_VTYPE_CURR)
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			for ix in range(self._hwSpecs["realMemPresetLocations"]):
				self._set_mempreset_state(ix, valArr[ix * 2]["val"], valArr[(ix * 2) + 1]["val"])
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_runm_or_sabc(self):
		isRunm = (self._inpCmdStr == MICMD_RUNM)
		if isRunm and self._modelId not in MODEL_LIST_SERIES_HCS:
			return
		if not isRunm and self._modelId not in MODEL_LIST_SERIES_SSP:
			return
		try:
			listValueTypes = [SZR_VTYPE_IX]
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			self._set_state("active_preset", valArr[0]["val"])
			if self._modelId in MODEL_LIST_SSP90XX:
				valArr[0]["val"] -= 1
			valStateD = self._get_mempreset_state(valArr[0]["val"])
			self._set_state("preset_volt", valStateD["volt"])
			self._set_state("preset_curr", valStateD["curr"])
			self._set_state("disp_volt", valStateD["volt"])
			self._set_state("disp_curr", valStateD["curr"])
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_sovp_or_socp(self):
		if self._modelId in MODEL_LIST_SERIES_NTP or self._modelId in MODEL_LIST_SERIES_HCS:
			return
		try:
			isVolt = (self._inpCmdStr == MICMD_SOVP)
			listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			self._set_state("over_" + ("volt" if isVolt else "curr") + "_prot", valArr[0]["val"])
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_govp_or_gocp(self):
		if self._modelId in MODEL_LIST_SERIES_NTP or self._modelId in MODEL_LIST_SERIES_HCS:
			return
		outpStr = ""
		try:
			isVolt = (self._inpCmdStr == MICMD_GOVP)
			listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
			valVC = self._get_state("over_" + ("volt" if isVolt else "curr") + "_prot")
			outpStr = self._szrObj.serialize_data([valVC], listValueTypes)
		except InvalidInputDataError:
			return
		self._append_output(outpStr)

	def _cmd_svsh_or_sish(self):
		if self._modelId not in MODEL_LIST_SERIES_NTP:
			return
		try:
			isVolt = (self._inpCmdStr == MICMD_SVSH)
			listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			self._set_state("over_" + ("volt" if isVolt else "curr") + "_prot", valArr[0]["val"])
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_gvsh_or_gish(self):
		if self._modelId not in MODEL_LIST_SERIES_NTP:
			return
		outpStr = ""
		try:
			isVolt = (self._inpCmdStr == MICMD_GVSH)
			listValueTypes = [SZR_VTYPE_VOLT if isVolt else SZR_VTYPE_CURR]
			valVC = self._get_state("over_" + ("volt" if isVolt else "curr") + "_prot")
			outpStr = self._szrObj.serialize_data([valVC], listValueTypes)
		except InvalidInputDataError:
			return
		self._append_output(outpStr)

	def _cmd_setd(self):
		if self._modelId not in MODEL_LIST_SERIES_SSP and \
				self._modelId not in MODEL_LIST_SERIES_NTP:
			return
		try:
			listValueTypes = []
			offsVcIx = 0
			if self._modelId in MODEL_LIST_SERIES_SSP:
				listValueTypes.append(SZR_VTYPE_IX)
				offsVcIx = 1
			listValueTypes.append(SZR_VTYPE_VOLT)
			listValueTypes.append(SZR_VTYPE_CURR)
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			#
			saveAsPreset = False
			presetIx = -1
			if self._modelId in MODEL_LIST_SSP80XX:
				presetIx = valArr[0]["val"]
				saveAsPreset = True
			elif self._modelId in MODEL_LIST_SSP81XX or self._modelId in MODEL_LIST_SSP83XX:
				presetIx = valArr[0]["val"]
				saveAsPreset = (presetIx != 3)
			elif self._modelId in MODEL_LIST_SSP90XX:
				presetIx = valArr[0]["val"]
				saveAsPreset = (presetIx > 0)
				presetIx -= (1 if saveAsPreset else 0)
			valVolt = valArr[offsVcIx]["val"]
			valCurr = valArr[offsVcIx + 1]["val"]
			if saveAsPreset:
				self._set_mempreset_state(presetIx, valVolt, valCurr)
			else:
				self._set_state("preset_volt", valVolt)
				self._set_state("preset_curr", valCurr)
				self._set_state("disp_volt", valVolt)
				self._set_state("disp_curr", valCurr)
		except InvalidInputDataError:
			return
		self._append_output("")

	def _cmd_gabc(self):
		if self._modelId not in MODEL_LIST_SERIES_SSP:
			return
		self._szrObj.unserialize_data(self._inpCargsStr, [])
		valState = self._get_state("active_preset")
		outpStr = self._szrObj.serialize_data([valState], [SZR_VTYPE_IX])
		self._append_output(outpStr)

	def _cmd_gcha(self):
		if self._modelId not in MODEL_LIST_SERIES_SSP:
			return
		self._szrObj.unserialize_data(self._inpCargsStr, [])
		valState = self._get_state("active_range")
		outpStr = self._szrObj.serialize_data([valState], [SZR_VTYPE_RANGE])
		self._append_output(outpStr)

	def _cmd_scha(self):
		if self._modelId not in MODEL_LIST_SERIES_SSP:
			return
		try:
			listValueTypes = [SZR_VTYPE_RANGE]
			valArr = self._szrObj.unserialize_data(self._inpCargsStr, listValueTypes)
			self._set_state("active_range", valArr[0]["val"])
		except InvalidInputDataError:
			return
		self._append_output("")
