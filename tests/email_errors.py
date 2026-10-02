"""Provider rejection diagnostics use mocked HTTP, without sending mail."""
from v4 import *
import urllib.error, json
from unittest.mock import patch
cases=[(401,'unauthorized','Key not found','EMAIL_AUTH'),(401,'unauthorized','IP address is not authorized','EMAIL_IP'),(400,'invalid_parameter','sender email is invalid','EMAIL_SENDER'),(403,'permission_denied','Permission denied','EMAIL_PERMISSION'),(429,'too_many_requests','Rate limit reached','EMAIL_LIMIT')]
for status,code,message,reference in cases:
 body=json.dumps({'code':code,'message':message+' PRIVATE-DO-NOT-EXPOSE'}).encode()
 error=urllib.error.HTTPError('https://api.brevo.com/v3/smtp/email',status,'Rejected',{},io.BytesIO(body))
 with app.app_context(),patch('urllib.request.urlopen',side_effect=error):
  try:m.brevo_send_otp('recipient@example.test','123456');raise AssertionError('Expected error')
  except RuntimeError as exc:assert reference in str(exc)
 report=admin.get('/api/admin/email-status').json
 assert reference in report['status']['message']
 assert 'PRIVATE-DO-NOT-EXPOSE' not in str(report) and '123456' not in str(report) and 'test-secret' not in str(report)
print('PASS: API authentication, IP blocking, sender, permissions and quota diagnostics without exposing provider messages, keys or OTPs.')
