"""Deterministic violation-detection rules.

One pure function per legal rule, each citing the Act section in its comment.
The engine (`engine.py`) runs every module's `run()` and aggregates the results.
"""

from . import contract, hours, leave, social_security, termination, wages

RULE_MODULES = [
    hours,
    wages,
    leave,
    social_security,
    termination,
    contract,
]


def run_rules(ctx) -> list:
    """Run every rule module against one submission and aggregate findings."""
    violations = []
    for module in RULE_MODULES:
        violations.extend(module.run(ctx))
    return violations
