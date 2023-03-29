# string = "123444"

# r1 = 0
# for a in string:
#     a = int(a)
#     r1 = r1 * 10
#     r1 = r1 + a

# print(r1)


# r1 = 467678343
# r11 = 0
# stos = []
# while True:
#     r11 = r1
#     r11 = r11 % 10
#     stos.append(r11)
#     r1 = r1 // 10

#     if not r1:
#         break
# print(stos)

########################################################################################################################################################
# code = ",>,>++++++++[<------<------>>-]<<[>[>+>+<<-]>>[<<+>>-]<<<-]>>>++++++[<++++++++>-]<."
# code = "++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>."
# code = ",>++++++[<-------->-],[<+>-]<.,>++++++[<-------->-],[<+>-]<."

# import os

# def get_all_loop(code):
#     final_all_loop = {}
#     help_array = []
#     for index, char in enumerate(code):
#         if char == "[":
#             help_array.append(index)

#         if char == "]":
#             start = help_array.pop()
#             end = index
#             final_all_loop[start] = end
#             final_all_loop[end] = start

#     return final_all_loop


# final_all_loop = get_all_loop(code)

# print("[]:", final_all_loop)


# cells = [0]
# codeptr = 0
# cellptr = 0
# while codeptr < len(code):
#     command = code[codeptr]

#     if command == ">":
#         cellptr += 1
#         if cellptr == len(cells):
#             cells.append(0)

#     if command == "<":
#         cellptr = 0 if cellptr <= 0 else cellptr - 1

#     if command == "+":
#         cells[cellptr] = cells[cellptr] + 1 if cells[cellptr] < 255 else 0

#     if command == "-":
#         cells[cellptr] = cells[cellptr] - 1 if cells[cellptr] > 0 else 255

#     if command == "[" and cells[cellptr] == 0:
#         codeptr = final_all_loop[codeptr]
#     if command == "]" and cells[cellptr] != 0:
#         codeptr = final_all_loop[codeptr]

#     if command == ".":
#         print(chr(cells[cellptr]), end="")
#     if command == ",":
#         cells[cellptr] = ord(os.read(0, 1))

#     codeptr += 1

# print("\ncells: ", cells)
########################################################################################################################################################

import sys

if len(sys.argv) != 3:
    print("Bad args: python test.py hello.bf hello.exe")
    sys.exit()


allow_char = [">", "<", "+", "-", ".", ",", "[", "]"]

f = open(sys.argv[1], "r")
code = f.read()
f.close()
clear_code = ""
for char in code:
    if char in allow_char:
        clear_code += char

print(clear_code)


f = open(sys.argv[2], "wb")


def save_instr(opcode, rd, rs, val, val_len):
    len = 1 + (0 if rd < 0 else 1) + (0 if rs < 0 else 1) + (0 if val < 0 else val_len)
    buf = bytearray([0] * 8)
    buf[0] = opcode
    x = 1
    if rd >= 0:
        buf[x] = rd
        x += 1
    if rs >= 0:
        buf[x] = rs
        x += 1
    if val >= 0:
        buf[x] = val & 0xFF
        buf[x + 1] = (val >> 8) & 0xFF
        buf[x + 2] = (val >> 16) & 0xFF
        buf[x + 3] = (val >> 24) & 0xFF
    f.write(buf[:len])


def write_number_to_pos(pos, number, num_len):
    print("write_number_to_pos:", hex(pos), hex(number), hex(num_len))
    global f
    buf = bytearray(4)
    buf[0] = number & 0xFF
    buf[1] = (number >> 8) & 0xFF
    buf[2] = (number >> 16) & 0xFF
    buf[3] = (number >> 24) & 0xFF

    temp = f.tell()
    f.seek(pos, 0)
    if f.write(buf[:num_len]) != num_len:
        print("Couldn't write the file.")
        f.close()
        exit(0)
    f.seek(temp, 0)


br_stack = []

save_instr(0x1, 0, -1, 0, 4)
# vset r0, 0 ; this 0 will be changed to free memeory address at the end
save_instr(0x0, 1, 0, -1, 0)  # vmov r1, r0 ; r1 will be a memory pointer
save_instr(0x1, 2, -1, 1, 4)  # vset r2, 1 ; used for arithmetical operations
save_instr(0x1, 4, -1, 0, 4)  # vset r4, 0 ; used for comparations

for char in clear_code:
    match char:
        case "+":
            save_instr(0x4, 3, 1, -1, 0)  # vldb r3, r1
            save_instr(0x10, 3, 2, -1, 0)  # vadd r3, r2
            save_instr(0x5, 1, 3, -1, 0)  # vstb t1, r3
        case "-":
            save_instr(0x4, 3, 1, -1, 0)  # vldb r3, r1
            save_instr(0x11, 3, 2, -1, 0)  # vsub r3, r2
            save_instr(0x5, 1, 3, -1, 0)  # vstb t1, r3
        case ">":
            save_instr(0x10, 1, 2, -1, 0)  # vadd r1, r2
        case "<":
            save_instr(0x11, 1, 2, -1, 0)  # vadd r1, r2
        case ".":
            save_instr(0x4, 3, 1, -1, 0)
            # vldb r3, r1
            save_instr(0xF2, -1, 3, 0x20, 1)
            # voutb 0x20, r3
        case "[":
            br_stack.append(f.tell())
            save_instr(0x4, 3, 1, -1, 0)  # vldb r3, r1
            save_instr(0x20, 3, 4, -1, 0)  # vcmp r3, r4
            save_instr(
                0x21, -1, -1, 0, 2
            )  # vjz 0 ; address of the corresponding bracket, will be filled later
        case "]":
            prev = br_stack.pop()
            current = f.tell()
            offset1 = (prev - current - 3) & 0xFFFF
            offset2 = (current - prev - 6) & 0xFFFF
            save_instr(0x40, -1, -1, offset1, 2)
            write_number_to_pos(prev + 7, offset2, 2)
            # czeba wypelnic instr z lini 160

save_instr(0xFF, -1, -1, -1, 0)  # vset r4, 0 ; used for comparations 0x320
free_mem = f.tell()
write_number_to_pos(2, free_mem, 4)

write_number_to_pos(free_mem + 256, -1, 1)
