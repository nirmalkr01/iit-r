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
        "D3 1 AB 44 99 50 59 6F 53 22 0 20 8 38 90 5 40 0 0 0 4 0 88 80 7F FF FF FF FA B2 9A CA 92 C2 7A C2 D2 A8 0 0 0 0 4B 38 E7 74 DB 9E E6 D2 77 83 B5 DE F0 FE 4B F6 87 F4 40 3B FE F6 9 50 3F 0 62 E5 FC BE 6A BA E7 2E 36 70 5D 94 57 9 48 43 94 F2 89 4D 73 17 3B 41 72 AB 97 A2 F9 77 7E 85 53 18 4F A9 5 59 58 52 F1 E6 AE 26 75 76 E7 B7 DE 78 7D E1 1A 2E 12 DD E1 A2 E6 18 90 67 28 46 78 C3 E7 EF BE 7D C9 9B 5B 49 D4 A5 9D F2 51 DE E8 7C F3 7F D3 FC 7D C3 57 D9 8F 79 7E 9A F9 AF 48 F9 CD 21 79 C9 8F 85 18 96 85 23 A7 85 3E B 85 36 EE 5 D9 86 85 D2 BA 85 E9 A3 85 E2 7C 81 56 90 1 3C 69 1 56 CB 1 4C 19 79 B0 B2 79 D8 9F 79 EC 9 F9 E4 DD 78 47 F4 F8 4C CD 78 67 30 F8 5C 72 F9 C5 B7 F9 E2 DD 79 FD 43 F9 F2 94 86 D1 E8 87 51 27 87 6E D1 7 6B E 7F 42 9D 7F 4F 92 FF 6D 5B 7F 62 94 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 2D 4B 52 D4 B5 0 0 0 0 5 41 71 62 16 75 ED 8D 69 D8 54 4D 33 53 72 C5 A7 89 67 B7 DD 21 5E DD D4 C5 9D 76 E3 D6 85 3B 64 5F D5 94 C1 3A D5 13 55 6D 78 64 B6 81 30 62 60 84 C0 49 7F F4 5D E8 B9 D1 67 A2 B8 A8 B1 51 A2 A2 C5 44 74 46 E8 8F D1 B A2 30 71 E0 E3 E1 C8 3 91 7F 7D FF 7 FE 7 FB FF 51 7E A3 3D 44 FA 8C 5 A7 B 52 16 90 2D 47 F7 2F EF 5F DC 7F B8 80 4C 54 7B  "
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
