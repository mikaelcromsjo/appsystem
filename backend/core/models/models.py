# Re-export shim — canonical locations are models/base.py, models/user.py, models/tag.py
from models.base import BaseMixin, Update
from models.user import User, UserUpdate
from models.tag import Tag, TagLink

__all__ = ["BaseMixin", "Update", "User", "UserUpdate", "Tag", "TagLink"]
