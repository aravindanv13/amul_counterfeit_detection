"""Single-worker OCR deployment for Render's small free instance."""

import os

bind = f"0.0.0.0:{int(os.environ.get('PORT', '5000'))}"
workers = 1
threads = 1
# OCR can be slow on shared CPUs. Avoid concurrent large image allocations.
timeout = 180
graceful_timeout = 30
max_requests = 50
max_requests_jitter = 5
accesslog = "-"
errorlog = "-"
capture_output = True
