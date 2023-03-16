%include "nasm/vm.inc"
%define PROG_SIZE 100
%define MEM_SIZE 100

vset r4, prog
vxor r0, r0
vset r1, 1

vset r12, '['
vset r13, ']'

vxor r3, r3 ;index
vxor r5, r5 ;
vset r6, brack ; brack index
brack_loop:
  ; Pobierz bajt spod adresu z R0.
  vldb r2, r4

  ; Jesli to zero, wyjdź z pętli.
  vcmp r2, r0
  vjz .end

  ; W przeciwym wypadku, wypisz znak na konsoli.
  voutb 0x20, r2

  ; jesli [ dodaj do stosu index
  vcmp r2, r12
  vjne .continue
    vpush r3
  .continue:


  ; jesli ] no to zabawa
  vcmp r2, r13
  vjne .continue2
    vpop r5

    vstb r6, r5
    vadd r6, r1
    vstb r6, r3

    vadd r6, r1

    vstb r6, r3
    vadd r6, r1
    vstb r6, r5
    vadd r6, r1
  .continue2:

  ; Przesuń r4 na kolejny znak i idź na początek pętli.
  vadd r4, r1
  vadd r3, r1; index (wskaznik bezwzgledny)
  vjmp brack_loop
.end:


vxor r0, r0 ; CONST 0
vset r1, 1 ; CONST 1

vxor r2, r2 ; code pointer int
vxor r3, r3 ; memeory pointer int
vxor r10, r10 ; pomocnicza dla zapisu w memory

vset r4, prog
vset r5, brack
vset r6, mem

; vset r7, '>' ; r7 znaki
; vldb r8, r4  ; aktualny wczytany znak

main_loop:
  ; wczytanie kommendy
  vset r4, prog
  vadd r4, r2
  vldb r8, r4

  ; if command == 0: main_end
  vcmp r8, r0
  vjz main_end

  ; voutb 0x20, r8

  vset r7, '>'
  vcmp r7, r8
  vjne .loop1
    vadd r3, r1
  .loop1:

  vset r7, '<'
  vcmp r7, r8
  vjne .loop2
    vsub r3, r1
  .loop2:

  vset r7, '+'
  vcmp r7, r8
  vjne .loop3
    vset r6, mem
    vadd r6, r3 ; w r6 mam wskaznik na miejsce w pamieci do komurki
    vldb r10, r6 ; w r10 mam aktualna wartos z ~tablicy

    vadd r10, r1

    vstb r6, r10
  .loop3:

  vset r7, '-'
  vcmp r7, r8
  vjne .loop4
    vset r6, mem
    vadd r6, r3 ; w r6 mam wskaznik na miejsce w pamieci do komurki
    vldb r10, r6 ; w r10 mam aktualna wartos z ~tablicy

    vsub r10, r1

    vstb r6, r10
  .loop4:

  vset r7, '['
  vcmp r7, r8
  vjne .loop5
    vset r6, mem
    vadd r6, r3
    vldb r10, r6

    vcmp r10, r0
    vjne .inloop1
      ; skocz do ]
    .inloop1:
  .loop5:


  vset r7, '['
  vcmp r7, r8
  vjne .loop6
    vset r6, mem
    vadd r6, r3
    vldb r10, r6

    vcmp r10, r0
    vjne .inloop2
      ; skocz do ]
    .inloop2:
  .loop6:


  vset r7, ']'
  vcmp r7, r8
  vjne .loop7
    vset r6, mem
    vadd r6, r3
    vldb r10, r6

    vcmp r10, r0
    vje .inloop3
      vset r5, brack
      .startloop:
        vldb r10, r5

        vcmp r10, r2
        vjne .ininloop1
          vadd r5, r1
          vldb r10, r5
          vset r2, r10
          vjmp .loop7
        .ininloop1:
          vadd r5, r1
          vadd r5, r1
          vjmp .startloop
        ; r2 = brack[r2]
        ; odczytaj brack 1 bajt
        ; sprwadz czy rowne z r2
        ; TAK
        ;   dodaj 1
        ;   oczytaj 1 bajt
        ;   ustaw r2 na to odczytane
        ; NIE
        ;   dodaj 2 do brack
        ;   jampuj na poczatek

        ; skocz do ]
    .inloop3:
  .loop7:

  vset r7, '.'
  vcmp r7, r8
  vjne .loop8
    vset r6, mem
    vadd r6, r3
    vldb r10, r6
    voutb 0x20, r10
  .loop8:

  vadd r2, r1 ; i++
  vjmp main_loop
main_end:

vset r4, prog
vset r5, brack
vset r6, mem
voff
; program
prog:
  db "++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.", 0


brack:
	times PROG_SIZE db 0

;pamiec do wykorzystania przez program
mem:
	times MEM_SIZE db 0
