import re

PATTERNS = [
    r"ignore\s+(all|any|the|previous)?\s*instructions",
    r"disregard\s+(all|any|the|previous)?\s*instructions",
    r"override\s+instructions",
    r"system\s*prompt",
    r"developer\s+message",
    r"^\s*system\s*:",
    r"\bsystem\s*:\s*call\b",
    r"admin\s+authorization",
    r"drop\s+table",
    r"truncate\s+table",
    r"delete\s+(all|every)",
    r"delete_customer",
    r"reveal\s+.*password",
    r"send\s+.*(secret|password|credential|token)",
    r"bypass\s+.*security",
    r"you\s+are\s+now\b",
]

def detect_injection(text: str) -> list[str]:
    low = text.lower()
    return [p for p in PATTERNS if re.search(p, low)]

def classify_content(text: str) -> dict:
    hits = detect_injection(text)
    return {
        "suspicious": bool(hits),
        "patterns": hits,
        "instruction_authority": "untrusted" if hits else "data"
    }
