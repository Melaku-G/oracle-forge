"""
join_key_resolver.py
--------------------
Utility for resolving ill-formatted join key mismatches across heterogeneous
databases in the Oracle Forge data agent.

DAB Failure Category addressed: Ill-formatted join key mismatch.

Problem: Entity references (e.g. customer IDs) are formatted differently
across database systems. For example, a customer ID stored as integer 12345
in PostgreSQL may appear as "USR-12345" or "CUST-00123" in MongoDB.

Usage:
    from utils.join_key_resolver import resolve_join_key

    pg_id = 12345
    mongo_id = resolve_join_key(pg_id, source_db="postgresql", target_db="mongodb")
    # Returns: "USR-12345"  (if that is the confirmed format for this dataset)
"""

import re
from typing import Union


# Registry of known format rules per database pair.
# Key: (source_db, target_db) tuple.
# Value: dict with prefix and optional zero-padding width.
# Drivers: populate this registry as new mismatches are discovered.
# Document every entry in kb/domain/yelp_schema.md.
FORMAT_REGISTRY: dict = {
    # Yelp dataset: PostgreSQL integer user_id → MongoDB "USR-{id}" string
    # NOTE: Confirm exact prefix by inspecting loaded MongoDB collection.
    ("postgresql", "mongodb"): {
        "prefix": "USR-",
        "pad_width": 0,  # Set to e.g. 5 for zero-padded "USR-00123"
    },
}


def resolve_join_key(
    value: Union[int, str],
    source_db: str,
    target_db: str,
    dataset: str = "yelp",
) -> Union[str, int, None]:
    """
    Convert a join key value from source_db format to target_db format.

    Args:
        value:      The raw key value as it appears in source_db.
        source_db:  Name of the source database system.
                    One of: "postgresql", "mongodb", "sqlite", "duckdb".
        target_db:  Name of the target database system.
        dataset:    Dataset name (for future per-dataset rule overrides).

    Returns:
        The key value reformatted for target_db, or None if no rule is found.
        Logs a warning if the conversion rule is not registered.

    Raises:
        ValueError: If value cannot be parsed according to the registered rule.
    """
    rule = FORMAT_REGISTRY.get((source_db.lower(), target_db.lower()))

    if rule is None:
        # No registered rule — return None and let caller decide how to handle.
        # Drivers: add the missing rule to FORMAT_REGISTRY and kb/domain docs.
        print(
            f"[join_key_resolver] WARNING: No format rule registered for "
            f"{source_db} → {target_db} (dataset={dataset}). "
            f"Add rule to FORMAT_REGISTRY and document in kb/domain/."
        )
        return None

    # --- postgresql integer → mongodb prefixed string ---
    if source_db.lower() == "postgresql" and target_db.lower() == "mongodb":
        prefix = rule.get("prefix", "")
        pad = rule.get("pad_width", 0)
        int_val = int(value)
        padded = str(int_val).zfill(pad) if pad else str(int_val)
        return f"{prefix}{padded}"

    # --- mongodb prefixed string → postgresql integer ---
    if source_db.lower() == "mongodb" and target_db.lower() == "postgresql":
        str_val = str(value)
        rule_fwd = FORMAT_REGISTRY.get(("postgresql", "mongodb"), {})
        prefix = rule_fwd.get("prefix", "")
        stripped = str_val[len(prefix):] if str_val.startswith(prefix) else str_val
        digits = re.sub(r"\D", "", stripped)
        if not digits:
            raise ValueError(
                f"[join_key_resolver] Cannot extract integer from '{value}' "
                f"using prefix='{prefix}'"
            )
        return int(digits)

    # Fallback for unimplemented direction
    print(
        f"[join_key_resolver] WARNING: Rule found but direction not implemented "
        f"for {source_db} → {target_db}. Returning None."
    )
    return None


# ---------------------------------------------------------------------------
# Smoke test — run this file directly to verify basic behaviour
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # PostgreSQL int → MongoDB string
    result = resolve_join_key(12345, "postgresql", "mongodb")
    assert result == "USR-12345", f"Expected 'USR-12345', got {result!r}"

    # MongoDB string → PostgreSQL int
    result = resolve_join_key("USR-12345", "mongodb", "postgresql")
    assert result == 12345, f"Expected 12345, got {result!r}"

    # Unknown pair returns None
    result = resolve_join_key(99, "duckdb", "mongodb")
    assert result is None

    print("join_key_resolver: all smoke tests passed.")