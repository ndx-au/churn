"""Example driver implementation stub (post-cookiecutter fill-in)."""

from churn.drivers.base import FetchedContent, SourceDriver, SourceItem
from typing import Any


class MyFooDriver(SourceDriver):
    name = "myfoo"
    description = "Example driver for {{ cookiecutter.description }}"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)

    def list_items(self, query: str | None = None, **kwargs: Any) -> list[SourceItem]:
        # TODO: discover items
        return [SourceItem(id="example", path_or_uri="example://item")]

    def fetch_item(self, item: SourceItem) -> FetchedContent:
        # TODO
        return FetchedContent(item=item, content=b"# example\n\nStub content.", mime="text/markdown")
