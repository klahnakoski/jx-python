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


class ResolvedName:
    """
    ONE LEAF BINDING.  UNPACKS AS THE LEGACY (relative_name, value) PAIR, AND CARRIES THE
    TWO-KIND SPLIT OF THE NAME RELATIVE TO THE QUERIED PREFIX - JX NAMES ARE UNIFORM
    PROPERTY CHAINS, SO WHERE THE RELATION STOPS AND THE VALUE BEGINS IS NOT EXPRESSIBLE
    IN THE NAME ITSELF (docs/NAMES.md):

    push_name  - THE OUTPUT COLUMN THIS BINDING LANDS UNDER; "." MEANS THE QUERIED NAME
                 ITSELF IS A VALUE (AN ARRAY, OR AN ELEMENT OF ONE) AND THE BINDING
                 COLLAPSES UNDER IT
    push_child - PATH TO THIS BINDING INSIDE THAT VALUE ("." = THE VALUE ITSELF)
    """

    __slots__ = ["name", "value", "push_name", "push_child"]

    def __init__(self, name, value, push_name=".", push_child="."):
        self.name = name
        self.value = value
        self.push_name = push_name
        self.push_child = push_child

    def __iter__(self):
        # LEGACY (relative_name, value) UNPACKING
        return iter((self.name, self.value))

    def __getitem__(self, index):
        return (self.name, self.value)[index]

    def __eq__(self, other):
        try:
            n, v = other
        except Exception:
            return False
        return self.name == n and (self.value is v or self.value == v)

    def __repr__(self):
        return f"ResolvedName({self.name!r}, {self.value!r}, push_name={self.push_name!r}, push_child={self.push_child!r})"


def _push_split(prefix: str, rel_name: str, boundary: str, root_is_array: bool) -> Tuple[str, str]:
    """
    THE TWO-KIND SPLIT OF ONE BINDING'S NAME, RELATIVE TO THE QUERIED prefix.
    boundary IS THE PATH (RELATIVE TO THE SCOPE ROOT) OF THE ARRAY HOLDING THE VALUE;
    "." MEANS THE VALUE LIVES IN THE SCOPE'S OWN TABLE.
    """
    if boundary == ".":
        if root_is_array:
            # QUERIED NAME IS (INSIDE) AN ARRAY ELEMENT: COLLAPSE UNDER IT
            return ".", rel_name
        # PLAIN TUPLE LEAF: EACH LEAF ITS OWN COLUMN
        return rel_name, "."
    if root_is_array or startswith_field(prefix, boundary):
        # QUERIED NAME IS AT OR INSIDE THE ARRAY: COLLAPSE UNDER IT
        return ".", rel_name
    # ARRAY STRICTLY BELOW THE QUERIED NAME: SPREAD TO THE ARRAY; THE REST IS INSIDE ITS VALUE
    name = concat_field(prefix, rel_name)
    return relative_field(boundary, prefix), relative_field(name, boundary)


class Scope:
    """
    BINDINGS VISIBLE FROM ONE VANTAGE POINT (ONE TABLE OF A SNOWFLAKE, ONE stack() OVERLAY)

    names         - ENUMERABLE: JX (UNTYPED) NAMES -> TUPLE OF VALUES
    aliases       - EXACT LOOKUP ONLY: PHYSICAL (TYPED) NAMES -> TUPLE OF VALUES
    root_is_array - THE SCOPE'S OWN TABLE IS AN ARRAY (ITS ROWS ARE ELEMENTS, NOT FACTS)
    boundaries    - PER NAME: TUPLE (ALIGNED WITH names[name]) OF THE ARRAY PATH HOLDING
                    EACH VALUE, RELATIVE TO THE SCOPE ROOT ("." = THE SCOPE'S OWN TABLE)
    """

    __slots__ = ["names", "aliases", "root_is_array", "boundaries"]

    def __init__(
        self,
        names: Dict[str, Tuple] = None,
        aliases: Dict[str, Tuple] = None,
        root_is_array: bool = False,
        boundaries: Dict[str, Tuple] = None,
    ):
        self.names = names or {}
        self.aliases = aliases or {}
        self.root_is_array = root_is_array
        self.boundaries = boundaries or {}

    def _boundary(self, name: str, index: int) -> str:
        found = self.boundaries.get(name)
        if found is None:
            return "."
        return found[index]


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

    def leaves(self, prefix: str) -> List[ResolvedName]:
        """
        ALL LEAF BINDINGS UNDER prefix, EACH WITH ITS PUSH-NAME SPLIT (ResolvedName
        UNPACKS AS THE LEGACY (relative_name, value) PAIR)
        SHADOWING IS SCOPE-GRANULAR: THE FIRST SCOPE WITH ANY MATCH SUPPLIES THEM ALL
        """
        for scope in self.scopes:
            output = [
                ResolvedName(
                    rel_name,
                    self._deref(v),
                    *_push_split(prefix, rel_name, scope._boundary(name, i), scope.root_is_array),
                )
                for name, values in scope.names.items()
                if values is not AMBIGUOUS and startswith_field(name, prefix)
                for rel_name in [relative_field(name, prefix)]
                for i, v in enumerate(values)
            ]
            if output:
                return output
            exact = scope.aliases.get(prefix)
            if exact is not None and exact is not AMBIGUOUS:
                return [ResolvedName(".", self._deref(v)) for v in exact]
        return []

    def all_leaves(self, prefix: str) -> List[ResolvedName]:
        """
        DOCUMENT-ASSEMBLY ENUMERATION (select *): UNION OF LEAF BINDINGS UNDER prefix ACROSS
        ALL SCOPES, NEAREST FIRST.  A FARTHER SCOPE'S BINDING IS SKIPPED WHEN A NEARER SCOPE
        ALREADY BOUND THE SAME VALUE (SAME COLUMN SEEN UNDER ANOTHER NAME) OR THE SAME NAME
        (SHADOWING).  CONTRAST leaves(): FIRST SCOPE WITH ANY MATCH SUPPLIES THEM ALL.
        """
        output = []
        seen_values = set()
        seen_names = set()
        for scope in self.scopes:
            for name, values in scope.names.items():
                if values is AMBIGUOUS or not startswith_field(name, prefix):
                    continue
                rel_name = relative_field(name, prefix)
                if rel_name in seen_names:
                    continue
                seen_names.add(rel_name)
                for i, v in enumerate(values):
                    if id(v) in seen_values:
                        continue
                    seen_values.add(id(v))
                    output.append(ResolvedName(
                        rel_name,
                        self._deref(v),
                        *_push_split(prefix, rel_name, scope._boundary(name, i), scope.root_is_array),
                    ))
        return output

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
