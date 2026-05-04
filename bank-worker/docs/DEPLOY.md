## Deploy Bank-Worker

dienstkonto email
banking-service-worker@diy-ticket-system.iam.gserviceaccount.com


### Code rüberkopieren

  von deinem Mac aus
```bash
  rsync -av --exclude='venv' --exclude='tokens.json' --exclude='.env' \
    --exclude='service_account.json' --exclude='__pycache__' \
    ./bank-worker/ root@<CONTAINER-IP>:/opt/bank-worker/
```

### Im Container einrichten

```
ssh root@<CONTAINER-IP>
apt update && apt install -y python3 python3-venv python3-pip

cd /opt/bank-worker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env und service_account.json manuell anlegen
nano .env                  # Werte aus example.env eintragen
nano service_account.json  # Inhalt aus Google Cloud einfügen
```


### 4. Einmalig authentifizieren (PushTAN)

```
cd /opt/bank-worker
export $(cat .env | xargs) && source venv/bin/activate && python auth_setup.py
```

→ PushTAN bestätigen → Enter → tokens.json wird gespeichert

### 5. Systemd Service (läuft automatisch, startet nach Reboot)

  nano /etc/systemd/system/bank-worker.service

```txt
[Unit]
Description=Bank Worker
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/bank-worker
EnvironmentFile=/opt/bank-worker/.env
ExecStart=/opt/bank-worker/venv/bin/python main.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```


### 6. Logs prüfen
  
``` 
journalctl -u bank-worker -f

oder

tail -f /opt/bank-worker/worker.log
```

  
### Token abgelaufen (Fehlerfall)

```
ssh root@<CONTAINER-IP>
systemctl stop bank-worker
cd /opt/bank-worker
export $(cat .env | xargs) && source venv/bin/activate && python auth_setup.py
systemctl start bank-worker
```