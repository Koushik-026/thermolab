import json, math, random, threading, unittest
import io
from dataclasses import asdict
from decimal import Decimal, localcontext
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from core import Parameters, InputError, PRESETS, exact, simulate, target_time
from server import Handler
from app import application


def run(**changes):
    return simulate(asdict(Parameters(**changes)))


class Mathematics(unittest.TestCase):
    def test_default_against_decimal_reference(self):
        result=run()
        with localcontext() as ctx:
            ctx.prec=45
            expected=Decimal(22)+Decimal(63)*Decimal('-2.7').exp()
        self.assertAlmostEqual(result['summary']['final_temperature'],float(expected),places=12)
        self.assertEqual(result['samples'][0]['exact'],85)
        self.assertEqual(result['samples'][-1]['time'],60)

    def test_cooling_is_monotone_and_bounded(self):
        values=[s['exact'] for s in run()['samples']]
        self.assertTrue(all(22<t<=85 for t in values))
        self.assertTrue(all(a>b for a,b in zip(values,values[1:])))

    def test_warming_is_monotone_and_bounded(self):
        result=run(initial=5,ambient=24,coefficient=.055,target=20)
        values=[s['exact'] for s in result['samples']]
        self.assertEqual(result['summary']['direction'],'warming')
        self.assertTrue(all(a<b for a,b in zip(values,values[1:])))
        time=result['summary']['target']['minutes']
        self.assertAlmostEqual(exact(Parameters(initial=5,ambient=24,coefficient=.055),time),20)

    def test_half_life_halves_difference(self):
        p=Parameters();half=math.log(2)/p.coefficient
        self.assertAlmostEqual(exact(p,half)-p.ambient,(p.initial-p.ambient)/2)
        self.assertAlmostEqual(run(coefficient=.0225)['summary']['half_life'],2*run()['summary']['half_life'])

    def test_target_classifications(self):
        for target,status in [(85,'at_start'),(22,'asymptotic'),(45,'within_run'),(23,'after_run'),(90,'unreachable'),(10,'unreachable')]:
            self.assertEqual(target_time(Parameters(target=target))['status'],status)

    def test_constant_temperature_cases(self):
        for changes in [dict(coefficient=0),dict(initial=22,ambient=22)]:
            r=run(**changes)
            self.assertEqual(r['summary']['direction'],'steady')
            self.assertTrue(all(s['exact']==s['euler']==s['rk4'] for s in r['samples']))
        self.assertIsNone(run(coefficient=0)['summary']['half_life'])
        self.assertEqual(run(coefficient=0,target=85)['summary']['target']['status'],'at_start')

    def test_first_euler_and_rk4_step(self):
        f=run()['summary']['first_step']
        self.assertAlmostEqual(f['euler_next'],82.165)
        q=.045;amplification=1-q+q*q/2-q**3/6+q**4/24
        self.assertAlmostEqual(f['rk4_next'],22+63*amplification)
        self.assertLess(abs(f['rk4_next']-f['exact_next']),abs(f['euler_next']-f['exact_next']))

    def test_convergence_rates(self):
        a=run(coefficient=.2,duration=10,step=1)['summary']['methods']
        b=run(coefficient=.2,duration=10,step=.5)['summary']['methods']
        self.assertGreater(a['euler']['final_abs_error']/b['euler']['final_abs_error'],1.9)
        self.assertGreater(a['rk4']['final_abs_error']/b['rk4']['final_abs_error'],14)

    def test_shortened_last_step(self):
        r=run(duration=10,step=3)
        self.assertEqual([s['time'] for s in r['samples']],[0,3,6,9,10])
        self.assertAlmostEqual(r['samples'][-1]['euler'],22+63*(1-.045*3)**3*(1-.045))
        edge=run(duration=1.0000000000000002,step=.1)
        self.assertEqual(edge['samples'][-1]['time'],edge['parameters']['duration'])

    def test_step_longer_than_experiment(self):
        r=run(duration=1,step=20)
        self.assertEqual(len(r['samples']),2)
        self.assertEqual(r['summary']['first_step']['h'],1)
        self.assertAlmostEqual(r['summary']['methods']['euler']['amplification'],.955)

    def test_stability_cases(self):
        cases=[(.07,20,'oscillating'),(.1,10,'one_step_equilibrium'),(.1,20,'neutral'),(.2,20,'unstable')]
        for k,h,status in cases:
            r=run(coefficient=k,step=h)
            self.assertEqual(r['summary']['methods']['euler']['stability'],status)
            self.assertTrue(r['warnings'])

    def test_overflow_is_reported_not_clamped(self):
        r=run(coefficient=1,step=5,duration=240)
        self.assertIsNotNone(r['summary']['methods']['euler']['truncated_at'])
        self.assertIsNotNone(r['summary']['methods']['rk4']['truncated_at'])
        self.assertIsNone(r['samples'][-1]['euler'])
        self.assertIsNone(r['summary']['methods']['euler']['max_abs_error'])
        self.assertGreaterEqual(r['samples'][-1]['exact'],22)
        json.dumps(r,allow_nan=False)

    def test_reference_stays_smooth_at_coarse_steps(self):
        r=run(step=20)
        self.assertEqual(len(r['reference']),401)
        self.assertEqual(r['reference'][0]['time'],0)
        self.assertEqual(r['reference'][-1]['time'],60)

    def test_invalid_values(self):
        defaults=asdict(Parameters())
        for value in [True,None,'85',float('nan'),float('inf'),[],{}]:
            with self.assertRaises(InputError):simulate({**defaults,'initial':value})
        for key,value in [('initial',201),('ambient',-51),('coefficient',-1),('duration',0),('step',.001),('target',201)]:
            with self.assertRaises(InputError):simulate({**defaults,key:value})
        for value in [{},[],None,{**defaults,'unknown':1}]:
            with self.assertRaises(InputError):simulate(value)

    def test_random_time_grids_and_finite_outputs(self):
        rng=random.Random(2718)
        for _ in range(60):
            r=run(duration=rng.uniform(1,240),step=rng.uniform(.1,30),coefficient=rng.uniform(0,.04))
            times=[s['time'] for s in r['samples']]
            self.assertEqual(times[-1],r['parameters']['duration'])
            self.assertTrue(all(a<b for a,b in zip(times,times[1:])))
            for s in r['samples']:
                self.assertGreaterEqual(s['euler_error'],0)
                self.assertGreaterEqual(s['rk4_error'],0)
            json.dumps(r,allow_nan=False)

    def test_all_presets_reproduce(self):
        for preset in PRESETS:
            r=simulate(preset['parameters'])
            self.assertEqual(r['parameters'],preset['parameters'])
            self.assertGreater(len(r['samples']),1)


