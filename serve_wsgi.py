"""Local verification of the hosted WSGI application without Unix Gunicorn."""
from wsgiref.simple_server import make_server
from app import application
if __name__=='__main__':
    with make_server('127.0.0.1',3202,application) as server:
        print('ThermoLab WSGI check: http://127.0.0.1:3202',flush=True)
        server.serve_forever()
