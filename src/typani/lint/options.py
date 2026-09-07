"""The resolved settings one lint run needs, and the one place their defaults live.

Split out of ``__main__`` so both entry points -- ``python -m typani.lint``
and the ``typani lint`` console script, whose AppConfig layers a config
file and environment variables underneath the same flags -- resolve into
one dataclass instead of each carrying its own copy of the defaults.

Stdlib-only, like the rest of ``typani.lint``: this module must never
import typani proper (see design/typani.strata's lint isolation
constraint), so it validates nothing and returns no ``Result`` -- the
fallible layering lives in ``typani.app.config``, where those types exist.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Mapping

# frob:doc docs/lint.md#lintoptions
# frob:tests tests/test_cli.py::test_from_mapping_ignores_unknown_and_none_values
# frob:ticket T-0037
#: Flag names `add_lint_arguments` defines, i.e. exactly the keys
#: `LintOptions.from_mapping` understands. Named explicitly so a flag added
#: to the parser without a matching field fails loudly here rather than
#: being silently dropped on the way through AppConfig.
OPTION_NAMES = frozenset({"paths", "json", "exclude", "select", "ignore", "no_info"})


# frob:doc docs/lint.md#lintoptions
# frob:tests tests/test_cli.py::test_from_external_defaults_when_nothing_is_set
# frob:ticket T-0037
#: The default scan root. A module constant rather than a read of the
#: dataclass field: `slots=True` replaces class attributes with slot
#: descriptors, so `cls.paths` is not the default value.
DEFAULT_PATHS: tuple[str, ...] = (".",)


# frob:doc docs/lint.md#lintoptions
# frob:tests tests/test_cli.py::test_from_mapping_ignores_unknown_and_none_values
# frob:ticket T-0037
@dataclass(frozen=True, slots=True)
class LintOptions:
    """One lint run's resolved settings: what to scan, what to keep, how to print."""

    paths: tuple[str, ...] = DEFAULT_PATHS
    json: bool = False
    exclude: tuple[str, ...] = ()
    select: tuple[str, ...] = ()
    ignore: tuple[str, ...] = ()
    no_info: bool = False

    # frob:doc docs/lint.md#lintoptions
    # frob:tests tests/test_cli.py::test_from_mapping_ignores_unknown_and_none_values
    # frob:ticket T-0037
    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> LintOptions:
        """Build options from an already-merged mapping; unknown keys are ignored.

        Keys absent from `values` (or mapped to None, argparse's "flag not
        given" marker) fall back to this class's field defaults, which is
        what makes the CLI > env > file > default layering work: each layer
        contributes only the keys it actually set.
        """
        known = {k: v for k, v in values.items() if k in OPTION_NAMES and v is not None}
        return cls(
            paths=_as_tuple(known.get("paths"), DEFAULT_PATHS) or DEFAULT_PATHS,
            json=bool(known.get("json", False)),
            exclude=_as_tuple(known.get("exclude"), ()),
            select=_as_tuple(known.get("select"), ()),
            ignore=_as_tuple(known.get("ignore"), ()),
            no_info=bool(known.get("no_info", False)),
        )


def _as_tuple(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    """Normalize a str / sequence-of-str / missing value into a tuple of strings."""
    if value is None:
        return default
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return default


# frob:doc docs/lint.md#lintoptions
# frob:tests tests/test_cli.py::test_from_external_defaults_when_nothing_is_set
# frob:ticket T-0037
def namespace_to_mapping(args: argparse.Namespace) -> dict[str, object]:
    """Extract only the lint flags a user actually passed from a parsed namespace."""
    values: dict[str, object] = {}
    for name in OPTION_NAMES:
        # frob:waive OPAQUE001 reason="name comes from this module's own fixed set"
        value = getattr(args, name, None)
        # An `nargs="*"` positional the user omitted arrives as `[]`, not None.
        # Treating that as "set to nothing" would clobber the env and file
        # layers underneath it, so it counts as unset like every other default.
        if value is None or (isinstance(value, (list, tuple)) and not value):
            continue
        values[name] = value
    return values
