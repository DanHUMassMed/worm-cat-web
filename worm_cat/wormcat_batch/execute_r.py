"""Compatibility shim for ExecuteR service in wormcat_batch."""

from services.r_runner import ExecuteR, RRunnerProtocol

__all__ = ["ExecuteR", "RRunnerProtocol"]
