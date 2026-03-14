"use client";

import { useEffect, useState } from "react";
import { getAsistenciaHoy, RegistroAsistencia } from "@/lib/api";

export default function AsistenciaPage() {
  const [registros, setRegistros] = useState<RegistroAsistencia[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const data = await getAsistenciaHoy();
      setRegistros(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const entradas = registros.filter((r) => r.tipo === "entrada").length;
  const salidas = registros.filter((r) => r.tipo === "salida").length;

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
        <h1 className="text-2xl font-bold text-gray-900">Asistencia Hoy</h1>
        <button onClick={loadData} className="text-sm text-blue-600 hover:underline">
          Actualizar
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{registros.length}</p>
          <p className="text-sm text-gray-500">Total Registros</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{entradas}</p>
          <p className="text-sm text-gray-500">Entradas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{salidas}</p>
          <p className="text-sm text-gray-500">Salidas</p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          {registros.length === 0 ? (
            <p className="text-gray-500 text-center py-12">No hay registros de asistencia hoy</p>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empleado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hora</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confianza</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ubicacion</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Distancia</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {registros.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{r.empleado_nombre}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${r.tipo === "entrada" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                        {r.tipo === "entrada" ? "Entrada" : "Salida"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{r.hora?.slice(0, 5)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{r.confianza_match ? `${r.confianza_match}%` : "--"}</td>
                    <td className="px-6 py-4">
                      <span className={`text-sm ${r.dentro_rango ? "text-green-600" : "text-amber-600"}`}>
                        {r.dentro_rango === null ? "--" : r.dentro_rango ? "En rango" : "Fuera"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {r.distancia_sucursal ? `${Math.round(r.distancia_sucursal)}m` : "--"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
