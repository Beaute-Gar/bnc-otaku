"""Limiteur de débit par contact — anti-spam entrant et sortant."""

import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Limiteur entrant : max X messages par contact par fenêtre."""

    def __init__(self, max_per_contact: int, window_seconds: int):
        self.max_per_contact = max_per_contact
        self.window_seconds = window_seconds
        self._contacts: dict = defaultdict(deque)

    def is_allowed(self, sender_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        history = self._contacts[sender_id]
        while history and history[0] < window_start:
            history.popleft()
        if len(history) >= self.max_per_contact:
            return False
        history.append(now)
        return True

    def get_remaining(self, sender_id: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        history = self._contacts[sender_id]
        while history and history[0] < window_start:
            history.popleft()
        return max(0, self.max_per_contact - len(history))

    def reset(self, sender_id: str):
        self._contacts.pop(sender_id, None)


class OutgoingRateLimiter:
    """Limiteur sortant : max X messages/heure + délai min entre deux envois."""

    def __init__(self, max_per_hour: int, min_delay_seconds: float):
        self.max_per_hour = max_per_hour
        self.min_delay_seconds = min_delay_seconds
        self._sent_timestamps: deque = deque()
        self._last_sent_per_contact: dict = {}

    def can_send(self) -> bool:
        now = time.time()
        cutoff = now - 3600
        while self._sent_timestamps and self._sent_timestamps[0] < cutoff:
            self._sent_timestamps.popleft()
        return len(self._sent_timestamps) < self.max_per_hour

    def can_send_to(self, contact_id: str) -> bool:
        now = time.time()
        last = self._last_sent_per_contact.get(contact_id, 0)
        return (now - last) >= self.min_delay_seconds

    def record_send(self, contact_id: str):
        now = time.time()
        self._sent_timestamps.append(now)
        self._last_sent_per_contact[contact_id] = now

    def get_wait_time(self, contact_id: str) -> float:
        now = time.time()
        last = self._last_sent_per_contact.get(contact_id, 0)
        return max(0.0, self.min_delay_seconds - (now - last))
