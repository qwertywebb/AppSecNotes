╔══════════╦════════╦══════════════════════════════╦═══════════════════════════════════════╗
║ Порт     ║ Протокол║ Название службы              ║ Типичное использование                 ║
╠══════════╬════════╬══════════════════════════════╬═══════════════════════════════════════╣
║ 20/21    ║ TCP    ║ FTP (File Transfer Protocol) ║ Передача файлов (данные/управление)   ║
║ 22       ║ TCP    ║ SSH (Secure Shell)           ║ Удаленное управление (безопасное)      ║
║ 23       ║ TCP    ║ Telnet                       ║ Удаленное управление (небезопасно)     ║
║ 25       ║ TCP    ║ SMTP                         ║ Отправка почты                         ║
║ 53       ║ TCP/UDP║ DNS                          ║ Система доменных имен                  ║
║ 67/68    ║ UDP    ║ DHCP                         ║ Назначение IP-адресов                  ║
║ 80       ║ TCP    ║ HTTP                         ║ Веб-сайты (без шифрования)             ║
  88         tcp/udp  Kerberos                       Протокол авторизации Active Directory
║ 110      ║ TCP    ║ POP3                         ║ Получение почты                        ║
║ 123      ║ UDP    ║ NTP                          ║ Синхронизация времени                  ║
║ 137-139  ║ TCP/UDP║ NetBIOS                      ║ Общий доступ в Windows                 ║
║ 143      ║ TCP    ║ IMAP                         ║ Доступ к почте на сервере              ║
║ 161/162  ║ UDP    ║ SNMP                         ║ Мониторинг сети                        ║
║ 389      ║ TCP    ║ LDAP                         ║ Службы каталогов                       ║
║ 443      ║ TCP    ║ HTTPS                        ║ Веб-сайты (с шифрованием)              ║
║ 445      ║ TCP    ║ SMB                          ║ Общий доступ Windows (файлы/принтеры)  ║
  464        TCP/UDP  KPASSWD                        Kerberos смена паролей
