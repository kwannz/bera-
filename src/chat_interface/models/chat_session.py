from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class ChatSession:
    session_id: str
    messages: List[Dict[str, str]]
    created_at: datetime = datetime.now()
    last_updated: datetime = datetime.now()
    metadata: Optional[Dict] = None
