.start:                     ;Initialize registers for drawing
    mov V0, 0               ;X
    mov V1, 0               ;Y
    mov I, .mySpr           ;N

.drawLoop:                  ;Fill the screen and clear it again
    draw V0, V1, 1
    add V0, 8
    neq V0, 64              ;if(x == screenWidth)
    add V1, 1
    neq V0, 64
    mov V0, 0
    neq V1, 32              ;if(y == screenHeight)
    mov V1, 0
    jmp .drawLoop

.mySpr:
.spr "xxxxxxxx"