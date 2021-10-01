from bitstring import BitArray

class Sprite:
    
    sprite_data = BitArray()
    bit_planes = [BitArray(),BitArray()]

    def __init__(self,width,height,active_bit_plane,zip_mode=None) -> None:
        self.width = width
        self.height = height
        self.active_bit_plane = active_bit_plane
        self.zip_mode = zip_mode

    def move_bitplane(self):
        self.active_bit_plane ^= 1

    def __str__(self):
        return f"[Width: {self.width}, Height: {self.height}, ZipMode: {self.zip_mode}]"

    