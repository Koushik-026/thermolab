"""Build the self-contained Computational Mathematics teaching notebook."""
from pathlib import Path
import nbformat as nb

ROOT=Path(__file__).resolve().parent
cells=[]
def md(text):cells.append(nb.v4.new_markdown_cell(text))
def code(text):cells.append(nb.v4.new_code_cell(text))

md('''# ThermoLab
## The mathematics of cooling

Explore how a hot object cools, or a cold object warms, towards a constant room
temperature. Compare the exact solution with **Euler** and **Runge–Kutta (RK4)**.

This notebook contains all its calculation code. In Google Colab, choose a standard
CPU runtime and **Runtime → Run all**. No website server, GPU, account registration,
API key or Drive mount is needed. Use the controls near the end to create an experiment.

The default illustrative cup starts at **85°C** in a **22°C** room with
**k = 0.045 per minute**. Its exact temperature after 60 minutes is about **26.23°C**.
It reaches 45°C in about **22.39 minutes**. These are model outputs, not measurements.
''')
md('''## 1. Setup
The calculation engine uses Python's standard library. Matplotlib draws the graphs,
and ipywidgets supplies notebook controls. This cell installs a missing plotting or
widget package only when needed. A fresh installation needs internet access.''')
code('''import importlib.util
import subprocess
import sys
missing = [name for name in ['matplotlib', 'ipywidgets'] if importlib.util.find_spec(name) is None]
if missing:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML, FileLink, clear_output
import csv, io, json, html
from pathlib import Path
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'figure.facecolor':'#fafbf6',
                     'axes.facecolor':'#fafbf6','axes.labelcolor':'#314d3e',
                     'text.color':'#314d3e','axes.edgecolor':'#cfd9c6'})
print('ThermoLab is ready. All time values below use minutes.')''')
md(r'''## 2. The model

Newton's law of cooling describes a rate proportional to the temperature difference:

$$\frac{dT}{dt}=-k(T-T_a),\qquad T(0)=T_0.$$

Its exact solution is

$$T(t)=T_a+(T_0-T_a)e^{-kt}.$$

Here $T$ is the object's temperature in °C, $T_a$ is the constant room temperature,
$t$ is time in minutes and $k$ has units min$^{-1}$.

**Assumptions:** the object has one uniform temperature, the room stays constant,
and $k$ does not change. The model excludes evaporation, phase changes and detailed
heat flow. It is an educational example, not advice about food or drink safety.

The same equation models warming when the object starts below room temperature.
With $k=0$, the temperature stays unchanged. Room temperature is an asymptote when
the starting temperature differs from it and $k>0$.
''')
code((ROOT/'core.py').read_text(encoding='utf-8'))
md(r'''## 3. A worked experiment

Euler uses the current rate for one step:

$$T_{n+1}=T_n-hk(T_n-T_a).$$

RK4 evaluates four rates within the same step and combines them. Both methods use
the same time grid for comparison with the exact solution. The final step shortens
when necessary so the experiment ends at the requested time.

The exact graph uses a separate dense grid, so a large numerical step does not
turn the physical reference into a few straight segments.
''')
code('''def plot_experiment(result):
    p=result['parameters']; rows=result['samples']; reference=result['reference']
    fig,axes=plt.subplots(1,2,figsize=(12,4.2),layout='constrained')
    axes[0].plot([r['time'] for r in reference],[r['exact'] for r in reference],
                 color='#51734e',linewidth=2.5,label='Exact reference')
    for key,color,style in [('euler','#cf8954','--'),('rk4','#8c83ab',':')]:
        axes[0].plot([r['time'] for r in rows],[r[key] for r in rows],
                     color=color,linestyle=style,label='Euler' if key=='euler' else 'RK4')
        axes[1].plot([r['time'] for r in rows],[r[key+'_error'] for r in rows],
                     color=color,linestyle=style,label='Euler' if key=='euler' else 'RK4')
    axes[0].axhline(p['ambient'],color='#a9b99d',linewidth=1,label='Room temperature')
    axes[0].set(title='Object temperature over time',xlabel='Time (min)',ylabel='Temperature (°C)')
    axes[1].set(title='Absolute error against the exact solution',xlabel='Time (min)',ylabel='Absolute error (°C)')
    for axis in axes:
        axis.grid(alpha=.18);axis.legend(frameon=False,fontsize=8);axis.set_xlim(0,p['duration'])
    if result['warnings']:
        print('Numerical note: '+' '.join(result['warnings']))
    display(fig);plt.close(fig)
    return fig

default_result=simulate(asdict(Parameters()))
p=default_result['parameters'];s=default_result['summary'];f=s['first_step']
print(f"Start: {p['initial']}°C | room: {p['ambient']}°C | k: {p['coefficient']} per minute")
print(f"First Euler step: {p['initial']} + {f['h']} × ({f['slope']:.4f}) = {f['euler_next']:.5f}°C")
print(f"First RK4 step: {f['rk4_next']:.5f}°C | exact: {f['exact_next']:.5f}°C")
print(f"After 60 min: {s['final_temperature']:.5f}°C")
print(f"Time to 45°C: {s['target']['minutes']:.5f} min")
print(f"Time to halve the temperature difference: {s['half_life']:.5f} min")
plot_experiment(default_result);''')
md('''## 4. What a larger step changes

The big-step preset deliberately makes Euler cross room temperature. That oscillation
belongs to the approximation, not the physical model. Compare it with the smooth
reference. Reducing the step should bring a suitable approximation closer to the reference.

For Euler, the difference from room temperature is multiplied by $1-kh$ per full
step. Values between 0 and 1 decay without crossing. A negative factor can create
alternation. A factor with absolute value greater than 1 produces growth.

If an approximation exceeds the documented 100 million °C numerical limit, the
engine marks subsequent values unavailable instead of silently clamping them.
''')
code('''big_step=simulate(PRESETS[3]['parameters'])
plot_experiment(big_step);
print('Euler state:',big_step['summary']['methods']['euler']['stability'])
assert big_step['summary']['methods']['euler']['stability']=='oscillating'
assert default_result['summary']['methods']['rk4']['max_abs_error'] < default_result['summary']['methods']['euler']['max_abs_error']
assert abs(exact(Parameters(),default_result['summary']['target']['minutes'])-45)<1e-10
assert target_time(Parameters(target=22))['status']=='asymptotic'
assert target_time(Parameters(target=100))['status']=='unreachable'
print('Model checks passed: target time, numerical comparison and unreachable targets.')''')
md('''## 5. Create your own experiment

Choose a preset, change a field and press **Calculate experiment**. The displayed
result and exports always describe the last calculated settings, not unsubmitted
edits. Change one value at a time to understand its effect.

- **Cooling coefficient:** a larger value approaches room temperature faster.
- **Calculation step:** the gap between numerical calculations, in minutes.
- **Chosen temperature:** a target for the exact crossing-time calculation.
- **Half-life:** time for the difference from room temperature to halve. This does
  not mean halving a Celsius temperature.
''')
code('''controls={}
labels={'initial':'Start (°C)','ambient':'Room (°C)','coefficient':'k (per min)',
        'duration':'Duration (min)','step':'Step (min)','target':'Target (°C)'}
for key in Parameters.__dataclass_fields__:
    controls[key]=widgets.FloatText(value=asdict(Parameters())[key],description=labels[key],
        style={'description_width':'110px'},layout=widgets.Layout(width='285px'))
preset_picker=widgets.Dropdown(options=[(p['name'],p['id']) for p in PRESETS],
                               description='Experiment:',layout=widgets.Layout(width='360px'))
calculate_button=widgets.Button(description='Calculate experiment',button_style='success',layout=widgets.Layout(width='190px'))
csv_button=widgets.Button(description='Download CSV')
settings_button=widgets.Button(description='Download settings')
result_output=widgets.Output()
export_output=widgets.Output()
last_result={'value':default_result}

def choose_preset(change):
    p=next(p for p in PRESETS if p['id']==change['new'])
    for key,value in p['parameters'].items():controls[key].value=value

def calculate_clicked(_=None):
    with result_output:
        clear_output(wait=True)
        try:
            result=simulate({key:widget.value for key,widget in controls.items()})
        except InputError as error:
            print('Please check your inputs:',error)
            print('Downloads still refer to the last successful calculation.')
            return
        last_result['value']=result
        p=result['parameters'];s=result['summary'];target=s['target']
        print(f"Calculated: start {p['initial']:g}°C, room {p['ambient']:g}°C, k={p['coefficient']:g}, step={p['step']:g} min")
        print(f"Final reference temperature: {s['final_temperature']:.4f}°C")
        if target['minutes'] is not None:print(f"Chosen temperature reached at {target['minutes']:.4f} min. {target['message']}")
        else:print(target['message'])
        plot_experiment(result)
        print('First six numerical samples:')
        print(f"{'min':>9} {'exact °C':>13} {'Euler °C':>13} {'RK4 °C':>13}")
        for row in result['samples'][:6]:
            values=[f"{row[key]:.5f}" if row[key] is not None else 'unavailable' for key in ['exact','euler','rk4']]
            print(f"{row['time']:9.3f} {values[0]:>13} {values[1]:>13} {values[2]:>13}")

def save_export(kind):
    result=last_result['value'];folder=Path('thermolab_exports');folder.mkdir(exist_ok=True)
    if kind=='csv':
        target=folder/'ThermoLab-results.csv'
        with target.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream)
            writer.writerow(['time_min','exact_C','euler_C','rk4_C','abs_error_euler_C','abs_error_rk4_C',
                             'initial_C','ambient_C','coefficient_per_min','duration_min','calculation_step_min','target_C'])
            for row in result['samples']:
                writer.writerow([row[key] for key in ['time','exact','euler','rk4','euler_error','rk4_error']]+
                                [result['parameters'][key] for key in Parameters.__dataclass_fields__])
    else:
        target=folder/'ThermoLab-settings.json'
        target.write_text(json.dumps({'application':'ThermoLab','schema_version':1,'parameters':result['parameters']},indent=2),encoding='utf-8')
    with export_output:
        clear_output(wait=True)
        try:
            from google.colab import files
        except ImportError:
            display(FileLink(str(target)))
        else:
            files.download(str(target))

preset_picker.observe(choose_preset,names='value')
calculate_button.on_click(calculate_clicked)
csv_button.on_click(lambda _:save_export('csv'))
settings_button.on_click(lambda _:save_export('json'))
display(widgets.VBox([preset_picker,
    widgets.HBox([widgets.VBox([controls['initial'],controls['coefficient'],controls['step']]),
                  widgets.VBox([controls['ambient'],controls['duration'],controls['target']])]),
    widgets.HBox([calculate_button,csv_button,settings_button]),result_output,export_output]))
calculate_clicked()''')
md('''## 6. One question to investigate

Keep everything else fixed and halve $k$. What happens to the time needed to halve
the temperature difference? The calculation below checks the relationship with
the exact solution. Try the same comparison in the website.
''')
code('''original=Parameters()
slower=Parameters(coefficient=original.coefficient/2)
first=math.log(2)/original.coefficient
second=math.log(2)/slower.coefficient
print(f"Original half-life: {first:.4f} min")
print(f"Half the coefficient: {second:.4f} min")
assert math.isclose(second,2*first)
print('Halving the coefficient doubles the half-life of the difference.')''')
md('''## References and practical limits

- [OpenStax: Exponential and logarithmic models, including Newton cooling](https://openstax.org/books/algebra-and-trigonometry-2e/pages/6-7-exponential-and-logarithmic-models)
- [OpenStax: Basics of differential equations](https://openstax.org/books/calculus-volume-2/pages/4-1-basics-of-differential-equations)
- [Google Colab FAQ](https://research.google.com/colaboratory/faq.html)

Sources checked 17 November 2026. Colab resources and runtimes are temporary.
Download the notebook, results and settings before disconnecting. Widgets need a
connected Python runtime. Saved plots remain useful without an active runtime.
This notebook runs in the normal notebook interface and does not need a website
tunnel. The separate local ThermoLab website uses the same calculation engine.

The project demonstrates a first-order differential-equation model and numerical
approximations. It does not claim to cover every Computational Mathematics experiment.
''')

notebook=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12'},'colab':{'provenance':[]}})
nb.validate(notebook)
nb.write(notebook,ROOT/'ThermoLab.ipynb')
print('Built ThermoLab.ipynb with',len(cells),'cells')
