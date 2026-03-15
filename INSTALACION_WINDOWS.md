# 🖥️ INSTALACIÓN EN WINDOWS CON PYCHARM

## PASO 1: Instalar Programas Necesarios

### 1.1 PostgreSQL (Base de datos)
1. Descarga: https://www.postgresql.org/download/windows/
2. Ejecuta el instalador
3. **IMPORTANTE:** Anota la contraseña que pongas (ej: `postgres123`)
4. Puerto por defecto: `5432`
5. Al finalizar, abre **pgAdmin 4** (se instala junto)

### 1.2 Python 3.11
1. Descarga: https://www.python.org/downloads/
2. **IMPORTANTE:** Marca ✅ "Add Python to PATH" al instalar
3. Verifica en CMD: `python --version`

### 1.3 Visual Studio Build Tools (necesario para face_recognition)
1. Descarga: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Instala "Desktop development with C++"

### 1.4 CMake
1. Descarga: https://cmake.org/download/
2. Instala y marca "Add to PATH"

### 1.5 PyCharm
1. Descarga: https://www.jetbrains.com/pycharm/download/ (Community es gratis)
2. Instala normalmente

### 1.6 XAMPP (para PHP)
1. Descarga: https://www.apachefriends.org/
2. Instala con Apache y PHP

---

## PASO 2: Crear Base de Datos

1. Abre **pgAdmin 4**
2. Click derecho en "Databases" → Create → Database
3. Nombre: `biometric_db`
4. Click en Save
5. Click derecho en `biometric_db` → Query Tool
6. Copia y pega TODO el contenido de `database/schema.sql`
7. Click en ▶️ Execute

---

## PASO 3: Configurar Proyecto en PyCharm

1. Abre PyCharm
2. File → Open → Selecciona la carpeta `python-api`
3. PyCharm detectará que no hay intérprete:
   - Click en "Configure Python Interpreter"
   - Add Interpreter → Add Local Interpreter
   - Virtualenv Environment → OK

4. Abre Terminal en PyCharm (abajo) y ejecuta:
```bash
pip install -r requirements.txt
```
(Esto tarda varios minutos por dlib)

5. Edita `config.py`:
   - Cambia `DB_PASSWORD` por tu contraseña de PostgreSQL

6. Click derecho en `main.py` → Run 'main'

7. Verás: `Uvicorn running on http://0.0.0.0:8000`

8. Abre en navegador: http://localhost:8000/docs

---

## PASO 4: Configurar PHP (XAMPP)

1. Copia la carpeta `php-frontend` a `C:\xampp\htdocs\biometric`
2. Abre XAMPP Control Panel
3. Start → Apache
4. Edita `C:\xampp\htdocs\biometric\config.php`:
   - Cambia `DB_PASSWORD` por tu contraseña
5. Abre: http://localhost/biometric/install.php
6. Luego: http://localhost/biometric/login.php
7. Usuario: `admin` / Contraseña: `admin123`

---

## PASO 5: App Móvil

1. Copia `mobile-app` a `C:\xampp\htdocs\checkin`
2. Edita `index.html`, línea con `API_URL`:
   - Cambia `localhost` por la IP de tu PC (ej: `192.168.1.100`)
   - Para ver tu IP: abre CMD y escribe `ipconfig`
3. En tu celular, abre: `http://TU_IP/checkin/`

---

## 🎯 URLs FINALES

| Qué | URL |
|-----|-----|
| API Docs | http://localhost:8000/docs |
| Dashboard Admin | http://localhost/biometric/ |
| App Móvil | http://TU_IP/checkin/ |

---

## ⚠️ Solución de Problemas

### Error "dlib no instala"
```bash
pip install cmake
pip install dlib
pip install face_recognition
```

### Error "No se conecta a PostgreSQL"
- Verifica que PostgreSQL esté corriendo (busca en servicios de Windows)
- Verifica usuario/contraseña en config.py

### La cámara no funciona en el celular
- Debes usar HTTPS o localhost
- O acceder desde el mismo PC
