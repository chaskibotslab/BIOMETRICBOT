const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions {
  method?: string;
  body?: unknown;
  token?: string;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { method = "GET", body, token } = options;
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error de conexion" }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}

// Auth
export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
  rol: string;
}

export function login(username: string, password: string) {
  return apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: { username, password },
  });
}

export function getMe(token: string) {
  return apiFetch<{ sub: string; username: string; rol: string }>("/api/auth/me", { token });
}

// Empresas
export interface Empresa {
  id: string;
  nombre: string;
  rfc: string | null;
  activo: boolean;
}

export function getEmpresas() {
  return apiFetch<Empresa[]>("/api/empresas");
}

export function createEmpresa(data: { nombre: string; rfc?: string; email?: string }, token: string) {
  return apiFetch<Empresa>("/api/empresas", { method: "POST", body: data, token });
}

// Sucursales
export interface Sucursal {
  id: string;
  nombre: string;
  latitud: number;
  longitud: number;
  radio_permitido_metros: number;
}

export function getSucursales() {
  return apiFetch<Sucursal[]>("/api/sucursales");
}

export function createSucursal(data: { empresa_id: string; nombre: string; direccion?: string; latitud: number; longitud: number; radio_permitido_metros?: number }, token: string) {
  return apiFetch<Sucursal>("/api/sucursales", { method: "POST", body: data, token });
}

// Empleados
export interface Empleado {
  id: string;
  numero_empleado: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string | null;
  email: string | null;
  puesto: string | null;
  activo: boolean;
  tiene_biometrico: boolean;
}

export function getEmpleados(empresaId?: string) {
  const qs = empresaId ? `?empresa_id=${empresaId}` : "";
  return apiFetch<Empleado[]>(`/api/empleados${qs}`);
}

export function createEmpleado(data: {
  empresa_id: string;
  numero_empleado: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  email?: string;
  puesto?: string;
  departamento?: string;
}, token: string) {
  return apiFetch<Empleado>("/api/empleados", { method: "POST", body: data, token });
}

export function updateEmpleado(id: string, data: {
  nombre?: string;
  apellido_paterno?: string;
  apellido_materno?: string;
  email?: string;
  puesto?: string;
  departamento?: string;
  activo?: boolean;
}, token: string) {
  return apiFetch<Empleado>(`/api/empleados/${id}`, { method: "PUT", body: data, token });
}

// Biometrico
export interface RegistroBiometricoResponse {
  success: boolean;
  message: string;
  empleado_id: string | null;
  calidad: number | null;
}

export function registrarBiometrico(data: { empleado_id: string; imagen_base64: string; dispositivo?: string }) {
  return apiFetch<RegistroBiometricoResponse>("/api/biometrico/registrar", { method: "POST", body: data });
}

// Check-in
export interface CheckInResponse {
  success: boolean;
  message: string;
  empleado_id: string | null;
  empleado_nombre: string | null;
  confianza_facial: number | null;
  distancia_metros: number | null;
  dentro_rango: boolean | null;
  registro_id: string | null;
  timestamp: string | null;
}

export function realizarCheckin(data: {
  imagen_base64: string;
  latitud: number;
  longitud: number;
  precision_gps?: number;
  tipo_registro: "entrada" | "salida";
  sucursal_id?: string;
  dispositivo_id?: string;
}) {
  return apiFetch<CheckInResponse>("/api/checkin", { method: "POST", body: data });
}

// Reportes
export interface RegistroAsistencia {
  id: string;
  empleado_id: string;
  empleado_nombre: string | null;
  tipo: string;
  fecha: string;
  hora: string;
  confianza_match: number | null;
  dentro_rango: boolean | null;
  distancia_sucursal: number | null;
}

export function getAsistenciaHoy() {
  return apiFetch<RegistroAsistencia[]>("/api/asistencia/hoy");
}

// Cambiar contraseña
export function changePassword(data: { current_password: string; new_password: string }, token: string) {
  return apiFetch<{ message: string }>("/api/auth/change-password", { method: "POST", body: data, token });
}

// Health
export function getHealth() {
  return apiFetch<{ status: string; database: string }>("/health");
}
