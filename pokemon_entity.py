from sprite import Sprite

class Pokemon:
    def __init__(self, name, back_sprite, front_sprite) -> None:
        self.name = name
        self.back_sprite = back_sprite
        self.front_sprite = front_sprite

    def __str__(self) -> str:
        return f"{self.front_sprite},{self.back_sprite}"