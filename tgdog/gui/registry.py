import binascii


window_registry = {}
button_registry = {}


class RegistryMeta(type):

    def __new__(cls, name, bases, dct):
        if not bases:  # Base window class
            return super().__new__(cls, name, bases, dct)
        crc32 = binascii.crc32(name.encode())
        crc32 = crc32.to_bytes(4, 'big')
        if crc32 in cls.registry:
            if cls.registry[crc32].__name__ == name:
                raise ValueError(f'Class {name} already registered')
            raise ValueError(f'CRC32 for classes {cls.registry[crc32].__name__} and {name} matched!')
        dct['crc32'] = crc32
        instance = super().__new__(cls, name, bases, dct)
        cls.registry[crc32] = instance
        return instance


class WindowMeta(RegistryMeta):
    registry = window_registry


class ButtonMeta(RegistryMeta):
    registry = button_registry
