import re
import datetime
import struct

# Constants
GPS_EPOCH = datetime.datetime(1980, 1, 6, 0, 0, 0)
LEAP_SECONDS = 18  # As of 2025
MS_PER_SECOND = 1000
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
VALID_RTCM_TYPES = {1005, 1077, 1097, 1117, 1127}

def normalize_hex_string(hex_str):
    """Normalize hex string: pad single-digit hex (e.g., 1→01, 0→00), remove non-hex."""
    cleaned = re.sub(r'[^0-9a-fA-F\s]', '', hex_str)
    parts = cleaned.split()
    normalized = [f"{int(p, 16):02X}" for p in parts]
    return ''.join(normalized)

def parse_nmea_gga(line):
    """Parse NMEA GGA sentence to extract UTC time in seconds."""
    if not line.startswith('$GPGGA'):
        return None
    parts = line.split(',')
    if len(parts) < 2:
        return None
    time_str = parts[1]
    try:
        hours = int(time_str[:2])
        minutes = int(time_str[2:4])
        seconds = float(time_str[4:])
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError):
        return None

def nmea_time_to_tow(utc_seconds, date):
    """Convert NMEA UTC time to GPS TOW (milliseconds) and GPS week."""
    delta = date - GPS_EPOCH
    total_days = delta.days
    gps_week = total_days // 7
    day_of_week = total_days % 7
    gps_seconds = utc_seconds + LEAP_SECONDS
    tow_ms = (day_of_week * SECONDS_PER_DAY + gps_seconds) * MS_PER_SECOND
    return tow_ms, gps_week

def tow_to_utc(tow_ms, gps_week):
    """Convert GPS TOW and week to UTC datetime."""
    tow_seconds = tow_ms // MS_PER_SECOND
    days = tow_seconds // SECONDS_PER_DAY
    seconds_in_day = tow_seconds % SECONDS_PER_DAY
    gps_seconds = gps_week * SECONDS_PER_WEEK + days * SECONDS_PER_DAY + seconds_in_day - LEAP_SECONDS
    utc_time = GPS_EPOCH + datetime.timedelta(seconds=gps_seconds)
    return utc_time

def compute_crc24q(data):
    """Compute CRC-24Q (used by RTCM)"""
    crc = 0
    poly = 0x1864CFB
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= poly
    return crc & 0xFFFFFF

def parse_rtcm_message(hex_str):
    """Parse RTCM message to extract message type, TOW, and CRC check."""
    normalized_hex = normalize_hex_string(hex_str)
    if not normalized_hex.startswith('D3'):
        print(f"Invalid RTCM message: does not start with D3")
        return None, None
    try:
        bytes_data = bytes.fromhex(normalized_hex)
        if len(bytes_data) < 6:
            print(f"Invalid RTCM message: too short, length {len(bytes_data)}")
            return None, None
        length = int.from_bytes(bytes_data[1:3], 'big') & 0x3FF
        if len(bytes_data) < length + 6:
            print(f"Invalid RTCM message: incomplete length {length}, available {len(bytes_data)-6}")
            return None, None
        msg_num_bits = int.from_bytes(bytes_data[3:5], 'big') >> 4
        msg_num = msg_num_bits & 0xFFF
        if msg_num not in VALID_RTCM_TYPES:
            print(f"Skipping message type {msg_num}: not in {VALID_RTCM_TYPES}")
            return None, None
        if len(bytes_data) < 10:
            print(f"Message {msg_num}: not enough data for TOW")
            return None, None

        # Extract TOW (Time of Week)
        tow_bits = int.from_bytes(bytes_data[6:10], 'big') >> 2
        tow_ms = tow_bits & 0x3FFFFFFF

        # Extract CRC from last 3 bytes
        actual_crc = int.from_bytes(bytes_data[-3:], byteorder='big')
        calculated_crc = compute_crc24q(bytes_data[:len(bytes_data) - 3])

        if calculated_crc == actual_crc:
            print(f"CRC Check Passed: 0x{calculated_crc:06X}")
        else:
            print(f"CRC Check Failed: expected 0x{actual_crc:06X}, got 0x{calculated_crc:06X}")

        return msg_num, tow_ms
    except ValueError as e:
        print(f"Error parsing RTCM: non-hexadecimal number in fromhex() - {e}")
        return None, None
    except Exception as e:
        print(f"Error parsing RTCM: {e}")
        return None, None

