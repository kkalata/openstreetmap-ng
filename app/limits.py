from datetime import timedelta

_kb = 1024
_mb = 1024 * _kb

AUTH_CREDENTIALS_CACHE_EXPIRE = timedelta(hours=8)

AVATAR_MAX_RATIO = 2
AVATAR_MAX_MEGAPIXELS = 384 * 384  # (resolution)
AVATAR_MAX_FILE_SIZE = 80 * _kb  # 80 KB

# this is in-memory cache configuration
CACHE_DEFAULT_EXPIRE = timedelta(days=3)
CACHE_COMPRESS_MIN_SIZE = 512
CACHE_COMPRESS_ZSTD_LEVEL = 1
CACHE_COMPRESS_ZSTD_THREADS = 0  # disabled

CHANGESET_IDLE_TIMEOUT = timedelta(hours=1)
CHANGESET_OPEN_TIMEOUT = timedelta(days=1)
CHANGESET_EMPTY_DELETE_TIMEOUT = timedelta(hours=1)
CHANGESET_COMMENT_BODY_MAX_LENGTH = 5_000  # NOTE: value TBD
CHANGESET_QUERY_DEFAULT_LIMIT = 100
CHANGESET_QUERY_MAX_LIMIT = 100
CHANGESET_QUERY_WEB_LIMIT = 30
CHANGESET_BBOX_LIMIT = 10
CHANGESET_NEW_BBOX_MIN_DISTANCE = 0.5  # degrees
CHANGESET_NEW_BBOX_MIN_RATIO = 3

COMPRESS_HTTP_MIN_SIZE = 1 * _kb
COMPRESS_HTTP_ZSTD_LEVEL = 3
COMPRESS_HTTP_BROTLI_QUALITY = 3
COMPRESS_HTTP_GZIP_LEVEL = 3

COOKIE_AUTH_MAX_AGE = 365 * 24 * 3600  # 1 year
COOKIE_GENERIC_MAX_AGE = 365 * 24 * 3600  # 1 year

# Q95: 1745, Q99: 3646, Q99.9: 10864, Q100: 636536
DIARY_BODY_MAX_LENGTH = 100_000  # NOTE: value TBD
DIARY_COMMENT_BODY_MAX_LENGTH = 5_000  # NOTE: value TBD

DISPLAY_NAME_MAX_LENGTH = 255

EMAIL_DELIVERABILITY_CACHE_EXPIRE = timedelta(hours=1)
EMAIL_DELIVERABILITY_DNS_TIMEOUT = timedelta(seconds=10)

ELEMENT_HISTORY_PAGE_SIZE = 10
ELEMENT_TAGS_LIMIT = 600
ELEMENT_TAGS_MAX_SIZE = 64 * _kb
ELEMENT_TAGS_KEY_MAX_LENGTH = 63
ELEMENT_WAY_MEMBERS_LIMIT = 2_000
ELEMENT_RELATION_MEMBERS_LIMIT = 32_000

FEATURE_PREFIX_TAGS_LIMIT = 100

FIND_LIMIT = 100

GEO_COORDINATE_PRECISION = 7

GRAVATAR_CACHE_EXPIRE = timedelta(days=1)

ISSUE_COMMENT_BODY_MAX_LENGTH = 5_000  # NOTE: value TBD

LANGUAGE_CODE_MAX_LENGTH = 15

MAIL_PROCESSING_TIMEOUT = timedelta(minutes=1)
MAIL_UNPROCESSED_EXPONENT = 2  # 1 min, 2 mins, 4 mins, etc.
MAIL_UNPROCESSED_EXPIRE = timedelta(days=3)

MAP_QUERY_AREA_MAX_SIZE = 0.25  # in square degrees
MAP_QUERY_LEGACY_NODES_LIMIT = 50_000

MESSAGE_BODY_MAX_LENGTH = 50_000  # NOTE: value TBD

NEARBY_USERS_LIMIT = 30
NEARBY_USERS_RADIUS_METERS = 50_000

NOMINATIM_CACHE_LONG_EXPIRE = timedelta(days=7)
NOMINATIM_CACHE_SHORT_EXPIRE = timedelta(hours=1)
NOMINATIM_HTTP_LONG_TIMEOUT = timedelta(seconds=10)
NOMINATIM_HTTP_SHORT_TIMEOUT = timedelta(seconds=5)

