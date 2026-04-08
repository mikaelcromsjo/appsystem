from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.models.base import Base


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class TagLink(Base):
    __tablename__ = "tag_links"
    id = Column(Integer, primary_key=True)
    tag_id = Column(ForeignKey("tags.id"))
    object_id = Column(Integer, index=True)
    object_type = Column(String, index=True)
    tag = relationship("Tag")
