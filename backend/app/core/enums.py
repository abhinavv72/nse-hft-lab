from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class StrategyKind(str, Enum):
    MARKET_MAKER = "market_maker"
    MEAN_REVERSION = "mean_reversion"


class SessionMode(str, Enum):
    LIVE = "live"
    REPLAY = "replay"
    PAUSED = "paused"

