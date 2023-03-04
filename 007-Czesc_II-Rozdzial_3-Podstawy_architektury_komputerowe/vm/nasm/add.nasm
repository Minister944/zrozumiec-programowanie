%include "nasm/vm.inc"

; Wypisz dane, znak po znaku.
vxor r1, r1 ;pierwsza liczba
vset r3, 48
vset r4, 10
vset r0, 0xa
vset r6, 1

first_number:
  vinb 0x20, r2

  vcmp r2, r0     ; czy to znak konca lini
	vje end_first_number

  vsub r2, r3

  vmul r1, r4
  vadd r1, r2

  vjmp first_number
end_first_number:
; druga liczba
vxor r5, r5
vxor r2, r2
two_number:
  vinb 0x20, r2

  vcmp r2, r0
	vje end_two_number

  vsub r2, r3

  vmul r5, r4
  vadd r5, r2

  vjmp two_number
end_two_number:

; dodawanie dwoch liczb
vadd r1, r5

vxor r3, r3
vxor r5, r5 ; licznik ilosci
vset r7, 48
push_nubmer:
  vmov r11, r1
  vmod r11, r4
  vadd r11, r7
  vpush r11

  vadd r5, r6 ; odanie 1 do licznika

  vdiv r1, r4
  vcmp r1, r3
  vjne push_nubmer

print_numbers:
	vpop r10                 ; sciagamy cyfre ze stosu
	voutb 0x20, r10          ; zapisujemy bajt na wyjscie
	vsub r5, r6              ; odejmujemy od licznika
	vcmp r5, r3              ; sprawdzamy czy licznik jest rowny 0, czyli czy wypisalismy juz cala liczbe
	vjne print_numbers
	voutb 0x20, r0




voff
