from .errors import ValidationError


def get_json_body(request):
    """Return the request JSON body as a dict, or raise ValidationError."""
    body = request.get_json(silent=True)
    if body is None:
        raise ValidationError({"body": "Request body must be valid JSON"})
    if not isinstance(body, dict):
        raise ValidationError({"body": "Request body must be a JSON object"})
    return body


def clean_string(value, field, errors, *, required=False, max_length=None, allowed=None):
    """Validate and normalize an optional string field.

    Returns the trimmed value, or None when the field is absent/blank.
    Collects problems into `errors` rather than raising, so a single response
    can report every bad field at once.
    """
    if value is None:
        if required:
            errors[field] = "This field is required"
        return None

    if not isinstance(value, str):
        errors[field] = "Must be a string"
        return None

    value = value.strip()
    if not value:
        if required:
            errors[field] = "This field is required"
        return None

    if max_length is not None and len(value) > max_length:
        errors[field] = f"Must be at most {max_length} characters"
        return None

    if allowed is not None and value.lower() not in allowed:
        errors[field] = f"Must be one of: {', '.join(allowed)}"
        return None

    return value.lower() if allowed is not None else value
