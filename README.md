# ThermoLab

A small Computational Mathematics lab for a familiar question: how does an object
approach room temperature? Change the conditions, watch the result and compare
the exact solution with Euler and Runge–Kutta estimates.

**[Open the live showcase](https://thermolab-cooling.onrender.com)**. The warm-cup
experiment loads automatically. Press Play or change a setting and run it again.

## Run the website

Install Python 3.10 or later. No extra Python packages are required for the website.
On Windows, double-click **Open ThermoLab.cmd**. Or run:

```sh
python server.py
```

Open **http://127.0.0.1:3201**. Keep the terminal open. This local command runs the
server on your laptop. It needs no internet connection, API key or account.
If that port is occupied, run `python server.py --port 3202` and open that port.

## Try it

The warm-cup experiment loads automatically. Press Play, move the timeline, then
change one input and press Run experiment. Edited controls stay pending until
calculated; results and downloads keep the previous calculated settings meanwhile.

Pin a reference, halve the cooling coefficient and run again. The half-life of the
temperature difference doubles. The cold-object example demonstrates warming.
The big-step example deliberately exposes Euler's numerical oscillation.

The mathematics section explains the model. Open the method lab to see the first
Euler and RK4 steps, their errors and every calculated row. CSV exports include all
samples and parameters. Settings JSON can be saved and loaded again.

## Run the Python notebook

Upload **ThermoLab.ipynb** in Google Colab and choose **Runtime → Run all** with a
standard CPU runtime. The notebook embeds the same calculation engine, static
worked examples and interactive Python controls. No project files, website tunnel,
Drive mount or GPU are needed. Missing Matplotlib/ipywidgets packages install in
the setup cell, which requires internet only if packages are missing.

The notebook also runs in local Jupyter. Colab's temporary runtime can disconnect;
download the notebook, CSV and settings before leaving. Notebook controls need a
live Python kernel. Saved figures remain visible without one.

## The model

```text
dT/dt = -k(T - Ta)
T(t)  = Ta + (T0 - Ta) exp(-kt)
```

Temperatures are Celsius, time is minutes, and k is per minute. The model assumes
one uniform object temperature, a constant room temperature and constant k.
It excludes evaporation, phase changes and detailed heat flow. Presets are
illustrative, not measured tea properties or food-safety recommendations.

The object animation always follows the exact reference. Numerical step size is
independent of playback speed. Euler and classical RK4 use the same time grid and
shorten the last step to end at the exact requested duration. The exact graph uses
its own dense grid even when numerical steps are large.

Targets distinguish an immediate match, a finite crossing, a crossing beyond the
plotted duration, the ambient asymptote and an unreachable value. k=0 gives constant
temperature. Half-life means halving the temperature difference from the room.

Numerical instability is labelled instead of disguised as physical behaviour.
An approximation exceeding 100 million °C stops and returns unavailable values;
the exact reference stays available. The app does not silently clamp numbers.

## Check it

```sh
python -m unittest test_core -v
```

Tests cover fixed independent values, convergence, cooling/warming, targets,
stability, shortened steps, bad inputs and the HTTP API. `browser-check.mjs` is an
optional Playwright workflow check. The hosted HTTPS workflow passed 42 browser
checks. [Verification notes](docs/verification.md) describe the scope.
`output/` keeps local verification records.

Source files: `core.py` owns the model, `app.py` handles the shared web application,
`server.py` runs it locally, and `web/` contains the interface. `build_notebook.py` embeds the model in
the notebook, and `execute_notebook.py` checks it in a fresh local kernel. Notebook
authoring needs nbformat, nbclient, ipykernel, Matplotlib and ipywidgets.

## Host the showcase

The hosted application uses Gunicorn on Linux and the same calculation engine as
the local site. Install `requirements.txt`, then run `gunicorn app:application`.
`gunicorn.conf.py` binds to `0.0.0.0` using the hosting platform's `PORT` value.
The readiness endpoint is `/api/health`. `.python-version` pins Python 3.12.14.

There are no accounts or stored experiments on the server. Save CSV and settings
files to retain a result. A free Render service may take longer to wake after
inactivity. It does not need a database or persistent disk.

Personalised college reports and private team details stay outside public source.

References: [OpenStax model](https://openstax.org/books/algebra-and-trigonometry-2e/pages/6-7-exponential-and-logarithmic-models),
[differential equations](https://openstax.org/books/calculus-volume-2/pages/4-1-basics-of-differential-equations),
[Colab FAQ](https://research.google.com/colaboratory/faq.html).
