"""Named cut registry for reusable WHERE clause aliases."""

import re


class CutRegistry:
    """Stores named cuts as raw expression strings."""

    def __init__(self):
        self._cuts: dict[str, str] = {}

    def define(self, name: str, expression: str) -> None:
        self._cuts[name] = expression

    def remove(self, name: str) -> None:
        del self._cuts[name]

    def list_all(self) -> dict[str, str]:
        return dict(self._cuts)

    def resolve(self, text: str) -> str:
        """Replace $name references with parenthesized expressions.

        Raises ValueError for undefined references.
        """
        def replacer(match):
            name = match.group(1)
            if name not in self._cuts:
                raise ValueError(f"Undefined cut: ${name}")
            return f"({self._cuts[name]})"

        return re.sub(r'\$([a-zA-Z_]\w*)', replacer, text)
