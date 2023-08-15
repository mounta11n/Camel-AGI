Um den Server auszuführen: 

i) Erstellen Sie eine neue conda Umgebung.

ii) Gehen Sie zum Serverordner und installieren Sie alle erforderlichen Pakete mit dem Befehl `pip install --r -requirements.txt`. 

ii) Setzen Sie Umgebungsvariablen `FLASK_ENV = dev` und `FLASK_APP = webserver.py` 

iv) Erstellen Sie eine DB zum Speichern aller Informationen mit den Befehlen
    1) `flask db init`
    2) `flask db migrate`
    3) `flask db -upgrade`

v) Führen Sie den Server mit `python webserver.py` aus