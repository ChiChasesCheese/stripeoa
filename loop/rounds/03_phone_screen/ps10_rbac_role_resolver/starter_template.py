"""ps10 RBAC Role Resolver — YOUR implementation."""

from __future__ import annotations

import sys


def part1(
    accounts: list[dict], roles: list[dict], assignments: list[dict], user_id: str, account_id: str
) -> list[str]:
    """accounts: [{'account_id','parent_id'}]. roles: [{'role_id','permissions': list[str]}].
    assignments: [{'user_id','account_id','role_id'}]. No hierarchy in this part: return the
    sorted permissions of the role the user is directly assigned AT account_id itself (or []
    if none). Assume well-formed input, no validation needed."""
    # TODO
    return []


def part2(
    accounts: list[dict], roles: list[dict], assignments: list[dict], user_id: str, account_id: str
) -> list[str]:
    """Now accounts form a tree via parent_id (falsy/missing = root). Return the sorted UNION of
    permissions from every role the user holds anywhere along account_id's ancestor chain (root
    down to account_id itself). Validate: raise ValueError on a duplicate account_id/role_id, an
    assignment referencing an unknown account/role, a duplicate assignment for the same
    (user_id, account_id), an unknown account anywhere in the chain, or a parent_id cycle
    (including account_id == parent_id)."""
    # TODO
    return []


def part3(
    accounts: list[dict],
    roles: list[dict],
    assignments: list[dict],
    user_id: str,
    account_id: str,
    permission: str,
) -> bool:
    """Same hierarchy + validation as part2, but a role's permissions may now include wildcards
    ('*' matches anything, 'ns:*' matches any 'ns:...' permission) and explicit denies (a
    permission prefixed with '!'). Return whether user_id effectively has `permission` at
    account_id: an explicit deny ANYWHERE in the chain wins over a grant from any level
    (deny-overrides-allow globally, not "nearest level wins")."""
    # TODO
    return False


def part4(
    accounts: list[dict],
    roles: list[dict],
    assignments: list[dict],
    queries: list[tuple[str, str, str]],
) -> list[bool]:
    """queries: (user_id, account_id, permission) tuples, possibly repeating the same
    (user_id, account_id) pair. Same rules as part3. Return one bool per query, same order.
    Must not re-walk the same account's ancestor chain, nor re-aggregate the same
    (user_id, account_id) pair's grants/denies, once per query -- cache both."""
    # TODO
    return [False for _ in queries]


# ---------------------------------------------------------------- I/O
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
