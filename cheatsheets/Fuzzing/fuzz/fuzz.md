# Директории
ffuf -w /usr/share/wordlists/wfuzz/general/common.txt -u http://10.80.160.76/FUZZ

# Фильтрация
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-small-directories.txt \              
-u http://10.80.160.76/FUZZ \
-fc 404 -fs 0

# Поддомены
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
-u http://FUZZ.10.80.160.76/ \
-fc 404 -fs 0 -t 50


# Фазинг параметров запроса, фильр -hh длина chars 45 отлична от 45:
wfuzz -X POST -u "http://10.82.161.140/api/items?FUZZ=test" -H "Cookie: token=this_is_not_real" -w /usr/share/wordlists/SecLists/Discovery/Web-Content/burp-parameter-names.txt --hh 45