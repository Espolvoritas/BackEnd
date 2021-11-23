from enum import Enum

import sys

WS_CURR_PLAYER=1
WS_CARD_LIST=2
WS_SUSPICION=4
WS_PICK_CARD=8
WS_SUSPICION_STATUS=16
WS_SENT_CARD_NOTIFY=32
WS_AVAIL_MOVES=64
WS_POS_LIST=128
WS_ROOM=256
WS_ACCUSATION=512
WS_LOST=1024
WS_SALEM=2048
WS_CHAT_MSG=8192

class trapped_status(Enum):
	NOT_TRAPPED=0
	TRAPPED=1
	CAN_LEAVE=2


#Yes i know, pytest behaviour bad, but otherwise we'd be waiting a full 60 seconds extra per test
#And nobody's got time for that
if "pytest" in sys.modules:
    DISCONNECT_TIMER=1
    CHOOSE_CARD_TIMER=1
else: # pragma: no cover
    DISCONNECT_TIMER=60
    CHOOSE_CARD_TIMER=30
