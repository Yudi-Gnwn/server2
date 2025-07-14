# Konfigurasi Server 2 

- Mempersiapkan Folder & library
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

- Prepare library pada ```requirement.txt``` 

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

- Pastikan file requirements.txt tersimpan dan jalankan command:
  
  ```
  pip install --no-cache-dir -r requirements.txt
  ```


### 1. Install Docker & Docker Compose 
  ```
  sudo apt install docker-compose-plugin -y
  ```

### 2. Konfigurasi App.py
  - full codenya dalam ```app.py``` diatas👆🏻

    
### 3. Konfigurasi Dockerfile & docker-compose.yml
  
  - ```Dockerfile```
    ```
    FROM python:3.11
    WORKDIR /app
    COPY . .
    RUN pip install --no-cache-dir -r requirements.txt
    CMD ["python", "app.py"]
    ```

- ```docker-compose.yml```
  ```
  version: '3'
  services:
    voting_app:
      build: .
      ports:
        - "9032:9032"  # Ganti X dengan 2 atau 3
      environment:
        - PORT=9032
        - DB_HOST=192.168.138.35
      restart: always
  ```

### 4. Membuat halaman Voting App (templates) & Styling
 - Disini merupakan bagian Main dari Webiste Voting app, jadi buatlah ini dibagian folder ```templates/``` untuk dashboard,
   login - register dan ```static/``` untuk main.css & main.js.

    - dashboard.html
    - login.html
    - register.html
  
    - main.css
      
    - main.js
      source code tersedia diatas👆🏻

### 5. Jalankan Server
  - Jalankan command berikut:
    ```
    docker compose up --build
    ```
