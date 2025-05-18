import asyncio

from app.dtos.events.settlement_event import SettlementEvent

email_event_queue: asyncio.Queue[str] = asyncio.Queue()
settlement_event_queue: asyncio.Queue[SettlementEvent] = asyncio.Queue()