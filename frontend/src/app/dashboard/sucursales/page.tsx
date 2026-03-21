"use client";

import { useEffect, useState } from "react";
import {
  getSucursales, getEmpresas, createSucursal, updateSucursal, deleteSucursal,
  Sucursal, Empresa,
} from "@/lib/api";
import { getAuth } from "@/lib/auth";

const emptyForm = {
  empresa_id: "", nombre: "", direccion: "", latitud: "", longitud: "",
  radio_permitido_metros: "100", hora_entrada: "08:00", hora_salida: "17:00", tolerancia_minutos: "15",
};

export default function SucursalesPage() {
  const [sucursales, setSucursales] = useState<Sucursal[]>([]);
  const [empresas, setEmpresas] = useState<Empresa[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [s, e] = await Promise.all([getSucursales(), getEmpresas()]);
      setSucursales(s);
      setEmpresas(e);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditId(null);
    setForm({ ...emptyForm, empresa_id: empresas[0]?.id || "" });
    setError("");
    setSuccess("");
    setShowForm(true);
  }

  function openEdit(s: Sucursal) {
    setEditId(s.id);
    setForm({
      empresa_id: s.empresa_id || "",
      nombre: s.nombre,
      direccion: s.direccion || "",
      latitud: String(s.latitud || ""),
      longitud: String(s.longitud || ""),
      radio_permitido_metros: String(s.radio_permitido_metros),
      hora_entrada: s.hora_entrada || "08:00",
      hora_salida: s.hora_salida || "17:00",
      tolerancia_minutos: String(s.tolerancia_minutos),
    });
    setError("");
    setSuccess("");
    setShowForm(true);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const auth = getAuth();
    if (!auth) return;
    setError("");
    setSaving(true);

    try {
      if (editId) {
        await updateSucursal(editId, {
          nombre: form.nombre,
          direccion: form.direccion || undefined,
          latitud: parseFloat(form.latitud),
          longitud: parseFloat(form.longitud),
          radio_permitido_metros: parseInt(form.radio_permitido_metros),
          hora_entrada: form.hora_entrada || undefined,
          hora_salida: form.hora_salida || undefined,
          tolerancia_minutos: parseInt(form.tolerancia_minutos),
        }, auth.token);
        setSuccess("Sucursal actualizada");
      } else {
        await createSucursal({
          empresa_id: form.empresa_id,
          nombre: form.nombre,
          direccion: form.direccion || undefined,
          latitud: parseFloat(form.latitud),
          longitud: parseFloat(form.longitud),
          radio_permitido_metros: parseInt(form.radio_permitido_metros),
          hora_entrada: form.hora_entrada || undefined,
          hora_salida: form.hora_salida || undefined,
          tolerancia_minutos: parseInt(form.tolerancia_minutos),
        }, auth.token);
        setSuccess("Sucursal creada");
      }
      setShowForm(false);
      loadData();
      setTimeout(() => setSuccess(""), 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string, nombre: string) {
    if (!confirm(`Desactivar sucursal "${nombre}"?`)) return;
    const auth = getAuth();
    if (!auth) return;
    try {
      await deleteSucursal(id, auth.token);
      loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Error");
    }
  }

  const f = (k: string, v: string) => setForm({ ...form, [k]: v });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sucursales</h1>
        <button onClick={openCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition">
          + Nueva Sucursal
        </button>
      </div>

      {success && <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{success}</div>}

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sucursales.map((s) => (
          <div key={s.id} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-gray-900">{s.nombre}</h3>
              <div className="flex gap-1">
                <button onClick={() => openEdit(s)} className="text-blue-600 hover:text-blue-800 text-xs font-medium">Editar</button>
                <span className="text-gray-300">|</span>
                <button onClick={() => handleDelete(s.id, s.nombre)} className="text-red-600 hover:text-red-800 text-xs font-medium">Eliminar</button>
              </div>
            </div>
            {s.direccion && <p className="text-sm text-gray-500 mb-3">{s.direccion}</p>}

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Coordenadas:</span>
                <span className="text-gray-900 font-mono text-xs">{s.latitud?.toFixed(6)}, {s.longitud?.toFixed(6)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Radio permitido:</span>
                <span className="text-gray-900">{s.radio_permitido_metros}m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Horario:</span>
                <span className="text-gray-900 font-medium">
                  {s.hora_entrada || "--:--"} a {s.hora_salida || "--:--"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Tolerancia:</span>
                <span className="text-gray-900">{s.tolerancia_minutos} min</span>
              </div>
            </div>
          </div>
        ))}
        {sucursales.length === 0 && (
          <p className="text-gray-500 col-span-full text-center py-12">No hay sucursales registradas</p>
        )}
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-gray-900 mb-4">{editId ? "Editar" : "Nueva"} Sucursal</h2>

            {error && <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>}

            <form onSubmit={handleSubmit} className="space-y-4">
              {!editId && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
                  <select value={form.empresa_id} onChange={(e) => f("empresa_id", e.target.value)} required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500">
                    {empresas.map((emp) => (
                      <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                <input type="text" required value={form.nombre} onChange={(e) => f("nombre", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ej: Oficina Central" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Direccion</label>
                <input type="text" value={form.direccion} onChange={(e) => f("direccion", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Direccion completa" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Latitud</label>
                  <input type="number" step="any" required value={form.latitud} onChange={(e) => f("latitud", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="-17.783333" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Longitud</label>
                  <input type="number" step="any" required value={form.longitud} onChange={(e) => f("longitud", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="-63.182222" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Radio permitido (metros)</label>
                <input type="number" required value={form.radio_permitido_metros} onChange={(e) => f("radio_permitido_metros", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500" />
              </div>

              <div className="border-t border-gray-200 pt-4">
                <p className="text-sm font-semibold text-gray-900 mb-3">Horario Laboral</p>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Entrada</label>
                    <input type="time" value={form.hora_entrada} onChange={(e) => f("hora_entrada", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Salida</label>
                    <input type="time" value={form.hora_salida} onChange={(e) => f("hora_salida", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-1">Tolerancia (min)</label>
                    <input type="number" value={form.tolerancia_minutos} onChange={(e) => f("tolerancia_minutos", e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)}
                  className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
                  Cancelar
                </button>
                <button type="submit" disabled={saving}
                  className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-blue-400 transition">
                  {saving ? "Guardando..." : editId ? "Actualizar" : "Crear"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
