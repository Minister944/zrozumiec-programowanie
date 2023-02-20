%include "vm/vm.inc"

; Wypisz dane, znak po znaku.
vset r1, 0
vset r2, 1
start_loop:
  vadd r1, r2
  vjmp start_loop

voff


