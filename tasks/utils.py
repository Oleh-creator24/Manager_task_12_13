# tasks/utils.py
from __future__ import annotations
from typing import Tuple, Dict, Any
from django.http import JsonResponse
import json

_JSON_CT = "application/json; charset=utf-8"

def json_ok(data: Dict[str, Any], status: int = 200) -> JsonResponse:
    """Успешный JSON-ответ с правильным charset и без ASCII-эскейпа."""
    return JsonResponse(
        data,
        status=status,
        json_dumps_params={"ensure_ascii": False},
        content_type=_JSON_CT,
        safe=False if isinstance(data, list) else True,
    )

def json_error(error: Dict[str, Any], status: int = 400) -> JsonResponse:
    """Ошибка JSON-ответ (те же параметры кодировки)."""
    payload = error if isinstance(error, dict) else {"error": error}
    return JsonResponse(
        payload,
        status=status,
        json_dumps_params={"ensure_ascii": False},
        content_type=_JSON_CT,
    )

def parse_json_body(request) -> Tuple[bool, Dict[str, Any]]:
    """
    Надёжно парсим тело запроса как UTF-8 (поддержка BOM через utf-8-sig).
    Возвращает (ok, data|error_dict).
    """
    try:
        raw = request.body
        if isinstance(raw, bytes):
            s = raw.decode("utf-8-sig")  # на всякий случай, если вдруг BOM
        else:
            # Django обычно даёт bytes, но если str — просто используем
            s = str(raw)
        data = json.loads(s)
        if not isinstance(data, dict):
            return False, {"error": "JSON body must be an object"}
        return True, data
    except json.JSONDecodeError as e:
        return False, {"error": f"Invalid JSON: {e}"}
    except UnicodeDecodeError:
        return False, {"error": "Request body must be UTF-8 encoded"}
