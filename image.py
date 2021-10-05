from bitstring import BitArray

class Sprite:

    def __init__(self,rom_index,width,height,high_bit_plane,zip_mode=None) -> None:
        self.rom_index = rom_index
        self.width = width
        self.height = height
        self.high_bit_plane = high_bit_plane
        self.zip_mode = zip_mode
        self.sprite_data = BitArray()
        self.bit_planes = [BitArray(),BitArray()]
        self.active_bit_plane = 1
        self.bitlength = 0
        

    def move_bitplane(self):
        self.active_bit_plane ^= 1

    def __str__(self):
        return f"[Loc: {self.rom_index:08X} => Width: {self.width}, Height: {self.height}, ZipMode: {self.zip_mode}, (Length {self.bitlength:04X})]"

    