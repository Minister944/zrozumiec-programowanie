%include "nasm/vm.inc"

vset r2, 0xFFFF
vset r1, 1
vset r0, 0 

vset r3, 0x1
vstb r2, r3
vadd r2, r1
vstb r2, r0
vadd r2, r1
vset r3, 0x41
vstb r2, r3
vadd r2, r1
vstb r2, r0
vadd r2, r1
vstb r2, r0
vadd r2, r1
vstb r2, r0
vadd r2, r1
vset r3, 0xF2
vstb r2, r3
vadd r2, r1
vstb r2, r0
vadd r2, r1
vset r3, 0x20
vstb r2, r3
vadd r2, r1
vset r3, 0xFF
vstb r2, r3
vadd r2, r1

vset r2, 0xFFFF
vjmpr r2
voff