"""Stateless WSGI application shared by local and hosted servers."""
from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json, mimetypes
from core import InputError, PRESETS, simulate

ROOT=Path(__file__).resolve().parent
WEB=ROOT/'web'
MAX_BODY=16384

def response(status,data,content_type='application/json; charset=utf-8',extra=()):
    if isinstance(data,(dict,list)):
        data=json.dumps(data,allow_nan=False,separators=(',',':')).encode('utf-8')
    headers=[('Content-Type',content_type),('Content-Length',str(len(data))),
             ('X-Content-Type-Options','nosniff'),('Cache-Control','no-store'),
             ('Referrer-Policy','no-referrer'),
             ('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")]
    return status,headers+list(extra),data

def problem(status,message):return response(status,{'error':message})

def handle_request(method,path,body=b'',content_type='',origin='',host=''):
    path=unquote(urlsplit(path).path)
    if method in ('GET','HEAD'):
        if path=='/api/health':return response(200,{'status':'ready','engine':'Python','model':'Newton cooling','version':1})
        if path=='/api/presets':return response(200,{'presets':PRESETS})
        if path=='/ThermoLab.ipynb':target=ROOT/'ThermoLab.ipynb'
        else:
            target=(WEB/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            if not target.is_relative_to(WEB.resolve()):return problem(404,'That page was not found.')
        if not target.is_file():return problem(404,'That page was not found.')
        file_type={'.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.html':'text/html',
                   '.ipynb':'application/x-ipynb+json'}.get(target.suffix,mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        return response(200,target.read_bytes(),file_type+('; charset=utf-8' if file_type.startswith('text/') else ''))
    if method!='POST':return response(405,{'error':'Use GET or POST for this application.'},extra=[('Allow','GET, HEAD, POST')])
    if path!='/api/simulate':return problem(404,'That action was not found.')
    if origin and origin not in (f'http://{host}',f'https://{host}'):
        return problem(403,'Open this experiment on the ThermoLab website.')
    if content_type.split(';')[0].strip()!='application/json':return problem(415,'Send experiment settings as JSON.')
    if not 0<len(body)<=MAX_BODY:return problem(413,'Experiment settings must be smaller than 16 KB.')
    try:values=json.loads(body)
    except (ValueError,UnicodeError):return problem(400,'Enter valid JSON experiment settings.')
    try:return response(200,simulate(values))
    except InputError as error:return problem(400,str(error))
    except (ValueError,OverflowError):return problem(400,'Use a larger cooling coefficient. This time estimate is beyond the numerical range.')

def application(environ,start_response):
    method=environ.get('REQUEST_METHOD','GET')
    try:length=int(environ.get('CONTENT_LENGTH') or 0)
    except ValueError:length=-1
    if method=='POST' and not 0<length<=MAX_BODY:
        result=problem(413,'Experiment settings must be smaller than 16 KB.')
    else:
        body=environ['wsgi.input'].read(length) if method=='POST' else b''
        result=handle_request(method,environ.get('PATH_INFO','/'),body,environ.get('CONTENT_TYPE',''),
                              environ.get('HTTP_ORIGIN',''),environ.get('HTTP_HOST',environ.get('SERVER_NAME','')))
    status,headers,data=result
    start_response(f'{status} {HTTPStatus(status).phrase}',headers)
    return [b'' if method=='HEAD' else data]
