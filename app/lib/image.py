import logging
from asyncio import get_running_loop
from enum import Enum
from functools import partial
from io import BytesIO
from pathlib import Path
from typing import Literal, overload

import cython
import PIL.Image
from PIL import ImageOps

from app.lib.exceptions_context import raise_for
from app.lib.naturalsize import naturalsize
from app.limits import (
    AVATAR_MAX_FILE_SIZE,
    AVATAR_MAX_MEGAPIXELS,
    AVATAR_MAX_RATIO,
    BACKGROUND_MAX_FILE_SIZE,
    BACKGROUND_MAX_MEGAPIXELS,
    BACKGROUND_MAX_RATIO,
)
from app.models.types import StorageKey

if cython.compiled:
    from cython.cimports.libc.math import sqrt
else:
    from math import sqrt

# Support up to 256MP images
# TODO: handle errors
PIL.Image.MAX_IMAGE_PIXELS = 2 * int(1024 * 1024 * 1024 // 4 // 3)


class AvatarType(str, Enum):
    default = 'default'
    gravatar = 'gravatar'
    custom = 'custom'


class Image:
    default_avatar: bytes = Path('app/static/img/avatar.webp').read_bytes()

    @overload
    @staticmethod
    def get_avatar_url(image_type: Literal[AvatarType.default]) -> str: ...

    @overload
    @staticmethod
    def get_avatar_url(image_type: Literal[AvatarType.gravatar], image_id: int) -> str: ...

    @overload
    @staticmethod
    def get_avatar_url(image_type: Literal[AvatarType.custom], image_id: StorageKey) -> str: ...

    @staticmethod
    def get_avatar_url(image_type: AvatarType, image_id: int | StorageKey = 0) -> str:
        """
        Get the url of the avatar image.

        >>> Image.get_avatar_url(AvatarType.custom, '123456')
        '/api/web/avatar/123456'
        """
        if image_type == AvatarType.default:
            return '/static/img/avatar.webp'
        elif image_type == AvatarType.gravatar:
            return f'/api/web/gravatar/{image_id}'
        elif image_type == AvatarType.custom:
            return f'/api/web/avatar/{image_id}'
        else:
            raise NotImplementedError(f'Unsupported avatar type {image_type!r}')

    @staticmethod
    async def normalize_avatar(data: bytes) -> bytes:
        """
        Normalize the avatar image.
        """
        return await _normalize_image(
            data,
            min_ratio=1 / AVATAR_MAX_RATIO,
            max_ratio=AVATAR_MAX_RATIO,
            max_megapixels=AVATAR_MAX_MEGAPIXELS,
            max_file_size=AVATAR_MAX_FILE_SIZE,
        )

    @staticmethod
    def get_background_url(image_id: StorageKey | None) -> str | None:
        """
        Get the url of the background image.

        >>> Image.get_background_url('123456')
        '/api/web/background/123456'
        """
        if image_id is not None:
            return f'/api/web/background/{image_id}'
        else:
            return None

    @staticmethod
    async def normalize_background(data: bytes) -> bytes:
        """
        Normalize the background image.
        """
        return await _normalize_image(
            data,
            min_ratio=1 / BACKGROUND_MAX_RATIO,
            max_ratio=BACKGROUND_MAX_RATIO,
            max_megapixels=BACKGROUND_MAX_MEGAPIXELS,
            max_file_size=BACKGROUND_MAX_FILE_SIZE,
        )


async def _normalize_image(
    data: bytes,
    *,
    min_ratio: cython.double,
    max_ratio: cython.double,
    max_megapixels: cython.int,
    max_file_size: cython.int,
) -> bytes:
    """
    Normalize the avatar image.

    - Orientation: rotate
    - Shape ratio: crop
    - Megapixels: downscale
    - File size: reduce quality
    """
    img: PIL.Image.Image = PIL.Image.open(BytesIO(data))

    # normalize orientation
    ImageOps.exif_transpose(img, in_place=True)

    # normalize shape ratio
    img_width: cython.int = img.width
    img_height: cython.int = img.height
    ratio: cython.double = img_width / img_height

    # image is too wide
    if max_ratio and ratio > max_ratio:
        logging.debug('Image is too wide %dx%d', img_width, img_height)
        new_width: cython.int = int(img_height * max_ratio)
        x1: cython.int = (img_width - new_width) // 2
        x2: cython.int = (img_width + new_width) // 2
        img = img.crop((x1, 0, x2, img_height))
        img_width = img.width

    # image is too tall
    elif min_ratio and ratio < min_ratio:
        logging.debug('Image is too tall %dx%d', img_width, img_height)
        new_height: cython.int = int(img_width / min_ratio)
        y1: cython.int = (img_height - new_height) // 2
        y2: cython.int = (img_height + new_height) // 2
        img = img.crop((0, y1, img_width, y2))
        img_height = img.height

    # normalize megapixels
    if max_megapixels:
        mp_ratio: cython.double = (img_width * img_height) / max_megapixels
        if mp_ratio > 1:
            logging.debug('Image is too big %dx%d', img_width, img_height)
            mp_ratio = sqrt(mp_ratio)
            img_width = int(img_width / mp_ratio)
            img_height = int(img_height / mp_ratio)
            img.thumbnail((img_width, img_height))

    # optimize file size
    quality, buffer = await _optimize_quality(img, max_file_size)
    logging.debug('Optimized avatar quality: Q%d', quality)
    return buffer


async def _optimize_quality(img: PIL.Image.Image, max_file_size: int | None) -> tuple[int, bytes]:
    """
    Find the best image quality given the maximum file size.

    Returns the quality and the image buffer.
    """
    lossless_effort: int = 80
    loop = get_running_loop()

    with BytesIO() as buffer:
        await loop.run_in_executor(
            None,
            partial(
                img.save,
                buffer,
                format='WEBP',
                lossless=True,
                quality=lossless_effort,
            ),
        )
        size = buffer.tell()
        logging.debug('Optimizing avatar quality (lossless): Q%d -> %s', lossless_effort, naturalsize(size))

        if max_file_size is None or size <= max_file_size:
            return lossless_effort, buffer.getvalue()

        high: cython.int = 90
        low: cython.int = 20
        bs_step: cython.int = 5
        best_quality: cython.int = -1
        best_buffer: bytes | None = None

        # initial quick scan
        quality: cython.int
        for quality in range(80, 20 - 1, -20):
            buffer.seek(0)
            buffer.truncate()

            await loop.run_in_executor(
                None,
                partial(
                    img.save,
                    buffer,
                    format='WEBP',
                    quality=quality,
                ),
            )
            size = buffer.tell()
            logging.debug('Optimizing avatar quality (quick): Q%d -> %s', quality, naturalsize(size))

            if size > max_file_size:
                high = quality - bs_step
            else:
                low = quality + bs_step
                best_quality = quality
                best_buffer = buffer.getvalue()
                break
        else:
            raise_for().image_too_big()

        # fine-tune with binary search
        while low <= high:
            # round down to the nearest bs_step
            quality = ((low + high) // 2) // bs_step * bs_step
            buffer.seek(0)
            buffer.truncate()

            await loop.run_in_executor(
                None,
                partial(
                    img.save,
                    buffer,
                    format='WEBP',
                    quality=quality,
                ),
            )
            size = buffer.tell()
            logging.debug('Optimizing avatar quality (fine): Q%d -> %s', quality, naturalsize(size))

            if size > max_file_size:
                high = quality - bs_step
            else:
                low = quality + bs_step
                best_quality = quality
                best_buffer = buffer.getvalue()

        return best_quality, best_buffer
