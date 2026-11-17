# Verification

Recorded on 17 November 2026.

- 27 Python mathematical, local HTTP and hosted-application tests passed.
- 37 complete browser workflow checks passed through the production WSGI entry.
- The earlier local review also passed 5 additional checks for fractional labels,
  notebook download, playback speed, restarting from the end and phone graph size.
- The self-contained notebook executed all 6 code cells in a fresh Python kernel
  with zero error outputs. Its three saved figures were inspected.

The mathematical checks include a Decimal-based reference value, cooling and
warming, target classification, half-life, Euler and RK4 convergence, nonuniform
last steps, numerical instability, unavailable values and invalid inputs.

Browser checks exercise all presets, playback, timeline, pending settings, pinned
comparison, numerical/error graphs, table pages, CSV/JSON exports, settings import,
target edge cases, the guided comparison, the dialog and a 390-pixel phone layout.

These are small deterministic educational examples. They are not measured thermal
experiments, a load-capacity benchmark or a full accessibility audit.
