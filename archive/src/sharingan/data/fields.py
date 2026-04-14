"""Field type detection for form inputs."""

from __future__ import annotations

import re
from enum import Enum


class FieldType(str, Enum):
    """Detected type of a form field."""

    EMAIL = "email"
    PASSWORD = "password"
    CONFIRM_PASSWORD = "confirm_password"
    USERNAME = "username"
    NAME = "name"
    PHONE = "phone"
    URL = "url"
    NUMBER = "number"
    DATE = "date"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    TEXT = "text"
    UNKNOWN = "unknown"


def detect_field_type(
    input_type: str | None,
    name: str | None = None,
    id_attr: str | None = None,
    label: str | None = None,
    placeholder: str | None = None,
) -> FieldType:
    """Detect the semantic type of a form field from its HTML attributes.

    Uses a combination of the type attribute, name/id/label, and placeholder
    to determine what kind of data the field expects.

    Args:
        input_type: The HTML type attribute (e.g., "email", "password").
        name: The name attribute.
        id_attr: The id attribute.
        label: The associated label text.
        placeholder: The placeholder text.

    Returns:
        The detected field type.
    """
    if input_type:
        t = input_type.lower()
        direct_map = {
            "email": FieldType.EMAIL,
            "password": FieldType.PASSWORD,
            "tel": FieldType.PHONE,
            "url": FieldType.URL,
            "number": FieldType.NUMBER,
            "date": FieldType.DATE,
            "datetime-local": FieldType.DATE,
            "time": FieldType.DATE,
            "checkbox": FieldType.CHECKBOX,
            "radio": FieldType.RADIO,
            "file": FieldType.FILE,
        }
        if t in direct_map:
            base = direct_map[t]
            if base == FieldType.PASSWORD and _looks_like_confirm(name, id_attr, label, placeholder):
                return FieldType.CONFIRM_PASSWORD
            return base

    # Combine text attributes for keyword matching
    haystack = " ".join(s for s in [name, id_attr, label, placeholder] if s).lower()

    if not haystack:
        return FieldType.TEXT

    if _matches(haystack, ("email", "e-mail")):
        return FieldType.EMAIL
    if _matches(haystack, ("confirm", "repeat")) and "password" in haystack:
        return FieldType.CONFIRM_PASSWORD
    if "password" in haystack:
        return FieldType.PASSWORD
    if _matches(haystack, ("username", "user name", "handle", "login")):
        return FieldType.USERNAME
    if _matches(haystack, ("phone", "mobile", "tel")):
        return FieldType.PHONE
    if _matches(haystack, ("url", "website", "link")):
        return FieldType.URL
    if _matches(haystack, ("first name", "last name", "full name", "firstname", "lastname")):
        return FieldType.NAME
    if re.search(r"\bname\b", haystack):
        return FieldType.NAME
    if _matches(haystack, ("age", "year", "count", "quantity", "amount", "price")):
        return FieldType.NUMBER
    if _matches(haystack, ("date", "birthday", "dob", "birth")):
        return FieldType.DATE

    return FieldType.TEXT


def _looks_like_confirm(*attrs: str | None) -> bool:
    """Check if any attribute suggests this is a confirm password field."""
    for attr in attrs:
        if attr and re.search(r"confirm|repeat|verify", attr, re.IGNORECASE):
            return True
    return False


def _matches(haystack: str, needles: tuple[str, ...]) -> bool:
    """Check if any needle is in the haystack."""
    return any(needle in haystack for needle in needles)
