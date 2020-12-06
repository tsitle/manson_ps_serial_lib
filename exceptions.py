#
# by TS, Dec 2020
#

class InstrumentError(Exception):
	pass

class CouldNotConnectError(InstrumentError):
	def __init__(self, msg=""):
		super().__init__("'%s'" % msg)

class FunctionNotSupportedForModelError(InstrumentError):
	pass

class InvalidInputDataError(InstrumentError):
	def __init__(self, valStr="", valType="n/a"):
		super().__init__("'%s' (VT=%s)" % (valStr, valType))

class InvalidModelError(InstrumentError):
	def __init__(self, msg=""):
		super().__init__("'%s'" % msg)

class InvalidResponseError(InstrumentError):
	def __init__(self, msg=""):
		super().__init__("'%s'" % msg)

class InvalidTestType(InstrumentError):
	def __init__(self, msg=""):
		super().__init__("'%s'" % msg)

class NotConnectedError(InstrumentError):
	pass

class TestFailedError(InstrumentError):
	pass

class UnsupportedModelError(InstrumentError):
	def __init__(self, msg=""):
		super().__init__("'%s'" % msg)

class UnknownCommandError(InstrumentError):
	def __init__(self, msg=""):
		super().__init__("'%s'" % msg)
