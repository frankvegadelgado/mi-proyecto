"""
Communication & Activities
  activity_types    ← mail.activity.type
  activities        ← mail.activity
  messages          ← mail.message
  meetings          ← calendar.event
  meeting_attendees ← calendar.attendee
"""
from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


meeting_attendees_table = Table(
    "meeting_attendees",
    Base.metadata,
    Column("meeting_id", UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True),
    Column("partner_id", UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True),
    Column("state", String(32)),          # needsAction, tentative, declined, accepted
    Column("availability", String(32)),   # busy, free
)


class ActivityType(Base):
    __tablename__ = "activity_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(256))
    icon: Mapped[str | None] = mapped_column(String(64))    # Font Awesome class, e.g. "fa-phone"
    decoration_type: Mapped[str | None] = mapped_column(String(32))  # warning, danger, success, info
    delay_count: Mapped[int | None] = mapped_column(Integer)
    delay_unit: Mapped[str | None] = mapped_column(String(16))  # days, weeks, months
    delay_from: Mapped[str | None] = mapped_column(String(32))  # current_date, previous_activity_deadline
    category: Mapped[str | None] = mapped_column(String(32))    # default, upload_file, sign_request, email, sms, meeting, phonecall, todo

    activities: Mapped[list["Activity"]] = relationship(back_populates="activity_type")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    activity_type_id: Mapped[int | None] = mapped_column(ForeignKey("activity_types.id"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Polymorphic target (what record is this activity for?)
    res_model: Mapped[str | None] = mapped_column(String(128), index=True)  # e.g. crm.lead, sale.order
    res_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # UUID of the target record
    res_name: Mapped[str | None] = mapped_column(String(256))  # denorm display name

    summary: Mapped[str | None] = mapped_column(String(256))
    note: Mapped[str | None] = mapped_column(Text)
    date_deadline: Mapped[date | None] = mapped_column(Date, index=True)
    date_done: Mapped[date | None] = mapped_column(Date)
    state: Mapped[str | None] = mapped_column(String(32))  # overdue, today, planned, done, cancelled

    # For email / meeting activities
    calendar_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    activity_type: Mapped[ActivityType | None] = relationship(back_populates="activities")
    user: Mapped["User | None"] = relationship(back_populates="activities")             # noqa: F821
    meeting: Mapped["Meeting | None"] = relationship()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)

    author_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Polymorphic target
    res_model: Mapped[str | None] = mapped_column(String(128), index=True)
    res_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    res_name: Mapped[str | None] = mapped_column(String(256))

    message_type: Mapped[str] = mapped_column(String(32), default="comment")  # email, comment, notification, sms
    subtype_name: Mapped[str | None] = mapped_column(String(128))  # e.g. Discussions, Note, Log Note
    subject: Mapped[str | None] = mapped_column(String(512))
    body: Mapped[str | None] = mapped_column(Text)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    email_from: Mapped[str | None] = mapped_column(String(320))
    reply_to: Mapped[str | None] = mapped_column(String(320))
    message_id: Mapped[str | None] = mapped_column(String(512), index=True)  # SMTP Message-ID
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"))
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)  # internal note / log

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped["User | None"] = relationship(back_populates="messages")            # noqa: F821
    parent: Mapped["Message | None"] = relationship("Message", remote_side="Message.id")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    odoo_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    organizer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    stop: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    allday: Mapped[bool] = mapped_column(Boolean, default=False)
    start_date: Mapped[date | None] = mapped_column(Date)  # for all-day events
    stop_date: Mapped[date | None] = mapped_column(Date)

    location: Mapped[str | None] = mapped_column(String(512))
    videocall_location: Mapped[str | None] = mapped_column(String(512))
    privacy: Mapped[str | None] = mapped_column(String(32))          # public, private, confidential
    show_as: Mapped[str | None] = mapped_column(String(32))          # busy, free
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Recurrence
    recurrency: Mapped[bool] = mapped_column(Boolean, default=False)
    rrule: Mapped[str | None] = mapped_column(String(512))           # iCal RRULE string
    recurrence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.id"))

    # Linked CRM lead
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("crm_leads.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organizer: Mapped["User | None"] = relationship(back_populates="organized_meetings")  # noqa: F821
    attendees: Mapped[list["Partner"]] = relationship(secondary="meeting_attendees", back_populates="meeting_attendances")  # noqa: F821
    recurrence: Mapped["Meeting | None"] = relationship("Meeting", remote_side="Meeting.id")


class MeetingAttendee(Base):
    """View-model for querying attendee state — wraps the association table."""
    __tablename__ = "meeting_attendees"
    __table_args__ = {"extend_existing": True}

    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True)
    state: Mapped[str | None] = mapped_column(String(32))
    availability: Mapped[str | None] = mapped_column(String(32))

    partner: Mapped["Partner"] = relationship(back_populates="meeting_attendances")   # noqa: F821
    meeting: Mapped[Meeting] = relationship()
