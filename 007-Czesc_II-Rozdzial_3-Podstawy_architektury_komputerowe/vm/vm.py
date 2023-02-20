import codecs
import collections
import os
import sys
import threading

from termcolor import colored
from vm_dev_con import VMDeviceConsole
from vm_dev_timer import VMDeviceTimer
from vm_instr import VM_OPCODES
from vm_memory import VMMemory
from vm_regs import VMGeneralPurposeRegister


def debug_print(r, name, argument_bytes, register):
    print(
        f"{r[15].v:0>4x}: {name.ljust(20)}{(argument_bytes).hex().ljust(10)}{register}",
        end="",
    )


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
            r_help += f"sp={r[i].v:x}"
            continue
        if i == 15:
            continue

        if len(f"{r[i].v:x}") + len(str(r[i].v)) <= 9 and r[i].v != 0:
            r_help += f" r{i}={r[i].v:x}({r[i].v})".ljust(14)
        else:
            r_help += f" r{i}={r[i].v:x}".ljust(14)
    debug_print(r, opcode_name, argument_bytes, r_help)
    print()


class VMInstance(object):
    INSTR_HANDLER = 0
    INSTR_LENGTH = 1
    INT_MEMORY_ERROR = 0
    INT_DIVISION_ERROR = 1
    INT_GENERAL_ERROR = 2
    INT_PIT = 8
    INT_CONSOLE = 9
    FLAG_ZF = 1 << 0
    FLAG_CF = 1 << 1
    CREG_INT_FIRST = 0x100
    CREG_INT_LAST = 0x10F
    CREG_INT_CONTROL = 0x110
    MASKABLE_INTS = [8, 9]

    def __init__(self):
        self.r = [VMGeneralPurposeRegister() for _ in range(16)]
        self.fr = 0
        self.sp = self.r[14]
        self.pc = self.r[15]
        self.mem = VMMemory()
        self.terminated = False
        self.opcodes = VM_OPCODES

        self.sp.v = 0x10000
        self.cr = {}

        # Interrupt registers.
        for creg in range(self.CREG_INT_FIRST, self.CREG_INT_LAST + 1):
            self.cr[creg] = 0xFFFFFFFF

        self.cr[self.CREG_INT_CONTROL] = 0  # Maskable interrupts disabled.

        self.dev_pit = VMDeviceTimer(self)
        self.dev_console = VMDeviceConsole(self)

        self.io = {
            0x20: self.dev_console,
            0x21: self.dev_console,
            0x22: self.dev_console,
            0x70: self.dev_pit,
            0x71: self.dev_pit,
        }

        self.interrupt_queue = []
        self.interrupt_queue_mutex = threading.Lock()

        self.defered_queue = collections.deque()

    def reg(self, r):
        """Given a register ID, returns a reference to the register object. It takes
        only the lower 4 bits of the ID into account ignoring any upper bits.
        """
        return self.r[r & 0xF]

    def crash(self):
        """Terminates the virtual machine on critical error."""
        self.terminated = True
        print("The virtual machine entered an erroneous state and is terminating.")
        print("Register values at termination:")
        for ri, r in enumerate(vm.r):
            print("  r%u = %x" % (ri, r.v))

    def interrupt(self, i):
        """Add an interrupt to the interrupt queue."""
        with self.interrupt_queue_mutex:
            self.interrupt_queue.append(i)

    def _fetch_pending_interrupt(self):
        """Returns a pending interrupt to be processed. If maskable interrupts are
        disabled, returns a non-maskable interrupt (NMI) if available. If no
        interrupts are available for processing, returns None.
        """
        with self.interrupt_queue_mutex:
            if not self.interrupt_queue:
                return None

            # In disable-interrupts state we can process only non-maskable interrupts
            # (faults).
            if self.cr[self.CREG_INT_CONTROL] & 1 == 0:
                # Maskable interrupts disabled. Find a non-maskable one.
                for i, interrupt in enumerate(self.interrupt_queue):
                    if interrupt not in self.MASKABLE_INTS:
                        return self.interrupt_queue.pop(i)

                # No non-maskable interrupts found.
                return None

            # Return the first interrupt available.
            return self.interrupt_queue.pop()

    def _process_interrupt_queue(self):
        """Processes an interrupt if available."""
        i = self._fetch_pending_interrupt()

        if i is None:
            return True

        # Save context.
        tmp_sp = self.sp.v
        for r in [rr.v for rr in self.r] + [self.fr]:
            tmp_sp -= 4
            if self.mem.store_dword(tmp_sp, r) is False:
                # Since there is no way to save state, and therefore no way to
                # recover, crash the machine.
                self.crash()
                return False

        self.sp.v = tmp_sp
        self.pc.v = self.cr[self.CREG_INT_FIRST + (i & 0xF)]

        # Turn off maskable interrupts.
        self.cr[self.CREG_INT_CONTROL] &= 0xFFFFFFFE
        return True

    def load_memory_from_file(self, addr, name):
        """Loads up to 64KB of data from a file into RAM."""
        with open(name, "rb") as f:
            # Read at most the size of RAM.
            data = f.read(64 * 1024)
        return self.mem.store_many(addr, data)

    def run_single_step(self):
        # If there is any interrupt on the queue, we need to know about it now.
        if self._process_interrupt_queue() is False:
            # Something failed hard.
            return

        # Check if there is anything in the defered queue. If so, process it now.

        while self.defered_queue:
            action = self.defered_queue.pop()
            action()

        # Normal execution.
        opcode = self.mem.fetch_byte(self.pc.v)
        if opcode is None:
            self.interrupt(self.INT_MEMORY_ERROR)
            return

        if opcode not in self.opcodes:
            self.interrupt(self.INT_GENERAL_ERROR)
            return

        length = self.opcodes[opcode][self.INSTR_LENGTH]
        argument_bytes = self.mem.fetch_many(self.pc.v + 1, length)
        if argument_bytes is None:
            self.interrupt(self.INT_MEMORY_ERROR)
            return

        handler = self.opcodes[opcode][self.INSTR_HANDLER]
        # Uncomment this line to get a dump of executed instructions.
        debug_colored(handler.__name__, self.r, argument_bytes)
        # if handler.__name__ in [
        #     "VJZ",
        #     "VJE",
        #     "VJNZ",
        #     "VJNE",
        #     "VJC",
        #     "VJB",
        #     "VJNC",
        #     "VJAE",
        #     "VJBE",
        #     "VJA",
        # ]:
        #     name = colored(handler.__name__, on_color="on_red")
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {name: ^13}  {argument_bytes.hex(): <11}",
        #         end="",
        #     )
        # elif handler.__name__ in "VCMP":
        #     name = colored(handler.__name__, color="black", on_color="on_red")
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {name: ^13}  {argument_bytes.hex(): <11}",
        #         end="",
        #     )

        # elif handler.__name__ in ["VADD", "VSUB", "VMUL", "VDIV", "VMOD"]:
        #     name = colored(handler.__name__, on_color="on_cyan")
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {name: ^13}  {argument_bytes.hex(): <11}",
        #         end="",
        #     )
        # elif handler.__name__ in ["VJMP", "VJMPR", "VCALL", "VCLLR", "VRET"]:
        #     name = colored(handler.__name__, on_color="on_magenta")
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {name: ^13}  {argument_bytes.hex(): <11}",
        #         end="",
        #     )
        # elif handler.__name__ in [
        #     "VOR",
        #     "VAND",
        #     "VXOR",
        #     "VNOT",
        #     "VSHL",
        #     "VSHR",
        # ]:
        #     name = colored(handler.__name__, on_color="on_green")
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {name: ^13}  {argument_bytes.hex(): <11}",
        #         end="",
        #     )
        # elif handler.__name__ in ["VMOV", "VSET", "VLD", "VST", "VLDB", "VSTB"]:
        #     name = colored(handler.__name__, color="white", on_color="on_yellow")
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {name: ^13}  {argument_bytes.hex(): <11}",
        #         end="",
        #     )
        # else:
        #     print(
        #         f"{self.pc.v.to_bytes(2, byteorder='big').hex()}: {handler.__name__: <5} {argument_bytes.hex(): <11}",
        #         end="",
        #     )
        # for i in range(16):
        #     # if i == 4:
        #     #     r = f"sp={self.r[i].v.to_bytes(2, byteorder='big').hex()}"
        #     #     print(f"{r: ^10}", end="")
        #     #     continue
        #     if i == 14:
        #         r = f"sp={self.r[i].v}"
        #         print(f"{r: ^7}", end="")
        #         continue
        #     if i == 15:
        #         continue
        #     r = f"r{i}={self.r[i].v}"
        #     print(f"{r: <10}", end="")
        # print()

        with open("ramcopy", "wb") as f:
            # Read at most the size of RAM.
            f.write(self.mem._mem)
        self.pc.v += 1 + length
        handler(self, argument_bytes)

    def run(self):
        while not self.terminated:
            self.run_single_step()

        self.dev_console.terminate()
        self.dev_pit.terminate()

        # Simple (though ugly) method to make sure all threads exit.
        os._exit(0)


__all__ = [VMInstance]

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: vm.py <filename>")
        sys.exit(1)

    vm = VMInstance()
    vm.load_memory_from_file(0, sys.argv[1])
    vm.run()
