from bitstring import Bits, BitString, BitArray, ConstBitStream

import base64

class Addr:
    def __init__(self,bank,addr) -> None:
        self.bank = bank
        self.addr = addr

    def absolute_pos(self) -> int:
        return (((self.bank-1)*BANK_SIZE)+self.addr)

    @classmethod
    def convert_to_addr(cls, long_addr) -> None:
        bank = int(long_addr/BANK_SIZE)
        addr = (long_addr%BANK_SIZE)+(BANK_SIZE if bank > 0 else 0)
        return cls(bank,addr)
    
    def __str__(self) -> str:
        return f"{self.bank:#04X}:{self.addr:04X}"

    def __add__(self, other):
        if isinstance(other, int):
            diff = other
        elif isinstance(other, Addr):
            diff = abs(self.absolute_pos() - other.absolute_pos())
        return self.convert_to_addr(self.absolute_pos() + diff)

    def __sub__(self, other):
        if isinstance(other, int):
            diff = other
        elif isinstance(other, Addr):
            diff = abs(self.absolute_pos() - other.absolute_pos())
        return self.convert_to_addr(self.absolute_pos() - diff)

    def __eq__(self, other) -> bool:
        return self.absolute_pos() == other.absolute_pos()

    def __gt__(self, other) -> bool:
        return self.absolute_pos() > other.absolute_pos()
    
    def __lt__(self, other) -> bool:
        return self.absolute_pos() < other.absolute_pos()
    
    def __ge__(self, other) -> bool:
        return self.absolute_pos() >= other.absolute_pos()
    
    def __le__(self, other) -> bool:
        return self.absolute_pos() <= other.absolute_pos()
    
    def __ne__(self, other) -> bool:
        return self.absolute_pos() != other.absolute_pos()

class GBDataPacket:
    def __init__(self, addr, packet_size, data) -> None:
        self.addr = addr
        self.packet_size = packet_size
        self.data = data
    
    @classmethod
    def get_static_data(cls, addr, packet_size, length):
        ROM.bytepos = addr.absolute_pos()
        data = ROM.readlist([f'uint:{packet_size}']*length)
        return cls(addr,packet_size,data)

    @classmethod
    def get_var_data(cls, addr, packet_size, target, bytealigned=True):
        ROM.bytepos = addr.absolute_pos()
        data = ROM.readto(target,bytealigned)
        data_list = data.readlist([f'uint:{packet_size}']*int(data.len/packet_size))
        return cls(addr,packet_size,data_list)

    def collapse(self, rev=False) -> int:
        out = 0
        if rev:
            self.data.reverse()
        for val in self.data:
            out = out << self.packet_size
            out+=val
        self.data.reverse()
        return out

    def __str__(self) -> str:
        return f"{self.addr}  " + " ".join(map((lambda n: f"{n:02x}"), self.data))

    def raw_dump(self) -> str:
        out = ""
        out+=(f"Start:{self.addr} Finish:{self.addr+len(self.data)} Length:{(len(self.data))} 2BPP:{len(self.data)/16:0.0f} 1BPP:{len(self.data)/8:0.0f}\n")
        

        data_fmt = []
        for i in range(int(len(self.data)/16)):
            data_fmt.append(f"{(i*16):#07X} " + ' '.join(map(lambda n: f"{n:02X}", self.data[16*i:(16*i)+16])))

        out+=('\n'.join(data_fmt))
        if (len(self.data) % 16 != 0):
            out+=(f"\n{len(data_fmt)*16:#07X} " + ' '.join(map(lambda n: f"{n:02X}", self.data[len(data_fmt)*16:])))
        return out

