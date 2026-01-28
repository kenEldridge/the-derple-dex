"""Example custom source.

Rename this file (remove the _ prefix) and implement your source.
It will be auto-discovered by cdata on next run.
"""

from typing import Any
from datetime import datetime

from cdata.sources.base import BaseSource
from cdata.models import FetchResult


class ExampleSource(BaseSource):
    source_type = "example"

    def fetch(self, **kwargs: Any) -> FetchResult:
        started_at = datetime.utcnow()
        records = []
        # Your fetch logic here — use self._create_record(data={...})
        return self._create_result(records, started_at)

    def test_connection(self) -> bool:
        return True
