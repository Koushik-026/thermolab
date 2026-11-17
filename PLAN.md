# ThermoLab

Local Computational Mathematics project for students and teachers. First deliver
the working local preview. GitHub, hosting and the college report are later steps.

## Model and interpretation

Time is in minutes. Temperatures use degrees Celsius. With constant surroundings
Ta and constant coefficient k (per minute), dT/dt = -k(T-Ta). The exact reference
is T(t) = Ta + (T0-Ta) exp(-kt). A uniform object, constant ambient temperature and
unchanging cooling coefficient are assumptions, not measured properties of tea.
The model also describes warming from below ambient. It excludes evaporation,
phase changes, detailed heat flow and food-safety decisions.

Python owns calculations. A standard-library local HTTP server serves the site,
presets and simulation API. No account, database, API key or third-party runtime
package is needed for the website. Browser code handles presentation and playback.
The teaching notebook embeds the same Python model and runs inside Colab's normal
notebook UI instead of trying to turn Colab into a web host.

## Calculation contract

- Validate finite numeric values, ranges and sample count before computation.
- Compare forward Euler and classical RK4 with the analytic solution at identical
  time points. Include t=0 and the exact requested ending time; shorten the final
  integration step where necessary. Keep numerical step and animation speed separate.
- Animation evaluates the analytic expression at the playback time, never an
  inaccurate Euler trajectory. Exports retain calculated settings when edits pend.
- Label Euler oscillation, neutral behaviour and instability using its amplification
  factor. RK4 uses its own amplification factor. Do not silently clamp outputs.
- Stop only an approximation which exceeds the documented 1e8 C display/computation
  threshold, return null thereafter, and report truncation. Keep the exact model.
- Target calculation distinguishes t=0, finite reach, beyond plotted duration,
  ambient asymptote, an unreachable target and no temperature change (k=0).
- Half-life means halving the temperature difference, not halving Celsius temperature.
- Comparison pins one prior calculated exact curve. Parameters and identifiers stay
  attached to every run, table, comparison and download.

## Experience

Four populated presets: warm cup, slower cooling, cold object warming, and a
deliberately coarse Euler step. Edit inputs with short notes, calculate, play,
scrub, inspect temperature/error graphs, compare a baseline and download CSV or
settings JSON. A method lab shows the actual first Euler/RK4 step and a paged
results table. A short guide explains the workflow and model limits.

## Verification

Independent fixed examples, closed-form crossing times, numerical convergence,
edge cases, invalid input, final-step accuracy, instability/truncation and export
consistency. Browser checks must cover all presets, playback, scrubbing, pending
inputs, comparison, method tabs, file downloads, import, errors and phone layout.
Execute the teaching notebook top-to-bottom and inspect its plots.

Sources checked 17 November 2026:
- https://openstax.org/books/algebra-and-trigonometry-2e/pages/6-7-exponential-and-logarithmic-models
- https://openstax.org/books/calculus-volume-2/pages/4-1-basics-of-differential-equations
- https://research.google.com/colaboratory/faq.html
