"""ps10 RBAC Role Resolver — reference solution.

RECONSTRUCTED problem (see problem.md's warning block) — Stripe-style account hierarchy
(platform -> connected account -> ... -> user) where a user's *effective* permission at some
account is resolved by walking that account's ancestor chain and combining every role the user
holds along the way. Each part deliberately breaks the previous part's data structure:

  Part 1 - flat lookup, no hierarchy at all (a linear scan is fine).
  Part 2 - hierarchy is introduced: a flat scan can no longer answer "does this user have any
            role *anywhere in the chain*" -- needs an indexed graph walk, with cycle protection.
  Part 3 - wildcards ("ns:*", "*") and explicit denies ("!perm") are introduced. Part 2's
            "resolve to a flat, enumerable permission list" representation stops working -- a
            wildcard cannot be expanded into concrete permissions without knowing the full
            universe of permission strings, so from here on we keep raw grant/deny *patterns* and
            match a single queried permission against them on demand instead of materializing a
            list.
  Part 4 - batch efficiency: resolving many (user, account, permission) queries must not re-walk
            the same account's ancestor chain, nor re-aggregate the same (user, account) pair's
            grants/denies, once per query.
"""

from __future__ import annotations

import sys


# ------------------------------------------------------------------ Part 1: flat, no hierarchy
def part1(
    accounts: list[dict], roles: list[dict], assignments: list[dict], user_id: str, account_id: str
) -> list[str]:
    """Happy path, no hierarchy: the permissions of the role (if any) the user is DIRECTLY
    assigned at account_id itself. No inheritance, no validation -- assume well-formed input."""
    roles_by_id = {r["role_id"]: r for r in roles}
    for a in assignments:
        if a["user_id"] == user_id and a["account_id"] == account_id:
            return sorted(roles_by_id[a["role_id"]]["permissions"])
    return []


# ------------------------------------------------------------------ shared indexing (Part 2+)
def _index(accounts: list[dict], roles: list[dict], assignments: list[dict]):
    """Build lookup structures and validate structural integrity. Raises ValueError on: a
    duplicate account_id or role_id, an assignment referencing an unknown account or role, or two
    assignments for the same (user_id, account_id) pair (ambiguous -- which role applies?)."""
    accounts_by_id: dict[str, dict] = {}
    for acc in accounts:
        aid = acc["account_id"]
        if aid in accounts_by_id:
            raise ValueError(f"duplicate account_id: {aid!r}")
        accounts_by_id[aid] = acc

    roles_by_id: dict[str, dict] = {}
    for role in roles:
        rid = role["role_id"]
        if rid in roles_by_id:
            raise ValueError(f"duplicate role_id: {rid!r}")
        roles_by_id[rid] = role

    assignment_by_user_account: dict[tuple[str, str], str] = {}
    for a in assignments:
        key = (a["user_id"], a["account_id"])
        if key in assignment_by_user_account:
            raise ValueError(f"duplicate assignment for user {a['user_id']!r} at account {a['account_id']!r}")
        if a["account_id"] not in accounts_by_id:
            raise ValueError(f"assignment references unknown account: {a['account_id']!r}")
        if a["role_id"] not in roles_by_id:
            raise ValueError(f"assignment references unknown role: {a['role_id']!r}")
        assignment_by_user_account[key] = a["role_id"]

    return accounts_by_id, roles_by_id, assignment_by_user_account


def _ancestor_chain(
    accounts_by_id: dict[str, dict], account_id: str, cache: dict[str, list[str]]
) -> list[str]:
    """Root-first list of account ids from the topmost ancestor down to account_id (inclusive).
    Memoized in `cache` (shared across a whole batch in Part 4, fresh per call in Parts 2-3), so
    an account whose chain was already resolved is O(1) on every later lookup. Raises ValueError
    on an unknown account_id anywhere in the chain, or a parent_id cycle (including a
    self-referencing account_id == parent_id)."""
    if account_id in cache:
        return cache[account_id]
    path: list[str] = []
    visiting: set[str] = set()
    current: str | None = account_id
    while current not in cache:
        if current in visiting:
            raise ValueError(f"cycle detected in account hierarchy at {current!r}")
        if current not in accounts_by_id:
            raise ValueError(f"unknown account: {current!r}")
        visiting.add(current)
        path.append(current)
        parent = accounts_by_id[current].get("parent_id")
        if not parent:
            current = None
            break
        current = parent
    path.reverse()  # was leaf -> ... -> topmost; now topmost -> ... -> leaf
    prefix = cache[current] if current is not None else []
    full = prefix + path
    cache[account_id] = full
    return full


