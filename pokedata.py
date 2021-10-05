from bitstring import BitArray, Bits, BitString, ConstBitStream
from image import Sprite
from pokemon_entity import Pokemon

def expandRLEPacket(bit_length, value) -> BitString:
    return BitString((bit_length+value+1)*2)

def findRLEBound(sprite_data) -> Bits:
    length_found = sprite_data.readto('0b0')
    return length_found

def mode1(sprite) -> list:
    sprite.bit_planes[1] = deltaDecode(sprite.bit_planes[1],sprite.width)
    sprite.bit_planes[0] = deltaDecode(sprite.bit_planes[0],sprite.width)
    return sprite.bit_planes

def mode2(sprite) -> list:
    sprite.bit_planes[1] = deltaDecode(sprite.bit_planes[1],sprite.width)
    sprite.bit_planes[0] = sprite.bit_planes[0] ^ sprite.bit_planes[1] 
    return sprite.bit_planes

def mode3(sprite) -> list:
    sprite.bit_planes[1] = deltaDecode(sprite.bit_planes[1],sprite.width)
    sprite.bit_planes[0] = deltaDecode(sprite.bit_planes[0],sprite.width)
    sprite.bit_planes[0] = sprite.bit_planes[0] ^ sprite.bit_planes[1]
    return sprite.bit_planes

def fillMatrix(arr,row_num, coloumn_num) -> BitArray:
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

def bufferToList(arr, row_num, coloumn_num) -> list:
    bufList = [0] * row_num*8
    column_bits = coloumn_num*8
    for row in range(row_num*8):
        bufList[row]=list(map(int,(','.join(arr[(row*column_bits):((row*column_bits)+column_bits)].bin).split(','))))

    return bufList

def combineBuffers(sprite) -> list:
    result = [[(sprite.bit_planes[sprite.high_bit_plane][i][j]<<1) + sprite.bit_planes[sprite.high_bit_plane^1][i][j]  for j in range(len(sprite.bit_planes[sprite.high_bit_plane][0]))] for i in range(len(sprite.bit_planes[1]))]
    return result


def printPixels(buffer):
    for row in buffer:
        print(','.join(map(str,row)))
        

def deltaDecode(arr, width) -> BitArray:
    output = BitArray()
    currentBit = 0
    for index, bit in enumerate(arr):
        if index % (width*8) == 0:
            currentBit = 0
        if bit:
            currentBit = (currentBit ^ 1)
        
        output.append('0b%s' % currentBit)
    return output

def parseData(packet_type, sprite):
    data_packet_count = 1
    while sprite.bit_planes[sprite.active_bit_plane].len < (sprite.width*sprite.height*64):
        if packet_type == 0:
            length = findRLEBound(rom)
            value = rom.read((f"uint:{length.len}"))
            zero_bits = expandRLEPacket(length.uint,value)
            sprite.bit_planes[sprite.active_bit_plane].append(zero_bits)
            packet_type = 1
            data_packet_count = 1
        else:
            data_packet = rom.read('bin:2')

            if data_packet != '00':
                sprite.bit_planes[sprite.active_bit_plane].append('0b'+data_packet)
                data_packet_count+=1
            else:
                packet_type = 0

        #Debug print for pulling my hair out on why it didnt work
        #print(len(sprite_data['mew_sprite']['bit_planes'][sprite_info['active_bit_plane']]),'Pos: ', (rom.pos),'PKT:', packet_type) 

def parseSprite(sprite, index) -> Sprite:
    pass

def printPkmnFront(pkmn):
    ### Debug Prints ###
    # print(pkmn.front_sprite)
    # printPixels(pkmn.front_sprite.bit_planes[0])
    # print()
    # printPixels(pkmn.front_sprite.bit_planes[1])
    # print()
    ### Debug Prints ###
    printPixels(pkmn.front_sprite.sprite)
def printPkmnBack(pkmn):
    ### Debug Prints ###
    # print(pkmn.back_sprite)
    # printPixels(pkmn.back_sprite.bit_planes[0])
    # print()
    # printPixels(pkmn.back_sprite.bit_planes[1])
    # print()
    ### Debug Prints ###
    printPixels(pkmn.back_sprite.sprite)
