class BrowserExportError(RuntimeError):
    """Base error for local assisted browser export."""


class BrowserExportSafetyError(BrowserExportError):
    """Raised when a browser export configuration violates safety policy."""


class BrowserAutomationUnavailableError(BrowserExportError):
    """Raised when optional browser automation dependencies are unavailable."""
