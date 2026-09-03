import pytest

ACCOUNTS = [
    {"account_id": "platform", "parent_id": None},
    {"account_id": "connected", "parent_id": "platform"},
    {"account_id": "submerchant", "parent_id": "connected"},
]

ROLES = [
    {"role_id": "viewer", "permissions": ["payouts:read", "charges:read"]},  # deliberately unsorted
    {"role_id": "admin", "permissions": ["charges:read", "charges:write", "payouts:read", "payouts:write"]},
]

ASSIGNMENTS = [
    {"user_id": "alice", "account_id": "platform", "role_id": "viewer"},
    {"user_id": "alice", "account_id": "connected", "role_id": "admin"},
    {"user_id": "bob", "account_id": "submerchant", "role_id": "viewer"},
]

ADMIN_PERMS = ["charges:read", "charges:write", "payouts:read", "payouts:write"]
VIEWER_PERMS = ["charges:read", "payouts:read"]


def _accounts_lines(accounts):
    return ["ACCOUNTS", "account_id,parent_id"] + [
        f"{a['account_id']},{a['parent_id'] or ''}" for a in accounts
    ]


def _roles_lines(roles):
    return ["ROLES", "role_id,permissions"] + [f"{r['role_id']},{';'.join(r['permissions'])}" for r in roles]


def _assignments_lines(assignments):
    return ["ASSIGNMENTS", "user_id,account_id,role_id"] + [
        f"{a['user_id']},{a['account_id']},{a['role_id']}" for a in assignments
    ]


def _stdin(part, accounts, roles, assignments, query_lines):
    lines = [f"PART {part}"]
    lines += _accounts_lines(accounts)
    lines += _roles_lines(roles)
    lines += _assignments_lines(assignments)
    lines += ["QUERY", "user_id,account_id,permission"] + query_lines
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- Part 1: flat, no hierarchy
@pytest.mark.part1
def test_direct_role_at_own_account(impl):
    assert impl.part1(ACCOUNTS, ROLES, ASSIGNMENTS, "alice", "connected") == ADMIN_PERMS


@pytest.mark.part1
def test_no_inheritance_from_ancestor(impl):
    # alice's role is at platform/connected, not at submerchant itself -- Part 1 has no inheritance
    assert impl.part1(ACCOUNTS, ROLES, ASSIGNMENTS, "alice", "submerchant") == []


@pytest.mark.part1
def test_no_role_anywhere_returns_empty(impl):
    assert impl.part1(ACCOUNTS, ROLES, ASSIGNMENTS, "carol", "platform") == []


@pytest.mark.part1
@pytest.mark.fmt
def test_permissions_are_sorted_even_though_role_lists_them_unsorted(impl):
    # ROLES['viewer'] lists payouts:read before charges:read
    assert impl.part1(ACCOUNTS, ROLES, ASSIGNMENTS, "alice", "platform") == VIEWER_PERMS


@pytest.mark.part1
@pytest.mark.io
def test_stdin_stdout_part1(run_script):
    # QUERY line for part1/2 is "user_id,account_id" (no trailing permission field)
    stdin_text = (
        _stdin(1, ACCOUNTS, ROLES, ASSIGNMENTS, []).rsplit("QUERY\n", 1)[0]
        + "QUERY\nuser_id,account_id\nalice,connected\n"
    )
    r = run_script(stdin_text)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ",".join(ADMIN_PERMS) + "\n"


# ---------------------------------------------------------------- Part 2: hierarchy (union, no wildcards)
@pytest.mark.part2
def test_inherits_union_of_ancestor_permissions(impl):
    # alice: viewer@platform + admin@connected, nothing at submerchant itself -> union of both
    assert impl.part2(ACCOUNTS, ROLES, ASSIGNMENTS, "alice", "submerchant") == ADMIN_PERMS


@pytest.mark.part2
def test_own_level_role_with_no_ancestors_assigned(impl):
    assert impl.part2(ACCOUNTS, ROLES, ASSIGNMENTS, "bob", "submerchant") == VIEWER_PERMS


@pytest.mark.part2
def test_no_role_anywhere_in_chain_returns_empty(impl):
    assert impl.part2(ACCOUNTS, ROLES, ASSIGNMENTS, "carol", "submerchant") == []


@pytest.mark.part2
@pytest.mark.edge
def test_unknown_account_id_raises(impl):
    with pytest.raises(ValueError):
        impl.part2(ACCOUNTS, ROLES, ASSIGNMENTS, "alice", "does-not-exist")


@pytest.mark.part2
@pytest.mark.edge
def test_duplicate_assignment_same_user_account_raises(impl):
    bad = ASSIGNMENTS + [{"user_id": "alice", "account_id": "platform", "role_id": "admin"}]
    with pytest.raises(ValueError):
        impl.part2(ACCOUNTS, ROLES, bad, "alice", "platform")