def printPkmn(pkmn,sprite):
    if sprite == 0:
        printPkmnBack(pkmn)
    else:
        printPkmnFront(pkmn)

rom = ConstBitStream(filename='Pokemon Red.gb')
pokedex = [
    ('RHYDON',[0x00024202,0x00024000]),
    ('KANGASKHAN',[0x000244A6,0x0002429A]),
    ('NIDORAN_M',[0x00024623,0x0002453C]),
    ('CLEFAIRY',[0x00024785,0x00024682]),
    ('SPEAROW',[0x000248C2,0x000247DF]),
    ('VOLTORB',[0x0002499A,0x00024911]),
    ('NIDOKING',[0x00024C60,0x000249F8]),
    ('SLOWBRO',[0x00024F87,0x00024D0A]),
    ('IVYSAUR',[0x00025157,0x0002502B]),
    ('EXEGGUTOR',[0x000253F8,0x000251D6]),
    ('LICKITUNG',[0x0002563E,0x000254A7]),
    ('EXEGGCUTE',[0x000258F0,0x000256D7]),
    ('GRIMER',[0x00025AB0,0x00025973]),
    ('GENGAR',[0x00025CC6,0x00025B76]),
    ('NIDORAN_F',[0x00025DC2,0x00025D28]),
    ('NIDOQUEEN',[0x00025FEF,0x00025E09]),
    ('CUBONE',[0x00026196,0x000260A8]),
    ('RHYHORN',[0x0002640F,0x00026208]),
    ('LAPRAS',[0x0002667C,0x000264C1]),
    ('ARCANINE',[0x0002693D,0x000266FF]),
    ('GYARADOS',[0x00026C25,0x000269D4]),
    ('SHELLDER',[0x00026DC3,0x00026CB6]),
    ('TENTACOOL',[0x00026F1C,0x00026E2A]),
    ('GASTLY',[0x00027190,0x00026F77]),
    ('SCYTHER',[0x0002743C,0x0002721C]),
    ('STARYU',[0x000275EC,0x000274E0]),
    ('BLASTOISE',[0x00027851,0x00027637]),
    ('PINSIR',[0x00027AAA,0x000278DA]),
    ('TANGELA',[0x00027CE7,0x00027B39]),
    ('GROWLITHE',[0x00028101,0x00028000]),
    ('ONIX',[0x00028300,0x00028164]),
    ('FEAROW',[0x00028529,0x00028383]),
    ('PIDGEY',[0x0002865B,0x000285A7]),
    ('SLOWPOKE',[0x000287C2,0x000286A0]),
    ('KADABRA',[0x000289B9,0x00028830]),
    ('GRAVELER',[0x00028C00,0x00028A4C]),
    ('CHANSEY',[0x00028E21,0x00028CAE]),
    ('MACHOKE',[0x00029063,0x00028E85]),
    ('MR_MIME',[0x00029247,0x000290F3]),
    ('HITMONLEE',[0x0002945E,0x000292BF]),
    ('HITMONCHAN',[0x00029643,0x000294BC]),
    ('ARBOK',[0x00029911,0x000296B4]),
    ('PARASECT',[0x00029B8C,0x000299A8]),
    ('PSYDUCK',[0x00029D3E,0x00029C0A]),
    ('DROWZEE',[0x00029F05,0x00029DA9]),
    ('GOLEM',[0x0002A0F2,0x00029F74]),
    ('MAGMAR',[0x0002A2BF,0x0002A161]),
    ('ELECTABUZZ',[0x0002A4EF,0x0002A367]),
    ('MAGNETON',[0x0002A723,0x0002A588]),
    ('KOFFING',[0x0002A974,0x0002A7A6]),
    ('MANKEY',[0x0002AB16,0x0002AA11]),
    ('SEEL',[0x0002ACE8,0x0002AB84]),
    ('DIGLETT',[0x0002AE10,0x0002AD33]),
    ('TAUROS',[0x0002B054,0x0002AE7E]),
    ('FARFETCHD',[0x0002B2C6,0x0002B0E9]),
    ('VENONAT',[0x0002B45C,0x0002B357]),
    ('DRAGONITE',[0x0002B67F,0x0002B4AA]),
    ('DODUO',[0x0002B80D,0x0002B72C]),
    ('POLIWAG',[0x0002B947,0x0002B875]),
    ('JYNX',[0x0002BB42,0x0002B98E]),
    ('MOLTRES',[0x0002BE02,0x0002BBAC]),
    ('ARTICUNO',[0x0002C238,0x0002C000]),
    ('ZAPDOS',[0x0002C484,0x0002C29D]),
    ('DITTO',[0x0002C5BD,0x0002C514]),
    ('MEOWTH',[0x0002C71F,0x0002C609]),
    ('KRABBY',[0x0002C8B0,0x0002C777]),
    ('VULPIX',[0x0002CA9A,0x0002C924]),
    ('NINETALES',[0x0002CCFB,0x0002CAFF]),
    ('PIKACHU',[0x0002CE8B,0x0002CD7D]),
    ('RAICHU',[0x0002D0C3,0x0002CF03]),
    ('DRATINI',[0x0002D234,0x0002D151]),
    ('DRAGONAIR',[0x0002D3D9,0x0002D297]),
    ('KABUTO',[0x0002D529,0x0002D464]),
    ('KABUTOPS',[0x0002D73C,0x0002D583]),
    ('HORSEA',[0x0002D873,0x0002D7C1]),
    ('SEADRA',[0x0002DA2B,0x0002D8C4]),
    ('SANDSHREW',[0x0002DBE7,0x0002DAC9]),
    ('SANDSLASH',[0x0002DE04,0x0002DC6B]),
    ('OMANYTE',[0x0002DF76,0x0002DE9D]),
    ('OMASTAR',[0x0002E18B,0x0002DFD3]),
    ('JIGGLYPUFF',[0x0002E30F,0x0002E22F]),
    ('WIGGLYTUFF',[0x0002E4BF,0x0002E348]),
    ('EEVEE',[0x0002E625,0x0002E531]),
    ('FLAREON',[0x0002E806,0x0002E68D]),
    ('JOLTEON',[0x0002EA0A,0x0002E88F]),
    ('VAPOREON',[0x0002EC02,0x0002EAAE]),
    ('MACHOP',[0x0002EDA2,0x0002EC9F]),
    ('ZUBAT',[0x0002EF17,0x0002EE0C]),
    ('EKANS',[0x0002F06D,0x0002EF6B]),
    ('PARAS',[0x0002F177,0x0002F0B4]),
    ('POLIWHIRL',[0x0002F35E,0x0002F1ED]),
    ('POLIWRATH',[0x0002F52C,0x0002F3C1]),
    ('WEEDLE',[0x0002F624,0x0002F57D]),
    ('KAKUNA',[0x0002F736,0x0002F677]),
    ('BEEDRILL',[0x0002F980,0x0002F788]),
    ('DODRIO',[0x000301A2,0x00030000]),
    ('PRIMEAPE',[0x00030408,0x00030247]),
    ('DUGTRIO',[0x0003062A,0x00030480]),
    ('VENOMOTH',[0x00030841,0x000306A9]),
    ('DEWGONG',[0x000309E2,0x00030899]),
    ('CATERPIE',[0x00030AE1,0x00030A49]),
    ('METAPOD',[0x00030BC8,0x00030B3A]),
    ('BUTTERFREE',[0x00030E0E,0x00030C37]),
    ('MACHAMP',[0x0003108C,0x00030E93]),
    ('GOLDUCK',[0x000312C2,0x00031108]),
    ('HYPNO',[0x00031552,0x0003135D]),
    ('GOLBAT',[0x0003180A,0x000315E0]),
    ('MEWTWO',[0x00031A85,0x0003187F]),
    ('SNORLAX',[0x00031CE5,0x00031B19]),
    ('MAGIKARP',[0x00031EC3,0x00031D31]),
    ('MUK',[0x0003215F,0x00031F56]),
    ('KINGLER',[0x000323DE,0x000321EC]),
    ('CLOYSTER',[0x000326AB,0x0003247F]),
    ('ELECTRODE',[0x00032827,0x00032760]),
    ('CLEFABLE',[0x000329B8,0x0003288C]),
    ('WEEZING',[0x00032C76,0x00032A44]),
    ('PERSIAN',[0x00032F04,0x00032D1E]),
    ('MAROWAK',[0x00033101,0x00032F8F]),
    ('HAUNTER',[0x00033345,0x0003318A]),
    ('ABRA',[0x000334CF,0x000333CC]),
    ('ALAKAZAM',[0x00033779,0x0003355A]),
    ('PIDGEOTTO',[0x0003395B,0x0003380A]),
    ('PIDGEOT',[0x00033B79,0x000339C2]),
    ('STARMIE',[0x00033DAC,0x00033C1C]),
    ('BULBASAUR',[0x000340E5,0x00034000]),
    ('VENUSAUR',[0x00034397,0x00034162]),
    ('TENTACRUEL',[0x000345C3,0x00034455]),
    ('GOLDEEN',[0x00034796,0x0003466F]),
    ('SEAKING',[0x00034A03,0x00034803]),
    ('PONYTA',[0x00034E32,0x00034AB1]),
    ('RAPIDASH',[0x00034EBA,0x00034C10]),
    ('RATTATA',[0x00035041,0x00034F6A]),
    ('RATICATE',[0x0003520D,0x0003507A]),
    ('NIDORINO',[0x000353F0,0x00035282]),
    ('NIDORINA',[0x000355C8,0x0003548B]),
    ('GEODUDE',[0x00035729,0x0003564F]),
    ('PORYGON',[0x000358D1,0x00035784]),
    ('AERODACTYL',[0x00035AEC,0x00035931]),
    ('MAGNEMITE',[0x00035C0D,0x00035B87]),
    ('CHARMANDER',[0x00035D5C,0x00035C5C]),
    ('SQUIRTLE',[0x00035E8F,0x00035DB8]),
    ('CHARMELEON',[0x00036048,0x00035F0C]),
    ('WARTORTLE',[0x000361F1,0x000360B1]),
    ('CHARIZARD',[0x00036495,0x00036286]),
    ('ODDISH',[0x000368A9,0x0003680B]),
    ('GLOOM',[0x00036A78,0x00036941]),
    ('VILEPLUME',[0x00036C82,0x00036B21]),
    ('BELLSPROUT',[0x00036DBA,0x00036D00]),
    ('WEEPINBELL',[0x00036F6F,0x00036E30]),
    ('VICTREEBEL',[0x000371B2,0x00036FEA]),
    ('AERODACTYL_F',[0x00036536,0x00036536]),
    ('GHOST',[0x000366B5,0x000366B5])
]

