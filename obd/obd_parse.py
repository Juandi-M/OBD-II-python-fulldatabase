import re
from typing import List, Dict, Tuple, Optional

NOISE_PREFIXES = (
    "SEARCHING",
    "BUS INIT",
    "UNABLE TO CONNECT",
    "STOPPED",
    "NO DATA",
    "CAN ERROR",
    "BUFFER FULL",
    "BUS BUSY",
    "BUS ERROR",
    "DATA ERROR",
    "?",
    "ELM",
    "OK",
)

HEXISH_RE = re.compile(r"^[0-9A-Fa-f ]+$")

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")  # excludes I,O,Q


def _is_noise(line: str) -> bool:
    up = line.strip().upper()
    return any(up.startswith(p) for p in NOISE_PREFIXES)


def normalize_tokens(line: str) -> List[str]:
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
    Typical ELM line (CAN): <ECU> <LEN> <DATA...>
    We drop ECU, and drop LEN if it looks like a length byte.
    """
    rest = tokens[1:] if headers_on else tokens[:]

    # Drop a length byte if plausible
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


def find_obd_response_payload(
    merged_payloads: Dict[str, List[str]],
    expected_prefix: List[str],
    prefer_ecus: Optional[List[str]] = None,
) -> Optional[Tuple[str, List[str]]]:
    """
    Find ECU whose merged payload contains expected_prefix.
    If prefer_ecus provided, try those ECUs first (in order).
    Returns (ecu, payload_from_prefix) or None.
    """
    ecu_order = list(merged_payloads.keys())

    if prefer_ecus:
        # stable ordering: preferred first, then the rest
        preferred = [e for e in prefer_ecus if e in merged_payloads]
        rest = [e for e in ecu_order if e not in preferred]
        ecu_order = preferred + rest

    n = len(expected_prefix)
    for ecu in ecu_order:
        payload = merged_payloads.get(ecu, [])
        for i in range(0, max(0, len(payload) - n + 1)):
            if payload[i : i + n] == expected_prefix:
                return ecu, payload[i:]
    return None


def extract_ascii_from_hex_tokens(tokens: List[str]) -> str:
    s = ""
    for t in tokens:
        try:
            b = int(t, 16)
        except Exception:
            continue
        if 32 <= b <= 126:
            s += chr(b)
    return s


def is_valid_vin(vin: str) -> bool:
    vin = (vin or "").strip().upper()
    return bool(VIN_RE.match(vin))

def strip_isotp_pci_from_payload(payload: List[str]) -> List[str]:
    """
    Minimal ISO-TP cleanup:
    - If payload contains ISO-TP frame markers like 10 xx (first frame) and 21/22/23... (consecutive),
      remove the PCI byte(s) so they don't turn into ASCII (e.g., 0x21 -> '!').

    This is a minimal Stage-1 cleanup good enough for VIN (09 02) and other long responses.
    """
    out: List[str] = []
    i = 0
    n = len(payload)

    while i < n:
        t = payload[i].upper()

        # First Frame: 10 LL ...
        if t == "10" and (i + 1) < n:
            # drop "10" and the length byte
            i += 2
            continue

        # Consecutive Frame: 21/22/23... 2F
        if len(t) == 2:
            try:
                b = int(t, 16)
                # 0x21..0x2F are typical consecutive frame indices in ISO-TP
                if 0x21 <= b <= 0x2F:
                    i += 1
                    continue
            except ValueError:
                pass

        out.append(t)
        i += 1

    return out