@pytest.mark.part2
@pytest.mark.edge
def test_two_node_cycle_raises(impl):
    cyclic = [{"account_id": "x", "parent_id": "y"}, {"account_id": "y", "parent_id": "x"}]
    with pytest.raises(ValueError):
        impl.part2(cyclic, ROLES, [], "anyone", "x")


@pytest.mark.part2
@pytest.mark.edge
def test_self_parent_cycle_raises(impl):
    cyclic = [{"account_id": "x", "parent_id": "x"}]
    with pytest.raises(ValueError):
        impl.part2(cyclic, ROLES, [], "anyone", "x")


@pytest.mark.part2
@pytest.mark.fmt
def test_union_deduplicates_permission_appearing_at_two_levels(impl):
    accounts = [{"account_id": "p", "parent_id": None}, {"account_id": "c", "parent_id": "p"}]
    roles = [
        {"role_id": "r1", "permissions": ["charges:read"]},
        {"role_id": "r2", "permissions": ["charges:read"]},
    ]
    assignments = [
        {"user_id": "u", "account_id": "p", "role_id": "r1"},
        {"user_id": "u", "account_id": "c", "role_id": "r2"},
    ]
    assert impl.part2(accounts, roles, assignments, "u", "c") == ["charges:read"]


@pytest.mark.part2
@pytest.mark.io
def test_stdin_stdout_part2(run_script):
    stdin_text = (
        _stdin(2, ACCOUNTS, ROLES, ASSIGNMENTS, []).rsplit("QUERY\n", 1)[0]
        + "QUERY\nuser_id,account_id\nalice,submerchant\n"
    )
    r = run_script(stdin_text)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ",".join(ADMIN_PERMS) + "\n"


# ---------------------------------------------------------------- Part 3: wildcards + deny-overrides-allow
@pytest.mark.part3
def test_wildcard_grant_inherited_matches_specific_permission(impl):
    roles = ROLES + [{"role_id": "wild_admin", "permissions": ["charges:*"]}]
    assignments = ASSIGNMENTS + [{"user_id": "carol", "account_id": "connected", "role_id": "wild_admin"}]
    assert impl.part3(ACCOUNTS, roles, assignments, "carol", "submerchant", "charges:read") is True


@pytest.mark.part3
def test_global_wildcard_matches_anything(impl):
    roles = ROLES + [{"role_id": "root", "permissions": ["*"]}]
    assignments = ASSIGNMENTS + [{"user_id": "carol", "account_id": "platform", "role_id": "root"}]
    assert impl.part3(ACCOUNTS, roles, assignments, "carol", "submerchant", "payouts:refund") is True


@pytest.mark.part3
def test_explicit_deny_beats_wildcard_at_same_level(impl):
    roles = ROLES + [{"role_id": "support", "permissions": ["charges:*", "!charges:refund"]}]
    assignments = ASSIGNMENTS + [{"user_id": "dave", "account_id": "connected", "role_id": "support"}]
    assert impl.part3(ACCOUNTS, roles, assignments, "dave", "submerchant", "charges:refund") is False
    assert impl.part3(ACCOUNTS, roles, assignments, "dave", "submerchant", "charges:read") is True


@pytest.mark.part3
@pytest.mark.edge
def test_deny_at_a_farther_level_still_beats_a_grant_at_a_closer_level(impl):
    # This is the decided rule (see problem.md): deny-overrides-allow GLOBALLY, not "nearest scope
    # wins" -- if it were nearest-wins, the closer (submerchant) grant would win and this would be
    # True. A grant closer to the account than the deny is still overridden.
    roles = [
        {"role_id": "grant_close", "permissions": ["charges:read"]},
        {"role_id": "deny_far", "permissions": ["!charges:read"]},
    ]
    assignments = [
        {"user_id": "erin", "account_id": "submerchant", "role_id": "grant_close"},
        {"user_id": "erin", "account_id": "platform", "role_id": "deny_far"},
    ]
    assert impl.part3(ACCOUNTS, roles, assignments, "erin", "submerchant", "charges:read") is False


@pytest.mark.part3
@pytest.mark.edge
def test_no_role_anywhere_defaults_to_false(impl):
    assert impl.part3(ACCOUNTS, ROLES, ASSIGNMENTS, "carol", "submerchant", "charges:read") is False


@pytest.mark.part3
@pytest.mark.edge
def test_cycle_still_raises_in_part3(impl):
    cyclic = [{"account_id": "x", "parent_id": "y"}, {"account_id": "y", "parent_id": "x"}]
    with pytest.raises(ValueError):
        impl.part3(cyclic, ROLES, [], "anyone", "x", "charges:read")


