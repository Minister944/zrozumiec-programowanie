%include "nasm/vm.inc"


; reset alarm
  vset r0, 0
  voutb 0x71, r0
  voutb 0x71, r0

; put 1 sec in alarm clock
  vset r0, 250
  vmov r1, r0
  vset r2, 8
  vshr r1, r2
  vset r2, 0xff
  vand r0, r2
  vand r1, r2
  voutb 0x71, r1
  voutb 0x71, r0

; set up interrupt
  ; timer
  vset r0, int_8
  vcrl 0x108, r0
  ; keyboard
  vset r0, int_9
  vcrl 0x109, r0
;turn on interrupts
  vset r0, 1 
  vcrl 0x110, r0
  voutb 0x70, r0 
  voutb 0x22, r0

; Enter an infinite loop.
infloop:
  vjmp infloop

; Interrupt.
int_8:
  vcall print
  vset r0, 1 
  vcrl 0x110, r0
  voutb 0x70, r0 
  voutb 0x22, r0
  viret

int_9:
  vcall set
  vset r4, data
  vset r1, 0
  vset r2, 1
  vset r3, 0xa
  while_data:
    vinb 0x21, r0  ; Any data on STDIN?
    vcmp r0, r1
    vjz end_of_data  ; Nope, go away.

    vinb 0x20, r0 ; read one char
    vcmp r0, r3
    vjz end_of_data  ; Nope, go away.

    vstb r4, r0
    vadd r4, r2
    vjmp while_data
  end_of_data:
    vstb r4, r3 ; newline character
    vset r0, 1 
    voutb 0x70, r0 
    voutb 0x22, r0
    vcrl 0x110, r0
    viret

set:
  vset r0, 0
  vset r1, 1
  vset r4, data
  set_loop:
    ; Pobierz bajt spod adresu z R4.
    vldb r2, r4
    vinb 0x21, r8
    ; Jesli to zero, wyjdź z pętli.
    vcmp r2, r0
    vjz set_end

    ; W przeciwym wypadku, nadpisz na 0.
    vstb r4, r0
    ; Przesuń r4 na kolejny znak i idź na początek pętli.
    vadd r4, r1
    vjmp set_loop
  set_end:
    vret

print:
  vset r4, data
  vxor r0, r0
  vset r1, 1
  print_loop:
    ; Pobierz bajt spod adresu z R0.
    vldb r2, r4

    ; Jesli to zero, wyjdź z pętli.
    vcmp r2, r0
    vjz end

    ; W przeciwym wypadku, wypisz znak na konsoli.
    voutb 0x20, r2

    ; Przesuń r4 na kolejny znak i idź na początek pętli.
    vadd r4, r1
    vjmp print_loop
  end:
    vret

data:
  db "example text", 0xa, 0