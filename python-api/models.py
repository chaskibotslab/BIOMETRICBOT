"""
Modelos SQLAlchemy para PostgreSQL
"""
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Time,
    Integer, Numeric, Text, ForeignKey, LargeBinary
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Empresa(Base):
    __tablename__ = "empresas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    rfc = Column(String(20))
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(255))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    sucursales = relationship("Sucursal", back_populates="empresa")
    empleados = relationship("Empleado", back_populates="empresa")


class Sucursal(Base):
    __tablename__ = "sucursales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"))
    nombre = Column(String(255), nullable=False)
    direccion = Column(Text)
    latitud = Column(Numeric(10, 8))
    longitud = Column(Numeric(11, 8))
    radio_permitido_metros = Column(Integer, default=100)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    empresa = relationship("Empresa", back_populates="sucursales")


class Empleado(Base):
    __tablename__ = "empleados"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"))
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey("sucursales.id"))
    numero_empleado = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido_paterno = Column(String(100), nullable=False)
    apellido_materno = Column(String(100))
    email = Column(String(255))
    telefono = Column(String(20))
    puesto = Column(String(100))
    departamento = Column(String(100))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    empresa = relationship("Empresa", back_populates="empleados")
    datos_biometricos = relationship("DatoBiometrico", back_populates="empleado")
    registros = relationship("RegistroAsistencia", back_populates="empleado")
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno or ''}".strip()


class DatoBiometrico(Base):
    __tablename__ = "datos_biometricos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id = Column(UUID(as_uuid=True), ForeignKey("empleados.id"))
    tipo = Column(String(50), default="facial")
    encoding = Column(LargeBinary, nullable=False)  # Vector 128D
    imagen_referencia = Column(Text)  # Base64 thumbnail
    calidad_registro = Column(Numeric(5, 2))
    dispositivo_registro = Column(String(255))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    empleado = relationship("Empleado", back_populates="datos_biometricos")


class RegistroAsistencia(Base):
    __tablename__ = "registros_asistencia"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id = Column(UUID(as_uuid=True), ForeignKey("empleados.id"))
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey("sucursales.id"))
    tipo = Column(String(20), nullable=False)  # entrada, salida
    
    # Biométrico
    metodo_verificacion = Column(String(50), default="facial")
    confianza_match = Column(Numeric(5, 2))  # Porcentaje
    imagen_captura = Column(Text)
    
    # Ubicación
    latitud = Column(Numeric(10, 8))
    longitud = Column(Numeric(11, 8))
    precision_gps = Column(Numeric(10, 2))
    dentro_rango = Column(Boolean)
    distancia_sucursal = Column(Numeric(10, 2))
    
    # Dispositivo
    dispositivo_id = Column(String(255))
    dispositivo_info = Column(JSONB)
    ip_address = Column(INET)
    
    # Tiempo
    fecha = Column(Date, nullable=False, server_default=func.current_date())
    hora = Column(Time(timezone=True), nullable=False, server_default=func.current_time())
    timestamp_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    empleado = relationship("Empleado", back_populates="registros")


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    empleado_id = Column(UUID(as_uuid=True), ForeignKey("empleados.id"))
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), default="empleado")
    ultimo_acceso = Column(DateTime(timezone=True))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