class Sprite:

    def __init__(self,addr,width,height,data) -> None:
        self.addr = addr
        self.width = width
        self.height = height
        self.data = data

    def __str__(self):
        return f"[Loc: {self.addr} => Width: {self.width}, Height: {self.height}]"

    def to_json(self) -> dict:
        return {'width': self.width, 'height': self.height, 'data': self.to_base64()}

    @classmethod
    def __expandRLEPacket(cls, bit_length, value) -> BitString:
        return BitString((bit_length+value+1)*2)

    @classmethod
    def __findRLEBoundry(cls, sprite_data) -> Bits:
        length_found = sprite_data.readto('0b0')
        return length_found

    @classmethod
    def __mode1(cls,bit_planes,width) -> list:
        bit_planes[1] = cls.__deltaDecode(bit_planes[1],width)
        bit_planes[0] = cls.__deltaDecode(bit_planes[0],width)
        return bit_planes

    @classmethod
    def __mode2(cls,bit_planes,width) -> list:
        bit_planes[1] = cls.__deltaDecode(bit_planes[1],width)
        bit_planes[0] = bit_planes[0] ^ bit_planes[1] 
        return bit_planes

    @classmethod
    def __mode3(cls,bit_planes,width) -> list:
        bit_planes[1] = cls.__deltaDecode(bit_planes[1],width)
        bit_planes[0] = cls.__deltaDecode(bit_planes[0],width)
        bit_planes[0] = bit_planes[0] ^ bit_planes[1]
        return bit_planes

    @classmethod
    def ___translate(cls, arr,row_num,coloumn_num):
        matrix = [[0 for x in range(coloumn_num)] for y in range(row_num)]
        for row in range(row_num):
            for col in range(int(coloumn_num/8)):
                for i in range(8):
                    matrix[row][col+i]=arr[(row*col)+row+i]
        return matrix


    @classmethod
    def __fillMatrix(cls, arr,row_num, coloumn_num) -> BitArray:
        #Array math is hard touch numbers at own risk
        matrix = [[0 for x in range(coloumn_num*4)] for y in range(row_num*8)]
        for row in range(row_num*8):
            for col in range(coloumn_num*4):
                matrix[row][col]=(''.join(arr[((col*row_num*16)+(row*2)):((col*row_num*16)+(row*2))+2].bin))
            matrix[row] = ''.join(matrix[row])
        
        output = BitArray()
        for out_row in matrix:    
            output.append('0b'+out_row)

        return output

    @classmethod
    def __bufferToList(cls, arr, row_num, coloumn_num) -> list:
        #1 byte per row per tile
        #1 byte per coloumn per tile
        bufList = [0] * row_num*BYTE
        column_bits = coloumn_num*BYTE
        for row in range(row_num*BYTE):
            bufList[row]=list(map(int,(','.join(arr[(row*column_bits):((row*column_bits)+column_bits)].bin).split(','))))
        return bufList

    @classmethod
    def __combineBuffers(cls,bit_planes,high_bit_plane) -> list:
        result = [[(bit_planes[high_bit_plane][i][j]<<1) + bit_planes[high_bit_plane^1][i][j]  for j in range(len(bit_planes[high_bit_plane][0]))] for i in range(len(bit_planes[1]))]
        return result

    @classmethod
    def __fillTileMatrix(cls, arr, sprite_height_tiles, sprite_width_tiles) -> list:
        tile_side_px = 8
        tile_size = tile_side_px*tile_side_px
        out = []
        for tile_row in range (sprite_height_tiles):
            for row in range(tile_side_px):
                temp = []
                for col in range (sprite_width_tiles):
                    temp.extend(arr[((tile_row*tile_size*sprite_width_tiles)+(col*tile_size)+(row*tile_side_px)):((tile_row*tile_size*sprite_width_tiles)+(col*tile_size)+(row*tile_side_px))+tile_side_px])
                out.append(temp)
        return out

    def print_pixels(self):
        for row in self.data:
            print(','.join(map(str,row)))

    def __to_bignum(self) -> int:
        output = 0
        for row in self.data:
            for col in row:
                output = output << 2
                output += col
        return output

    def to_base64(self) -> str:
        num = self.__to_bignum()
        num_bytes = num.to_bytes((int(self.height*self.width*TWO_BPP_TILE_SIZE/BYTE)),'big')
        return base64.b64encode(num_bytes).decode()
    
    @classmethod
    def __deltaDecode(cls, arr, width) -> BitArray:
        output = BitArray()
        currentBit = 0
        for index, bit in enumerate(arr):
            if index % (width*8) == 0:
                currentBit = 0
            if bit:
                currentBit = (currentBit ^ 1)
            
            output.append('0b%s' % currentBit)
        return output

    @classmethod
    def __parseData(cls, packet_type, width, height, bit_plane):
        while bit_plane.len < (width*height*ONE_BPP_TILE_SIZE):
            if packet_type == 0:
                length = cls.__findRLEBoundry(ROM)
                value = ROM.read((f"uint:{length.len}"))
                zero_bits = cls.__expandRLEPacket(length.uint,value)
                bit_plane.append(zero_bits)
                packet_type = 1
            else:
                data_packet = ROM.read('bin:2')
                if data_packet != '00':
                    bit_plane.append('0b'+data_packet)
                else:
                    packet_type = 0

    @classmethod
    def parse_pkmn_sprite(cls, addr) -> None:
        ROM.bytepos = addr.absolute_pos()
        width = ROM.read('uint:4')
        height = ROM.read('uint:4')
        high_bit_plane = ROM.read('uint:1')
        packet_type = ROM.read('uint:1')
        bit_planes = [BitArray(), BitArray()]
        cls.__parseData(packet_type,width,height,bit_planes[1])
        zip_mode = -1
        if ROM.peek('uint:1') == 0:
            zip_mode = ROM.read('uint:1')
        else:
            zip_mode = ROM.read('uint:2')
        packet_type = ROM.read('uint:1')

        cls.__parseData(packet_type,width,height,bit_planes[0])

        bit_planes[0] = cls.__fillMatrix(bit_planes[0],width,height)
        bit_planes[1] = cls.__fillMatrix(bit_planes[1],width,height)

        if zip_mode == 0:
            bit_planes = cls.__mode1(bit_planes,width)
        elif zip_mode == 2:
            bit_planes = cls.__mode2(bit_planes,width)
        else:
            bit_planes = cls.__mode3(bit_planes,width)

        bit_planes[0] = cls.__bufferToList(bit_planes[0],width,height)
        bit_planes[1] = cls.__bufferToList(bit_planes[1],width,height)

        sprite_data = cls.__combineBuffers(bit_planes,high_bit_plane)

        return cls(addr,width,height,sprite_data)

    @classmethod
    def decode1BPP(cls, rom, start, finish, height, width):
        rom.pos = start
        output = Sprite(int(rom.pos/8),width,height,1)
        for i in range(int((finish-start)/8)):
            output.bit_planes[0].append(rom.peek('bits:8'))
            output.bit_planes[1].append(rom.read('bits:8'))
        
        for i in range(2):
            output.bit_planes[i] = cls.__fillTileMatrix(output.bit_planes[i],height,width)

        output.sprite = cls.__combineBuffers(output)

        return output

    @classmethod
    def decode2BPP(cls,rom, start, finish, height, width):
        rom.pos = start
        output = Sprite(int(rom.pos/8),width,height,1)
        for i in range(int((finish-start)/16)):
            output.bit_planes[0].append(rom.read('bits:8'))
            output.bit_planes[1].append(rom.read('bits:8'))
        
        for i in range(2):
            output.bit_planes[i] = cls.__fillTileMatrix(output.bit_planes[i],height,width)

        output.sprite = cls.__combineBuffers(output)

        return output

    # def pwshOutput(sprite):
    #     out = []
    #     for row in range(len(sprite)):
    #         if row % 2 == 0:
    #             for top,bottom in zip(sprite[row],sprite[row+1]):
    #                 out.append((top<<2)+bottom)

    #     print("".join("{:01x}".format(num) for num in out))

    # def poshOutputDebug(strArr):
    #     out = []
    #     for i in range(0,len(strArr),2):
    #         out.append(strArr[i])
    #         out.append(strArr[i+1])
    #     return "".join(out)

    # def printPkmnFront(pkmn):
    #     ### Debug Prints ###
    #     # print(pkmn.front_sprite)
    #     # printPixels(pkmn.front_sprite.bit_planes[0])
    #     # print()
    #     # printPixels(pkmn.front_sprite.bit_planes[1])
    #     # print()
    #     ### Debug Prints ###
    #     printPixels(pkmn.front_sprite.sprite)
    # def printPkmnBack(pkmn):
    #     ### Debug Prints ###
    #     # print(pkmn.back_sprite)
    #     # printPixels(pkmn.back_sprite.bit_planes[0])
    #     # print()
    #     # printPixels(pkmn.back_sprite.bit_planes[1])
    #     # print()
    #     ### Debug Prints ###
    #     printPixels(pkmn.back_sprite.sprite)
    # def printPkmn(pkmn,sprite):
    #     if sprite == 0:
    #         printPkmnBack(pkmn)
    #     else:
    #         printPkmnFront(pkmn)

