from datetime import timedelta
from typing import Annotated
from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, HTTPException, Path, Request, status
from starlette.responses import RedirectResponse

from app.config import APP_URL
from app.lib.shortlink import shortlink_decode
from app.middlewares.cache_control_middleware import cache_control

router = APIRouter()


@router.get('/go/{code}')
@cache_control(max_age=timedelta(days=30), stale=timedelta(days=30))
async def go(
    request: Request,
    code: Annotated[str, Path(min_length=3, max_length=15)],
) -> RedirectResponse:
    """
    Redirect to a map from a shortlink code.
    """

    try:
        lon, lat, z = shortlink_decode(code)
    except Exception as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from e

    query = parse_qs(request.url.query, strict_parsing=True)
    query['map'] = [f'{z}/{lat:.5f}/{lon:.5f}']
    fragment = '#' + urlencode(query, doseq=True)
    redirect_url = APP_URL + fragment

    return RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
