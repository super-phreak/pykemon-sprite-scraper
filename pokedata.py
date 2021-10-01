from bitstring import BitArray, BitString, ConstBitStream
from sprite import Sprite

def expandRLEPacket(bit_length, value):
    return BitString((bit_length+value+1)*2)

def findRLEBound(sprite_data):
    length_found = sprite_data.readto('0b0')
    return length_found

def mode1(bit_planes):
    bit_planes[1] = deltaDecode(bit_planes[1])
    bit_planes[0] = deltaDecode(bit_planes[0])
    return bit_planes

def mode2(bit_planes):
    bit_planes[1] = deltaDecode(bit_planes[1])
    bit_planes[0] = bit_planes[0] ^ bit_planes[1] 
    return bit_planes

def mode3(bit_planes):
    bit_planes[1] = deltaDecode(bit_planes[1])
    bit_planes[0] = deltaDecode(bit_planes[0])
    bit_planes[0] = bit_planes[0] ^ bit_planes[1]
    return bit_planes

def fillMatrix(arr,row_num, coloumn_num):
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

def bufferToList(arr, row_num, coloumn_num):
    bufList = [0] * row_num*8
    column_bits = coloumn_num*8
    for row in range(row_num*8):
        bufList[row]=list(map(int,(','.join(arr[(row*column_bits):((row*column_bits)+column_bits)].bin).split(','))))

    return bufList

def combineBuffers(bit_planes):
    result = [[bit_planes[0][i][j] + bit_planes[1][i][j]  for j in range(len(bit_planes[0][0]))] for i in range(len(bit_planes[0]))]
    return result


def printPixels(buffer):
    for row in buffer:
        print(','.join(map(str,row)))
        

def deltaDecode(arr):
    output = BitArray()
    currentBit = 0
    for bit in arr:
        if bit:
            currentBit = currentBit ^ 1
        output.append('0b%s' % currentBit)
    return output

def parseData(packet_type, sprite):
    data_packet_count = 1
    while sprite.bit_planes[sprite.active_bit_plane].len < (sprite.width*sprite.height*64):
        if packet_type == 0:
            length = findRLEBound(mew_sprite_compressed)
            value = mew_sprite_compressed.read((f"uint:{length.len}"))
            zero_bits = expandRLEPacket(length.uint,value)
            sprite.bit_planes[sprite.active_bit_plane].append(zero_bits)
            packet_type = 1
            data_packet_count = 1
        else:
            data_packet = mew_sprite_compressed.read('bin:2')

            if data_packet != '00':
                sprite.bit_planes[sprite.active_bit_plane].append('0b'+data_packet)
                data_packet_count+=1
            else:
                packet_type = 0

        #Debug print for pulling my hair out on why it didnt work
        #print(len(sprite_data['mew_sprite']['bit_planes'][sprite_info['active_bit_plane']]),'Pos: ', (mew_sprite_compressed.pos),'PKT:', packet_type) 

#mew_sprite_compressed = ConstBitStream(hex='0x55be0553c37eaf5304e6507d5ad2633548552546ad8118d66baaf52942213650a07f2126a92638d6e45810554e1a2a752288889218ed8b81391548418a55354a70c114c7ab5349217e15943549562548589a8548509ffc8a07a885ad55e294149a214850aa828232b8ba38a94e35689525794e586d46ffb78ebaffffa3aa7c0a09e1b0d040982732a420fa9319a52291d176911adad0c3c52431299c311f11a4430d6846893e4e12452a9c31563e4bf9169d3e4fe5e11c6a3e2871871ad93e4ca1e4b109b513e985fd6bde5a5aa534457a1117040c3135861598dc63025264f1c8826ef471d4090a928b47577f908677551d844b')
#mew_offset = 0
###Uncomment next two lines if you have the rom
mew_sprite_compressed = ConstBitStream(filename='Pokemon Red.gb')
mew_offset = 0x4112*8
#mew_offset = 135207

mew_sprite_compressed.pos += mew_offset

sprite = Sprite(mew_sprite_compressed.read('uint:4'),mew_sprite_compressed.read('uint:4'),mew_sprite_compressed.read('uint:1'))
packet_type = mew_sprite_compressed.read('uint:1')

parseData(packet_type,sprite)
if mew_sprite_compressed.peek('uint:1') == 0:
    sprite.zip_mode = mew_sprite_compressed.read('uint:1')
else:
    sprite.zip_mode = mew_sprite_compressed.read('uint:2')

sprite.move_bitplane()
packet_type = mew_sprite_compressed.read('uint:1')


input("Press enter to process next buffer")
parseData(packet_type,sprite)

print(sprite)

sprite.bit_planes[0] = fillMatrix(sprite.bit_planes[0],sprite.width,sprite.height)
sprite.bit_planes[1] = fillMatrix(sprite.bit_planes[1],sprite.width,sprite.height)

if sprite.zip_mode == 0:
    sprite.bit_planes = mode1(sprite.bit_planes)
elif sprite.zip_mode == 2:
    sprite.bit_planes = mode2(sprite.bit_planes)
else:
    sprite.bit_planes = mode3(sprite.bit_planes)

sprite.bit_planes[0] = bufferToList(sprite.bit_planes[0],sprite.width,sprite.height)
sprite.bit_planes[1] = bufferToList(sprite.bit_planes[1],sprite.width,sprite.height)

sprite.sprite = combineBuffers(sprite.bit_planes)

print('---------FIRST BUFFER----------')
printPixels(sprite.bit_planes[0])
print('---------SECOND BUFFER----------')
printPixels(sprite.bit_planes[1])
print('---------Combined BUFFER----------')
printPixels(sprite.sprite)
#print('{:08X}'.format(int(mew_sprite_compressed.pos/8)))