class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()

    def request(self,path,body=None,headers=None):
        request=Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers or ({'Content-Type':'application/json'} if body is not None else {}))
        try:
            with urlopen(request,timeout=5) as response:return response.status,response.read(),response.headers
        except HTTPError as e:return e.code,e.read(),e.headers

    def test_health_and_initial_presets(self):
        status,body,_=self.request('/api/health');self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['engine'],'Python')
        self.assertEqual(len(json.loads(self.request('/api/presets')[1])['presets']),4)

    def test_full_calculation_round_trip(self):
        status,body,_=self.request('/api/simulate',asdict(Parameters()))
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['parameters'],asdict(Parameters()))

    def test_input_errors_are_readable(self):
        status,body,_=self.request('/api/simulate',{'initial':1})
        self.assertEqual(status,400);self.assertIn('error',json.loads(body))

    def test_unrepresentable_time_is_a_readable_error(self):
        status,body,_=self.request('/api/simulate',{**asdict(Parameters()),'coefficient':1e-320})
        self.assertEqual(status,400)
        self.assertIn('numerical range',json.loads(body)['error'])

    def test_private_files_and_unknown_paths_unavailable(self):
        for path in ['/core.py','/../core.py','/%2e%2e/core.py','/data/anything','/api/missing']:
            self.assertEqual(self.request(path)[0],404)

    def test_origin_and_content_type(self):
        self.assertEqual(self.request('/api/simulate',asdict(Parameters()),{'Content-Type':'application/json','Origin':'http://elsewhere.invalid'})[0],403)
        self.assertEqual(self.request('/api/simulate',asdict(Parameters()),{'Content-Type':'text/plain'})[0],415)

    def test_assets_and_security_headers(self):
        for path in ['/','/app.js','/style.css','/mark.svg']:
            status,body,headers=self.request(path)
            self.assertEqual(status,200);self.assertGreater(len(body),10)
            self.assertIn("default-src 'self'",headers['Content-Security-Policy'])


class HostedApplication(unittest.TestCase):
    def call(self,method,path,body=b'',**extra):
        environ={'REQUEST_METHOD':method,'PATH_INFO':path,'wsgi.input':io.BytesIO(body),
                 'CONTENT_LENGTH':str(len(body)),'CONTENT_TYPE':'application/json',
                 'HTTP_HOST':'thermolab.example','HTTP_ORIGIN':'https://thermolab.example',**extra}
        captured={}
        def start(status,headers):captured.update(status=status,headers=dict(headers))
        captured['body']=b''.join(application(environ,start))
        return captured

    def test_https_origin_calculates(self):
        result=self.call('POST','/api/simulate',json.dumps(asdict(Parameters())).encode())
        self.assertEqual(result['status'],'200 OK')
        self.assertEqual(json.loads(result['body'])['parameters'],asdict(Parameters()))

    def test_origin_rejection_and_body_limit(self):
        payload=json.dumps(asdict(Parameters())).encode()
        self.assertEqual(self.call('POST','/api/simulate',payload,HTTP_ORIGIN='https://other.example')['status'],'403 Forbidden')
        self.assertEqual(self.call('POST','/api/simulate',payload,CONTENT_LENGTH='20000')['status'],'413 Request Entity Too Large')

    def test_head_and_methods(self):
        result=self.call('HEAD','/')
        self.assertEqual(result['status'],'200 OK');self.assertEqual(result['body'],b'')
        self.assertGreater(int(result['headers']['Content-Length']),100)
        self.assertEqual(self.call('DELETE','/api/simulate')['status'],'405 Method Not Allowed')

    def test_platform_independent_asset_types(self):
        self.assertTrue(self.call('GET','/app.js')['headers']['Content-Type'].startswith('text/javascript'))
        self.assertEqual(self.call('GET','/ThermoLab.ipynb')['headers']['Content-Type'],'application/x-ipynb+json')


if __name__=='__main__':unittest.main(verbosity=2)
