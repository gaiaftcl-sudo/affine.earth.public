# ARC-icecuber (third-party, MIT)

Vendored from https://github.com/victorvikram/ARC-icecuber
(fork of top-quarks/ARC-solution; original Kaggle ARC 1st-place search solver).

License: MIT (see LICENSE). Copyright (c) 2020 top-quarks.

Local macOS port patches in this tree:
- prefer `#include <filesystem>` over experimental
- drop `-lstdc++fs` link flag on Apple Clang
- allow absolute sample directories in `readAll`

Used only for offline local mastery. Never submitted to Kaggle from this harness.