║ 465/587  ║ TCP    ║ SMTP с шифрованием           ║ Отправка почты (безопасно)             ║
║ 500      ║ UDP    ║ ISAKMP/IPsec                 ║ VPN                                     ║
║ 514      ║ UDP    ║ Syslog                       ║ Сбор логов системы                     ║
║ 546/547  ║ UDP    ║ DHCPv6                       ║ Назначение IPv6                        ║
║ 631      ║ TCP/UDP║ IPP                          ║ Печать через интернет                  ║
║ 636      ║ TCP    ║ LDAPS                        ║ LDAP с шифрованием                     ║
║ 990/989  ║ TCP    ║ FTPS                         ║ FTP с шифрованием                      ║
║ 993      ║ TCP    ║ IMAPS                        ║ IMAP с шифрованием                     ║
║ 995      ║ TCP    ║ POP3S                        ║ POP3 с шифрованием                     ║
║ 1194     ║ TCP/UDP║ OpenVPN                      ║ VPN                                     ║
║ 1433     ║ TCP    ║ MSSQL                        ║ База данных Microsoft SQL              ║
║ 1701     ║ UDP    ║ L2TP                         ║ VPN                                     ║
║ 1723     ║ TCP    ║ PPTP                         ║ VPN (устаревший)                       ║
║ 2049     ║ TCP/UDP║ NFS                          ║ Сетевые файловые системы               ║
║ 2082/2083║ TCP    ║ cPanel                       ║ Хостинг-панель (обычный/SSL)           ║
║ 2181     ║ TCP    ║ ZooKeeper                    ║ Координация распределенных систем      ║
║ 2375/2376║ TCP    ║ Docker                       ║ API Docker (без TLS/с TLS)             ║
║ 2424     ║ TCP    ║ OrientDB                     ║ База данных OrientDB                   ║
║ 2480     ║ TCP    ║ OrientDB HTTP                ║ Веб-интерфейс OrientDB                 ║
║ 3000     ║ TCP    ║ Development                   ║ Часто для Node.js/React/Grafana        ║
║ 3306     ║ TCP    ║ MySQL                        ║ База данных MySQL                      ║
║ 3389     ║ TCP    ║ RDP                          ║ Удаленный рабочий стол Windows         ║
║ 3690     ║ TCP/UDP║ SVN                          ║ Subversion (система контроля версий)   ║
║ 4000      ║ TCP    ║ Grafana                      ║ Визуализация метрик                    ║
║ 4369     ║ TCP    ║ EPMD                         ║ Erlang Port Mapper                     ║
║ 4444     ║ TCP    ║ Metasploit/Вредоносы         ║ Бэкдоры/эксплойты                      ║
║ 4500     ║ UDP    ║ IPsec NAT-T                  ║ VPN (прохождение через NAT)            ║
║ 4567     ║ TCP    ║ FileBeat                      ║ Сбор логов ELK                         ║
║ 4789     ║ UDP    ║ VXLAN                        ║ Виртуальные сети                       ║
║ 5000      ║ TCP    ║ UPnP/Промышленные системы    ║ Часто в Docker/Traefik                 ║
║ 5432     ║ TCP    ║ PostgreSQL                   ║ База данных PostgreSQL                 ║
║ 5500     ║ TCP    ║ VNC                          ║ Удаленный рабочий стол                 ║
║ 5601     ║ TCP    ║ Kibana                       ║ Визуализация логов ELK                 ║
║ 5672     ║ TCP    ║ AMQP                         ║ RabbitMQ/очереди сообщений             ║
║ 5800     ║ TCP    ║ VNC через HTTP               ║ VNC в браузере                         ║
║ 5900     ║ TCP/UDP║ VNC                          ║ Удаленный рабочий стол                 ║
║ 5984     ║ TCP    ║ CouchDB                      ║ База данных CouchDB                    ║
║ 6000     ║ TCP    ║ X11                          ║ Оконная система Linux                  ║
║ 6080     ║ TCP    ║ Apache Ambari                ║ Управление Hadoop                      ║
║ 6379     ║ TCP    ║ Redis                        ║ Кэш/база данных                        ║
║ 6443     ║ TCP    ║ Kubernetes API               ║ Управление кластером K8s               ║
║ 6660-6669║ TCP    ║ IRC                          ║ Интернет-чат                           ║
║ 6881-6889║ TCP/UDP║ BitTorrent                   ║ P2P-файлообмен                         ║
║ 7000-7001║ TCP    ║ Cassandra                    ║ База данных Cassandra                  ║
║ 7199     ║ TCP    ║ Cassandra JMX                ║ Мониторинг Cassandra                   ║
║ 8000     ║ TCP    ║ Альтернативный HTTP          ║ Часто для разработки                   ║
║ 8005     ║ TCP    ║ Tomcat Shutdown              ║ Остановка Tomcat                       ║
║ 8009     ║ TCP    ║ Tomcat AJP                   ║ Коннектор Apache к Tomcat              ║
║ 8010     ║ TCP    ║ Zabbix                        ║ Мониторинг                             ║
║ 8020     ║ TCP    ║ Apache Drill                  ║ SQL-движок для Hadoop                  ║
║ 8030-8033║ TCP    ║ YARN ResourceManager          ║ Управление ресурсами Hadoop            ║
║ 8042     ║ TCP    ║ YARN NodeManager              ║ Управление нодами Hadoop               ║
║ 8043     ║ TCP    ║ Elasticsearch                 ║ Поиск/аналитика (часто 9200-9400)      ║
║ 8080     ║ TCP    ║ Альтернативный HTTP/API       ║ Tomcat, Jenkins, прокси                ║
║ 8086     ║ TCP    ║ InfluxDB                      ║ База данных временных рядов            ║
║ 8087     ║ TCP    ║ Apache NiFi                   ║ Потоковая обработка данных             ║
║ 8088     ║ TCP    ║ Hadoop YARN ResourceManager   ║ UI Hadoop                              ║
║ 8089     ║ TCP    ║ Splunk                        ║ Сбор и анализ логов                    ║
║ 8090     ║ TCP    ║ Apache Druid                  ║ Аналитика больших данных               ║
║ 8096     ║ TCP    ║ Apache CloudStack             ║ Облачная платформа                     ║
║ 8123     ║ TCP    ║ Poloniex API                   ║ API криптобиржи/тестирование           ║
║ 8161     ║ TCP    ║ Apache ActiveMQ                ║ Очереди сообщений                      ║
║ 8181     ║ TCP    ║ Apache Knox                     ║ Gateway для Hadoop                     ║
║ 8200     ║ TCP    ║ Vault                          ║ Управление секретами                   ║
║ 8300-8302║ TCP    ║ Consul                         ║ Service discovery                      ║
║ 8400     ║ TCP    ║ Zabbix                          ║ Мониторинг                             ║
║ 8443     ║ TCP    ║ HTTPS альтернативный           ║ Apache Tomcat SSL, панели управления   ║
║ 8500     ║ TCP    ║ Consul UI                      ║ Веб-интерфейс Consul                   ║
║ 8888     ║ TCP    ║ Jupyter/Альтернативный HTTP    ║ Ноутбуки/дашборды                      ║
║ 8889     ║ TCP    ║ TP-Link уязвимость             ║ CMD-инъекция на роутерах               ║
║ 8983     ║ TCP    ║ Apache Solr                    ║ Поисковая платформа                    ║
║ 8984     ║ TCP    ║ Apache NiFi                     ║ Управление потоками данных             ║
║ 9000     ║ TCP    ║ Hadoop NameNode                 ║ Файловая система Hadoop                ║
║ 9001     ║ TCP    ║ HBase Master                    ║ База данных Hadoop                     ║
║ 9042     ║ TCP    ║ Cassandra CQL                   ║ Язык запросов Cassandra                ║
║ 9090     ║ TCP    ║ Prometheus/CloudStack           ║ Мониторинг/уязвимость RCE              ║
║ 9092     ║ TCP    ║ Apache Kafka                    ║ Потоковая платформа                    ║
║ 9093     ║ TCP    ║ Alertmanager                    ║ Управление алертами Prometheus         ║
║ 9094     ║ TCP    ║ Apache Phoenix                  ║ SQL для HBase                          ║
║ 9100     ║ TCP    ║ HP JetDirect/Node Exporter      ║ Печать/Мониторинг (Prometheus)         ║
║ 9200     ║ TCP    ║ Elasticsearch                   ║ Поиск/аналитика                        ║
║ 9300     ║ TCP    ║ Elasticsearch                    ║ Кластерные коммуникации                ║
║ 9418     ║ TCP/UDP║ Git                             ║ Протокол передачи Git                  ║
║ 10000    ║ TCP    ║ Webmin/NAT-PMP                  ║ Управление системой/проброс портов     ║
║ 11211    ║ TCP/UDP║ Memcached                       ║ Кэширование                            ║
║ 17000    ║ TCP    ║ Kaspersky активация             ║ Прокси-сервер активации                ║
║ 27017    ║ TCP    ║ MongoDB                         ║ База данных MongoDB                    ║
║ 28017    ║ TCP    ║ MongoDB Web UI                  ║ Веб-интерфейс MongoDB                  ║
║ 3074     ║ TCP/UDP║ Xbox Live                       ║ Игровой сервис                         ║
║ 50000    ║ TCP    ║ SAP DB                           ║ База данных SAP                        ║
║ 50070    ║ TCP    ║ Hadoop NameNode UI              ║ Веб-интерфейс Hadoop                   ║
║ 50075    ║ TCP    ║ Hadoop DataNode                  ║ Хранилище Hadoop                       ║
║ 50090    ║ TCP    ║ Hadoop Secondary NameNode        ║ Резервный NameNode                     ║
║ 61616    ║ TCP    ║ ActiveMQ Artemis                 ║ Очереди сообщений                      ║
╚══════════╩════════╩══════════════════════════════╩═══════════════════════════════════════╝


## Критичные для AD (почти всегда на DC)

88 — Kerberos (KDC) — атаки: Golden Ticket, Silver Ticket, Kerberoasting
389 — LDAP (plaintext) — перечисление пользователей, групп
445 — SMB (современный) — файловые шары, Pass-the-Hash, NTLM Relay
636 — LDAPS (безопасный) — перечисление через TLS

## Дополнительные AD сервисы

135 — RPC Endpoint Mapper — DCOM атаки, удаленное управление
139 — NetBIOS/SMB (старый) — null sessions, перечисление
464 — Kerberos kpasswd — смена паролей

## Общие опасные порты
22 — SSH — брутфорс, подбор паролей
23 — Telnet — нет шифрования, перехват трафика
80 — HTTP — XSS, SQLi, уязвимости веба
443 — HTTPS — уязвимости SSL/TLS, MiTM
3389 — RDP — брутфорс, BlueKeep (CVE-2019-0708)
3306 — MySQL — утечки данных, слабые пароли
5432 — PostgreSQL — утечки данных
5900 — VNC — слабые пароли, доступ к экрану

## Для перечисления SMB 
139, 445 — основные порты SMB

