from enum import Enum


class GarageItemRelations(str, Enum):
    HAS_OWNED = "HAS_OWNED"
    OWNS = "OWNS"
    HAS_RIDDEN = "HAS_RIDDEN"
    SAT_ON = "SAT_ON"
