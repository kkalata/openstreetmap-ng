from collections.abc import Sequence
from typing import Annotated

from anyio import create_task_group
from fastapi import APIRouter, Query, Response
from pydantic import PositiveInt
from sqlalchemy.orm import joinedload
from starlette import status

from app.format07 import Format07
from app.lib.element_list_formatter import format_element_members_list, format_element_parents_list
from app.lib.feature_name import feature_name
from app.lib.render_response import render_response
from app.lib.statement_context import options_context
from app.lib.tags_format import tags_format
from app.lib.translation import t
from app.limits import ELEMENT_HISTORY_PAGE_SIZE
from app.models.db.changeset import Changeset
from app.models.db.element import Element
from app.models.element_list_entry import ElementMemberEntry
from app.models.element_ref import ElementRef, VersionedElementRef
from app.models.element_type import ElementType
from app.models.tag_format import TagFormatCollection
from app.repositories.element_repository import ElementRepository
from app.utils import JSON_ENCODE

router = APIRouter(prefix='/api/partial/element')


async def _get_element_data(element: Element, at_sequence_id: int) -> dict:
    list_parents: Sequence[ElementMemberEntry] = ()
    full_data: Sequence[Element] = ()
    list_elements: Sequence[ElementMemberEntry] = ()

    if element.visible:

        async def parents_task():
            nonlocal list_parents
            parents = await ElementRepository.get_many_parents_by_refs(
                (element.element_ref,),
                at_sequence_id=at_sequence_id,
                limit=None,
            )
            list_parents = format_element_parents_list(element.element_ref, parents)

        async def data_task():
            nonlocal full_data, list_elements
            with options_context(joinedload(Element.changeset).load_only(Changeset.user_id)):
                members_element_refs = frozenset(member.element_ref for member in element.members)
                members_elements = await ElementRepository.get_many_by_refs(
                    members_element_refs,
                    at_sequence_id=at_sequence_id,
                    recurse_ways=True,
                    limit=None,
                )
            direct_members = tuple(member for member in members_elements if member.element_ref in members_element_refs)
            full_data = (element, *members_elements)
            list_elements = format_element_members_list(element.members, direct_members)

        async with create_task_group() as tg:
            tg.start_soon(parents_task)
            if element.members:
                tg.start_soon(data_task)
            else:
                full_data = (element,)

    changeset_tags_ = element.changeset.tags
    if 'comment' in changeset_tags_:
        changeset_tags = tags_format(changeset_tags_)
        comment_tag = changeset_tags['comment']
    else:
        comment_tag = TagFormatCollection('comment', t('browse.no_comment'))

    prev_version = element.version - 1 if element.version > 1 else None
    next_version = element.version + 1 if (element.next_sequence_id is not None) else None
    name = feature_name(element.tags)
    tags = tags_format(element.tags)

    return {
        'element': element,
        'prev_version': prev_version,
        'next_version': next_version,
        'name': name,
        'tags': tags.values(),
        'comment_tag': comment_tag,
        'show_elements': bool(list_elements),
        'show_part_of': bool(list_parents),
        'params': JSON_ENCODE(
            {
                'type': element.type,
                'id': element.id,
                'version': element.version,
                'full_data': Format07.encode_elements(full_data),
                'lists': {
                    'part_of': list_parents,
                    'elements': list_elements,
                },
            }
        ).decode(),
    }


@router.get('/{type}/{id:int}')
async def get_latest(type: ElementType, id: PositiveInt):
    at_sequence_id = await ElementRepository.get_current_sequence_id()

    with options_context(joinedload(Element.changeset)):
        ref = ElementRef(type, id)
        elements = await ElementRepository.get_many_by_refs(
            (ref,),
            at_sequence_id=at_sequence_id,
            limit=1,
        )
        element = elements[0] if elements else None

    if element is None:
        return render_response(
            'partial/not_found.jinja2',
            {'type': type, 'id': id},
        )

    # return error if element is no longer latest (small chance race condition)
    if element.next_sequence_id is not None:
        return Response(None, status.HTTP_503_SERVICE_UNAVAILABLE)

    data = await _get_element_data(element, at_sequence_id)
    return render_response('partial/element.jinja2', data)


@router.get('/{type}/{id:int}/history/{version:int}')
async def get_versioned(type: ElementType, id: PositiveInt, version: PositiveInt):
    at_sequence_id = await ElementRepository.get_current_sequence_id()

    with options_context(joinedload(Element.changeset)):
        ref = VersionedElementRef(type, id, version)
        elements = await ElementRepository.get_many_by_versioned_refs((ref,), limit=1)
        element = elements[0] if elements else None

    if element is None:
        id_text = f'{id} {t("browse.version").lower()} {version}'
        return render_response(
            'partial/not_found.jinja2',
            {'type': type, 'id': id_text},
        )

    # if the element was superseded, get data just before
    if element.next_sequence_id is not None:
        at_sequence_id = element.next_sequence_id - 1

    # forward sequence if element was created after (very small chance)
    elif element.sequence_id > at_sequence_id:
        at_sequence_id = element.sequence_id

    data = await _get_element_data(element, at_sequence_id)
    return render_response('partial/element.jinja2', data)


@router.get('/{type}/{id:int}/history')
async def get_history(
    type: ElementType,
    id: PositiveInt,
    page: Annotated[PositiveInt, Query()] = 1,
):
    at_sequence_id = await ElementRepository.get_current_sequence_id()

    ref = ElementRef(type, id)
    current_version = await ElementRepository.get_current_version_by_ref(ref, at_sequence_id=at_sequence_id)

    num_pages = (current_version + ELEMENT_HISTORY_PAGE_SIZE - 1) // ELEMENT_HISTORY_PAGE_SIZE
    from_inclusive = current_version - ELEMENT_HISTORY_PAGE_SIZE * (page - 1)
    to_exclusive = from_inclusive - ELEMENT_HISTORY_PAGE_SIZE

    with options_context(joinedload(Element.changeset)):
        elements = await ElementRepository.get_versions_by_ref(
            ref,
            at_sequence_id=at_sequence_id,
            ascending=False,
            max_version=from_inclusive,
            min_version=to_exclusive - 1,
            limit=ELEMENT_HISTORY_PAGE_SIZE,
        )

    elements_data = [None] * len(elements)

    async with create_task_group() as tg:

        async def data_task(i: int, element: Element):
            at_sequence_id_ = at_sequence_id

            # if the element was superseded, get data just before
            if element.next_sequence_id is not None:
                at_sequence_id_ = element.next_sequence_id - 1

            # forward sequence if element was created after (very small chance)
            elif element.sequence_id > at_sequence_id_:
                at_sequence_id_ = element.sequence_id

            element_data = await _get_element_data(element, at_sequence_id_)
            elements_data[i] = element_data

        for i, element in enumerate(elements):
            tg.start_soon(data_task, i, element)

    return render_response(
        'partial/element_history.jinja2',
        {
            'type': type,
            'id': id,
            'page': page,
            'num_pages': num_pages,
            'elements_data': elements_data,
        },
    )
