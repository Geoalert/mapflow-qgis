"""Functional tests for the central error-message registry (mapflow/errors).

Covers the template-creation error feedback:
* the latent ``to_str`` crash when a backend error carries no ``params``,
* mapping a generic-coded backend message to a translatable description,
* synthesizing the client-side template-area-limit message from a code.
"""
from mapflow.errors.errors import ErrorMessage
from mapflow.http import api_message_parser


def test_to_str_with_empty_params_returns_backend_message():
    # Reproduces the blank-messagebox bug: code is unknown and params is empty,
    # so the backend `message` must be surfaced instead of raising/returning None.
    error = ErrorMessage(code="SOME_UNKNOWN_CODE", parameters={}, message="boom")
    assert error.to_str() == "boom"


def test_to_str_with_no_message_and_no_params_returns_default():
    error = ErrorMessage(code="SOME_UNKNOWN_CODE", parameters={}, message=None)
    assert "Unknown error" in error.to_str()


def test_known_backend_limit_message_is_mapped_to_translatable_text():
    error = ErrorMessage(
        code="BAD_REQUEST",
        parameters=None,
        message="You don't have enough limit, please contact admin!",
    )
    resolved = error.to_str()
    # Recognized and replaced with our own, translatable wording — not the raw backend English.
    assert resolved != "You don't have enough limit, please contact admin!"
    assert "planned processing" in resolved.lower()


def test_api_message_parser_resolves_limit_payload_to_clear_text():
    # End-to-end through the parser used by create_search_template_error_handler.
    body = '{"code": "BAD_REQUEST", "message": "You don\'t have enough limit, please contact admin!", "params": null}'
    resolved = api_message_parser(response_body=body)
    assert resolved is not None
    assert "planned processing" in resolved.lower()


def test_template_area_limit_code_is_formatted_with_limit():
    error = ErrorMessage(
        code="TEMPLATE_AREA_LIMIT_EXCEEDED",
        parameters={"templateAreaLimit": 12.5},
    )
    resolved = error.to_str()
    assert "12.5" in resolved
    assert "sq km" in resolved


def test_too_large_processing_code_is_formatted_with_area_and_limit():
    # Backend rejects an over-limit processing on start; params carry area and aoiAreaLimit (sq.m).
    error = ErrorMessage(
        code="TOO_LARGE_PROCESSING",
        parameters={"area": "48669864", "aoiAreaLimit": "2500000"},
        message="Processings larger than 2500000 sq.m. are prohibited. Area: 48669864 sq.m.",
    )
    resolved = error.to_str()
    assert "48669864" in resolved and "2500000" in resolved
    # Our translatable wording, not the raw backend English.
    assert "prohibited" not in resolved
    assert "too large" in resolved.lower()


def test_api_message_parser_resolves_too_large_processing():
    body = ('{"code":"TOO_LARGE_PROCESSING",'
            '"message":"Processings larger than 2500000 sq.m. are prohibited. Area: 48669864 sq.m.",'
            '"params":{"area":"48669864","aoiAreaLimit":"2500000"}}')
    resolved = api_message_parser(response_body=body)
    assert resolved is not None
    assert "48669864" in resolved and "2500000" in resolved
    assert "too large" in resolved.lower()
