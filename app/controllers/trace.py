from typing import Annotated

from fastapi import APIRouter, Response
from pydantic import PositiveInt
from sqlalchemy.orm import joinedload
from starlette import status
from starlette.responses import RedirectResponse

from app.config import API_URL
from app.lib.auth_context import web_user
from app.lib.options_context import options_context
from app.lib.render_response import render_response
from app.models.db.trace_ import Trace
from app.models.db.user import User
from app.repositories.trace_point_repository import TracePointRepository
from app.repositories.trace_repository import TraceRepository
from app.utils import JSON_ENCODE

# TODO: legacy traces url: user profiles
router = APIRouter(prefix='/trace')


@router.get('/upload')
async def upload(_: Annotated[User, web_user()]):
    return render_response('traces/upload.jinja2')


@router.get('/{trace_id:int}')
async def details(trace_id: PositiveInt):
    with options_context(joinedload(Trace.user)):
        trace = await TraceRepository.get_one_by_id(trace_id)
    await TracePointRepository.resolve_image_coords((trace,), limit_per_trace=300, resolution=200)
    image_coords = JSON_ENCODE(trace.image_coords).decode()
    return render_response('traces/details.jinja2', {'trace': trace, 'image_coords': image_coords})


@router.get('/{trace_id:int}/edit')
async def edit(trace_id: PositiveInt, user: Annotated[User, web_user()]):
    with options_context(joinedload(Trace.user)):
        trace = await TraceRepository.get_one_by_id(trace_id)
    if trace.user_id != user.id:
        # TODO: this could be nicer?
        return Response(None, status.HTTP_403_FORBIDDEN)
    await TracePointRepository.resolve_image_coords((trace,), limit_per_trace=300, resolution=200)
    image_coords = JSON_ENCODE(trace.image_coords).decode()
    return render_response('traces/edit.jinja2', {'trace': trace, 'image_coords': image_coords})


@router.get('/{trace_id:int}/data')
async def legacy_data(trace_id: PositiveInt):
    return RedirectResponse(f'{API_URL}/api/0.6/gpx/{trace_id}/data.gpx', status.HTTP_302_FOUND)
