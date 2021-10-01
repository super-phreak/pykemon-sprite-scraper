from bitstring import BitArray, BitString, ConstBitStream

def expandRLEPacket(bit_length, value):
    return BitString((bit_length+value+1)*2)

def findRLEBound(sprite_data):
    length_found = sprite_data.readto('0b0')
    return length_found

def mode1(buf0, buf1):
    buf1 = deltaDecode(buf1)
    buf0 = deltaDecode(buf0)
    return buf0,buf1

def mode2(buf0, buf1):
    buf1 = deltaDecode(buf1)
    buf0 = buf0 ^ buf1
    return buf0,buf1

def mode3(buf0, buf1):
    buf1 = deltaDecode(buf1)
    buf0 = deltaDecode(buf0)
    buf0 = buf0 ^ buf1
    return buf0,buf1

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

def combineBuffers(buf0, buf1):
    result = [[buf0[i][j] + buf1[i][j]  for j in range(len(buf0[0]))] for i in range(len(buf0))]
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

mew_sprite_compressed = ConstBitStream(hex='0x55be0553c37eaf5304e6507d5ad2633548552546ad8118d66baaf52942213650a07f2126a92638d6e45810554e1a2a752288889218ed8b81391548418a55354a70c114c7ab5349217e15943549562548589a8548509ffc8a07a885ad55e294149a214850aa828232b8ba38a94e35689525794e586d46ffb78ebaffffa3aa7c0a09e1b0d040982732a420fa9319a52291d176911adad0c3c52431299c311f11a4430d6846893e4e12452a9c31563e4bf9169d3e4fe5e11c6a3e2871871ad93e4ca1e4b109b513e985fd6bde5a5aa534457a1117040c3135861598dc63025264f1c8826ef471d4090a928b47577f908677551d844b')
mew_offset = 0
###Uncomment next two lines if you have the rom
#mew_sprite_compressed = ConstBitStream(filename='Pokemon Red.gb')
#mew_offset = 0x4112*8


mew_sprite_compressed.pos += mew_offset

sprite_info = {}
sprite_info['width'] = mew_sprite_compressed.read('uint:4')
sprite_info['height'] = mew_sprite_compressed.read('uint:4')
sprite_info['active_bit_plane'] = mew_sprite_compressed.read('uint:1')

packet_type = mew_sprite_compressed.read('uint:1')

sprite_data = {}
sprite_data['mew_sprite'] = {
    'bit_planes': [BitArray(),BitArray()],
    'sprite': []
}

def parseData(packet_type):
    data_packet_count = 1
    while sprite_data['mew_sprite']['bit_planes'][sprite_info['active_bit_plane']].len < (sprite_info['width']*sprite_info['height']*64):
        if packet_type == 0:
            length = findRLEBound(mew_sprite_compressed)
            value = mew_sprite_compressed.read(("uint:%s" % length.len))
            zero_bits = expandRLEPacket(length.uint,value)
            sprite_data['mew_sprite']['bit_planes'][sprite_info['active_bit_plane']].append(zero_bits)
            packet_type = 1
            data_packet_count = 1
        else:
            data_packet = mew_sprite_compressed.read('bin:2')

            if data_packet != '00':
                sprite_data['mew_sprite']['bit_planes'][sprite_info['active_bit_plane']].append('0b'+data_packet)
                data_packet_count+=1
            else:
                packet_type = 0

        #Debug print for pulling my hair out on why it didnt work
        #print(len(sprite_data['mew_sprite']['bit_planes'][sprite_info['active_bit_plane']]),'Pos: ', (mew_sprite_compressed.pos),'PKT:', packet_type) 

parseData(packet_type)
if mew_sprite_compressed.peek('uint:1') == 0:
    sprite_info['zip_mode'] = mew_sprite_compressed.read('uint:1')
else:
    sprite_info['zip_mode'] = mew_sprite_compressed.read('uint:2')

sprite_info['active_bit_plane'] = sprite_info['active_bit_plane'] ^ 1
packet_type = mew_sprite_compressed.read('uint:1')


input("Press enter to process next buffer")
parseData(packet_type)

print(sprite_info)

sprite_data['mew_sprite']['bit_planes'][0] = fillMatrix(sprite_data['mew_sprite']['bit_planes'][0],sprite_info['width'],sprite_info['height'])
sprite_data['mew_sprite']['bit_planes'][1] = fillMatrix(sprite_data['mew_sprite']['bit_planes'][1],sprite_info['width'],sprite_info['height'])

if sprite_info['zip_mode'] == 0:
    sprite_data['mew_sprite']['bit_planes'][0], sprite_data['mew_sprite']['bit_planes'][1] = mode1(sprite_data['mew_sprite']['bit_planes'][0], sprite_data['mew_sprite']['bit_planes'][1])
elif sprite_info['zip_mode'] == 2:
    sprite_data['mew_sprite']['bit_planes'][0], sprite_data['mew_sprite']['bit_planes'][1] = mode2(sprite_data['mew_sprite']['bit_planes'][0], sprite_data['mew_sprite']['bit_planes'][1])
else:
    sprite_data['mew_sprite']['bit_planes'][0], sprite_data['mew_sprite']['bit_planes'][1] = mode3(sprite_data['mew_sprite']['bit_planes'][0], sprite_data['mew_sprite']['bit_planes'][1])

sprite_data['mew_sprite']['bit_planes'][0] = bufferToList(sprite_data['mew_sprite']['bit_planes'][0],sprite_info['width'],sprite_info['height'])
sprite_data['mew_sprite']['bit_planes'][1] = bufferToList(sprite_data['mew_sprite']['bit_planes'][1],sprite_info['width'],sprite_info['height'])

sprite_data['mew_sprite']['sprite'] = combineBuffers(sprite_data['mew_sprite']['bit_planes'][0],sprite_data['mew_sprite']['bit_planes'][1])

print('---------FIRST BUFFER----------')
printPixels(sprite_data['mew_sprite']['bit_planes'][0])
print('---------SECOND BUFFER----------')
printPixels(sprite_data['mew_sprite']['bit_planes'][1])
print('---------Combined BUFFER----------')
printPixels(sprite_data['mew_sprite']['sprite'])
