"""
Users & Sales Teams
  users               ← res.users
  sales_teams         ← crm.team
  sales_team_members  ← crm.team.member (many-to-many)
"""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


sales_team_members = Table(
    "sales_team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("sales_teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    login: Mapped[str | None] = mapped_column(String(256), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(64))
    mobile: Mapped[str | None] = mapped_column(String(64))
    lang: Mapped[str | None] = mapped_column(String(16))
    tz: Mapped[str | None] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    share: Mapped[bool] = mapped_column(Boolean, default=False)  # portal/public user flag
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    led_teams: Mapped[list["SalesTeam"]] = relationship(back_populates="leader", foreign_keys="SalesTeam.leader_id")
    teams: Mapped[list["SalesTeam"]] = relationship(secondary="sales_team_members", back_populates="members")
    crm_leads: Mapped[list["CrmLead"]] = relationship(back_populates="user")           # noqa: F821
    sale_orders: Mapped[list["SaleOrder"]] = relationship(back_populates="user")       # noqa: F821
    activities: Mapped[list["Activity"]] = relationship(back_populates="user")         # noqa: F821
    messages: Mapped[list["Message"]] = relationship(back_populates="author")          # noqa: F821
    organized_meetings: Mapped[list["Meeting"]] = relationship(back_populates="organizer")  # noqa: F821


class SalesTeam(Base):
    __tablename__ = "sales_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odoo_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    leader_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    alias_email: Mapped[str | None] = mapped_column(String(320))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    leader: Mapped[User | None] = relationship(back_populates="led_teams", foreign_keys=[leader_id])
    members: Mapped[list[User]] = relationship(secondary="sales_team_members", back_populates="teams")
    crm_leads: Mapped[list["CrmLead"]] = relationship(back_populates="team")           # noqa: F821
    sale_orders: Mapped[list["SaleOrder"]] = relationship(back_populates="team")       # noqa: F821
