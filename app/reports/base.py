"""Base class for report generators."""

from abc import ABC, abstractmethod

from app.models.signal import Signal


class BaseReportGenerator(ABC):
    report_type: str
    name: str

    @abstractmethod
    async def generate(self, signals: list[Signal], audit_data: dict) -> dict:
        ...
