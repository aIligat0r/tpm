import structlog
from structlog.typing import FilteringBoundLogger


logger: FilteringBoundLogger = structlog.get_logger()
