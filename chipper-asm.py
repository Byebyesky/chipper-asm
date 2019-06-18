#!/usr/bin/env python3

import sys
import re

offset = 0x200  #chip8 start address
lineNumber = 0
labels = {}
executable = bytearray()

#Helper funcs
def numberValid(number, bits):
    try:
        if number.startswith('0x'):
            number = int(number, 16)
        else:
            number = int(number)
        if number.bit_length() > bits or number < 0:
            raise ValueError
    except ValueError:
        print("{}: '{}': Value '{}' is not in range of {} bits!".format(lineNumber, line, number, bits))
        exit(1)
    return number

def getOffset(arguments):
    try:
        if arguments.startswith("."):
            offset = labels.get(arguments)
        else: 
            offset = numberValid(arguments, 12)

        opUpper = 0x00 | offset >> 8
        opLower = offset & 0xFF
        return opUpper, opLower
    except ValueError:
        print("Error in getOffset")
        exit(1)

def returnValidRegister(argument):
    try:
        if argument.startswith('v') and len(argument) == 2:
            register = int(argument[1], 16)
            if register.bit_length() <= 4:
                return register
        raise ValueError
    except ValueError:
        print("{}: '{}': Value '{}' is not a valid register!".format(lineNumber, line, argument))
        exit(1)

def prepareUpperByte(op, X):
    vx = returnValidRegister(X)
    return op | vx

#Assembler directive funcs
def defineByte(line):
    global offset
    number = line.split(' ', 1)[1]
    number = numberValid(number, 8)
    executable.append(number)
    offset += 1

def defineSprite(line):
    global offset
    try:
        sprite = line.split(' ', 1)[1]
        if re.search("^\"[x\ ]{8}\"$", sprite) is None:
            raise ValueError
        sprite = sprite.strip('"')
        binarySprite = 0
        for i in range(8):
            if sprite[i] == 'x':
                binarySprite |= 1 << 7-i
        executable.append(binarySprite)
        offset += 1
    except ValueError:
        print("{}: '{}': Couldn't find valid sprite definition".format(lineNumber, line))
        exit(1)

def defineLabel(line):
    try:
        if " " in line or not line.endswith(":"):
            raise ValueError
        labels.update( {line[:-1]: offset})
    except ValueError:
        print("{}: '{}': Labels may not contain spaces and must end with ':' on declaration".format(lineNumber, line))
        exit(1)

def nop(line):
    pass

#opcode funcs
def mnemonicNotFound(line, arguments):
    print("{}: '{}': mnemonic not valid".format(lineNumber, line))
    exit(1)

def getJumpOpcode(line, arguments):
    opUpper, opLower = getOffset(arguments)
    opUpper = 0x10 | opUpper
    return bytes([opUpper, opLower])

def getCallOpcode(line, arguments):
    opUpper, opLower = getOffset(arguments)
    opUpper = 0x20 | opUpper
    return bytes([opUpper, opLower])

def getCondOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    arg2 = arguments.split(',')[1].strip()
    mnemonic = line.split(' ', 1)[0]

    if mnemonic == 'eq':
        if arg2.startswith('v'):
            opUpper = prepareUpperByte(0x50, arg1)
            vy = returnValidRegister(arg2)
            return bytes([opUpper, vy << 4])

        opUpper = prepareUpperByte(0x30, arg1)
        return bytes([opUpper, numberValid(arg2, 8)]) 
    
    elif mnemonic == 'neq':
        if arg2.startswith('v'):
            opUpper = prepareUpperByte(0x90, arg1)
            vy = returnValidRegister(arg2)
            return bytes([opUpper, vy << 4])

        opUpper = prepareUpperByte(0x40, arg1)
        return bytes([opUpper, numberValid(arg2, 8)]) 

def getMovOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    arg2 = arguments.split(',')[1].strip()
    if arg1 == 'i':
        opUp, opLo = getOffset(arg2)
        opUp = 0xA0 | opUp
        return bytes([opUp, opLo])
    elif arg2[0] == 'v':
        regX = returnValidRegister(arg1)
        regY = returnValidRegister(arg2)
        opUp = 0x80 | regX
        opLo = regY << 4
        return bytes([opUp, opLo])
    else:
        regX = returnValidRegister(arg1)
        opUp = 0x60 | regX
        opLo = numberValid(arg2, 8)
        return bytes([opUp, opLo])

def getAddOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    arg2 = arguments.split(',')[1].strip()
    
    if arg1 == 'i':
        regX = returnValidRegister(arg2)
        opUp = 0xF0 | regX
        opLo = 0x1E
        return bytes([opUp, opLo])
    elif arg2[0] == 'v':
        regX = returnValidRegister(arg1)
        regY = returnValidRegister(arg2)
        opUp = 0x80 | regX
        opLo = regY << 4 | 0x4
        return bytes([opUp, opLo])
    else:
        regX = returnValidRegister(arg1)
        opUp = 0x70 | regX
        opLo = numberValid(arg2, 8)
        return bytes([opUp, opLo])

def getBooleanArithmeticOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    arg2 = arguments.split(',')[1].strip()
    mnemonic = line.split(' ', 1)[0]

    if mnemonic == 'or':
        regX = returnValidRegister(arg1)
        regY = returnValidRegister(arg2)
        opUp = 0x80 | regX
        opLo = regY << 4 | 0x1
        return bytes([opUp, opLo])
    elif mnemonic == 'and':
        regX = returnValidRegister(arg1)
        regY = returnValidRegister(arg2)
        opUp = 0x80 | regX
        opLo = regY << 4 | 0x2
        return bytes([opUp, opLo])
    elif mnemonic == 'xor':
        regX = returnValidRegister(arg1)
        regY = returnValidRegister(arg2)
        opUp = 0x80 | regX
        opLo = regY << 4 | 0x3
        return bytes([opUp, opLo])

def makeOpcode(Op, X, Y, lo):
    return bytes([Op << 4 | X, Y << 4 | lo])

def getSingleArgOpcode(line, arguments):
    vx = returnValidRegister(arguments)
    mnemonic = line.split(' ', 1)[0]
    if mnemonic == "gky":
        return makeOpcode(0x0F, vx, 0x0, 0xA)
    if mnemonic == "keq":
        return makeOpcode(0xE, vx, 0x9, 0xE)
    if mnemonic == "kneq":
        return makeOpcode(0xE, vx, 0xA, 0x1)
    if mnemonic == "dly":
        return makeOpcode(0xF, vx, 0x0, 0x7)
    if mnemonic == "stm":
        return makeOpcode(0xF, vx, 0x5, 0x5)
    if mnemonic == "ldm":
        return makeOpcode(0xF, vx, 0x6, 0x5)
    if mnemonic == "bcd":
        return makeOpcode(0xF, vx, 0x3, 0x3)
    if mnemonic == "chr":
        return makeOpcode(0xF, vx, 0x2, 0x9)
    if mnemonic == "sdly":
        return makeOpcode(0xF, vx, 0x1, 0x5)
    if mnemonic == "ssnd":
        return makeOpcode(0xF, vx, 0x1, 0x8)
    
def getSubOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    arg2 = arguments.split(',')[1].strip()
    regX = returnValidRegister(arg1)
    mnemonic = line.split(" ", 1)[0]

    if mnemonic  == "sub":
        return makeOpcode(0x8, regX,regY, 0x5)
    elif mnemonic == "rsub":
        return makeOpcode(0x8, regX,regY, 0x7)        

def getShiftOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    regY = 0
    regX = returnValidRegister(arg1)
    try: 
        arg2 = arguments.split(',')[1].strip()
        regY = returnValidRegister(arg2)
    except IndexError:
        pass
    
    if line.split(" ", 1)[0] == "lsl":
        return makeOpcode(0x8, regX, regY, 0xE)
    else:
        return makeOpcode(0x8, regX, regY, 0x6)

