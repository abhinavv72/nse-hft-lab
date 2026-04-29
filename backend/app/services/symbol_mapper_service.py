from __future__ import annotations


class SymbolMapperService:
    def __init__(self) -> None:
        self.aliases: dict[str, set[str]] = {
            "NIFTY": {"NIFTY", "NIFTY 50", "NIFTY50"},
            "BANKNIFTY": {"BANKNIFTY", "BANK NIFTY", "BANKING INDEX"},
            "RELIANCE": {"RELIANCE", "RIL", "RELIANCE INDUSTRIES"},
            "TCS": {"TCS", "TATA CONSULTANCY SERVICES"},
            "INFY": {"INFY", "INFOSYS"},
            "SBIN": {"SBIN", "SBI", "STATE BANK OF INDIA"},
        }

    def map_text(self, text: str) -> list[str]:
        upper_text = text.upper()
        matches = [symbol for symbol, aliases in self.aliases.items() if any(alias in upper_text for alias in aliases)]
        if "IT " in upper_text or "TECH STOCKS" in upper_text or "SOFTWARE" in upper_text:
            for symbol in ("TCS", "INFY"):
                if symbol not in matches:
                    matches.append(symbol)
        if "BANK" in upper_text and "BANKNIFTY" not in matches:
            matches.append("BANKNIFTY")
        return matches
