from datetime import datetime
from typing import Optional, Union, Dict, Any

from ted_sws.core.model import PropertyBaseModel, BaseModel
from ted_sws.event_manager.adapters.log import SeverityLevelType
from pydantic import Field

DictType = Union[Dict[str, Any], None]


class EventMessageDatetime(BaseModel):
    utc: datetime = Field(default_factory=datetime.utcnow)


class EventMessage(PropertyBaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    created_at: EventMessageDatetime = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    severity_level: Optional[SeverityLevelType] = None
    caller_name: Optional[str] = None
    started_at: EventMessageDatetime = None
    ended_at: EventMessageDatetime = None
    duration: Optional[float] = None
    kwargs: Optional[DictType] = None

    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True

    def __init__(self, **data):
        super().__init__(**data)
        self.create()

    def create(self):
        self.created_at = EventMessageDatetime()
        self.year = self.created_at.utc.year
        self.month = self.created_at.utc.month
        self.day = self.created_at.utc.day

    def start(self):
        self.started_at = EventMessageDatetime()

    def end(self):
        self.ended_at = EventMessageDatetime()
        self.duration = (self.ended_at.utc - self.started_at.utc).total_seconds()


class TechnicalEventMessage(EventMessage):
    pass


class NoticeEventMessage(EventMessage):
    notice_id: Optional[str] = None
    domain_action: Optional[str] = None


class MappingSuiteEventMessage(EventMessage):
    mapping_suite_id: Optional[str] = None


class EventMessageLogSettings(PropertyBaseModel):
    briefly: Optional[bool] = False
    force_handlers: Optional[bool] = False