def getRjmpOpcode(line, arguments):
    up, lo = getOffset(arguments)
    up = 0xB0 | up
    return bytes([up, lo])

def getRndOpcode(line, arguments):
    arg1 = arguments.split(',')[0].strip()
    arg2 = arguments.split(',')[1].strip()
    regX = returnValidRegister(arg1)
    opUp = 0xC0 | regX
    opLo = numberValid(arg2, 8)
    return bytes([opUp, opLo])


directiveHandlers = {
    ".db":  defineByte,
    ".spr": defineSprite
}

mnemonicHandlers = {
    "rcall":    None,
    "jmp":      getJumpOpcode,
    "call":     getCallOpcode,
    "eq":       getCondOpcode,
    "neq":      getCondOpcode,
    "mov":      getMovOpcode,
    "add":      getAddOpcode,
    "or":       getBooleanArithmeticOpcode,
    "and":      getBooleanArithmeticOpcode,
    "xor":      getBooleanArithmeticOpcode,
    "gky":      getSingleArgOpcode,
    "keq":      getSingleArgOpcode,
    "kneq":     getSingleArgOpcode,
    "sub":      getSubOpcode,
    "rsub":     getSubOpcode,
    "lsr":      getShiftOpcode,
    "lsl":      getShiftOpcode,
    "rjmp":     getRjmpOpcode,
    "rnd":      getRndOpcode,
    "dly":      getSingleArgOpcode,
    "sdly":     getSingleArgOpcode,
    "ssnd":     getSingleArgOpcode,
    "chr":      getSingleArgOpcode,
    "bcd":      getSingleArgOpcode,
    "stm":      getSingleArgOpcode,
    "ldm":      getSingleArgOpcode
}


if len(sys.argv) == 3:
    with open(sys.argv[1], 'r') as asmFile:
        #preparse for labels
        for line in asmFile:
            lineNumber += 1
            line = line.split(";")[0]   #strip comments
            line = line.strip()
            line = line.lower()

            if line == "":
                continue

            if line[0] == ".":
                directive = line.split(' ', 1)[0]
                if directive not in directiveHandlers:
                    defineLabel(line)
                else:
                    offset += 1
            else:
                offset += 2

        offset = 0x200
        lineNumber = 0
        asmFile.seek(0)

        #actual assembly
        for line in asmFile:
            lineNumber += 1
            line = line.split(";")[0]   #strip comments
            line = line.strip()
            line = line.lower()

            if line == "":
                continue

            #Assembler directive
            if line[0] == '.':
                directive = line.split(' ', 1)[0]
                directiveHandlers.get(directive, nop)(line)

            #instruction
            else:
                if line == "clear":
                    executable += bytes([0x00, 0xE0])
                elif line == "ret":
                    executable += bytes([0x00, 0xEE])
                else:
                    try:
                        mnemonic = line.split(' ', 1)[0]
                        arguments = line.split(' ', 1)[1]
                        args = arguments.split(',')
                        args = list(map(str.strip, args))
                        if mnemonic == "draw":
                            vx = returnValidRegister(args[0])
                            vy = returnValidRegister(args[1])
                            n = numberValid(args[2], 4)
                            machineCode = makeOpcode(0xD, vx, vy, n)
                        else:                    
                            machineCode = mnemonicHandlers.get(mnemonic, mnemonicNotFound)(line, arguments)

                        #print("{}: {}".format(mnemonic,machineCode))
                        executable += machineCode
                    except IndexError:
                        print("{}: '{}': Error in line".format(lineNumber, line))

                offset += 2

        outputFile = open(sys.argv[2], 'wb')
        outputFile.write(executable)
        outputFile.close()
else:
    print("Usage {} assembly.s output".format(sys.argv[0]))