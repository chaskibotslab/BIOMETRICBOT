"use client";

import { useState } from "react";
import { changePassword } from "@/lib/api";
import { getAuth } from "@/lib/auth";

export default function ConfiguracionPage() {
  const [form, setForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (form.new_password.length < 6) {
      setError("La nueva contrasena debe tener al menos 6 caracteres");
      return;
    }

    if (form.new_password !== form.confirm_password) {
      setError("Las contrasenas no coinciden");
      return;
    }

    const auth = getAuth();
    if (!auth) return;

    setLoading(true);
    try {
      await changePassword(
        { current_password: form.current_password, new_password: form.new_password },
        auth.token
      );
      setSuccess("Contrasena actualizada correctamente");
      setForm({ current_password: "", new_password: "", confirm_password: "" });
      setTimeout(() => setSuccess(""), 5000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al cambiar contrasena");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Configuracion</h1>

      <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Cambiar Contrasena</h2>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">{error}</div>
        )}
        {success && (
          <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm">{success}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena Actual</label>
            <input
              type="password"
              required
              value={form.current_password}
              onChange={(e) => setForm({ ...form, current_password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nueva Contrasena</label>
            <input
              type="password"
              required
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar Nueva Contrasena</label>
            <input
              type="password"
              required
              value={form.confirm_password}
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white py-2.5 rounded-lg text-sm font-medium transition"
          >
            {loading ? "Guardando..." : "Cambiar Contrasena"}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-md mt-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Informacion del Sistema</h2>
        <div className="space-y-2 text-sm text-gray-600">
          <p><span className="font-medium text-gray-900">Version:</span> 2.0.0</p>
          <p><span className="font-medium text-gray-900">Motor facial:</span> InsightFace (ArcFace)</p>
          <p><span className="font-medium text-gray-900">Precision:</span> 99.8% (LFW benchmark)</p>
        </div>
      </div>
    </div>
  );
}
