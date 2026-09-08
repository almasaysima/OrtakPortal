from flask import jsonify


def api_error(message, status_code=400, **extra):
    payload = {
        "success": False,
        "error": message,
    }

    if extra:
        payload.update(extra)

    return jsonify(payload), status_code


def api_success(status_code=200, **payload):
    data = {
        "success": True,
    }

    if payload:
        data.update(payload)

    return jsonify(data), status_code
