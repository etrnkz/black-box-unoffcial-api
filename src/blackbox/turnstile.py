"""
Turnstile bytecode decompiler and virtual machine emulator.
Ported from OpenAI Sentinel Turnstile decompiler (by realasfngl & etrnzk).
"""

import base64
import json
import math
import random
import re
from typing import Any, Dict, List, Optional, Tuple

INITIAL_MAP: Dict[str, str] = {
    "1": "XOR_STR",
    "2": "SET_VALUE",
    "3": "BTOA",
    "4": "BTOA_2",
    "5": "ADD_OR_PUSH",
    "6": "ARRAY_ACCESS",
    "7": "CALL",
    "8": "COPY",
    "10": "window",
    "11": "GET_SCRIPT_SRC",
    "12": "GET_MAP",
    "13": "TRY_CALL",
    "14": "JSON_PARSE",
    "15": "JSON_STRINGIFY",
    "17": "CALL_AND_SET",
    "18": "ATOB",
    "19": "BTOA_3",
    "20": "IF_EQUAL_CALL",
    "21": "IF_DIFF_CALL",
    "22": "TEMP_STACK_CALL",
    "23": "IF_DEFINED_CALL",
    "24": "BIND_METHOD",
    "27": "REMOVE_OR_SUBTRACT",
    "28": "undefined",
    "25": "undefined",
    "26": "undefined",
    "29": "LESS_THAN",
    "31": "INCREMENT",
    "32": "DECREMENT_AND_EXEC",
    "33": "MULTIPLY",
    "34": "MOVE",
}


def xor_str(s: str, key: str) -> str:
    s = str(s)
    key = str(key)
    if not key:
        return s
    res = []
    k_len = len(key)
    for i, ch in enumerate(s):
        res.append(chr(ord(ch) ^ ord(key[i % k_len])))
    return "".join(res)


class Decompiler:
    xorkey: str = ""
    xorkey2: str = ""
    decompiled: str = ""
    array_dict: Dict[Any, Any] = {}
    vg: int = 0
    round1: int = 0
    found: bool = False
    potential: List[Any] = []
    mapping: Dict[str, str] = {}

    @classmethod
    def start(cls):
        cls.xorkey = ""
        cls.xorkey2 = ""
        cls.decompiled = "var mem = {};\n"
        cls.array_dict = {}
        cls.vg = 0
        cls.round1 = 0
        cls.found = False
        cls.potential = []
        cls.mapping = INITIAL_MAP.copy()

    @classmethod
    def _k(cls, v: Any) -> str:
        return f"var_{str(v).replace('.', '_')}"

    @classmethod
    def handle_op(cls, op: str, args: List[Any]):
        k = cls._k
        if op == "COPY":
            if len(args) >= 2:
                cls.mapping[str(args[0])] = cls.mapping.get(str(args[1]), "")

        elif op == "SET_VALUE":
            if len(args) >= 2:
                vn = k(args[0])
                val = args[1]
                if val == "[]":
                    cls.decompiled += f"var {vn} = [];\n"
                    cls.array_dict[args[0]] = []
                elif val in ("None", None, "undefined"):
                    cls.decompiled += f"var {vn} = null;\n"
                    cls.array_dict[args[0]] = "null"
                elif isinstance(val, (int, float)) or (isinstance(val, str) and val.replace(".", "", 1).isdigit()):
                    num = float(val) if "." in str(val) else int(val)
                    cls.decompiled += f"var {vn} = {num};\n"
                    cls.array_dict[args[0]] = str(num)
                else:
                    cls.decompiled += f'var {vn} = "{val}";\n'
                    cls.array_dict[args[0]] = f'"{val}"'

        elif op == "ARRAY_ACCESS":
            if len(args) >= 3:
                v0, v1, v2 = k(args[0]), k(args[1]), k(args[2])
                cls.decompiled += f"var {v0} = {v1}[{v2}];\n"

        elif op == "ADD_OR_PUSH":
            if len(args) >= 3:
                v0, v1, v2 = k(args[0]), k(args[1]), k(args[2])
                cls.decompiled += f"var {v0} = {v1} + {v2};\n"

        elif op == "XOR_STR":
            if len(args) >= 3:
                v0, v1, v2 = k(args[0]), k(args[1]), k(args[2])
                cls.decompiled += f"var {v0} = XOR_STR({v1}, {v2});\n"
                if not cls.found:
                    cls.xorkey = str(args[2])
                    cls.found = True

    @classmethod
    def decompile(cls, bytecode: List[Any]):
        for item in bytecode:
            if not isinstance(item, list) or len(item) == 0:
                continue
            op_code = str(item[0])
            args = item[1:]
            op_name = cls.mapping.get(op_code, op_code)
            cls.handle_op(op_name, args)

    @classmethod
    def decompile_vm(cls, turnstile_b64: str, token: str) -> str:
        cls.start()
        raw_bytes = base64.b64decode(turnstile_b64)
        try:
            decoded = xor_str(raw_bytes.decode("latin-1"), token)
            bytecode = json.loads(decoded)
            cls.decompile(bytecode)
        except Exception:
            pass
        return cls.decompiled