def _grants_denies_for_pair(
    accounts_by_id: dict[str, dict],
    roles_by_id: dict[str, dict],
    assignment_by_user_account: dict[tuple[str, str], str],
    chain_cache: dict[str, list[str]],
    user_id: str,
    account_id: str,
) -> tuple[set[str], set[str]]:
    """Union of grant patterns and deny patterns (the '!' stripped off) from every role the user
    holds anywhere along account_id's ancestor chain. A level where the user has no assignment
    simply contributes nothing (not an error -- most users have a role at only one or two levels
    of a deep chain)."""
    chain = _ancestor_chain(accounts_by_id, account_id, chain_cache)
    grants: set[str] = set()
    denies: set[str] = set()
    for level in chain:
        role_id = assignment_by_user_account.get((user_id, level))
        if role_id is None:
            continue
        for perm in roles_by_id[role_id]["permissions"]:
            if perm.startswith("!"):
                denies.add(perm[1:])
            else:
                grants.add(perm)
    return grants, denies


# ------------------------------------------------------------------ Part 2: hierarchy, no wildcards yet
def part2(
    accounts: list[dict], roles: list[dict], assignments: list[dict], user_id: str, account_id: str
) -> list[str]:
    """Effective permissions at account_id, inheriting (union, not override) every role the user
    holds at any ancestor level, root down to account_id itself. No wildcards/denies expected in
    this part's data -- every permission string in `roles` is a plain, literal permission name."""
    accounts_by_id, roles_by_id, assignment_by_user_account = _index(accounts, roles, assignments)
    grants, _denies = _grants_denies_for_pair(
        accounts_by_id, roles_by_id, assignment_by_user_account, {}, user_id, account_id
    )
    return sorted(grants)


# ------------------------------------------------------------------ Part 3: wildcards + deny-overrides-allow
def _matches(pattern: str, permission: str) -> bool:
    """'*' matches anything. 'ns:*' matches any 'ns:...' permission (but not the bare 'ns' with
    nothing after the colon). Anything else must match `permission` exactly."""
    if pattern == "*" or pattern == permission:
        return True
    if pattern.endswith(":*"):
        prefix = pattern[:-1]  # e.g. 'charges:'
        return permission.startswith(prefix) and len(permission) > len(prefix)
    return False


def _has_permission(grants: set[str], denies: set[str], permission: str) -> bool:
    """Deny-overrides-allow, globally: an explicit deny anywhere in the chain wins over a grant
    from ANY level (including a more specific grant at a closer level) -- this repo's own decided
    rule (see problem.md), not derived from any source."""
    if any(_matches(p, permission) for p in denies):
        return False
    return any(_matches(p, permission) for p in grants)


def part3(
    accounts: list[dict],
    roles: list[dict],
    assignments: list[dict],
    user_id: str,
    account_id: str,
    permission: str,
) -> bool:
    """Does user_id effectively have `permission` at account_id, accounting for wildcard grants
    and explicit ('!'-prefixed) denies anywhere in the ancestor chain? Same chain-walk as Part 2,
    but denies now block grants regardless of which level produced either one, and a wildcard
    pattern can grant a permission it never spells out literally."""
    accounts_by_id, roles_by_id, assignment_by_user_account = _index(accounts, roles, assignments)
    grants, denies = _grants_denies_for_pair(
        accounts_by_id, roles_by_id, assignment_by_user_account, {}, user_id, account_id
    )
    return _has_permission(grants, denies, permission)


