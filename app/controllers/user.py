from datetime import timedelta
from typing import Annotated

from anyio import create_task_group
from fastapi import APIRouter, Path
from starlette import status
from starlette.responses import RedirectResponse

from app.lib.auth_context import auth_user, web_user
from app.lib.date_utils import utcnow
from app.lib.legal import legal_terms
from app.lib.render_response import render_response
from app.limits import DISPLAY_NAME_MAX_LENGTH, USER_NEW_DAYS
from app.models.db.user import User
from app.models.note_event import NoteEvent
from app.models.user_status import UserStatus
from app.queries.changeset_comment_query import ChangesetCommentQuery
from app.queries.changeset_query import ChangesetQuery
from app.queries.note_comment_query import NoteCommentQuery
from app.queries.note_query import NoteQuery
from app.queries.trace_query import TraceQuery
from app.queries.user_query import UserQuery

router = APIRouter(prefix='/user')


@router.get('/terms')
async def terms(user: Annotated[User, web_user()]):
    if user.status != UserStatus.pending_terms:
        return RedirectResponse('/', status.HTTP_303_SEE_OTHER)
    return render_response(
        'user/terms.jinja2',
        {
            'legal_terms_GB': legal_terms('GB'),
            'legal_terms_FR': legal_terms('FR'),
            'legal_terms_IT': legal_terms('IT'),
        },
    )


@router.get('/account-confirm/pending')
async def account_confirm_pending(user: Annotated[User, web_user()]):
    if user.status != UserStatus.pending_activation:
        return RedirectResponse('/welcome', status.HTTP_303_SEE_OTHER)
    return render_response('user/account_confirm_pending.jinja2')


@router.get('/new')
async def legacy_signup():
    return RedirectResponse('/signup', status.HTTP_301_MOVED_PERMANENTLY)


# TODO: not found, https://www.openstreetmap.org/user/abafaegfeagaeg
# TODO: /u/UserName ?
# TODO: optimize
@router.get('/{display_name:str}')
async def index(display_name: Annotated[str, Path(min_length=1, max_length=DISPLAY_NAME_MAX_LENGTH)]):
    user = await UserQuery.find_one_by_display_name(display_name)
    await user.resolve_rich_text()

    me = auth_user()
    is_self = (me is not None) and me.id == user.id

    account_age = utcnow() - user.created_at
    is_new_user = account_age < timedelta(days=USER_NEW_DAYS)

    changesets_count = await ChangesetQuery.count_by_user_id(user.id)
    changeset_comments_count = 0  # TODO:
    changesets = await ChangesetQuery.find_many_by_query(user_id=user.id, sort='desc', limit=5)
    await ChangesetCommentQuery.resolve_num_comments(changesets)

    notes_count = await NoteQuery.count_by_user_id(user.id)
    note_comments_count = 0  # TODO:
    notes = await NoteQuery.find_many_by_query(user_id=user.id, event=NoteEvent.opened, sort_dir='desc', limit=5)
    await NoteCommentQuery.resolve_comments(notes, per_note_sort='asc', per_note_limit=1)

    async with create_task_group() as tg:
        for note in notes:
            tg.start_soon(note.comments[0].resolve_rich_text)

    traces_count = await TraceQuery.count_by_user_id(user.id)
    traces = await TraceQuery.find_many_by_user_id(user.id, sort='desc', limit=5)

    # TODO: diaries

    return render_response(
        'user/index.jinja2',
        {
            'profile': user,
            'is_self': is_self,
            'is_new_user': is_new_user,
            'changesets_count': changesets_count,
            'changeset_comments_count': changeset_comments_count,
            'changesets': changesets,
            'notes_count': notes_count,
            'note_comments_count': note_comments_count,
            'notes': notes,
            'traces_count': traces_count,
            'traces': traces,
        },
    )