class TurnstileParser:
    @staticmethod
    def parse_keys(decompiled_code: str) -> Tuple[Optional[str], Dict[str, str]]:
        xor_key = None
        for m in re.finditer(r"XOR_STR\(var_(\w+),\s*var_(\w+)\)", decompiled_code):
            key_var = m.group(2)
            val_match = re.search(rf'var var_{re.escape(key_var)}\s*=\s*"([^"]*)"', decompiled_code)
            if val_match:
                xor_key = val_match.group(1)
                break

        if not xor_key:
            for m in re.finditer(r'var var_(\w+)\s*=\s*"([^"]+)"', decompiled_code):
                val = m.group(2)
                if len(val) > 5 and "http" not in val:
                    xor_key = val
                    break

        keys: Dict[str, str] = {}
        for line in decompiled_code.splitlines():
            var_match = re.search(r"var var_(\w+)\s*=\s*(.+)", line)
            if not var_match:
                continue
            var_name = var_match.group(1)
            value = var_match.group(2).strip().rstrip(";")

            if "location" in line and "window" not in line:
                keys.setdefault(var_name, "location")
            elif "maxTouchPoints" in line or "vendor" in line:
                keys.setdefault(var_name, "vendor")
            elif "history" in line and "length" in line:
                keys.setdefault(var_name, "history")
            elif "random" in line and "Math.abs" not in line:
                keys.setdefault(var_name, "random")
            elif "ipLongitude" in line or "latitude" in line:
                keys.setdefault(var_name, "ipinfo")
            elif "createElement" in line:
                keys.setdefault(var_name, "element")
            elif "localStorage" in line:
                keys.setdefault(var_name, "localstorage")
            elif re.match(r"^-?\d+(\.\d+)?$", value):
                keys.setdefault(var_name, value)

        return xor_key, keys


HTML_OBJECT = json.dumps({
    "x": 0, "y": 1219, "width": 37.8125, "height": 30,
    "top": 1219, "right": 37.8125, "bottom": 1249, "left": 0
})


class TurnstileVM:
    @staticmethod
    def generate_turnstile(turnstile_dx: str, token: str, ip_info: str = "[]", location_url: str = "https://app.blackbox.ai/") -> str:
        """Solves Cloudflare Turnstile proof-of-work challenges in Python."""
        decompiled = Decompiler.decompile_vm(turnstile_dx, token)
        xor_key, keys = TurnstileParser.parse_keys(decompiled)
        effective_key = xor_key or token

        payload: Dict[str, str] = {}

        for key, value in keys.items():
            val_str = str(value)
            raw_val = ""

            if val_str.startswith("random"):
                raw_val = str(random.random())
            elif val_str == "ipinfo":
                raw_val = ip_info
            elif val_str == "element":
                raw_val = HTML_OBJECT
            elif val_str == "location":
                raw_val = location_url
            elif val_str == "vendor":
                raw_val = '["Google Inc.","Win32",8,0]'
            elif val_str == "localstorage":
                raw_val = "session_id,device_id,active_model,user_pref"
            elif val_str == "history":
                raw_val = str(random.randint(1, 5))
            else:
                raw_val = val_str

            encoded = xor_str(raw_val, effective_key)
            payload[key] = base64.b64encode(encoded.encode("latin-1")).decode("ascii")

        payload_json = json.dumps(payload)
        xored_payload = xor_str(payload_json, effective_key)
        return base64.b64encode(xored_payload.encode("latin-1")).decode("ascii")
