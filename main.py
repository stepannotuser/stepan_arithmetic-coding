from math import ceil, floor
import struct
from collections import Counter
import filecmp

def read_input(filename):
    with open(filename, "rb") as code_txt:
        return code_txt.read()

def add_padding(enc):
    padding = 8 - len(enc) % 8
    enc += [0] * padding
    return enc, padding

def write_encoded_data(file_path, len_txt, dictionary, enc, last_sim):
    padding = 8 - len(enc) % 8
    enc += [0] * padding    

    with open(file_path, "wb") as output_file:
        output_file.write(len_txt.to_bytes(4, 'little'))
        output_file.write(len(dictionary).to_bytes(1, 'little'))
        output_file.write(padding.to_bytes(1, 'little'))
        
        codes_str = b"".join([struct.pack("B", byte) + struct.pack(">I", freq) for byte, freq in dictionary.items()])
        output_file.write(codes_str)

        encoded_bytes = bytes(int(''.join(map(str, enc[i:i+8])), 2) for i in range(0, len(enc), 8))
        output_file.write(encoded_bytes)
        output_file.write(struct.pack("B", last_sim))

def read_encoded_data(file_path):
    with open(file_path, "rb") as encoded_file:
        txt_len, slo_len, new_padding = [int.from_bytes(encoded_file.read(n), 'little') for n in (4, 1, 1)]

        new_slov = {int.from_bytes(encoded_file.read(1), 'little'): int.from_bytes(encoded_file.read(4), 'big') for _ in range(slo_len)}
        
        data_bits = encoded_file.read()
        encoded_text = ''.join([bin(byte)[2:].rjust(8, '0') for byte in data_bits])[:-new_padding]
        new_last_sim = data_bits[-1]

    encoded_txt = [int(bit) for bit in encoded_text]

    return txt_len, new_slov, encoded_txt, new_last_sim

def write_decoded_text_to_file(file_path, decoded_text):
    with open(file_path, "wb") as file:
        file.write(decoded_text)

def arithmetic_encode(src):
    max_val, third, qtr, half = 4294967295, 3221225472, 1073741824, 2147483648

    freq = Counter(src)
    prob = {ch: cnt / len(src) for ch, cnt in freq.items()}

    cum_freq = [0.0]
    for p in prob.values():
        cum_freq.append(cum_freq[-1] + p)
    cum_freq.pop()
    cum_freq = {k: v for k, v in zip(prob.keys(), cum_freq)}

    enc_nums = []
    lb, ub = 0, max_val
    strdl = 0

    for b in src:
        rng = ub - lb + 1
        lb += ceil(rng * cum_freq[b])
        ub = lb + floor(rng * prob[b])

        tmp_nums = []
        while True:
            if ub < half:
                tmp_nums.append(0)
                tmp_nums.extend([1] * strdl)
                strdl = 0
            elif lb >= half:
                tmp_nums.append(1)
                tmp_nums.extend([0] * strdl)
                strdl = 0
                lb -= half
                ub -= half
            elif lb >= qtr and ub < third:
                strdl += 1
                lb -= qtr
                ub -= qtr
            else:
                break

            if tmp_nums:
                enc_nums.extend(tmp_nums)
                tmp_nums = []

            lb *= 2
            ub = 2 * ub + 1

    enc_nums.extend([0] + [1] * strdl if lb < qtr else [1] + [0] * strdl)

    return enc_nums

def arithmetic_decode(enc, prob, len_txt):
    p, max_val, third, qtr, half = 32, 4294967295, 3221225472, 1073741824, 2147483648

    alph = list(prob)
    cum_freq = [0]
    for i in prob:
        cum_freq.append(cum_freq[-1] + prob[i])
    cum_freq.pop()

    prob = list(prob.values())

    enc.extend(p * [0])
    dec_sym = len_txt * [0]

    cur_val = int(''.join(str(a) for a in enc[0:p]), 2)
    bit_pos = p
    lb, ub = 0, max_val

    dec_pos = 0
    while 1:
        rng = ub - lb + 1
        sym_idx = len(cum_freq)
        val = (cur_val - lb) / rng
        for i, item in enumerate(cum_freq):
            if item >= val:
                sym_idx = i
                break
        sym_idx -= 1
        dec_sym[dec_pos] = alph[sym_idx]

        lb = lb + ceil(cum_freq[sym_idx] * rng)
        ub = lb + floor(prob[sym_idx] * rng)

        while True:
            if ub < half:
                pass
            elif lb >= half:
                lb -= half
                ub -= half
                cur_val -= half
            elif lb >= qtr and ub < third:
                lb -= qtr
                ub -= qtr
                cur_val -= qtr
            else:
                break

            lb *= 2
            ub = 2 * ub + 1
            cur_val = 2 * cur_val + enc[bit_pos]
            bit_pos += 1
            if bit_pos == len(enc) + 1:
                break

        dec_pos += 1
        if dec_pos == len_txt or bit_pos == len(enc) + 1:
            break
    return bytearray(bytes(dec_sym))

def main():
    in_text = read_input("input.txt")
    len_txt = len(in_text)
    last_sim = in_text[-1]
    dictionary = dict(Counter(in_text))
    
    enc = arithmetic_encode(in_text)
    
    write_encoded_data("encoded", len_txt, dictionary, enc, last_sim)
    txt_len, new_slov, encoded_txt, new_last_sim = read_encoded_data("encoded")
    
    decoded_text = arithmetic_decode(encoded_txt, {symbol: count / txt_len for symbol, count in new_slov.items()}, txt_len)
    decoded_text[-1] = new_last_sim
    
    write_decoded_text_to_file("output.txt", decoded_text)


    print(filecmp.cmp('input.txt', 'output.txt')) # сравнение файлов input.txt и output.txt

if __name__ == "__main__":
    main()
