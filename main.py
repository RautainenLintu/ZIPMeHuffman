# The function asks for file name until it is correct
def ask_for_file():
    while True:
        print("Enter filename:")
        filename = input()
        if len(filename) <= 0:
            print("The file name is empty. Try again")
        try:
            file = open(filename)
            file.close()
        except FileNotFoundError:
            print("The file is not found. Please check the existence and location of the file, then try again")
        else:
            break
    return filename


# Returns the list of 256 elements, where i-th element represents the number of times byte i is presented in the file
def counting_bytes(filename):
    total_number = 0
    bytes_number = [0] * 256
    file = open(filename, "br")
    file_bytes = file.read()
    print("Binary representation of the file:")
    print(file_bytes)
    for byte in file_bytes:
        bytes_number[byte] += 1
        total_number += 1
    file.close()
    print("Bytes counted:")
    print(bytes_number)
    print("Total bytes:")
    print(total_number)
    return total_number, bytes_number


# Returns map of (int : list), where int is frequency of a byte and list contains all the bytes with that same frequency
def creating_model(bytes_number):
    print("Model is being created:")
    unsorted_model = {}
    for i in range(256):
        unsorted_model[i] = bytes_number[i]
    for i in unsorted_model:
        if unsorted_model[i] == 0:
            unsorted_model.pop(i)
    print(unsorted_model)
    print("Model is being sorted:")
    sorted_list = sorted(unsorted_model.values(), reverse=True)
    sorted_model = {}
    for value in sorted_list:
        sorted_model[value] = []
    for i in range(256):
        if bytes_number[i] != 0:
            sorted_model[bytes_number[i]].append(i)
    print(sorted_model)
    return sorted_model


# Returns the array of 256 elements, where the i-th element represents encoding for the byte i
def creating_code(total_count, model):
    model_copy = model
    code = [""] * 256
    while total_count not in list(model_copy.keys()):
        minfrequency1 = sorted(model_copy.keys())[0]
        minfrequency2 = minfrequency1
        minfrequency_charlist = model_copy[minfrequency1]
        if len(minfrequency_charlist) == 0:
            model_copy.pop(minfrequency1)
            continue
        rarest_chars1 = minfrequency_charlist.pop()
        if len(minfrequency_charlist) != 0:
            rarest_chars2 = minfrequency_charlist.pop()
            model_copy[minfrequency1] = minfrequency_charlist
        else:
            model_copy.pop(minfrequency1)
            minfrequency2 = sorted(model_copy.keys())[0]
            minfrequency_charlist = model_copy[minfrequency2]
            rarest_chars2 = minfrequency_charlist.pop()
            if len(minfrequency_charlist) == 0:
                model_copy.pop(minfrequency2)
            else:
                model_copy[minfrequency2] = minfrequency_charlist
        merged_list = []
        if type(rarest_chars1) is list:
            for i in rarest_chars1:
                code[i] = "0" + code[i]
                merged_list.append(i)
        else:
            code[rarest_chars1] = "0" + code[rarest_chars1]
            merged_list.append(rarest_chars1)
        if type(rarest_chars2) is list:
            for i in rarest_chars2:
                code[i] = "1" + code[i]
                merged_list.append(i)
        else:
            code[rarest_chars2] = "1" + code[rarest_chars2]
            merged_list.append(rarest_chars2)
        if (minfrequency1 + minfrequency2) in list(model_copy.keys()):
            model_copy[minfrequency1 + minfrequency2].append(merged_list)
        else:
            model_copy[minfrequency1 + minfrequency2] = [merged_list]
    print("Code created:")
    print({i: code[i] for i in range(256)})
    return code


# Function writes code to zmh-file: the i-th byte is written, then the length of coding word, then coding word
def write_code_to_file(output_file, code):
    print("Code is being written to file...")
    for i in range(256):
        output_file.write(i.to_bytes(1, "big"))
        output_file.write(len(code[i]).to_bytes(1, "big"))
        if code[i] != "":
            output_file.write(bytes(code[i], "utf-8"))
    output_file.write(bytes("\n", "utf-8"))


