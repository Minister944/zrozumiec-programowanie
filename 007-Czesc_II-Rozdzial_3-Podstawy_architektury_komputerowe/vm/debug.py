from regs import VMGeneralPurposeRegister
from termcolor import colored


class Debug:
    @staticmethod
    def _debug_print(r, name, argument_bytes, register):
        print(
            f"{r[15].v:0>4x}: {name.ljust(20)}{(argument_bytes).hex().ljust(10)}{register}",
            end="",
        )

    @staticmethod
    def debug_colored(
        opcode_name, r: VMGeneralPurposeRegister, argument_bytes: bytearray | None
    ):
        if opcode_name in [
            "VJZ",
            "VJE",
            "VJNZ",
            "VJNE",
            "VJC",
            "VJB",
            "VJNC",
            "VJAE",
            "VJBE",
            "VJA",
        ]:
            opcode_name = colored(opcode_name, color="white", on_color="on_red")
        elif opcode_name in "VCMP":
            opcode_name = colored(opcode_name, color="black", on_color="on_red")
        elif opcode_name in ["VADD", "VSUB", "VMUL", "VDIV", "VMOD"]:
            opcode_name = colored(opcode_name, color="white", on_color="on_cyan")
        elif opcode_name in ["VJMP", "VJMPR", "VCALL", "VCLLR", "VRET"]:
            opcode_name = colored(opcode_name, color="white", on_color="on_magenta")
        elif opcode_name in [
            "VOR",
            "VAND",
            "VXOR",
            "VNOT",
            "VSHL",
            "VSHR",
        ]:
            opcode_name = colored(opcode_name, color="white", on_color="on_green")
        elif opcode_name in ["VMOV", "VSET", "VLD", "VST", "VLDB", "VSTB"]:
            opcode_name = colored(opcode_name, color="white", on_color="on_yellow")
        else:
            opcode_name = colored(opcode_name, color="white", on_color="on_black")

        r_help = ""
        for i in range(16):
            if i == 14:
                if len(f"{r[i].v:x}") + len(str(r[i].v)) <= 9 and r[i].v != 0:
                    r_help += f"sp={r[i].v:x}({r[i].v})".ljust(14)
                else:
                    r_help += f"sp={r[i].v:x}".ljust(14)
                continue
            if i == 15:
                continue

            if len(f"{r[i].v:x}") + len(str(r[i].v)) <= 9 and r[i].v != 0:
                r_help += f"r{i}={r[i].v:x}({r[i].v})".ljust(14)
            else:
                r_help += f"r{i}={r[i].v:x}".ljust(14)
        Debug._debug_print(r, opcode_name, argument_bytes, r_help)
        print()
