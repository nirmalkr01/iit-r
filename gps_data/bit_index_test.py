def hex_to_binary_with_index(hex_string, label, start_index=0, limit_bits=None):
    print(f"\n{label} (Hex): {hex_string}")
    bytes_list = hex_string.strip().split()
    
    index_ranges = []
    binary_lines = []
    total_binary = ''
    current_index = start_index

    for i, byte in enumerate(bytes_list):
        byte_int = int(byte, 16)
        byte_bin = f"{byte_int:08b}"
        total_binary += byte_bin
        start = current_index
        end = current_index + 7
        index_ranges.append((start, end))
        binary_lines.append(byte_bin)
        current_index += 8

    if limit_bits is not None:
        total_binary = total_binary[:limit_bits]

    print(f"\n{label} Bytes Breakdown:")
    for i in range(len(bytes_list)):
        print(f"Byte {i} ({bytes_list[i]}): {binary_lines[i]} \t(Index Range: {index_ranges[i][0]}–{index_ranges[i][1]})")
    
    # Find positions of 1s (index starting from 0)
    set_bit_indexes = [i+1 for i, bit in enumerate(total_binary) if bit == '1']
    print(f"\n✅ {label} Indexes with 1s (starting from 0): {set_bit_indexes}\n")
    return set_bit_indexes


# Input data
sats_hex = "02 18 1A 80 00 00 00 00"
mask_hex = "20 00 00 80"
ncell_hex = "7D 56"  # Only 14 bits are valid

# Process and print
sats_indexes = hex_to_binary_with_index(sats_hex, "SATS", start_index=0)
mask_indexes = hex_to_binary_with_index(mask_hex, "MASK", start_index=0)
ncell_indexes = hex_to_binary_with_index(ncell_hex, "NCELL", start_index=0, limit_bits=14)
