from dataclasses import dataclass


@dataclass
class ProviderChargeResult:
    """Outcome of one charge attempt at the payment provider."""
    success: bool
    reference: str | None = None
    error: str | None = None