# ------------------------------------------------------------------ Part 4: batch efficiency
def part4(
    accounts: list[dict],
    roles: list[dict],
    assignments: list[dict],
    queries: list[tuple[str, str, str]],
) -> list[bool]:
    """queries: (user_id, account_id, permission) tuples, in any order, possibly repeating the
    same (user_id, account_id) pair with different permissions. Returns one bool per query, same
    order as input. Two caches make this sub-quadratic in the number of queries: `chain_cache`
    (ancestor chain per account_id, shared across every user that ever queries that account) and
    `pair_cache` (aggregated grants/denies per (user_id, account_id), shared across every
    permission checked for that same pair) -- neither is rebuilt once it has been computed once
    for the whole batch."""
    accounts_by_id, roles_by_id, assignment_by_user_account = _index(accounts, roles, assignments)
    chain_cache: dict[str, list[str]] = {}
    pair_cache: dict[tuple[str, str], tuple[set[str], set[str]]] = {}
    out: list[bool] = []
    for user_id, account_id, permission in queries:
        key = (user_id, account_id)
        if key not in pair_cache:
            pair_cache[key] = _grants_denies_for_pair(
                accounts_by_id, roles_by_id, assignment_by_user_account, chain_cache, user_id, account_id
            )
        grants, denies = pair_cache[key]
        out.append(_has_permission(grants, denies, permission))
    return out


# ------------------------------------------------------------------ I/O
SECTION_NAMES = ("ACCOUNTS", "ROLES", "ASSIGNMENTS", "QUERY")


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {name: [] for name in SECTION_NAMES}
    current: str | None = None
    for raw in lines:
        if raw.strip() in SECTION_NAMES:
            current = raw.strip()
            continue
        if current is not None:
            sections[current].append(raw)
    return sections


def _drop_header(lines: list[str]) -> list[str]:
    """Every section's own field-header row (e.g. 'account_id,parent_id') is always present and
    always skipped -- see problem.md Input."""
    return lines[1:] if lines else []


def _parse_accounts(lines: list[str]) -> list[dict]:
    out = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        account_id, parent_id = (p.strip() for p in raw.split(","))
        out.append({"account_id": account_id, "parent_id": parent_id or None})
    return out


def _parse_roles(lines: list[str]) -> list[dict]:
    out = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        role_id, perms = raw.split(",", 1)
        permissions = [p.strip() for p in perms.split(";") if p.strip()]
        out.append({"role_id": role_id.strip(), "permissions": permissions})
    return out


def _parse_assignments(lines: list[str]) -> list[dict]:
    out = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        user_id, account_id, role_id = (p.strip() for p in raw.split(","))
        out.append({"user_id": user_id, "account_id": account_id, "role_id": role_id})
    return out


def main(stdin=sys.stdin, stdout=sys.stdout) -> None:
    """Stdin protocol (see problem.md Input for the full spec):
        PART <n>
        ACCOUNTS
        account_id,parent_id
        ...
        ROLES
        role_id,permissions          <- ';'-joined, may include '!deny' / 'ns:*' from Part 3 on
        ...
        ASSIGNMENTS
        user_id,account_id,role_id
        ...
        QUERY
        user_id,account_id[,permission]
        ...                           <- Part 4 only: more than one query line
    Part 1/2 output: one line, the sorted permissions comma-joined, or 'NONE' if empty.
    Part 3 output: one line, 'True' or 'False'.
    Part 4 output: one 'True'/'False' line per query line, same order.
    """
    lines = stdin.read().splitlines()
    if not lines:
        return
    header = lines[0].strip()
    if not header.startswith("PART "):
        raise ValueError(f"unknown header: {header!r}")
    part_num = int(header.split()[1])

    sections = _split_sections(lines[1:])
    accounts = _parse_accounts(_drop_header(sections["ACCOUNTS"]))
    roles = _parse_roles(_drop_header(sections["ROLES"]))
    assignments = _parse_assignments(_drop_header(sections["ASSIGNMENTS"]))
    query_lines = [ln.strip() for ln in _drop_header(sections["QUERY"]) if ln.strip()]

    if part_num in (1, 2):
        user_id, account_id = (p.strip() for p in query_lines[0].split(","))
        fn = part1 if part_num == 1 else part2
        perms = fn(accounts, roles, assignments, user_id, account_id)
        stdout.write((",".join(perms) if perms else "NONE") + "\n")
    elif part_num == 3:
        user_id, account_id, permission = (p.strip() for p in query_lines[0].split(","))
        result = part3(accounts, roles, assignments, user_id, account_id, permission)
        stdout.write(("True" if result else "False") + "\n")
    elif part_num == 4:
        queries = []
        for ln in query_lines:
            user_id, account_id, permission = (p.strip() for p in ln.split(","))
            queries.append((user_id, account_id, permission))
        results = part4(accounts, roles, assignments, queries)
        stdout.write("\n".join("True" if r else "False" for r in results) + "\n")
    else:
        raise ValueError(f"unknown header: {header!r}")


if __name__ == "__main__":
    main()
