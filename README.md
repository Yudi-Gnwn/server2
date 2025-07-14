# Konfigurasi Server 2 

- Mempersiapkan Folder & ibrary
- Struktur Folder seperti dibawah:

  ```
  voting-app /
  --- templates /
  	  dashboard.html
  	  login.html
  	  register.html
  app.py
  docker-compose.yml
  Dockerfile
  init_db.sql
  requirement.txt

  ```

- Install library pada file ```requirement.txt``` 

  ```
  Flask==2.3.3
  Flask-Login==0.6.2
  Flask-Bcrypt==1.0.1
  Flask-SocketIO==5.3.6
  psycopg2-binary==2.9.9
  eventlet==0.33.3
  python-engineio==4.8.0
  python-socketio==5.10.0
  Werkzeug==2.3.7
  Flask-WTF
  ```

- Pastikan file requirements.txt tersimpan dan jalankan dengan command:
  
  ```
  pip install --no-cache-dir -r requirements.txt
  ```

### 1. 