NOTE_COMMENT_BODY_MAX_LENGTH = 2_000
NOTE_FRESHLY_CLOSED_TIMEOUT = timedelta(days=7)
NOTE_QUERY_AREA_MAX_SIZE = 25  # in square degrees
NOTE_QUERY_DEFAULT_LIMIT = 100
NOTE_QUERY_DEFAULT_CLOSED = 7  # open + max 7 days closed
NOTE_QUERY_WEB_LIMIT = 200
NOTE_QUERY_LEGACY_MAX_LIMIT = 10_000

OAUTH_APP_NAME_MAX_LENGTH = 50  # TODO:
OAUTH_APP_URI_MAX_LENGTH = 1000  # TODO:
OAUTH2_APP_USER_LIMIT = 100
OAUTH2_SILENT_AUTH_QUERY_SESSION_LIMIT = 10

OPTIMISTIC_DIFF_RETRY_TIMEOUT = timedelta(seconds=30)

OVERPASS_CACHE_EXPIRE = timedelta(hours=1)

# TODO: check pwned passwords
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 255  # TODO:

REPORT_BODY_MAX_LENGTH = 50_000  # NOTE: value TBD

RICH_TEXT_CACHE_EXPIRE = timedelta(hours=8)

S3_CACHE_EXPIRE = timedelta(days=1)

SEARCH_LOCAL_AREA_LIMIT = 100  # in square degrees
SEARCH_LOCAL_MAX_ITERATIONS = 7
SEARCH_LOCAL_RATIO = 0.5  # [0 - 1], smaller is prefer more local
SEARCH_QUERY_MAX_LENGTH = 255
SEARCH_RESULTS_LIMIT = 100  # nominatim has hard-coded upper limit of 50

TRACE_TAG_MAX_LENGTH = 40
TRACE_TAGS_LIMIT = 10

TRACE_FILE_UPLOAD_MAX_SIZE = 50 * _mb
TRACE_FILE_UNCOMPRESSED_MAX_SIZE = 80 * _mb
TRACE_FILE_ARCHIVE_MAX_FILES = 10
TRACE_FILE_MAX_LAYERS = 2
TRACE_FILE_COMPRESS_ZSTD_THREADS = 0  # disabled
# TODO: background trask to recompress files on disk
TRACE_FILE_COMPRESS_ZSTD_LEVEL = 1

TRACE_POINT_QUERY_AREA_MAX_SIZE = 0.25  # in square degrees
TRACE_POINT_QUERY_DEFAULT_LIMIT = 5_000
TRACE_POINT_QUERY_MAX_LIMIT = 5_000
TRACE_POINT_QUERY_LEGACY_MAX_SKIP = 45_000
TRACE_POINT_QUERY_CURSOR_EXPIRE = timedelta(hours=1)

TRACE_SEGMENT_MAX_AREA = 0.003**2  # in square degrees
TRACE_SEGMENT_MAX_AREA_LENGTH = 0.01  # in degrees
TRACE_SEGMENT_MAX_SIZE = 100

URLSAFE_BLACKLIST = '/;.,?%#'

USER_BLOCK_BODY_MAX_LENGTH = 50_000  # NOTE: value TBD
USER_LANGUAGES_LIMIT = 10
USER_DESCRIPTION_MAX_LENGTH = 100_000  # NOTE: value TBD

USER_NEW_DAYS = 21
USER_PENDING_EXPIRE = timedelta(days=365)  # 1 year
USER_RECENT_ACTIVITY_ENTRIES = 6
USER_SCHEDULED_DELETE_DELAY = timedelta(days=7)

USER_PREF_BULK_SET_LIMIT = 150

USER_TOKEN_ACCOUNT_CONFIRM_EXPIRE = timedelta(days=30)  # TODO: delete unconfirmed accounts
USER_TOKEN_EMAIL_CHANGE_EXPIRE = timedelta(days=1)
USER_TOKEN_EMAIL_REPLY_EXPIRE = timedelta(days=2 * 365)  # 2 years
USER_TOKEN_SESSION_EXPIRE = timedelta(days=365)  # 1 year  # TODO:

XML_PARSE_MAX_SIZE = 50 * _mb  # the same as CGImap

REQUEST_BODY_MAX_SIZE = max(TRACE_FILE_UPLOAD_MAX_SIZE, XML_PARSE_MAX_SIZE) + 5 * _mb  # MAX + 5 MB
REQUEST_PATH_QUERY_MAX_LENGTH = 2 * _kb
