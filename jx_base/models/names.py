# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
# RESURRECTED FROM 4959d0c:vendor/jx_base/models/namespace.py (2024-06-13, "more use namespace")
# THE RENAME-MAP NAMESPACE: MANAGES SHADOWING OF VARIABLES AND CHANGING PERSPECTIVE.
# DEVIATIONS FROM THE ORIGINAL:
# - BINDINGS ARE A CHAIN OF Scopes (NEAREST FIRST) INSTEAD OF ONE FLAT DICT, SO SHADOWING IS
#   SCOPE-GRANULAR: leaves() TAKES ALL ITS ANSWERS FROM THE FIRST SCOPE THAT HAS ANY - THIS
#   MATCHES Schema.leaves() SEARCH-ORDER SEMANTICS (RELATIVE NAME SHADOWS ABSOLUTE)
# - VALUES ARE OPAQUE TUPLES (TYPICALLY Columns; ONE NAME MAY BIND SEVERAL TYPED COLUMNS),
#   NOT PATHS RESOLVED THROUGH container.namespace
# - EACH SCOPE CARRIES aliases: EXACT-MATCH-ONLY NAMES (TYPED/PHYSICAL, eg a.$N) THAT ARE
#   NEVER ENUMERATED BY leaves() - REQUIRED BECAUSE startswith_field("a.$N", "a") IS True
import re
from typing import Any, Dict, List, Tuple

from mo_dots import concat_field, relative_field, startswith_field, tail_field

AMBIGUOUS = object()
FREE_VAR_PREFIX = "__$"
is_free_var = re.compile(r"^" + re.escape(FREE_VAR_PREFIX) + r"\d+$")


class Scope:
    """
    BINDINGS VISIBLE FROM ONE VANTAGE POINT (ONE TABLE OF A SNOWFLAKE, ONE stack() OVERLAY)

    names   - ENUMERABLE: JX (UNTYPED) NAMES -> TUPLE OF VALUES
    aliases - EXACT LOOKUP ONLY: PHYSICAL (TYPED) NAMES -> TUPLE OF VALUES
    """

    __slots__ = ["names", "aliases"]

    def __init__(self, names: Dict[str, Tuple] = None, aliases: Dict[str, Tuple] = None):
        self.names = names or {}
        self.aliases = aliases or {}


class Names:
    """
    A NAMESPACE: MAP FROM VISIBLE NAMES TO COLUMNS (OR OTHER VALUES), AS SEEN FROM ONE
    PERSPECTIVE.  CHANGING PERSPECTIVE = HOLDING A DIFFERENT Names.  A NAME BINDS AT THE
    FIRST (NEAREST) SCOPE THAT KNOWS IT; NEARER SCOPES SHADOW FARTHER ONES.
    """

    def __init__(self, scopes: List[Scope], free_vars=()):
        self.scopes = list(scopes)  # NEAREST SCOPE FIRST
        self.free_vars = list(free_vars)  # VARIABLES USED FOR ITERATION

    def _deref(self, value: Any) -> Any:
        # FREE VARIABLES ARE PLACEHOLDER PATHS; SUBSTITUTE THE REAL PATH AT LOOKUP TIME
        if isinstance(value, str):
            head, rest = tail_field(value)
            if is_free_var.match(head):
                return concat_field(self.free_vars[int(head[len(FREE_VAR_PREFIX):])], rest)
        return value

    def resolve(self, name: str):
        """
        RETURN TUPLE OF VALUES BOUND TO name, AMBIGUOUS, OR None
        """
        for scope in self.scopes:
            found = scope.names.get(name)
            if found is None:
                found = scope.aliases.get(name)
            if found is AMBIGUOUS:
                return AMBIGUOUS
            if found is not None:
                return tuple(self._deref(v) for v in found)
        return None

    def leaves(self, prefix: str) -> List[Tuple[str, Any]]:
        """
        ALL LEAF BINDINGS UNDER prefix: (relative_name, value) PAIRS
        SHADOWING IS SCOPE-GRANULAR: THE FIRST SCOPE WITH ANY MATCH SUPPLIES THEM ALL
        """
        for scope in self.scopes:
            output = [
                (relative_field(name, prefix), self._deref(v))
                for name, values in scope.names.items()
                if values is not AMBIGUOUS and startswith_field(name, prefix)
                for v in values
            ]
            if output:
                return output
            exact = scope.aliases.get(prefix)
            if exact is not None and exact is not AMBIGUOUS:
                return [(".", self._deref(v)) for v in exact]
        return []

    def _flat(self) -> Dict[str, Tuple]:
        # ALL VISIBLE (ENUMERABLE) BINDINGS, NEARER SCOPES SHADOWING FARTHER
        output = {}
        for scope in reversed(self.scopes):
            output.update(scope.names)
        return output

    def _rename(self, renames: Dict[str, str]) -> Dict[str, Tuple]:
        # REBIND EXISTING SUBTREES UNDER NEW NAMES; renames MAPS new_name -> old_name
        return {
            concat_field(new_name, relative_field(name, old_name)): values
            for name, values in self._flat().items()
            for new_name, old_name in renames.items()
            if startswith_field(name, old_name)
        }

    def stack(self, **renames) -> "Names":
        # PUSH A SCOPE; NEW BINDINGS SHADOW OLD
        return Names([Scope(self._rename(renames)), *self.scopes], self.free_vars)

    def union(self, **renames) -> "Names":
        # MERGE NEW BINDINGS AT EQUAL PRECEDENCE; COLLISIONS BECOME AMBIGUOUS
        rename = self._rename(renames)
        ambiguous = {name: AMBIGUOUS for name in rename.keys() & self._flat().keys()}
        return Names([Scope({**rename, **ambiguous}), *self.scopes], self.free_vars)

    def add_free_var(self, name: str) -> Tuple[str, "Names"]:
        # MINT AN ITERATION VARIABLE BOUND TO name (eg THE ARRAY BEING ITERATED)
        var_name = f"{FREE_VAR_PREFIX}{len(self.free_vars)}"
        return var_name, Names([Scope({var_name: (var_name,)}), *self.scopes], [*self.free_vars, name])
