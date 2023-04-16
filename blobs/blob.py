
class BlobMeta(type):
    """A Blob metaclass."""

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass):
        return (hasattr(subclass, '__add__') and
                callable(subclass.__add__) and
                hasattr(subclass, 'add_blip') and
                callable(subclass.add_blip))

class BlobSuper:
    """A Blob superclass."""

    def __add__(self) -> str:
        pass

    def add_blip(self) -> int:
        pass

class Blob(metaclass=BlobMeta):
    """
    Blob interface built from Blob metaclass.

    Blobs hold data and can easily be combined.
    """
    pass
