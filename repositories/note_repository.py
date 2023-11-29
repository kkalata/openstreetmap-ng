from collections.abc import Sequence
from datetime import datetime, timedelta

from shapely import Polygon
from sqlalchemy import func, null, select

from db import DB
from lib.auth import auth_user
from limits import FIND_LIMIT
from models.db.note import Note
from models.db.note_comment import NoteComment
from utils import utcnow


class NoteRepository:
    @staticmethod
    async def find_many_by_query(
        *,
        note_ids: Sequence[int] | None = None,
        text: str | None = None,
        user_id: int | None = None,
        max_closed_for: timedelta | None = None,
        geometry: Polygon | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by_created: bool = True,
        sort_asc: bool = False,
        limit: int | None = FIND_LIMIT,
    ) -> Sequence[Note]:
        """
        Find notes by query.
        """

        async with DB() as session:
            stmt = select(Note).join(NoteComment)
            where_and = []
            sort_by_key = Note.created_at if sort_by_created else Note.updated_at

            # only show hidden notes to moderators
            if not (user := auth_user()) or not user.is_moderator:
                where_and.append(Note.hidden_at == null())

            if note_ids:
                where_and.append(Note.id.in_(note_ids))
            if text:
                where_and.append(func.to_tsvector(NoteComment.body).bool_op('@@')(func.phraseto_tsquery(text)))
            if user_id:
                where_and.append(NoteComment.user_id == user_id)
            if max_closed_for is not None:
                if max_closed_for:
                    where_and.append(Note.closed_at >= utcnow() - max_closed_for)
                else:
                    where_and.append(Note.closed_at == null())
            if geometry:
                where_and.append(func.ST_Intersects(Note.point, geometry.wkt))
            if date_from:
                where_and.append(sort_by_key >= date_from)
            if date_to:
                where_and.append(sort_by_key < date_to)

            if where_and:
                stmt = stmt.where(*where_and)

            # small optimization, skip sort if at most one note will be returned
            if not (note_ids and len(note_ids) == 1):
                stmt = stmt.order_by(sort_by_key.asc() if sort_asc else sort_by_key.desc())

            if limit is not None:
                stmt = stmt.limit(limit)

            return (await session.scalars(stmt)).all()
