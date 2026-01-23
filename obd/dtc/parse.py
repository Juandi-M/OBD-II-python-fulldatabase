from typing import List
from .decode import decode_dtc_bytes


def parse_dtc_response(response: str, mode: str = "03") -> List[str]:
    dtcs: List[str] = []
    if not response:
        return dtcs

    prefixes = {"03": "43", "07": "47", "0A": "4A"}
    prefix = prefixes.get(mode, "43")

    resp = response.replace(" ", "").upper()

    if prefix in resp:
        resp = resp.replace(prefix, "", 1)

    for i in range(0, len(resp), 4):
        chunk = resp[i : i + 4]
        if len(chunk) < 4:
            continue
        if chunk == "0000":
            continue

        dtc_code = decode_dtc_bytes(chunk)
        if not dtc_code.startswith("INVALID"):
            dtcs.append(dtc_code)

    return dtcs
