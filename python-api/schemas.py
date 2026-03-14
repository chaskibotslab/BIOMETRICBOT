"""
Schemas Pydantic para validación de datos
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum


class TipoRegistro(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"


# === EMPLEADOS ===

class EmpleadoCreate(BaseModel):
    empresa_id: UUID
    numero_empleado: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    puesto: Optional[str] = None
    departamento: Optional[str] = None


class EmpleadoResponse(BaseModel):
    id: UUID
    numero_empleado: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str]
    email: Optional[str]
    puesto: Optional[str]
    activo: bool
    tiene_biometrico: bool = False
    
    class Config:
        from_attributes = True


# === BIOMÉTRICO ===

class RegistroBiometricoRequest(BaseModel):
    empleado_id: UUID
    imagen_base64: str = Field(..., min_length=100)
    dispositivo: Optional[str] = None


class RegistroBiometricoResponse(BaseModel):
    success: bool
    message: str
    empleado_id: Optional[UUID] = None
    calidad: Optional[float] = None


# === CHECK-IN ===

class CheckInRequest(BaseModel):
    imagen_base64: str
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    precision_gps: Optional[float] = None
    tipo_registro: TipoRegistro = TipoRegistro.ENTRADA
    sucursal_id: Optional[UUID] = None
    dispositivo_id: Optional[str] = None
    dispositivo_info: Optional[dict] = None


class CheckInResponse(BaseModel):
    success: bool
    message: str
    empleado_id: Optional[UUID] = None
    empleado_nombre: Optional[str] = None
    confianza_facial: Optional[float] = None
    distancia_metros: Optional[float] = None
    dentro_rango: Optional[bool] = None
    registro_id: Optional[UUID] = None
    timestamp: Optional[datetime] = None


# === VERIFICACIÓN ===

class VerificacionRequest(BaseModel):
    imagen_base64: str
    empleado_id: Optional[UUID] = None


class VerificacionResponse(BaseModel):
    success: bool
    matched: bool
    empleado_id: Optional[UUID] = None
    empleado_nombre: Optional[str] = None
    confianza: float = 0.0
    message: str


# === ASISTENCIA ===

class RegistroAsistenciaResponse(BaseModel):
    id: UUID
    empleado_id: UUID
    empleado_nombre: Optional[str] = None
    tipo: str
    fecha: date
    hora: time
    confianza_match: Optional[float] = None
    dentro_rango: Optional[bool] = None
    distancia_sucursal: Optional[float] = None
    
    class Config:
        from_attributes = True


# === EMPRESAS Y SUCURSALES ===

class EmpresaCreate(BaseModel):
    nombre: str
    rfc: Optional[str] = None
    email: Optional[str] = None


class EmpresaResponse(BaseModel):
    id: UUID
    nombre: str
    rfc: Optional[str]
    activo: bool
    
    class Config:
        from_attributes = True


class SucursalCreate(BaseModel):
    empresa_id: UUID
    nombre: str
    direccion: Optional[str] = None
    latitud: float
    longitud: float
    radio_permitido_metros: int = 100


class SucursalResponse(BaseModel):
    id: UUID
    nombre: str
    latitud: float
    longitud: float
    radio_permitido_metros: int
    
    class Config:
        from_attributes = True
