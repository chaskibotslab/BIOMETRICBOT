-- ============================================
-- SISTEMA BIOMÉTRICO - PostgreSQL
-- Ejecutar en pgAdmin o psql
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- EMPRESAS
CREATE TABLE IF NOT EXISTS empresas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    rfc VARCHAR(20),
    direccion TEXT,
    telefono VARCHAR(20),
    email VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- SUCURSALES
CREATE TABLE IF NOT EXISTS sucursales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID REFERENCES empresas(id),
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    radio_permitido_metros INTEGER DEFAULT 100,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- EMPLEADOS
CREATE TABLE IF NOT EXISTS empleados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID REFERENCES empresas(id),
    sucursal_id UUID REFERENCES sucursales(id),
    numero_empleado VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    email VARCHAR(255),
    telefono VARCHAR(20),
    puesto VARCHAR(100),
    departamento VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- DATOS BIOMÉTRICOS
CREATE TABLE IF NOT EXISTS datos_biometricos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID REFERENCES empleados(id) ON DELETE CASCADE,
    tipo VARCHAR(50) DEFAULT 'facial',
    encoding BYTEA NOT NULL,
    imagen_referencia TEXT,
    calidad_registro DECIMAL(5, 2),
    dispositivo_registro VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(empleado_id, tipo)
);

-- REGISTROS DE ASISTENCIA
CREATE TABLE IF NOT EXISTS registros_asistencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID REFERENCES empleados(id),
    sucursal_id UUID REFERENCES sucursales(id),
    tipo VARCHAR(20) NOT NULL,
    metodo_verificacion VARCHAR(50) DEFAULT 'facial',
    confianza_match DECIMAL(5, 2),
    imagen_captura TEXT,
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    precision_gps DECIMAL(10, 2),
    dentro_rango BOOLEAN,
    distancia_sucursal DECIMAL(10, 2),
    dispositivo_id VARCHAR(255),
    dispositivo_info JSONB,
    ip_address INET,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    hora TIME WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIME,
    timestamp_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- USUARIOS DEL SISTEMA
CREATE TABLE IF NOT EXISTS usuarios_sistema (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empleado_id UUID REFERENCES empleados(id),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(50) DEFAULT 'empleado',
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_registros_fecha ON registros_asistencia(fecha);
CREATE INDEX IF NOT EXISTS idx_registros_empleado ON registros_asistencia(empleado_id);
CREATE INDEX IF NOT EXISTS idx_biometricos_empleado ON datos_biometricos(empleado_id);

-- DATOS INICIALES
INSERT INTO empresas (nombre, rfc, email) 
VALUES ('Mi Empresa', 'EMPR123456789', 'info@miempresa.com')
ON CONFLICT DO NOTHING;

-- Usuario admin (password: admin123)
INSERT INTO usuarios_sistema (username, password_hash, rol)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VpRUPEaHYdN1iy', 'admin')
ON CONFLICT (username) DO NOTHING;

SELECT 'Base de datos creada exitosamente ✅' as resultado;
