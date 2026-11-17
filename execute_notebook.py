"""Execute the self-contained teaching notebook in a fresh Python kernel."""
import asyncio,json,os,sys,time
from pathlib import Path
import nbformat
from nbclient import NotebookClient
if sys.platform=='win32':asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
root=Path(__file__).resolve().parent
kernel=root/'output/jupyter/kernels/thermolab-local';kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'ThermoLab validation','language':'python'}))
os.environ['JUPYTER_PATH']=str(root/'output/jupyter')
os.environ['JUPYTER_RUNTIME_DIR']=str(root/'output/jupyter-runtime')
Path(os.environ['JUPYTER_RUNTIME_DIR']).mkdir(exist_ok=True)
work=root/'output/notebook-run';work.mkdir(exist_ok=True)
book=nbformat.read(root/'ThermoLab.ipynb',as_version=4)
start=time.perf_counter()
client=NotebookClient(book,timeout=180,startup_timeout=120,kernel_name='thermolab-local',resources={'metadata':{'path':str(work)}})
client.on_cell_start=lambda cell,cell_index:print('Executing cell',cell_index+1,flush=True)
client.execute();nbformat.validate(book);nbformat.write(book,root/'ThermoLab.ipynb')
summary={'code_cells':sum(c.cell_type=='code' for c in book.cells),'error_outputs':sum(o.output_type=='error' for c in book.cells if c.cell_type=='code' for o in c.outputs),'elapsed_seconds':round(time.perf_counter()-start,2)}
(root/'output/notebook-validation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
