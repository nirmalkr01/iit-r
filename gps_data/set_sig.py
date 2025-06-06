import re

def normalize_hex_string(hex_str):
    """Normalize hex string: pad single-digit hex, remove non-hex."""
    cleaned = re.sub(r'[^0-9a-fA-F\s]', '', hex_str)
    parts = cleaned.split()
    normalized = [f"{int(p, 16):02X}" for p in parts]
    return ''.join(normalized)

def get_signal_frequency(signal_id):
    """Map RTCM MSM7 GPS signal ID to frequency (MHz) and frequency core."""
    signal_map = {
        1: ("L1 C/A", 1575.42, "L1"),
        3: ("L1 P(Y)", 1575.42, "L1"),
        6: ("L1C", 1575.42, "L1"),
        14: ("L2 P(Y)", 1227.60, "L2"),
        17: ("L2C", 1227.60, "L2"),
        19: ("L2 D", 1227.60, "L2"),
        20: ("L2C (M+L)", 1227.60, "L2"),
        26: ("L5 I", 1176.45, "L5"),
        27: ("L5 Q", 1176.45, "L5")
    }
    return signal_map.get(signal_id, ("Unknown", None, None))

def get_satellite_mask(bytes_data):
    """Extract satellite mask from MSM7 RTCM message (type 1077)."""
    try:
        if len(bytes_data) < 18:
            print(f"Insufficient data for satellite mask: {len(bytes_data)} bytes")
            return None
        satellite_mask = int.from_bytes(bytes_data[10:18], 'big')
        print(f"Raw satellite mask bytes: {bytes_data[10:18].hex()}")
        return satellite_mask
    except Exception as e:
        print(f"Error extracting satellite mask: {e}")
        return None

def get_signal_mask(bytes_data):
    """Extract signal mask from MSM7 RTCM message (type 1077)."""
    try:
        if len(bytes_data) < 22:
            print(f"Insufficient data for signal mask: {len(bytes_data)} bytes")
            return None
        signal_mask = int.from_bytes(bytes_data[18:22], 'big')
        print(f"Raw signal mask bytes: {bytes_data[18:22].hex()}")
        return signal_mask
    except Exception as e:
        print(f"Error extracting signal mask: {e}")
        return None

def parse_rtcm_message(hex_str):
    """Parse RTCM 1077 message to extract TOW, satellite mask, and signal mask."""
    normalized_hex = normalize_hex_string(hex_str)
    if not normalized_hex.startswith('D3'):
        print("Invalid RTCM message: does not start with D3")
        return None, None, None
    try:
        bytes_data = bytes.fromhex(normalized_hex)
        if len(bytes_data) < 6:
            print(f"Invalid RTCM message: too short, length {len(bytes_data)}")
            return None, None, None
        length = int.from_bytes(bytes_data[1:3], 'big') & 0x3FF
        if len(bytes_data) < length + 6:
            print(f"Invalid RTCM message: incomplete length {length}, available {len(bytes_data)-6}")
            return None, None, None
        msg_num_bits = int.from_bytes(bytes_data[3:5], 'big') >> 4
        msg_num = msg_num_bits & 0xFFF
        print(f"Parsed message type: {msg_num}")
        if msg_num != 1077:
            print(f"Message type {msg_num} is not MSM7 (1077), skipping")
            return None, None, None
        if len(bytes_data) < 10:
            print("Message 1077: not enough data for TOW")
            return None, None, None

        # Extract TOW (Time of Week)
        tow_bits = int.from_bytes(bytes_data[6:10], 'big') >> 2
        tow_ms = tow_bits & 0x3FFFFFFF

        # Extract satellite and signal masks
        satellite_mask = get_satellite_mask(bytes_data)
        signal_mask = get_signal_mask(bytes_data)

        return tow_ms, satellite_mask, signal_mask
    except ValueError as e:
        print(f"Error parsing RTCM: non-hexadecimal number in fromhex() - {e}")
        return None, None, None
    except Exception as e:
        print(f"Error parsing RTCM: {e}")
        return None, None, None

def main():
    """Process RTCM 1077 data to extract TOW, satellite mask, signal mask, and signal frequencies."""
    rtcm_data = [
        "D3 1 4C 43 59 50 59 6F 43 80 0 20 4 25 21 24 0 0 0 0 20 20 40 80 77 E7 7F FF 26 29 24 21 A4 23 A9 22 0 0 0 0 34 52 77 D9 B CD EE A6 40 3E 84 2B F1 58 1B 7F C9 7D 99 F8 48 11 0 64 E6 4B BE 7A 27 E7 86 BD D A 31 42 34 D A EA 24 E1 37 B6 13 15 E0 6E 58 BA 9E C D9 96 59 33 E6 A2 E 69 63 DF 9C 4E A 5E 60 A5 AE C C4 0 C 8 13 5E 81 2F 20 16 1F 99 EA C1 C4 6D 9C 4F 29 BA F2 63 7C 4E 49 16 64 8D AF 99 B 7F 9E E BF 9E F 6F 7B 9 6F 85 C0 17 85 1E BF 81 C6 A8 2E D2 A0 33 74 37 96 32 87 9A 74 37 9A 74 AF 7E A1 B7 83 2E 4F 82 8A A7 82 FC 90 0 47 48 4 D6 58 4 D6 80 5 99 10 67 6D F0 71 72 B0 70 CF B8 6D F9 BF 8D D6 DF 92 16 CF 92 17 5A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 20 0 0 2 A3 99 69 B8 49 76 88 E2 8A AD DB C1 72 8C 5A DB 98 B1 C AE E2 99 71 2C 96 22 5B A1 DA E F8 D4 33 AD CB DB 96 77 2C 8E 4 1C A 38 14 70 1F A9 2F 52 3E 52 BC A8 F9 51 DF F BE 1F 7C 3E F8 92 1E 44 3C C8 79 90 F4 E0 33 C0 6B 80 D7 1 82 2C E4 "
    ]

    # Process RTCM
    tow_ms, satellite_mask, signal_mask = parse_rtcm_message(rtcm_data[0])
    if tow_ms is None:
        print("Failed to parse RTCM message")
        return
    print(f"RTCM Msg Type: 1077, TOW: {tow_ms} ms")
    if satellite_mask is not None:
        print(f"Satellite Mask: 0x{satellite_mask:016X}")
        satellite_bits = format(satellite_mask, '064b')
        print(f"Satellite Mask Bits: {satellite_bits}")
        satellites = [i+1 for i in range(64) if satellite_mask & (1 << (63-i))]
        print(f"Active Satellites: {satellites}")
    else:
        print("Satellite Mask: Not available")
    if signal_mask is not None:
        print(f"Signal Mask: 0x{signal_mask:08X}")
        signal_bits = format(signal_mask, '032b')
        print(f"Signal Mask Bits: {signal_bits}")
        signals = [i+1 for i in range(32) if signal_mask & (1 << (31-i))]
        print(f"Active Signals: {signals}")
        print("Signal Frequencies:")
        for signal_id in signals:
            signal_name, frequency, freq_core = get_signal_frequency(signal_id)
            if frequency is not None:
                print(f"  Signal ID {signal_id}: {signal_name}, Frequency: {frequency} MHz, Frequency Core: {freq_core}")
            else:
                print(f"  Signal ID {signal_id}: {signal_name}, Frequency: Unknown, Frequency Core: Unknown")
    else:
        print("Signal Mask: Not available")

if __name__ == "__main__":
    main()