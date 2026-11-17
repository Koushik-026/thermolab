"""Newton cooling and numerical approximations. Units: Celsius and minutes."""
from dataclasses import asdict, dataclass
import math

VERSION = 1
LIMIT = 100_000_000.0


class InputError(ValueError):
    pass


@dataclass(frozen=True)
class Parameters:
    initial: float = 85
    ambient: float = 22
    coefficient: float = 0.045
    duration: float = 60
    step: float = 1
    target: float = 45

    @classmethod
    def parse(cls, values):
        if not isinstance(values, dict):
            raise InputError('Experiment settings must be an object.')
        fields = cls.__dataclass_fields__
        if set(values) != set(fields):
            raise InputError('Provide exactly initial, ambient, coefficient, duration, step and target.')
        ranges = {'initial': (-50, 200), 'ambient': (-50, 200),
                  'coefficient': (0, 1), 'duration': (1, 240),
                  'step': (0.05, 30), 'target': (-50, 200)}
        cleaned = {}
        labels = {'initial': 'Starting temperature', 'ambient': 'Room temperature',
                  'coefficient': 'Cooling coefficient', 'duration': 'Duration',
                  'step': 'Calculation step', 'target': 'Chosen temperature'}
        for key, (lower, upper) in ranges.items():
            value = values[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise InputError(f'{labels[key]} must be a finite number.')
            if not lower <= value <= upper:
                raise InputError(f'{labels[key]} must be between {lower} and {upper}.')
            cleaned[key] = float(value)
        if math.ceil(cleaned['duration'] / cleaned['step']) > 5000:
            raise InputError('Use a larger step to keep the experiment within 5,000 intervals.')
        return cls(**cleaned)


PRESETS = [
    {'id': 'warm-cup', 'name': 'The warm cup', 'description': 'A hot cup in a cooler room.',
     'tag': 'Start here', 'parameters': asdict(Parameters())},
    {'id': 'slow-cooling', 'name': 'A slower cool', 'description': 'Same start. A smaller cooling rate.',
     'tag': 'Compare rates', 'parameters': asdict(Parameters(coefficient=0.02, duration=120, step=2))},
    {'id': 'cold-object', 'name': 'From the cold', 'description': 'A cold object warms towards the room.',
     'tag': 'Reverse the story', 'parameters': asdict(Parameters(initial=5, ambient=24, coefficient=0.055, duration=60, target=20))},
    {'id': 'large-steps', 'name': 'The big-step test', 'description': 'See why the calculation step matters.',
     'tag': 'Numerical experiment', 'parameters': asdict(Parameters(coefficient=0.07, duration=90, step=20))},
]


def exact(p, time):
    return p.ambient + (p.initial - p.ambient) * math.exp(-p.coefficient * time)


def target_time(p):
    if p.target == p.initial:
        return {'status': 'at_start', 'minutes': 0.0, 'message': 'The object starts at the chosen temperature.'}
    if p.initial == p.ambient or p.coefficient == 0:
        return {'status': 'unreachable', 'minutes': None, 'message': 'The temperature stays constant in this experiment.'}
    if p.target == p.ambient:
        return {'status': 'asymptotic', 'minutes': None,
                'message': 'The model approaches room temperature without reaching it at a finite time.'}
    ratio = (p.target - p.ambient) / (p.initial - p.ambient)
    if not 0 < ratio < 1:
        return {'status': 'unreachable', 'minutes': None,
                'message': 'Choose a temperature strictly between the starting and room temperatures.'}
    time = -math.log(ratio) / p.coefficient
    return {'status': 'within_run' if time <= p.duration else 'after_run', 'minutes': time,
            'message': 'Reached within this experiment.' if time <= p.duration else 'Reached after the displayed duration.'}


def stability(factor, q, method):
    if q == 0:
        return 'constant'
    if abs(factor) > 1 + 1e-12:
        return 'unstable'
    if abs(abs(factor) - 1) <= 1e-12:
        return 'neutral'
    if factor < 0:
        return 'oscillating'
    if factor == 0:
        return 'one_step_equilibrium'
    return 'decaying'


def simulate(values):
    p = Parameters.parse(values)
    count = math.ceil(math.nextafter(p.duration / p.step, -math.inf))
    euler = rk4 = p.initial
    truncation = {'euler': None, 'rk4': None}
    samples = []
    first_step = None
    for index in range(count + 1):
        time = p.duration if index == count else index * p.step
        reference = exact(p, time)
        samples.append({'time': time, 'exact': reference, 'euler': euler, 'rk4': rk4,
                        'euler_error': abs(euler-reference) if euler is not None else None,
                        'rk4_error': abs(rk4-reference) if rk4 is not None else None})
        if index == count:
            break
        next_time = p.duration if index+1 == count else (index+1)*p.step
        h = next_time-time
        if euler is not None:
            euler = euler + h * (-p.coefficient * (euler-p.ambient))
        if rk4 is not None:
            f = lambda temperature: -p.coefficient * (temperature-p.ambient)
            a = f(rk4)
            b = f(rk4+h*a/2)
            c = f(rk4+h*b/2)
            d = f(rk4+h*c)
            rk4 = rk4 + h*(a+2*b+2*c+d)/6
            if first_step is None:
                first_step = {'h': h, 'slope': a, 'k1': a, 'k2': b, 'k3': c, 'k4': d,
                              'euler_next': euler, 'rk4_next': rk4, 'exact_next': exact(p, next_time)}
        if euler is not None and (not math.isfinite(euler) or abs(euler) > LIMIT):
            euler = None
            truncation['euler'] = next_time
        if rk4 is not None and (not math.isfinite(rk4) or abs(rk4) > LIMIT):
            rk4 = None
            truncation['rk4'] = next_time
    q = p.coefficient * min(p.step, p.duration)
    factor_euler = 1-q
    factor_rk4 = 1-q+q*q/2-q**3/6+q**4/24
    warnings = []
    methods = {}
    for name, factor in [('euler', factor_euler), ('rk4', factor_rk4)]:
        state = stability(factor, q, name)
        errors = [s[name+'_error'] for s in samples if s[name+'_error'] is not None]
        methods[name] = {'amplification': factor, 'stability': state,
                         'max_abs_error': None if truncation[name] is not None else max(errors),
                         'final_abs_error': samples[-1][name+'_error'], 'truncated_at': truncation[name]}
        label = 'Euler' if name == 'euler' else 'RK4'
        if state in ('oscillating', 'neutral', 'unstable', 'one_step_equilibrium'):
            descriptions = {'oscillating': 'crosses room temperature because the step is too large for a monotone estimate',
                            'neutral': 'does not reduce the temperature difference with this step',
                            'unstable': 'amplifies numerical errors with this step',
                            'one_step_equilibrium': 'jumps to room temperature in one step'}
            warnings.append(f'{label} {descriptions[state]}. This is a numerical effect, not the physical reference motion.')
        if truncation[name] is not None:
            warnings.append(f'{label} exceeds the {LIMIT:g} °C calculation limit at {truncation[name]:g} min. Later values are unavailable.')
    reference = [{'time': p.duration*i/400, 'exact': exact(p, p.duration*i/400)} for i in range(401)]
    return {'schema_version': VERSION, 'parameters': asdict(p), 'samples': samples, 'reference': reference,
            'summary': {'direction': 'steady' if p.initial == p.ambient or p.coefficient == 0 else ('cooling' if p.initial > p.ambient else 'warming'),
                        'half_life': math.log(2)/p.coefficient if p.coefficient else None,
                        'final_temperature': samples[-1]['exact'], 'target': target_time(p),
                        'steps': count, 'methods': methods, 'first_step': first_step},
            'warnings': warnings}
