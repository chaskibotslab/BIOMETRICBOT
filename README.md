# Sistema Biometrico - ChaskiBots

Control de asistencia con reconocimiento facial (InsightFace/ArcFace) y GPS.

## Arquitectura

| Componente | Tecnologia | Directorio |
|------------|-----------|------------|
| API Backend | Python + FastAPI | `python-api/` |
| Frontend Admin + PWA | Next.js + React + Tailwind | `frontend/` |
| Base de Datos | PostgreSQL | `database/` |

## URLs en Produccion

| Servicio | URL |
|----------|-----|
| API | `api.chaskibots.com` (Railway) |
| Admin | `admin.chaskibots.com` (Vercel) |
| Check-In PWA | `checkin.chaskibots.com` (Vercel) |

## Desarrollo Local

### 1. Base de Datos
```bash
# Crear base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE biometric_db;"
psql -U postgres -d biometric_db -f database/schema.sql
```

### 2. API Python
```bash
cd python-api
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp ../.env.example .env      # Editar con tus credenciales
python main.py
# API corriendo en http://localhost:8000
# Docs en http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
# Crear .env.local con:
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# Frontend corriendo en http://localhost:3000
```

## Deploy

### Railway (API)
1. Conectar repo de GitHub
2. Root directory: `python-api`
3. Agregar PostgreSQL addon
4. Variables de entorno: `SECRET_KEY`, `CORS_ORIGINS`
5. Railway provee `DATABASE_URL` automaticamente

### Vercel (Frontend)
1. Conectar repo de GitHub
2. Root directory: `frontend`
3. Variable: `NEXT_PUBLIC_API_URL` = URL de Railway

### Subdominios (chaskibots.com)
1. En tu proveedor DNS, agregar CNAME:
   - `api.chaskibots.com` -> tu-app.railway.app
   - `admin.chaskibots.com` -> tu-proyecto.vercel.app
   - `checkin.chaskibots.com` -> tu-proyecto.vercel.app

## Credenciales Iniciales
- Usuario: `admin`
- Contrasena: `admin123`

## Stack
- **Facial**: InsightFace (ArcFace) - 99.8% precision LFW
- **Auth**: JWT (python-jose)
- **DB**: PostgreSQL + SQLAlchemy
- **GPS**: Formula de Haversine
