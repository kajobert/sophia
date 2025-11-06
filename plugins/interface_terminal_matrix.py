"""Compatibility shim: expose InterfaceTerminalMatrix from demo implementation.

Some tests and scripts import `plugins.interface_terminal_matrix` but the
real implementation lives in `_demo_interface_matrix.py` (for demo reasons).
This small shim re-exports the class so imports succeed during tests and
runtime.
"""
from ._demo_interface_matrix import InterfaceTerminalMatrix as _Impl
from plugins.base_plugin import PluginType


class InterfaceTerminalMatrix(_Impl):
	"""Compatibility wrapper that ensures the plugin advertises the
	proper PluginType (INTERFACE) expected by the PluginManager.

	The demo implementation returns a string for `plugin_type`; that
	causes a KeyError during registration. This thin subclass fixes the
	type contract.
	"""

	@property
	def plugin_type(self):
		return PluginType.INTERFACE


__all__ = ["InterfaceTerminalMatrix"]
