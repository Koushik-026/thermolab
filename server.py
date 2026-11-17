"""Local HTTP adapter. Hosting uses the same application through Gunicorn."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
from app import MAX_BODY, handle_request, problem

class Handler(BaseHTTPRequestHandler):
    def respond(self):
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:length=-1
        if self.command=='POST' and not 0<length<=MAX_BODY:
            status,headers,data=problem(413,'Experiment settings must be smaller than 16 KB.')
        else:
            body=self.rfile.read(length) if self.command=='POST' else b''
            status,headers,data=handle_request(self.command,self.path,body,
                self.headers.get('Content-Type',''),self.headers.get('Origin',''),self.headers.get('Host',''))
        self.send_response(status)
        for key,value in headers:self.send_header(key,value)
        self.end_headers()
        if self.command!='HEAD':self.wfile.write(data)
    do_GET=respond
    do_HEAD=respond
    do_POST=respond

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=3201)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'ThermoLab is ready at http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