# Function writes encoded data of the initial file to zmh-file using the generated code
def write_encoded_data_to_file(input_file, output_file, code):
    print("Data is being written to file...")
    file_data = input_file.read()
    encoding = ""
    for symbol in file_data:
        temp_encoding = encoding + code[symbol]
        ending = len(temp_encoding) // 8
        encoding = temp_encoding[(ending * 8):]
        for i in range(0, ending):
            output_file.write((int(temp_encoding[i * 8: (i + 1) * 8], 2)).to_bytes(1, "big"))
    remainder = len(encoding)
    temp_encoding = encoding + "0" * (8 - remainder)
    output_file.write(int(temp_encoding, 2).to_bytes(1, "big"))
    output_file.write(remainder.to_bytes(1, "big"))


# Returns code written in the file as dictionary: {codeword : byte} (inverted format, if comparing with encoding to zmh)
def read_code_from_file(input_file):
    code = {}
    symbol = input_file.read(1)
    for i in range(256):
        byte = ord(symbol)
        length = ord(input_file.read(1))
        if length > 0:
            codeword = ""
            decoded_symbols = map(chr, input_file.read(length))
            for symbol in decoded_symbols:
                codeword += symbol
            code[codeword] = byte
        symbol = input_file.read(1)
    return code


# Transforms message into a binary string, adds additional zeros if required
def retrieve_binary_string(message):
    bin_str = (str(bin(message))[2:])
    bin_str = "0" * (8 - len(bin_str)) + bin_str
    return bin_str


# Searches for coding word in fragment, writes decoded symbol to output file, returns the remainder of a fragment
def decode_word_fragment(output_file, codes_dict, word_fragment):
    word = ""
    for i in range(len(word_fragment)):
        word += word_fragment[i]
        if word in codes_dict.keys():
            output_file.write(codes_dict[word].to_bytes(1, "big"))
            word = ""
    return word


# Reads and decodes encoded data from files
def read_data_from_file(input_file, output_file, code):
    bytes_message = []
    bytes_message.append(ord(input_file.read(1)))
    message = "".join(map(chr, bytes_message))
    bytes_message.append(ord(input_file.read(1)))
    symbol = input_file.read(1)
    remainder = ""
    while True:
        remainder = remainder + retrieve_binary_string(bytes_message[0])
        remainder = decode_word_fragment(output_file, code, remainder)
        for i in range(0, len(bytes_message) - 1):
            bytes_message[i] = bytes_message[i + 1]
        bytes_message[len(bytes_message) - 1] = ord(symbol)
        message = message[1:len(message)] + "".join(map(chr, symbol))
        symbol = input_file.read(1)
        if symbol == b'':
            break
    last_fragment = retrieve_binary_string(bytes_message[0])
    last_fragment = remainder + last_fragment[0:bytes_message[1]]
    decode_word_fragment(output_file, code, last_fragment)


while True:
    filename = ask_for_file()
    print("To convert to .zmh enter 1, to convert from .zmh enter 2")
    mode = input()
    while mode != '1' and mode != '2':
        print("Invalid mode. Try again")
        mode = input()
    if mode == '1':
        total_number, bytes_number = counting_bytes(filename)
        model = creating_model(bytes_number)
        code = creating_code(total_number, model)
        output_file = open(filename + "." + "zmh", "bw")
        write_code_to_file(output_file, code)
        input_file = open(filename, "rb")
        write_encoded_data_to_file(input_file, output_file, code)
        input_file.close()
        output_file.close()
    if mode == '2':
        filename_array = filename.split(".")
        extension = filename_array[len(filename_array) - 1]
        if extension != "zmh":
            print("Invalid format. You can only use zmh files. Try again")
            print("Enter filename:")
            filename = input()
            filename_array = filename.split(".")
            extension = filename_array[len(filename_array) - 1]
        input_file = open(filename, "rb")
        output_file = open("decodedfromzmh_" + filename_array[0] + "." + (filename_array[len(filename_array) - 2]), "wb")
        print("Code is being read from file...")
        code = read_code_from_file(input_file)
        print("Code reading finished:")
        print(code)
        read_data_from_file(input_file, output_file, code)
        input_file.close()
        output_file.close()
    print("File converted")
    input("Press Enter to execute the program again.")
