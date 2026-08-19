"""
SISTEMA DE REGISTRO BIOMÉTRICO - ChaskiBots
API Principal - FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, text, exists
from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from config import settings
from database import get_db, init_db
from models import Empresa, Sucursal, Empleado, DatoBiometrico, RegistroAsistencia, UsuarioSistema
from schemas import (
    EmpleadoCreate, EmpleadoUpdate, EmpleadoResponse,
    EmpresaCreate, EmpresaResponse,
    SucursalCreate, SucursalUpdate, SucursalResponse,
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
    init_db()
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


class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str


@app.post("/api/auth/reset-password", tags=["Auth"])
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Solo admin puede resetear contraseñas de otros usuarios"""
    if current_user.get("rol") != "admin":
        raise HTTPException(403, "Solo administradores pueden resetear contrasenas")

    user = db.query(UsuarioSistema).filter(UsuarioSistema.username == data.username).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    if len(data.new_password) < 6:
        raise HTTPException(400, "La contrasena debe tener al menos 6 caracteres")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": f"Contrasena de '{data.username}' reseteada correctamente"}


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
def _parse_time(t: Optional[str]):
    """Convierte string HH:MM a objeto time"""
    if not t:
        return None
    from datetime import time as dt_time
    parts = t.split(":")
    return dt_time(int(parts[0]), int(parts[1]))


def _format_time(t) -> Optional[str]:
    """Convierte time a string HH:MM"""
    if not t:
        return None
    return t.strftime("%H:%M")


