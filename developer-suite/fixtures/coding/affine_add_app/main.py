#!/usr/bin/env python3
"""AffineAddApp — teaching coding application for the coding language game."""


def add(a: int, b: int) -> int:
    """Jordan-simple adder used as the coding-game statement seed."""
    return a + b


def main() -> int:
    left, right = 2, 2
    total = add(left, right)
    print(f"AffineAddApp: {left} + {right} = {total}")
    assert total == 4, "teaching invariant: 2+2→4"
    print("status=CALORIE_TEACHING_ADD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