mons = {}

for mon in pokedex:
    sprites = []
    for i in range(2):
        rom.pos = mon[1][i]*8
        sprite = Sprite(int(rom.pos/8),rom.read('uint:4'),rom.read('uint:4'),rom.read('uint:1'))
        packet_type = rom.read('uint:1')
        parseData(packet_type,sprite)

        if rom.peek('uint:1') == 0:
            print("ZIP MODE0")
            sprite.zip_mode = rom.read('uint:1')
        else:
            sprite.zip_mode = rom.read('uint:2')

        sprite.move_bitplane()
        packet_type = rom.read('uint:1')

        parseData(packet_type,sprite)

        sprite.bit_planes[0] = fillMatrix(sprite.bit_planes[0],sprite.width,sprite.height)
        sprite.bit_planes[1] = fillMatrix(sprite.bit_planes[1],sprite.width,sprite.height)

        if sprite.zip_mode == 0:
            sprite.bit_planes = mode1(sprite)
        elif sprite.zip_mode == 2:
            sprite.bit_planes = mode2(sprite)
        else:
            sprite.bit_planes = mode3(sprite)

        sprite.bit_planes[0] = bufferToList(sprite.bit_planes[0],sprite.width,sprite.height)
        sprite.bit_planes[1] = bufferToList(sprite.bit_planes[1],sprite.width,sprite.height)

        sprite.sprite = combineBuffers(sprite)
        rom.pos = ((int(rom.pos/8))+1)*8
        sprite.bitlength = int(rom.pos/8) - sprite.rom_index
        sprites.append(sprite)
    
    mons[mon[0]] = Pokemon(mon[0],sprites[0],sprites[1])

for name,data in mons.items():
    print(f"'{name:12s}',{data}")
    printPkmnFront(data)
    print()
    printPkmnBack(data)
    print()