from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typani.option import Option
    from typani.result import Result


# frob:doc docs/result.md#unwraperror
# frob:ticket T-0009
class UnwrapError(AssertionError):
    """Raised by an unwrap/unwrap_err/danger_* access on the wrong variant.

    Subclasses ``AssertionError`` for backward compatibility with existing
    ``pytest.raises(AssertionError)`` expectations, but is always raised
    explicitly -- never via a bare ``assert`` -- so it survives ``python -O``.
    Carries the offending :class:`~typani.result.Result` or
    :class:`~typani.option.Option` in ``container`` so :func:`typani.propagate`
    can recover and return it.
    """

    def __init__(
        self,
        container: "Result[Any, Any] | Option[Any]",
        message: str | None = None,
    ) -> None:
        """Store the offending container and an optional caller-supplied prefix."""
        self.container = container
        self._message = message
        # args carries the constructor inputs (pickling rebuilds from them);
        # the message itself is rendered lazily in __str__ so the failure
        # path never pays for a repr nobody reads.
        super().__init__(container, message)

    def __str__(self) -> str:
        """Render as e.g. ``unwrap() on Err(...)``, prefixed by *message* when given."""
        default = self._default_message()
        if self._message is None:
            return default
        return f"{self._message}: {default}"

    def _default_message(self) -> str:
        """Describe which accessor failed against which container variant."""
        # Local import: avoids a module-level cycle between _exceptions,
        # result, and option.
        from typani.option import Nothing, Some
        from typani.result import Err, Ok

        container = self.container
        if isinstance(container, Ok):
            return f"unwrap_err() on Ok({container.value!r})"
        if isinstance(container, Err):
            return f"unwrap() on Err({container.error!r})"
        if isinstance(container, Some):
            return f"unwrap_err() on Some({container.value!r})"
        if isinstance(container, Nothing):
            return "unwrap() on Nothing"
        return f"unwrap() on {container!r}"
