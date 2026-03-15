"""
SISTEMA DE REGISTRO BIOMÉTRICO - ChaskiBots
API Principal - FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, text, exists
from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel

from config import settings
from database import get_db, init_db
from models import Empresa, Sucursal, Empleado, DatoBiometrico, RegistroAsistencia, UsuarioSistema
from schemas import (
    EmpleadoCreate, EmpleadoUpdate, EmpleadoResponse,
    EmpresaCreate, EmpresaResponse,
    SucursalCreate, SucursalResponse,
    RegistroBiometricoRequest, RegistroBiometricoResponse,
    CheckInRequest, CheckInResponse,
    VerificacionRequest, VerificacionResponse,
    RegistroAsistenciaResponse
)
from services import face_service, geo_service, Coordinates
from services import verify_password, hash_password, create_access_token, get_current_user

# ========================================
# LIFESPAN
# ========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 50)
    print("SISTEMA BIOMETRICO CHASKIBOTS - INICIANDO")
    print(f"Umbral similitud: {settings.SIMILARITY_THRESHOLD}")
    print("=" * 50)
    yield
    print("Sistema detenido.")


# ========================================
# CREAR APP
# ========================================
app = FastAPI(
    title="Sistema Biometrico API - ChaskiBots",
    description="Control de asistencia con reconocimiento facial y GPS",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# ENDPOINTS DE SALUD
# ========================================
@app.get("/", tags=["Info"])
async def root():
    return {
        "app": "Sistema Biometrico ChaskiBots",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Info"])
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "unhealthy", "database": "error"}


# ========================================
# AUTENTICACIÓN
# ========================================
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    rol: str


@app.post("/api/auth/login", response_model=LoginResponse, tags=["Auth"])
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UsuarioSistema).filter(
        UsuarioSistema.username == data.username,
        UsuarioSistema.activo == True
    ).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Usuario o contrasena incorrectos")

    token = create_access_token({"sub": str(user.id), "username": user.username, "rol": user.rol})

    user.ultimo_acceso = datetime.utcnow()
    db.commit()

    return LoginResponse(
        access_token=token,
        username=user.username,
        rol=user.rol
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@app.post("/api/auth/change-password", tags=["Auth"])
async def change_password(data: ChangePasswordRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(UsuarioSistema).filter(UsuarioSistema.id == current_user["sub"]).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Contrasena actual incorrecta")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Contrasena actualizada correctamente"}


@app.get("/api/auth/me", tags=["Auth"])
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ========================================
# EMPRESAS
# ========================================
@app.post("/api/empresas", response_model=EmpresaResponse, tags=["Empresas"])
async def crear_empresa(data: EmpresaCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    empresa = Empresa(**data.model_dump())
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return empresa


@app.get("/api/empresas", response_model=List[EmpresaResponse], tags=["Empresas"])
async def listar_empresas(db: Session = Depends(get_db)):
    return db.query(Empresa).filter(Empresa.activo == True).all()


# ========================================
# SUCURSALES
# ========================================
@app.post("/api/sucursales", response_model=SucursalResponse, tags=["Sucursales"])
async def crear_sucursal(data: SucursalCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sucursal = Sucursal(**data.model_dump())
    db.add(sucursal)
    db.commit()
    db.refresh(sucursal)
    return sucursal


@app.get("/api/sucursales", response_model=List[SucursalResponse], tags=["Sucursales"])
async def listar_sucursales(db: Session = Depends(get_db)):
    return db.query(Sucursal).filter(Sucursal.activo == True).all()


# ========================================
# EMPLEADOS
# ========================================
@app.post("/api/empleados", response_model=EmpleadoResponse, tags=["Empleados"])
async def crear_empleado(data: EmpleadoCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Verificar duplicado
    existe = db.query(Empleado).filter(
        Empleado.numero_empleado == data.numero_empleado
    ).first()

    if existe:
        raise HTTPException(400, "Ya existe un empleado con ese numero")

    empleado = Empleado(**data.model_dump())
    db.add(empleado)
    db.commit()
    db.refresh(empleado)

    return EmpleadoResponse(
        id=empleado.id,
        numero_empleado=empleado.numero_empleado,
        nombre=empleado.nombre,
        apellido_paterno=empleado.apellido_paterno,
        apellido_materno=empleado.apellido_materno,
        email=empleado.email,
        puesto=empleado.puesto,
        activo=empleado.activo,
        tiene_biometrico=False
    )


@app.get("/api/empleados", response_model=List[EmpleadoResponse], tags=["Empleados"])
async def listar_empleados(empresa_id: UUID = None, db: Session = Depends(get_db)):
    # Subquery para evitar N+1
    bio_exists = exists().where(
        and_(DatoBiometrico.empleado_id == Empleado.id, DatoBiometrico.activo == True)
    )

    query = db.query(Empleado, bio_exists.label("tiene_bio")).filter(Empleado.activo == True)

    if empresa_id:
        query = query.filter(Empleado.empresa_id == empresa_id)

    rows = query.all()

    return [
        EmpleadoResponse(
            id=emp.id,
            numero_empleado=emp.numero_empleado,
            nombre=emp.nombre,
            apellido_paterno=emp.apellido_paterno,
            apellido_materno=emp.apellido_materno,
            email=emp.email,
            puesto=emp.puesto,
            activo=emp.activo,
            tiene_biometrico=tiene_bio
        )
        for emp, tiene_bio in rows
    ]


@app.put("/api/empleados/{empleado_id}", response_model=EmpleadoResponse, tags=["Empleados"])
async def editar_empleado(empleado_id: UUID, data: EmpleadoUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado:
        raise HTTPException(404, "Empleado no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(empleado, field, value)

    db.commit()
    db.refresh(empleado)

    tiene_bio = db.query(exists().where(
        and_(DatoBiometrico.empleado_id == empleado.id, DatoBiometrico.activo == True)
    )).scalar()

    return EmpleadoResponse(
        id=empleado.id,
        numero_empleado=empleado.numero_empleado,
        nombre=empleado.nombre,
        apellido_paterno=empleado.apellido_paterno,
        apellido_materno=empleado.apellido_materno,
        email=empleado.email,
        puesto=empleado.puesto,
        activo=empleado.activo,
        tiene_biometrico=tiene_bio
    )


@app.delete("/api/empleados/{empleado_id}", tags=["Empleados"])
async def eliminar_empleado(empleado_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado:
        raise HTTPException(404, "Empleado no encontrado")

    # Eliminar datos biometricos asociados
    db.query(DatoBiometrico).filter(DatoBiometrico.empleado_id == empleado_id).delete()
    # Eliminar registros de asistencia asociados
    db.query(RegistroAsistencia).filter(RegistroAsistencia.empleado_id == empleado_id).delete()
    # Eliminar empleado
    db.delete(empleado)
    db.commit()

    return {"message": f"Empleado {empleado.nombre} {empleado.apellido_paterno} eliminado correctamente"}


# ========================================
# REGISTRO BIOMÉTRICO
# ========================================
@app.post("/api/biometrico/registrar", response_model=RegistroBiometricoResponse, tags=["Biométrico"])
async def registrar_biometrico(data: RegistroBiometricoRequest, db: Session = Depends(get_db)):
    """
    Registra el rostro de un empleado usando modelo CNN
    """
    # Verificar empleado
    empleado = db.query(Empleado).filter(Empleado.id == data.empleado_id).first()
    if not empleado:
        raise HTTPException(404, "Empleado no encontrado")

    print(f"\n📷 Registrando biométrico para: {empleado.nombre_completo}")

    # Procesar imagen con CNN
    result = face_service.detect_and_encode(data.imagen_base64)

    if not result.success:
        return RegistroBiometricoResponse(
            success=False,
            message=result.message,
            empleado_id=data.empleado_id
        )

    # Serializar encoding
    encoding_bytes = face_service.serialize_encoding(result.encoding)

    # Generar thumbnail
    thumbnail = face_service.get_face_thumbnail(
        data.imagen_base64,
        result.face_location
    )

    # Buscar registro existente
    existente = db.query(DatoBiometrico).filter(
        DatoBiometrico.empleado_id == data.empleado_id,
        DatoBiometrico.tipo == "facial"
    ).first()

    if existente:
        # Actualizar
        existente.encoding = encoding_bytes
        existente.imagen_referencia = thumbnail
        existente.calidad_registro = float(result.quality_score)
        existente.dispositivo_registro = data.dispositivo
        print("📝 Biométrico actualizado")
    else:
        # Crear nuevo
        bio = DatoBiometrico(
            empleado_id=data.empleado_id,
            tipo="facial",
            encoding=encoding_bytes,
            imagen_referencia=thumbnail,
            calidad_registro=float(result.quality_score),
            dispositivo_registro=data.dispositivo
        )
        db.add(bio)
        print("✨ Biométrico creado")

    db.commit()

    return RegistroBiometricoResponse(
        success=True,
        message=f"✅ Rostro registrado correctamente. Calidad: {result.quality_score}%",
        empleado_id=data.empleado_id,
        calidad=result.quality_score
    )


# ========================================
# VERIFICACIÓN FACIAL
# ========================================
@app.post("/api/biometrico/verificar", response_model=VerificacionResponse, tags=["Biométrico"])
async def verificar_rostro(data: VerificacionRequest, db: Session = Depends(get_db)):
    """
    Verifica un rostro contra los registros
    """
    if data.empleado_id:
        # Verificar contra empleado específico
        bio = db.query(DatoBiometrico).filter(
            DatoBiometrico.empleado_id == data.empleado_id,
            DatoBiometrico.activo == True
        ).first()

        if not bio:
            return VerificacionResponse(
                success=True,
                matched=False,
                message="El empleado no tiene registro biométrico"
            )

        known = face_service.deserialize_encoding(bio.encoding)
        result = face_service.compare_faces(known, data.imagen_base64)

        empleado = db.query(Empleado).filter(Empleado.id == data.empleado_id).first()

        return VerificacionResponse(
            success=True,
            matched=result.matched,
            empleado_id=data.empleado_id if result.matched else None,
            empleado_nombre=empleado.nombre_completo if result.matched else None,
            confianza=result.confidence,
            message=result.message
        )
    else:
        # Buscar en todos
        bios = db.query(DatoBiometrico).filter(DatoBiometrico.activo == True).all()

        if not bios:
            return VerificacionResponse(
                success=True,
                matched=False,
                message="No hay registros biométricos"
            )

        known_list = []
        for bio in bios:
            encoding = face_service.deserialize_encoding(bio.encoding)
            known_list.append((str(bio.empleado_id), encoding))

        result = face_service.find_match(data.imagen_base64, known_list)

        if result.matched:
            empleado = db.query(Empleado).filter(
                Empleado.id == UUID(result.empleado_id)
            ).first()

            return VerificacionResponse(
                success=True,
                matched=True,
                empleado_id=UUID(result.empleado_id),
                empleado_nombre=empleado.nombre_completo if empleado else None,
                confianza=result.confidence,
                message=result.message
            )

        return VerificacionResponse(
            success=True,
            matched=False,
            confianza=result.confidence,
            message=result.message
        )


# ========================================
# CHECK-IN / CHECK-OUT
# ========================================
@app.post("/api/checkin", response_model=CheckInResponse, tags=["Asistencia"])
async def realizar_checkin(data: CheckInRequest, request: Request, db: Session = Depends(get_db)):
    """
    Registro de asistencia con verificación facial CNN y GPS
    """
    print(f"\n🚀 Check-in tipo: {data.tipo_registro}")

    # 1. Obtener todos los biométricos
    bios = db.query(DatoBiometrico).filter(DatoBiometrico.activo == True).all()

    if not bios:
        return CheckInResponse(
            success=False,
            message="❌ No hay empleados registrados"
        )

    # 2. Buscar coincidencia facial
    known_list = [(str(b.empleado_id), face_service.deserialize_encoding(b.encoding)) for b in bios]
    face_result = face_service.find_match(data.imagen_base64, known_list)

    if not face_result.matched:
        return CheckInResponse(
            success=False,
            message=face_result.message,
            confianza_facial=face_result.confidence
        )

    empleado_id = UUID(face_result.empleado_id)
    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()

    print(f"👤 Empleado identificado: {empleado.nombre_completo}")

    # 3. Validar ubicación
    user_coords = Coordinates(
        latitude=data.latitud,
        longitude=data.longitud,
        accuracy=data.precision_gps
    )

    dentro_rango = True
    distancia = 0.0

    # Buscar sucursal
    sucursal = None
    if data.sucursal_id:
        sucursal = db.query(Sucursal).filter(Sucursal.id == data.sucursal_id).first()
    elif empleado.sucursal_id:
        sucursal = db.query(Sucursal).filter(Sucursal.id == empleado.sucursal_id).first()

    if sucursal and sucursal.latitud and sucursal.longitud:
        target = Coordinates(float(sucursal.latitud), float(sucursal.longitud))
        geo_result = geo_service.validate_location(user_coords, target, sucursal.radio_permitido_metros)
        dentro_rango = geo_result.within_range
        distancia = geo_result.distance_meters
        print(f"📍 {geo_result.message}")

    # 4. Verificar duplicado (mismo empleado, mismo tipo, mismo dia)
    registro_existente = db.query(RegistroAsistencia).filter(
        RegistroAsistencia.empleado_id == empleado_id,
        RegistroAsistencia.tipo == data.tipo_registro.value,
        RegistroAsistencia.fecha == datetime.now().date()
    ).first()

    if registro_existente:
        return CheckInResponse(
            success=False,
            message=f"Ya registraste {data.tipo_registro.value} hoy",
            empleado_id=empleado_id,
            empleado_nombre=empleado.nombre_completo,
            confianza_facial=face_result.confidence
        )

    # 5. Crear registro
    registro = RegistroAsistencia(
        empleado_id=empleado_id,
        sucursal_id=sucursal.id if sucursal else None,
        tipo=data.tipo_registro.value,
        metodo_verificacion="facial_cnn",
        confianza_match=float(face_result.confidence),
        latitud=data.latitud,
        longitud=data.longitud,
        precision_gps=data.precision_gps,
        dentro_rango=dentro_rango,
        distancia_sucursal=distancia,
        dispositivo_id=data.dispositivo_id,
        dispositivo_info=data.dispositivo_info,
        ip_address=str(request.client.host) if request.client else None
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    print(f"✅ Registro guardado: {registro.id}")

    return CheckInResponse(
        success=True,
        message=f"✅ {data.tipo_registro.value.upper()} registrada",
        empleado_id=empleado_id,
        empleado_nombre=empleado.nombre_completo,
        confianza_facial=face_result.confidence,
        distancia_metros=distancia,
        dentro_rango=dentro_rango,
        registro_id=registro.id,
        timestamp=registro.timestamp_registro
    )


# ========================================
# REPORTES
# ========================================
@app.get("/api/asistencia/hoy", response_model=List[RegistroAsistenciaResponse], tags=["Reportes"])
async def asistencia_hoy(db: Session = Depends(get_db)):
    """Obtiene registros de hoy"""
    rows = db.query(RegistroAsistencia, Empleado).join(
        Empleado, RegistroAsistencia.empleado_id == Empleado.id
    ).filter(
        RegistroAsistencia.fecha == datetime.now().date()
    ).order_by(RegistroAsistencia.hora.desc()).all()

    return [
        RegistroAsistenciaResponse(
            id=r.id,
            empleado_id=r.empleado_id,
            empleado_nombre=emp.nombre_completo,
            tipo=r.tipo,
            fecha=r.fecha,
            hora=r.hora,
            confianza_match=float(r.confianza_match) if r.confianza_match else None,
            dentro_rango=r.dentro_rango,
            distancia_sucursal=float(r.distancia_sucursal) if r.distancia_sucursal else None
        )
        for r, emp in rows
    ]


# ========================================
# MAIN
# ========================================
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
