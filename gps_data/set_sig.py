import re
from bitstring import BitStream

# Constants for GPS frequencies (MHz)
FREQL1 = 1575.42    # L1
FREQL2 = 1227.60    # L2
FREQL5 = 1176.45    # L5
SYS_GPS = 0         # GPS system ID

# GPS MSM signal ID table (complete mapping for RTCM 10403.3, Table 3.5-91)
msm_sig_gps = [
    "", "1C", "1P", "1W", "1Y", "1M", "1N", "2C", "2P", "2W", "2Y", "2M",
    "2N", "2D", "2S", "2L", "2X", "", "5D", "5P", "", "5I", "5Q", "5X",
    "1D", "", "", "", "", "1S", "1L", "1X"
]

# Observation code strings (from provided obscodes)
obscodes = [
    "", "1C", "1P", "1W", "1Y", "1M", "1N", "1S", "1L", "1E",
    "1A", "1B", "1X", "1Z", "2C", "2D", "2S", "2L", "2X", "2P",
    "2W", "2Y", "2M", "2N", "5I", "5Q", "5X", "7I", "7Q", "7X",
    "6A", "6B", "6C", "6X", "6Z", "6S", "6L", "8L", "8Q", "8X",
    "2I", "2Q", "6I", "6Q", "3I", "3Q", "3X", "1I", "1Q", "5A",
    "5B", "5C", "9A", "9B", "9C", "9X", "1D", "5D", "5P", "5Z",
    "6E", "7D", "7P", "7Z", "8D", "8P", "4A", "4B", "4X", ""
]

def normalize_hex_string(hex_str):
    """Normalize hex string: convert all tokens to 2-digit uppercase hex."""
    cleaned = re.sub(r'[^0-9a-fA-F\s]', '', hex_str)
    parts = cleaned.split()
    normalized_parts = []
    for p in parts:
        if len(p) == 1:
            normalized_parts.append(f'0{p.upper()}')  # pad single digit
        elif len(p) == 2:
            normalized_parts.append(p.upper())
        else:
            raise ValueError(f"Invalid hex byte: '{p}'")
    return ''.join(normalized_parts)

def code2obs(code):
    """Convert observation code index to string."""
    return obscodes[code] if 0 <= code < len(obscodes) else ""

def code2freq_GPS(code, freq):
    """GPS obs code to frequency."""
    obs = code2obs(code)
    if not obs:
        freq[0] = 0.0
        return -1
    freq[0] = {
        '1': FREQL1,  # L1
        '2': FREQL2,  # L2
        '5': FREQL5   # L5
    }.get(obs[0], 0.0)
    return {
        '1': 0,  # L1
        '2': 1,  # L2
        '5': 2   # L5
    }.get(obs[0], -1)

def get_signal_frequency(signal_id):
    """Map RTCM MSM7 GPS signal ID to frequency and frequency core."""
    if not (1 <= signal_id <= 32):
        return "Unknown", 0.0, "Unknown"
    obs_code = msm_sig_gps[signal_id - 1]
    if not obs_code:
        return "Unknown", 0.0, "Unknown"
    try:
        code_idx = obscodes.index(obs_code)
        freq = [0.0]
        freq_idx = code2freq_GPS(code_idx, freq)
        freq_core = {0: "L1", 1: "L2", 2: "L5"}.get(freq_idx, "Unknown")
        return obs_code, freq[0], freq_core
    except ValueError:
        return "Unknown", 0.0, "Unknown"

