from enum import Enum, auto


class IROpcode(Enum):
    MOVE_RUN = auto()
    MOVE_RUN_TIME = auto()
    MOVE_STOP = auto()
    WAIT = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()
    CALL = auto()
    RETURN = auto()