class GBText:
    STRING_END = 0x50
    ALPHABET = {
        0x00: "",           #charmap "<NULL>"
        0x49: "^",       #charmap "<PAGE>"
        #charmap "<PKMN>",    #  "<PK><MN>"
        #charmap "<_CONT>",   #  implements "<CONT>"
        #charmap "<SCROLL>",  $4c
        0x4E: ">",     #Next
        0x4F: " ",   
        0x57: "#",
        0x50: "@",   #charmap "@" string terminator
        0x51: "*",
        0x52: "A1",
        0x53: "A2",
        0x54: "POK??",
        0x55: "+",
        0x58: "$",
        0x5F: "}",   #charmap "<DEXEND>"
        0x75: "???",
        0x7F: " ",
        0x80: "A",
        0x81: "B",
        0x82: "C",
        0x83: "D",
        0x84: "E",
        0x85: "F",
        0x86: "G",
        0x87: "H",
        0x88: "I",
        0x89: "J",
        0x8A: "K",
        0x8B: "L",
        0x8C: "M",
        0x8D: "N",
        0x8E: "O",
        0x8F: "P",
        0x90: "Q",
        0x91: "R",
        0x92: "S",
        0x93: "T",
        0x94: "U",
        0x95: "V",
        0x96: "W",
        0x97: "X",
        0x98: "Y",
        0x99: "Z",
        0x9A: "(",
        0x9B: ")",
        0x9C: ":",
        0x9D: ";",
        0x9E: "[",
        0x9F: "]",
        0xA0: "a",
        0xA1: "b",
        0xA2: "c",
        0xA3: "d",
        0xA4: "e",
        0xA5: "f",
        0xA6: "g",
        0xA7: "h",
        0xA8: "i",
        0xA9: "j",
        0xAA: "k",
        0xAB: "l",
        0xAC: "m",
        0xAD: "n",
        0xAE: "o",
        0xAF: "p",
        0xB0: "q",
        0xB1: "r",
        0xB2: "s",
        0xB3: "t",
        0xB4: "u",
        0xB5: "v",
        0xB6: "w",
        0xB7: "x",
        0xB8: "y",
        0xB9: "z",
        0xBA: "??",
        0xBB: "'d",
        0xBC: "'l",
        0xBD: "'s",
        0xBE: "'t",
        0xBF: "'v",
        0xE0: "'",
        0xE1: "PK",
        0xE2: "MN",
        0xE3: "-",
        0xE4: "'r",
        0xE5: "'m",
        0xE6: "?",
        0xE7: "!",
        0xE8: ".",
        0xED: "???",
        0xEE: "???",
        0xEF: "???",

        0x60: "<BOLD_A>",  #  unused
        0x61: "<BOLD_B>",  #  unused
        0x62: "<BOLD_C>",  #  unused
        0x63: "<BOLD_D>",  #  unused
        0x64: "<BOLD_E>",  #  unused
        0x65: "<BOLD_F>",  #  unused
        0x66: "<BOLD_G>",  #  unused
        0x67: "<BOLD_H>",  #  unused
        0x68: "<BOLD_I>",  #  unused
        0x69: "<BOLD_V>",  
        0x6A: "<BOLD_S>",  
        0x6B: "<BOLD_L>",  #  unused
        0x6C: "<BOLD_M>",  #  unused
        0x6D: "<COLON>",   #  colon with tinier dots than ":"
        0x6E: "???",         #  hiragana small i, unused
        0x6F: "???",         #  hiragana small u, unused
        0x70: "???",         #  opening single quote
        0x71: "???",         #  closing single quote
        0x72: "???",         #  opening quote
        0x73: "???",         #  closing quote
        0x74: "??",         #  middle dot, unused
        0x75: "???",         #  ellipsis
        0x76: "???",         #  hiragana small a, unused
        0x77: "???",         #  hiragana small e, unused
        0x78: "???",         #  hiragana small o, unused


        0x79: "???",         
        0x7A: "???",         
        0x7B: "???",         
        0x7C: "???",         
        0x7D: "???",         
        0x7E: "???",         
        0x7F: " ",         

        0x05: "???", 
        0x06: "???",
        0x07: "???", 
        0x08: "???", 
        0x09: "???", 
        0x0A: "???", 
        0x0B: "???", 
        0x0C: "???", 
        0x0D: "???", 
        0x0E: "???", 
        0x0F: "???", 
        0x10: "???", 
        0x11: "???", 
        0x12: "???", 
        0x13: "???", 

        0x19: "???", 
        0x1A: "???", 
        0x1B: "???", 
        0x1C: "???", 

        0x26: "???", 
        0x27: "???", 
        0x28: "???", 
        0x29: "???", 
        0x2A: "???", 
        0x2B: "???", 
        0x2C: "???", 
        0x2D: "???", 
        0x2E: "???", 
        0x2F: "???", 
        0x30: "???", 
        0x31: "???", 
        0x32: "???", 
        0x33: "???", 
        0x34: "???", 

        0x3A: "???", 
        0x3B: "???", 
        0x3C: "???", 
        0x3D: "???", 
        0x3E: "???", 

        0x40: "???", 
        0x41: "???", 
        0x42: "???", 
        0x43: "???", 
        0x44: "???", 
        0x45: "???", 
        0x46: "???", 
        0x47: "???", 
        0x48: "???", 

        0x70: "???", 
        0x71: "???", 
        0x73: "???", 
        0x75: "???", 

        0x7F: " ", 

        # 0x80: "???", 
        # 0x81: "???", 
        # 0x82: "???", 
        # 0x83: "???", 
        # 0x84: "???", 
        # 0x85: "???", 
        # 0x86: "???", 
        # 0x87: "???", 
        # 0x88: "???", 
        # 0x89: "???", 
        # 0x8A: "???", 
        # 0x8B: "???", 
        # 0x8C: "???", 
        # 0x8D: "???", 
        # 0x8E: "???", 
        # 0x8F: "???", 
        # 0x90: "???", 
        # 0x91: "???", 
        # 0x92: "???", 
        # 0x93: "???", 
        # 0x94: "???", 
        # 0x95: "???", 
        # 0x96: "???", 
        # 0x97: "???", 
        # 0x98: "???", 
        # 0x99: "???", 
        # 0x9A: "???", 
        # 0x9B: "???", 
        # 0x9C: "???", 
        # 0x9D: "???", 
        # 0x9E: "???", 
        # 0x9F: "???", 
        # 0xA0: "???", 
        # 0xA1: "???", 
        # 0xA2: "???", 
        # 0xA3: "???", 
        # 0xA4: "???", 
        # 0xA5: "???", 
        # 0xA6: "???", 
        # 0xA7: "???", 
        # 0xA8: "???", 
        # 0xA9: "???", 
        # 0xAA: "???", 
        # 0xAB: "???", 
        # 0xAC: "???", 
        # 0xAD: "???", 
        # 0xAE: "???", 
        # 0xAF: "???", 
        # 0xB0: "???", 
        # 0xB1: "???", $b1
        # 0xB2: "???", $b2
        # 0xB3: "???", $b3
        # 0xB4: "???", $b4
        # 0xB5: "???", $b5
        # 0xB6: "???", $b6
        # 0xB7: "???", $b7
        # 0xB8: "???", $b8
        # 0xB9: "???", $b9
        # 0xBA: "???", $ba
        # 0xBB: "???", $bb
        # 0xBC: "???", $bc
        # 0xBD: "???", $bd
        # 0xBE: "???", $be
        # 0xBF: "???", $bf
        # 0xC0: "???", $c0
        # 0xC1: "???", $c1
        # 0xC2: "???", $c2
        # 0xC3: "???", $c3
        # 0xC4: "???", $c4
        # 0xC5: "???", $c5
        # 0xC6: "???", $c6
        # 0xC7: "???", $c7
        # 0xC8: "???", $c8
        # 0xC9: "???", $c9
        # 0xCA: "???", $ca
        # 0xCB: "???", $cb
        # 0xCC: "???", $cc
        # 0xCD: "???", $cd
        # 0xCE: "???", $ce
        # 0xCF: "???", $cf
        # 0xD0: "???", $d0
        # 0xD1: "???", $d1
        # 0xD2: "???", $d2
        # 0xD3 "???", $d3
        # 0xD4: "???", $d4
        # 0xD5: "???", $d5
        # 0xD6: "???", $d6
        # 0xD7: "???", $d7
        # 0xD8: "???", $d8
        # 0xD9: "???", $d9
        # 0xDA: "???", $da
        # 0xDB: "???", $db
        # 0xDC: "???", $dc
        # 0xDD: "???", $dd
        # 0xDE: "???", $de
        # 0xDF: "???", $df
        # 0xE0: "???", $e0
        # 0xE1: "???", $e1
        # 0xE2: "???", $e2
        # 0xE3: "???", $e3
        # 0xE4: "???", $e4
        # 0xE5: "???", $e5
        # 0xE6: "???", $e6
        # 0xE7: "???", $e7
        # 0xE8: "???", $e8

        # 0xF0: "???", $f0

        # 0xF2: "???", $f2
        # 0xF3: "???", $f3

        # 0xF4: "???", $f4

        0xF0: "??",
        0xF1: "??",
        0xF3: "/",
        0xF4: ",",
        0xF5: "???",
        0xF6: "0",
        0xF7: "1",
        0xF8: "2",
        0xF9: "3",
        0xFA: "4",
        0xFB: "5",
        0xFC: "6",
        0xFD: "7",
        0xFE: "8",
        0xFF: "9"
    }

    def decodeText(self) -> str:
        return list(map(self.ALPHABET.get, self.packet.data))

    def __init__(self,packet) -> None:
        self.packet = packet
        self.text =  self.decodeText()
       

    def __str__(self):
        return "".join(self.text).strip('@')