@pytest.mark.part3
@pytest.mark.io
def test_stdin_stdout_part3(run_script):
    roles = ROLES + [{"role_id": "wild_admin", "permissions": ["charges:*"]}]
    assignments = ASSIGNMENTS + [{"user_id": "carol", "account_id": "connected", "role_id": "wild_admin"}]
    stdin_text = (
        _stdin(3, ACCOUNTS, roles, assignments, []).rsplit("QUERY\n", 1)[0]
        + "QUERY\nuser_id,account_id,permission\ncarol,submerchant,charges:read\n"
    )
    r = run_script(stdin_text)
    assert r.returncode == 0, r.stderr
    assert r.stdout == "True\n"


# ---------------------------------------------------------------- Part 4: batch efficiency
@pytest.mark.part4
def test_batch_matches_individual_part3_results(impl):
    roles = ROLES + [{"role_id": "support", "permissions": ["charges:*", "!charges:refund"]}]
    assignments = ASSIGNMENTS + [{"user_id": "dave", "account_id": "connected", "role_id": "support"}]
    queries = [
        ("alice", "submerchant", "charges:write"),
        ("dave", "submerchant", "charges:refund"),
        ("dave", "submerchant", "charges:read"),
        ("carol", "submerchant", "charges:read"),
    ]
    expected = [impl.part3(ACCOUNTS, roles, assignments, u, a, p) for u, a, p in queries]
    assert impl.part4(ACCOUNTS, roles, assignments, queries) == expected


@pytest.mark.part4
def test_batch_repeated_pair_different_permissions(impl):
    roles = ROLES + [{"role_id": "wild_admin", "permissions": ["charges:*"]}]
    assignments = ASSIGNMENTS + [{"user_id": "carol", "account_id": "connected", "role_id": "wild_admin"}]
    queries = [
        ("carol", "submerchant", "charges:read"),
        ("carol", "submerchant", "charges:write"),
        ("carol", "submerchant", "payouts:read"),
    ]
    assert impl.part4(ACCOUNTS, roles, assignments, queries) == [True, True, False]


@pytest.mark.part4
def test_batch_preserves_query_order(impl):
    queries = [
        ("bob", "submerchant", "payouts:read"),
        ("alice", "connected", "charges:write"),
        ("bob", "submerchant", "charges:write"),
    ]
    assert impl.part4(ACCOUNTS, ROLES, ASSIGNMENTS, queries) == [True, True, False]


@pytest.mark.part4
@pytest.mark.edge
def test_batch_unknown_account_in_a_query_raises(impl):
    with pytest.raises(ValueError):
        impl.part4(ACCOUNTS, ROLES, ASSIGNMENTS, [("alice", "nonexistent", "charges:read")])


@pytest.mark.part4
@pytest.mark.edge
def test_batch_unknown_user_returns_false_not_an_error(impl):
    # a user_id that never appears in assignments is normal ("no access anywhere"), not malformed
    # data -- contrast with the previous test's unknown ACCOUNT, which IS malformed.
    assert impl.part4(ACCOUNTS, ROLES, ASSIGNMENTS, [("nobody", "submerchant", "charges:read")]) == [False]


@pytest.mark.part4
@pytest.mark.io
def test_stdin_stdout_part4(run_script):
    stdin_text = (
        _stdin(4, ACCOUNTS, ROLES, ASSIGNMENTS, []).rsplit("QUERY\n", 1)[0]
        + "QUERY\nuser_id,account_id,permission\n"
        "bob,submerchant,charges:read\n"
        "bob,submerchant,charges:write\n"
        "alice,connected,payouts:write\n"
    )
    r = run_script(stdin_text)
    assert r.returncode == 0, r.stderr
    assert r.stdout == "True\nFalse\nTrue\n"


@pytest.mark.part4
@pytest.mark.perf
def test_perf_deep_chain_repeated_pair_queries(run_script):
    depth = 3000
    n_queries = 25000
    accounts = [{"account_id": "acct0", "parent_id": ""}]
    for i in range(1, depth):
        accounts.append({"account_id": f"acct{i}", "parent_id": f"acct{i - 1}"})
    leaf = f"acct{depth - 1}"
    roles = [{"role_id": "root_role", "permissions": ["root:*"]}]
    assignments = [{"user_id": "root_user", "account_id": "acct0", "role_id": "root_role"}]
    query_lines = [f"root_user,{leaf},root:action{i}" for i in range(n_queries)]
    stdin_text = (
        _stdin(4, accounts, roles, assignments, []).rsplit("QUERY\n", 1)[0]
        + "QUERY\nuser_id,account_id,permission\n"
        + "\n".join(query_lines)
        + "\n"
    )
    r = run_script(stdin_text, timeout=30)
    assert r.returncode == 0, r.stderr
    out_lines = r.stdout.splitlines()
    assert len(out_lines) == n_queries
    assert all(line == "True" for line in out_lines)  # root:* grants every root:action{i}
    assert r.seconds < 2.0, f"too slow: {r.seconds:.2f}s"
    assert r.max_rss_mb < 256, f"too much memory: {r.max_rss_mb:.0f}MB"