def main():
    """Process NMEA and RTCM data to calculate UTC and compare TOWs with CRC."""
    date = datetime.datetime(2025, 6, 5)
    nmea_data = [
        "$GPGGA,081137.000,2951.7592674,N,07754.0120276,E,1,20,0.9,251.131,M,-34.800,M,,0000*7E"
    ]
    rtcm_data = [
        "D3 1 4C 43 59 50 59 6F 33 E0 0 20 4 25 21 24 0 0 0 0 20 20 40 80 77 E7 7F FF 26 29 24 21 A4 23 A9 22 0 0 0 0 34 12 7F D7 B CE E AE 40 3E 4 2B F1 58 1B 7F C9 7D 99 F8 48 11 0 64 F1 E2 1F 33 39 F3 22 20 D A 31 45 36 D A 52 63 7 B0 0 7B 18 86 E7 C1 BD 54 1D 3 67 DA 6E FE C2 D7 EB 49 E3 5 DE 41 13 64 12 4E 43 72 75 F8 77 71 E2 77 16 F 74 5D FC 4E 37 EA 69 7E A6 5F E0 C7 77 74 F 88 BF 78 83 37 C7 5A 77 CC 5E 7F CC 5D B8 15 0 50 1F B5 D0 1F 12 D8 1B BC 80 6F 76 78 74 18 27 F6 98 BF FA DA 87 FA DA 2F 8C 52 A7 90 DF 77 90 3B CF 90 AE 2F D7 E4 77 DC 73 5F DC 73 8F DD 36 9F F0 DC 3F FA E1 7F FA 3D 47 F7 68 CF DD BB 8F E1 FC 7 E1 FC 3A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 2B 4A D2 B4 AD 20 0 0 2 A5 99 A9 D8 D 65 87 62 6A B5 D3 C0 F2 5C 62 DB 9A F1 C 96 E6 97 B0 DC B6 2B 5B 62 39 EE F5 D4 33 AD EE 5B DB 37 B6 2 A0 5 4E A 9C 15 47 48 7E 91 DC 89 39 13 F2 27 DD 43 BA 7F 74 FE EA 11 CA 23 94 87 29 E 54 DA 53 B4 9B 69 36 D2 B1 8F C3  "
    ]

    # Process NMEA
    utc_seconds = parse_nmea_gga(nmea_data[0])
    if utc_seconds is None:
        print("Failed to parse NMEA GGA sentence")
        return
    nmea_tow_ms, gps_week = nmea_time_to_tow(utc_seconds, date)
    utc_time_str = f"{int(utc_seconds//3600):02d}:{int((utc_seconds%3600)//60):02d}:{utc_seconds%60:06.3f}"
    print(f"NMEA UTC: {utc_time_str}, TOW: {nmea_tow_ms} ms, GPS Week: {gps_week}")

    # Process RTCM
    msg_type, rtcm_tow_ms = parse_rtcm_message(rtcm_data[0])
    if msg_type is None or rtcm_tow_ms is None:
        print("Failed to parse RTCM message")
        return
    print(f"RTCM Msg Type: {msg_type}, TOW: {rtcm_tow_ms} ms")

    # Calculate UTC from RTCM TOW
    rtcm_utc = tow_to_utc(rtcm_tow_ms, gps_week)
    print(f"RTCM UTC: {rtcm_utc.strftime('%Y-%m-%d %H:%M:%S')}")

    # Compare TOWs
    time_diff = abs(nmea_tow_ms - rtcm_tow_ms)
    if time_diff <= 1000:
        print(f"NMEA and RTCM TOWs match within 1000 ms (diff: {time_diff} ms)")
    else:
        print(f"NMEA and RTCM TOWs do not match (diff: {time_diff} ms)")

if __name__ == "__main__":
    main()