#Constants that have hard pointers in Red/Blue
ROM = ConstBitStream(filename='Pokemon Red.gb')
BANK_SIZE = 0x4000
TWO_BPP_TILE_SIZE = 128
ONE_BPP_TILE_SIZE = 64
BYTE = 8
BIT = 1
NYBBLE = 4
TWO_BPP = 2
ONE_BPP = 1

POKEMON_NAME_LENGTH = 10

END_FILE = Addr.convert_to_addr(ROM.len/8)

POKEDEX_ORDER_POINTER = Addr(0x10,0x5024)
POKEDEX_ENTRY_POINTER = Addr(0x10,0x447e)
POKEMON_DATA_POINTER  = Addr(0X0E,0x43DE)
POKEMON_NAME_POINTER  = Addr(0x07,0x421e)


datamap = {'Index to Pokedex':  [],
           'Pokedex Entry Loc': []
}

pokedex_index_map = []
pokedex_loc_map = []

for i in range(0,380,2):
    datamap["Pokedex Entry Loc"].append(GBDataPacket.get_static_data(POKEDEX_ENTRY_POINTER+i,BYTE,2).collapse(rev=True))
    datamap["Index to Pokedex"].append(GBDataPacket.get_static_data(POKEDEX_ORDER_POINTER+int(i/2),BYTE,1).collapse())