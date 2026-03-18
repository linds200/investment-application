from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db

if TYPE_CHECKING:
    from app.models import User, Portfolio

class PortfolioSecurity(db.Model):
    __tablename__ = 'Portfolio_Security'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('Portfolio.id'), nullable=False)
    username: Mapped[str] = mapped_column(String(30), ForeignKey('User.username'), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    portfolio: Mapped['Portfolio'] = relationship('Portfolio', back_populates='portfolio_securities', lazy='selectin')
    user: Mapped['User'] = relationship('User', back_populates='portfolio_securities', lazy='selectin')

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            portfolio_id: int | None = None,
            username: str | None = None,
            role: str | None = None,
        ) -> None: ...
        
    def __str__(self):
        return f'<PortfolioSecurity: id={self.id}; portfolio_id={self.portfolio_id}; username={self.username}; role={self.role}>'

    def __to_dict__(self):
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'username': self.username,
            'role': self.role,
        }