@app.post("/api/sucursales", response_model=SucursalResponse, tags=["Sucursales"])
async def crear_sucursal(data: SucursalCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    d = data.model_dump()
    d["hora_entrada"] = _parse_time(d.get("hora_entrada"))
    d["hora_salida"] = _parse_time(d.get("hora_salida"))
    sucursal = Sucursal(**d)
    db.add(sucursal)
    db.commit()
    db.refresh(sucursal)
    return _sucursal_to_response(sucursal)


@app.get("/api/sucursales", response_model=List[SucursalResponse], tags=["Sucursales"])
async def listar_sucursales(db: Session = Depends(get_db)):
    sucursales = db.query(Sucursal).filter(Sucursal.activo == True).all()
    return [_sucursal_to_response(s) for s in sucursales]


@app.get("/api/sucursales/{sucursal_id}", response_model=SucursalResponse, tags=["Sucursales"])
async def obtener_sucursal(sucursal_id: UUID, db: Session = Depends(get_db)):
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(404, "Sucursal no encontrada")
    return _sucursal_to_response(sucursal)


@app.put("/api/sucursales/{sucursal_id}", response_model=SucursalResponse, tags=["Sucursales"])
async def editar_sucursal(sucursal_id: UUID, data: SucursalUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(404, "Sucursal no encontrada")

    update_data = data.model_dump(exclude_unset=True)
    if "hora_entrada" in update_data:
        update_data["hora_entrada"] = _parse_time(update_data["hora_entrada"])
    if "hora_salida" in update_data:
        update_data["hora_salida"] = _parse_time(update_data["hora_salida"])

    for field, value in update_data.items():
        setattr(sucursal, field, value)

    db.commit()
    db.refresh(sucursal)
    return _sucursal_to_response(sucursal)


@app.delete("/api/sucursales/{sucursal_id}", tags=["Sucursales"])
async def eliminar_sucursal(sucursal_id: UUID, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(404, "Sucursal no encontrada")
    sucursal.activo = False
    db.commit()
    return {"message": f"Sucursal '{sucursal.nombre}' desactivada"}


def _sucursal_to_response(s: Sucursal) -> SucursalResponse:
    return SucursalResponse(
        id=s.id,
        empresa_id=s.empresa_id,
        nombre=s.nombre,
        direccion=s.direccion,
        latitud=float(s.latitud) if s.latitud is not None else None,
        longitud=float(s.longitud) if s.longitud is not None else None,
        radio_permitido_metros=s.radio_permitido_metros or 100,
        hora_entrada=_format_time(s.hora_entrada),
        hora_salida=_format_time(s.hora_salida),
        tolerancia_minutos=s.tolerancia_minutos or 15,
        activo=s.activo,
    )


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

    # ── Verificar que el rostro NO pertenezca a otro empleado ──
    otros_bios = db.query(DatoBiometrico).filter(
        DatoBiometrico.empleado_id != data.empleado_id,
        DatoBiometrico.activo == True,
        DatoBiometrico.tipo == "facial"
    ).all()

    if otros_bios:
        known_list = []
        for bio in otros_bios:
            enc = face_service.deserialize_encoding(bio.encoding)
            known_list.append((str(bio.empleado_id), enc))

        dup_check = face_service.find_match_from_encoding(result.encoding, known_list)

        if dup_check.matched:
            otro_emp = db.query(Empleado).filter(
                Empleado.id == UUID(dup_check.empleado_id)
            ).first()
            nombre_otro = otro_emp.nombre_completo if otro_emp else "otro empleado"
            print(f"⚠️ Rostro duplicado detectado: coincide con {nombre_otro} ({dup_check.confidence:.1f}%)")
            return RegistroBiometricoResponse(
                success=False,
                message=f"Este rostro ya esta registrado para: {nombre_otro} (similitud: {dup_check.confidence:.1f}%). No se puede registrar el mismo rostro para dos empleados.",
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


@app.get("/api/asistencia", response_model=List[RegistroAsistenciaResponse], tags=["Reportes"])
async def buscar_asistencia(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    empleado_id: Optional[UUID] = None,
    tipo: Optional[str] = None,
    buscar: Optional[str] = None,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """Busca registros de asistencia con filtros avanzados"""
    query = db.query(RegistroAsistencia, Empleado).join(
        Empleado, RegistroAsistencia.empleado_id == Empleado.id
    )

    if fecha_desde:
        query = query.filter(RegistroAsistencia.fecha >= fecha_desde)
    else:
        query = query.filter(RegistroAsistencia.fecha >= datetime.now().date() - timedelta(days=30))

    if fecha_hasta:
        query = query.filter(RegistroAsistencia.fecha <= fecha_hasta)

    if empleado_id:
        query = query.filter(RegistroAsistencia.empleado_id == empleado_id)

    if tipo and tipo in ("entrada", "salida"):
        query = query.filter(RegistroAsistencia.tipo == tipo)

    if buscar:
        search_term = f"%{buscar}%"
        query = query.filter(
            (Empleado.nombre.ilike(search_term)) |
            (Empleado.apellido_paterno.ilike(search_term)) |
            (Empleado.apellido_materno.ilike(search_term)) |
            (Empleado.numero_empleado.ilike(search_term))
        )

    rows = query.order_by(
        RegistroAsistencia.fecha.desc(),
        RegistroAsistencia.hora.desc()
    ).limit(limit).all()

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


@app.get("/api/asistencia/resumen", tags=["Reportes"])
async def resumen_asistencia(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Resumen estadistico de asistencia por rango de fechas"""
    from sqlalchemy import func as sqlfunc

    if not fecha_desde:
        fecha_desde = datetime.now().date() - timedelta(days=30)
    if not fecha_hasta:
        fecha_hasta = datetime.now().date()

    # Total registros
    total = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta
    ).scalar() or 0

    # Entradas y salidas
    entradas = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta,
        RegistroAsistencia.tipo == "entrada"
    ).scalar() or 0

    salidas = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta,
        RegistroAsistencia.tipo == "salida"
    ).scalar() or 0

    # Empleados unicos
    empleados_unicos = db.query(
        sqlfunc.count(sqlfunc.distinct(RegistroAsistencia.empleado_id))
    ).filter(
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta
    ).scalar() or 0

    # Dias con registros
    dias_con_registro = db.query(
        sqlfunc.count(sqlfunc.distinct(RegistroAsistencia.fecha))
    ).filter(
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta
    ).scalar() or 0

    # Registros por dia (para grafica)
    registros_por_dia = db.query(
        RegistroAsistencia.fecha,
        sqlfunc.count(RegistroAsistencia.id).label("total"),
        sqlfunc.count(sqlfunc.distinct(RegistroAsistencia.empleado_id)).label("empleados")
    ).filter(
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta
    ).group_by(RegistroAsistencia.fecha).order_by(RegistroAsistencia.fecha).all()

    return {
        "fecha_desde": fecha_desde.isoformat(),
        "fecha_hasta": fecha_hasta.isoformat(),
        "total_registros": total,
        "entradas": entradas,
        "salidas": salidas,
        "empleados_unicos": empleados_unicos,
        "dias_con_registro": dias_con_registro,
        "por_dia": [
            {"fecha": row.fecha.isoformat(), "total": row.total, "empleados": row.empleados}
            for row in registros_por_dia
        ]
    }


# ========================================
# REPORTE INDIVIDUAL POR EMPLEADO
# ========================================
@app.get("/api/asistencia/empleado/{empleado_id}", tags=["Reportes"])
async def reporte_empleado(
    empleado_id: UUID,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Reporte detallado de asistencia de un empleado"""
    from sqlalchemy import func as sqlfunc

    empleado = db.query(Empleado).filter(Empleado.id == empleado_id).first()
    if not empleado:
        raise HTTPException(404, "Empleado no encontrado")

    if not fecha_desde:
        fecha_desde = datetime.now().date() - timedelta(days=30)
    if not fecha_hasta:
        fecha_hasta = datetime.now().date()

    # Obtener sucursal y horario
    sucursal = None
    hora_entrada_esperada = None
    hora_salida_esperada = None
    tolerancia = 15
    if empleado.sucursal_id:
        sucursal = db.query(Sucursal).filter(Sucursal.id == empleado.sucursal_id).first()
        if sucursal:
            hora_entrada_esperada = _format_time(sucursal.hora_entrada)
            hora_salida_esperada = _format_time(sucursal.hora_salida)
            tolerancia = sucursal.tolerancia_minutos or 15

    # Registros en rango
    registros = db.query(RegistroAsistencia).filter(
        RegistroAsistencia.empleado_id == empleado_id,
        RegistroAsistencia.fecha >= fecha_desde,
        RegistroAsistencia.fecha <= fecha_hasta
    ).order_by(RegistroAsistencia.fecha.desc(), RegistroAsistencia.hora.desc()).all()

    # Calcular estadisticas
    total_dias_rango = (fecha_hasta - fecha_desde).days + 1
    dias_laborales = sum(1 for i in range(total_dias_rango)
                        if (fecha_desde + timedelta(days=i)).weekday() < 5)

    entradas = [r for r in registros if r.tipo == "entrada"]
    salidas = [r for r in registros if r.tipo == "salida"]
    dias_asistidos = len(set(r.fecha for r in entradas))
    dias_faltados = max(0, dias_laborales - dias_asistidos)

    # Calcular retardos
    retardos = 0
    registros_detalle = []
    for r in registros:
        es_retardo = False
        if r.tipo == "entrada" and sucursal and sucursal.hora_entrada:
            from datetime import time as dt_time
            hora_limite = dt_time(
                sucursal.hora_entrada.hour,
                sucursal.hora_entrada.minute + tolerancia
            ) if sucursal.hora_entrada.minute + tolerancia < 60 else dt_time(
                sucursal.hora_entrada.hour + 1,
                (sucursal.hora_entrada.minute + tolerancia) % 60
            )
            hora_registro = r.hora.replace(tzinfo=None) if r.hora.tzinfo else r.hora
            if hora_registro > hora_limite:
                es_retardo = True
                retardos += 1

        registros_detalle.append({
            "id": str(r.id),
            "fecha": r.fecha.isoformat(),
            "hora": r.hora.strftime("%H:%M") if r.hora else None,
            "tipo": r.tipo,
            "confianza_match": float(r.confianza_match) if r.confianza_match else None,
            "dentro_rango": r.dentro_rango,
            "distancia_sucursal": float(r.distancia_sucursal) if r.distancia_sucursal else None,
            "retardo": es_retardo,
        })

    # Horas trabajadas (aprox)
    horas_totales = 0.0
    fechas_con_entrada = {}
    for r in registros:
        if r.tipo == "entrada":
            fechas_con_entrada[r.fecha] = r.hora
    for r in registros:
        if r.tipo == "salida" and r.fecha in fechas_con_entrada:
            entrada_hora = fechas_con_entrada[r.fecha]
            try:
                h_entrada = entrada_hora.hour + entrada_hora.minute / 60
                h_salida = r.hora.hour + r.hora.minute / 60
                diff = h_salida - h_entrada
                if diff > 0:
                    horas_totales += diff
            except Exception:
                pass

    return {
        "empleado": {
            "id": str(empleado.id),
            "nombre": empleado.nombre_completo,
            "numero_empleado": empleado.numero_empleado,
            "puesto": empleado.puesto,
            "departamento": empleado.departamento,
        },
        "sucursal": {
            "nombre": sucursal.nombre if sucursal else None,
            "hora_entrada": hora_entrada_esperada,
            "hora_salida": hora_salida_esperada,
            "tolerancia_minutos": tolerancia,
        },
        "periodo": {
            "fecha_desde": fecha_desde.isoformat(),
            "fecha_hasta": fecha_hasta.isoformat(),
            "dias_laborales": dias_laborales,
        },
        "estadisticas": {
            "dias_asistidos": dias_asistidos,
            "dias_faltados": dias_faltados,
            "total_entradas": len(entradas),
            "total_salidas": len(salidas),
            "retardos": retardos,
            "horas_trabajadas": round(horas_totales, 1),
            "promedio_horas_dia": round(horas_totales / dias_asistidos, 1) if dias_asistidos > 0 else 0,
        },
        "registros": registros_detalle,
    }


# ========================================
# FALTAS / NOTIFICACIONES
# ========================================
@app.get("/api/asistencia/faltas", tags=["Reportes"])
async def empleados_sin_entrada(
    fecha: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Empleados activos que NO han registrado entrada en la fecha dada"""
    target_date = fecha or datetime.now().date()

    # Empleados activos con biometrico
    empleados_activos = db.query(Empleado).filter(Empleado.activo == True).all()

    # IDs que SI registraron entrada hoy
    ids_con_entrada = set(
        r[0] for r in db.query(RegistroAsistencia.empleado_id).filter(
            RegistroAsistencia.fecha == target_date,
            RegistroAsistencia.tipo == "entrada"
        ).all()
    )

    faltantes = []
    for emp in empleados_activos:
        if emp.id not in ids_con_entrada:
            tiene_bio = db.query(exists().where(
                and_(DatoBiometrico.empleado_id == emp.id, DatoBiometrico.activo == True)
            )).scalar()
            faltantes.append({
                "id": str(emp.id),
                "nombre": emp.nombre_completo,
                "numero_empleado": emp.numero_empleado,
                "puesto": emp.puesto,
                "tiene_biometrico": tiene_bio,
            })

    return {
        "fecha": target_date.isoformat(),
        "total_activos": len(empleados_activos),
        "con_entrada": len(ids_con_entrada),
        "sin_entrada": len(faltantes),
        "faltantes": faltantes,
    }


# ========================================
# DASHBOARD STATS AVANZADO
# ========================================
@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def dashboard_stats(db: Session = Depends(get_db)):
    """Estadisticas avanzadas para el dashboard"""
    from sqlalchemy import func as sqlfunc

    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    # Conteos basicos
    total_empleados = db.query(sqlfunc.count(Empleado.id)).filter(Empleado.activo == True).scalar() or 0
    con_biometrico = db.query(sqlfunc.count(DatoBiometrico.empleado_id.distinct())).filter(
        DatoBiometrico.activo == True
    ).scalar() or 0

    # Hoy
    entradas_hoy = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha == hoy, RegistroAsistencia.tipo == "entrada"
    ).scalar() or 0
    salidas_hoy = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha == hoy, RegistroAsistencia.tipo == "salida"
    ).scalar() or 0

    # Esta semana
    registros_semana = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha >= inicio_semana,
        RegistroAsistencia.fecha <= hoy
    ).scalar() or 0

    # Este mes
    registros_mes = db.query(sqlfunc.count(RegistroAsistencia.id)).filter(
        RegistroAsistencia.fecha >= inicio_mes,
        RegistroAsistencia.fecha <= hoy
    ).scalar() or 0

    # Tendencia semanal (ultimos 7 dias)
    tendencia_semanal = db.query(
        RegistroAsistencia.fecha,
        sqlfunc.count(RegistroAsistencia.id).label("total"),
        sqlfunc.count(sqlfunc.distinct(RegistroAsistencia.empleado_id)).label("empleados")
    ).filter(
        RegistroAsistencia.fecha >= hoy - timedelta(days=6),
        RegistroAsistencia.fecha <= hoy
    ).group_by(RegistroAsistencia.fecha).order_by(RegistroAsistencia.fecha).all()

    # Retardos hoy (empleados que entraron tarde)
    retardos_hoy = 0
    sucursales_cache = {}
    entradas_hoy_list = db.query(RegistroAsistencia, Empleado).join(
        Empleado, RegistroAsistencia.empleado_id == Empleado.id
    ).filter(
        RegistroAsistencia.fecha == hoy,
        RegistroAsistencia.tipo == "entrada"
    ).all()

    for reg, emp in entradas_hoy_list:
        if emp.sucursal_id:
            if emp.sucursal_id not in sucursales_cache:
                suc = db.query(Sucursal).filter(Sucursal.id == emp.sucursal_id).first()
                sucursales_cache[emp.sucursal_id] = suc
            suc = sucursales_cache[emp.sucursal_id]
            if suc and suc.hora_entrada:
                tol = suc.tolerancia_minutos or 15
                from datetime import time as dt_time
                mins_total = suc.hora_entrada.hour * 60 + suc.hora_entrada.minute + tol
                hora_limite = dt_time(mins_total // 60, mins_total % 60)
                hora_reg = reg.hora.replace(tzinfo=None) if reg.hora.tzinfo else reg.hora
                if hora_reg > hora_limite:
                    retardos_hoy += 1

    # Faltas hoy
    ids_con_entrada = set(
        r[0] for r in db.query(RegistroAsistencia.empleado_id).filter(
            RegistroAsistencia.fecha == hoy,
            RegistroAsistencia.tipo == "entrada"
        ).all()
    )
    faltas_hoy = total_empleados - len(ids_con_entrada)

    return {
        "total_empleados": total_empleados,
        "con_biometrico": con_biometrico,
        "hoy": {
            "entradas": entradas_hoy,
            "salidas": salidas_hoy,
            "retardos": retardos_hoy,
            "faltas": max(0, faltas_hoy),
        },
        "semana": {"registros": registros_semana},
        "mes": {"registros": registros_mes},
        "tendencia_semanal": [
            {"fecha": row.fecha.isoformat(), "dia": row.fecha.strftime("%a"), "total": row.total, "empleados": row.empleados}
            for row in tendencia_semanal
        ],
    }


# ========================================
# MAIN
# ========================================
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
