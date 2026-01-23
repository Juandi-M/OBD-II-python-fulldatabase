def decode_dtc_bytes(hex_bytes: str) -> str:
    if not hex_bytes or len(hex_bytes) != 4:
        return f"INVALID:{hex_bytes}"

    try:
        first_nibble = int(hex_bytes[0], 16)

        type_bits = (first_nibble >> 2) & 0x03
        prefixes = {0: "P", 1: "C", 2: "B", 3: "U"}
        prefix = prefixes.get(type_bits, "P")

        second_char = str(first_nibble & 0x03)
        rest = hex_bytes[1:].upper()

        return f"{prefix}{second_char}{rest}"
    except (ValueError, IndexError):
        return f"INVALID:{hex_bytes}"
