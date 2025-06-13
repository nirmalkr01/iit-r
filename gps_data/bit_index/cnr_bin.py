# Original CNR bytes (from your data)
cnr_hex = [
    0x5C, 0x62, 0xDB, 0x9A, 0xF1, 0x0C, 0x96, 0xE6, 0x97, 0xB0,
    0xDC, 0xB6, 0x2B, 0x5B, 0x62, 0x39, 0xEE, 0xF5, 0xD4, 0x33,
    0xAD, 0xEE, 0x5B, 0xDB, 0x37, 0xB6, 0x02, 0xA0, 0x05, 0x4E,
    0x0A, 0x9C, 0x15, 0x4
]

# Step 1: Carry forward in binary (4 bits)
carry_forward_bin = format(10, '04b')  # 10 decimal = 1010 binary

# Step 2: Convert all hex values to 8-bit binary
hex_binary = ''.join(format(byte, '08b') for byte in cnr_hex)

# Step 3: Concatenate CF and hex binary
full_binary = carry_forward_bin + hex_binary

# Step 4: Display the full binary string
print("Full binary string (CF + data):")
print(full_binary)
print()

# Step 5: Split into 10-bit chunks
chunk_size = 10
binary_chunks = [full_binary[i:i + chunk_size] for i in range(0, len(full_binary), chunk_size)]

# Step 6: Print each group and its decimal value
print("10-bit Groups and Corresponding Decimal Values:")
for idx, chunk in enumerate(binary_chunks):
    if len(chunk) == chunk_size:
        decimal_val = int(chunk, 2)
        print(f"Group {idx + 1:2}: {chunk} -> {decimal_val}")
    else:
        print(f"Group {idx + 1:2}: {chunk:<10} -> Incomplete (ignored)")
