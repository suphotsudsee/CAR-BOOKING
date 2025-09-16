"""Minimal email validation utilities used for testing.

This lightweight implementation provides the subset of the :mod:`email_validator`
package interface that Pydantic relies on. It performs basic validation to ensure
an email address contains a local part and domain, and normalises the domain to
lowercase. It is *not* a full replacement for the external dependency but allows
running the application in constrained environments.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["EmailNotValidError", "ValidatedEmail", "validate_email"]


class EmailNotValidError(ValueError):
    """Exception raised when an email address fails validation."""


@dataclass(slots=True)
class ValidatedEmail:
    """Return type for :func:`validate_email`. Mimics the real library."""

    email: str
    local_part: str
    domain: str
    normalized: str


def validate_email(email: str, *, allow_empty_local: bool = False, **_: object) -> ValidatedEmail:
    """Perform a small subset of email validation logic.

    The function validates that *email* contains the ``@`` separator, has both a
    local part and domain, and returns a :class:`ValidatedEmail` instance with the
    domain normalised to lowercase.
    """

    if not isinstance(email, str):
        msg = "Email address must be provided as a string"
        raise EmailNotValidError(msg)

    candidate = email.strip()
    if "@" not in candidate:
        msg = "Email address must contain '@'"
        raise EmailNotValidError(msg)

    local_part, domain = candidate.split("@", 1)

    if not local_part and not allow_empty_local:
        msg = "Email address local part cannot be empty"
        raise EmailNotValidError(msg)

    if not domain or "." not in domain:
        msg = "Email address domain appears to be invalid"
        raise EmailNotValidError(msg)

    normalised_domain = domain.lower()
    normalised_email = f"{local_part}@{normalised_domain}"

    return ValidatedEmail(
        email=normalised_email,
        local_part=local_part,
        domain=normalised_domain,
        normalized=normalised_email,
    )
