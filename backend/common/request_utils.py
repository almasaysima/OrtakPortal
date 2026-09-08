from flask import request


def get_json_body():
    return request.get_json(
        silent=True
    ) or {}
