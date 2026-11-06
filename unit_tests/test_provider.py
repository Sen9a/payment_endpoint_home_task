"""Unit tests for the mock payment provider — no database involved."""
from unittest.mock import patch

import pytest

from payment_api import settings
from payment_api.services.provider import MockPaymentProvider


@pytest.fixture
def fail_marker():
    """Pin the decline marker to a known value for the duration of a test."""
    with patch.object(settings, 'PROVIDER_FAIL_TOKEN_MARKER', 'fail') as marker:
        yield marker


def test_charge_declines_token_containing_the_fail_marker(fail_marker):
    result = MockPaymentProvider.charge('tok_fail_visa')

    assert result.success is False
    assert result.reference is None
    assert fail_marker in result.error


def test_charge_succeeds_for_any_other_token(fail_marker):
    result = MockPaymentProvider.charge('tok_good_visa')

    assert result.success is True
    assert result.error is None
    assert result.reference.startswith('mock_charge_')


def test_charge_references_are_unique(fail_marker):
    first = MockPaymentProvider.charge('tok_good_visa')
    second = MockPaymentProvider.charge('tok_good_visa')

    assert first.reference != second.reference
