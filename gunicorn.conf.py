"""Small stateless showcase. No persistent storage or account secrets."""
import os
bind='0.0.0.0:'+os.environ.get('PORT','10000')
workers=1
threads=4
timeout=30
graceful_timeout=20
accesslog='-'
errorlog='-'
max_requests=1500
max_requests_jitter=100
