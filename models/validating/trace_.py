from collections.abc import Sequence
from typing import Annotated

from pydantic import PositiveInt

from models.db.base import Base
from models.file_name import FileName
from models.geometry import PointGeometry
from models.str import NonEmptyStr, Str255
from models.trace_visibility import TraceVisibility
from validators.url import URLSafeValidator


class TraceValidating(Base.Validating):
    user_id: PositiveInt
    name: FileName
    description: Str255
    visibility: TraceVisibility

    size: PositiveInt
    start_point: PointGeometry

    # defaults
    file_id: NonEmptyStr | None = None
    image_id: NonEmptyStr | None = None
    icon_id: NonEmptyStr | None = None
    tags: Sequence[Annotated[Str255, URLSafeValidator]] = ()