def parse_rtcm_message(hex_str):
    """Parse RTCM 1077 message to extract TOW, satellite mask, signal mask, and MSM header fields."""
    try:
        normalized_hex = normalize_hex_string(hex_str)
        if not normalized_hex.startswith('D3'):
            print("Invalid RTCM message: does not start with D3")
            return None, None, None, None

        data_bytes = bytes.fromhex(normalized_hex)
        if len(data_bytes) < 6:
            print("RTCM message too short.")
            return None, None, None, None

        length = int.from_bytes(data_bytes[1:3], 'big') & 0x3FF
        if len(data_bytes) < length + 6:
            print(f"Incomplete RTCM message. Needed: {length + 6}, got: {len(data_bytes)}")
            return None, None, None, None

        stream = BitStream(data_bytes)
        stream.pos = 24  # Skip 3-byte RTCM header (0xD3 + 10-bit length)

        message_number = stream.read('uint:12')
        if message_number != 1077:
            print(f"Message type {message_number} is not 1077 (MSM7).")
            return None, None, None, None

        msm_header = {
            'station_id': stream.read('uint:12'),
            'tow_ms': stream.read('uint:30'),
            'sync_flag': stream.read('uint:1'),
            'iod': stream.read('uint:3'),
            'time_s': stream.read('uint:7'),
            'clk_str': stream.read('uint:2'),
            'clk_ext': stream.read('uint:2'),
            'smooth': stream.read('uint:2'),
            'tint_s': stream.read('uint:3'),
            'nsat': stream.read('uint:6'),
            'nsig': stream.read('uint:5'),
            'cell_mask': stream.read('uint:64')
        }
        satellite_mask = stream.read('uint:64')
        signal_mask = stream.read('uint:32')

        return msm_header['tow_ms'], satellite_mask, signal_mask, msm_header

    except Exception as e:
        print(f"Error parsing RTCM: {e}")
        return None, None, None, None

def main():
    """Process RTCM 1077 data to extract TOW, satellite mask, signal mask, and signal frequencies."""
    rtcm_data = [
        "D3 1 4C 43 59 50 59 6F 33 E0 0 20 4 25 21 24 0 0 0 0 20 20 40 80 77 E7 7F FF 26 29 24 21 A4 23 A9 22 0 0 0 0 34 12 7F D7 B CE E AE 40 3E 4 2B F1 58 1B 7F C9 7D 99 F8 48 11 0 64 F1 E2 1F 33 39 F3 22 20 D A 31 45 36 D A 52 63 7 B0 0 7B 18 86 E7 C1 BD 54 1D 3 67 DA 6E FE C2 D7 EB 49 E3 5 DE 41 13 64 12 4E 43 72 75 F8 77 71 E2 77 16 F 74 5D FC 4E 37 EA 69 7E A6 5F E0 C7 77 74 F 88 BF 78 83 37 C7 5A 77 CC 5E 7F CC 5D B8 15 0 50 1F B5 D0 1F 12 D8 1B BC 80 6F 76 78 74 18 27 F6 98 BF FA DA 87 FA DA 2F 8C 52 A7 90 DF 77 90 3B CF 90 AE 2F D7 E4 77 DC 73 5F DC 73 8F DD 36 9F F0 DC 3F FA E1 7F FA 3D 47 F7 68 CF DD BB 8F E1 FC 7 E1 FC 3A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 20 0 0 2 A5 99 A9 D8 D 65 87 62 6A B5 D3 C0 F2 5C 62 DB 9A F1 C 96 E6 97 B0 DC B6 2B 5B 62 39 EE F5 D4 33 AD EE 5B DB 37 B6 2 A0 5 4E A 9C 15 47 48 7E 91 DC 89 39 13 F2 27 DD 43 BA 7F 74 FE EA 11 CA 23 94 87 29 E 54 DA 53 B4 9B 69 36 D2 B1 8F C3"
    ]

    tow_ms, satellite_mask, signal_mask, msm_header = parse_rtcm_message(rtcm_data[0])
    if tow_ms is None:
        print("❌ Failed to parse RTCM message.")
        return

    print(f"✅ RTCM 1077 Message Parsed")
    print(f"TOW: {tow_ms} ms")
    print("MSM Header:")
    print(f"  Station ID: {msm_header['station_id']}")
    print(f"  Sync Flag: {msm_header['sync_flag']}")
    print(f"  IOD: {msm_header['iod']}")
    print(f"  Time S: {msm_header['time_s']}")
    print(f"  Clock Steering: {msm_header['clk_str']}")
    print(f"  External Clock: {msm_header['clk_ext']}")
    print(f"  Smoothing: {msm_header['smooth']}")
    print(f"  Smoothing Interval: {msm_header['tint_s']}")
    print(f"  Number of Satellites: {msm_header['nsat']}")
    print(f"  Number of Signals: {msm_header['nsig']}")
    print(f"  Cell Mask: 0x{msm_header['cell_mask']:016X}")

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
            name, freq, core = get_signal_frequency(signal_id)
            print(f"  Signal ID {signal_id}: {name}, Frequency: {freq or 'Unknown'} MHz, Band: {core or 'Unknown'}")
    else:
        print("Signal Mask: Not available")

if __name__ == "__main__":
    main()