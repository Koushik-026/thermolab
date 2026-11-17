"""Open the local experiment and keep its calculation server in this terminal."""
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
import json, webbrowser
from server import Handler

url='http://127.0.0.1:3201'
try:
    with urlopen(url+'/api/health',timeout=1) as response:
        existing=json.load(response)
        if existing.get('model')=='Newton cooling' and existing.get('engine')=='Python':
            webbrowser.open(url)
            print('ThermoLab is already running at',url)
            raise SystemExit(0)
except (OSError, ValueError):
    pass
try:
    server=ThreadingHTTPServer(('127.0.0.1',3201),Handler)
except OSError:
    print('Port 3201 is in use. Run: python server.py --port 3202')
    input('Press Enter to close.')
    raise SystemExit(1)
print('ThermoLab is ready at',url)
print('Keep this terminal open. Press Ctrl+C to stop.')
webbrowser.open(url)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
