import re
from typing import List, Dict, Tuple

NOISE_PREFIXES = (
    "SEARCHING",
    "BUS INIT",
    "UNABLE TO CONNECT",
    "STOPPED",
    "NO DATA",
    "?",
    "ELM",
    "OK",
)

HEXISH_RE = re.compile(r"^[0-9A-Fa-f ]+$")

def _is_noise(line: str) -> bool:
    up = line.strip().upper()
    return any(up.startswith(p) for p in NOISE_PREFIXES)

def normalize_tokens(line: str) -> List[str]:
    # keep hex+spaces only
    clean = re.sub(r"[^0-9A-Fa-f ]", "", line)
    tokens = [t.upper() for t in clean.split() if t]
    return tokens

def group_by_ecu(lines: List[str], headers_on: bool = True) -> Dict[str, List[List[str]]]:
    out: Dict[str, List[List[str]]] = {}
    for ln in lines:
        if not ln:
            continue
        if _is_noise(ln):
            continue
        tokens = normalize_tokens(ln)
        if not tokens:
            continue
        if not HEXISH_RE.match(" ".join(tokens)):
            continue

        if headers_on:
            ecu = tokens[0]
            out.setdefault(ecu, []).append(tokens)
        else:
            out.setdefault("NOHDR", []).append(tokens)
    return out

def payload_from_tokens(tokens: List[str], headers_on: bool = True) -> List[str]:
    """
    Converts one ELM line into payload bytes (strings).
    Handles common ELM pattern: <ECU> <LEN> <DATA...>
    """
    if headers_on:
        rest = tokens[1:]
    else:
        rest = tokens[:]

    # Drop length byte if it looks like one
    if rest:
        try:
            ln = int(rest[0], 16)
            if 0 < ln <= (len(rest) - 1):
                rest = rest[1:]
        except ValueError:
            pass
    return rest

def merge_payloads(grouped: Dict[str, List[List[str]]], headers_on: bool = True) -> Dict[str, List[str]]:
    merged: Dict[str, List[str]] = {}
    for ecu, msgs in grouped.items():
        out: List[str] = []
        for msg in msgs:
            out.extend(payload_from_tokens(msg, headers_on=headers_on))
        merged[ecu] = out
    return merged

def find_obd_response_payload(merged_payloads: Dict[str, List[str]], expected_prefix: List[str]) -> Tuple[str, List[str]] | None:
    """
    Find first ECU whose merged payload contains expected_prefix (e.g. ["41","00"] or ["49","02"]).
    Returns (ecu, payload) or None.
    """
    for ecu, payload in merged_payloads.items():
        # scan for prefix
        n = len(expected_prefix)
        for i in range(0, max(0, len(payload) - n + 1)):
            if payload[i:i+n] == expected_prefix:
                return ecu, payload[i:]
    return None
