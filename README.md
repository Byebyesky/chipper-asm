# chipper-asm - A Chip-8 Assembler
c8asm is a chip-8 assembler written in python.  
The code is horrible and unorganized and could be a lot smaller if I grouped the instructions by their opcode structure.   
For an example on how to use the assembler see example.s  

Usage: ``./chipper-asm.py assembly.s output``


```
--------------      Instruction set      --------------
Opcode  Action                     Mnemonic    Operands
0NNN 	Call                        rcall       NNN
00E0 	disp_clear()                clear       
00EE 	return;                     ret         
1NNN 	goto NNN;                   jmp         NNN/label
2NNN 	*(0xNNN)()                  call        NNN/label
3XNN 	if(Vx==NN) 	            eq          Vx, NN
4XNN 	if(Vx!=NN) 	            neq         Vx, NN
5XY0 	if(Vx==Vy) 	            eq          Vx, Vy
6XNN 	Vx = NN 	            mov         Vx, NN
7XNN 	Vx += NN 	            add         Vx, NN
8XY0 	Vx=Vy 	                    mov         Vx, Vy
8XY1 	Vx=Vx|Vy 	            or          Vx, Vy
8XY2 	Vx=Vx&Vy 	            and         Vx, Vy
8XY3 	Vx=Vx^Vy 	            xor         Vx, Vy
8XY4 	Vx += Vy 	            add         Vx, Vy
8XY5 	Vx -= Vy 	            sub         Vx, Vy
8XY6 	Vx>>=1 	                    lsr         Vx
8XY7 	Vx=Vy-Vx 	            rsub        Vx, Vy
8XYE 	Vx<<=1 	                    lsl         Vx
9XY0 	if(Vx!=Vy) 	            neq         Vx, Vy
ANNN 	I = NNN 	            mov         I, NNN/label
BNNN 	PC=V0+NNN 	            rjmp        NNN/label
CXNN 	Vx=rand()&NN 	            rnd         Vx, NN
DXYN 	draw(Vx,Vy,N) 	            draw        Vx, Vy, N
EX9E 	if(key()==Vx) 	            keq         Vx
EXA1 	if(key()!=Vx) 	            kneq        Vx
FX07 	Vx = get_delay()            dly         Vx
FX0A 	Vx = get_key() 	            gky         Vx
FX15 	delay_timer(Vx)             sdly        Vx
FX18 	sound_timer(Vx)             ssnd        Vx
FX1E 	I +=Vx 	                    add         I, Vx
FX29 	I=sprite_addr[Vx]           chr         Vx
FX33 	set_BCD(Vx);                bcd         Vx
FX55 	MEM 	reg_dump(Vx,&I)     stm         Vx
FX65 	MEM 	reg_load(Vx,&I)     ldm         Vx
```

```
--------------      Assembler directives      --------------
.label:     -   defines a label
.db         -   defines a byte, in case you need it
.spr ""     -   defines a sprite (8 chars, space/x in one line)
;           -   defines a comment
```

```
Defining a byte:
.myData:
.db 0xFF

Defining a sprite:
e.g.:
.mySprite:
.spr "xxxxxxxx"
.spr "x      x"
.spr "x      x"
.spr "x      x"
.spr "x      x"
.spr "xxxxxxxx"
```