"use client";

import { useEffect, useState } from "react";
import { getDashboardStats, getFaltas, getAsistenciaHoy, DashboardStats, FaltasResponse, RegistroAsistencia } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [faltas, setFaltas] = useState<FaltasResponse | null>(null);
  const [registros, setRegistros] = useState<RegistroAsistencia[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, f, r] = await Promise.all([getDashboardStats(), getFaltas(), getAsistenciaHoy()]);
        setStats(s);
        setFaltas(f);
        setRegistros(r);
      } catch (err) {
        console.error("Error:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const maxBar = stats.tendencia_semanal.length ? Math.max(...stats.tendencia_semanal.map((d) => d.total), 1) : 1;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Top stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Empleados</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{stats.total_empleados}</p>
          <p className="text-xs text-gray-400 mt-1">{stats.con_biometrico} con biometrico</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Entradas Hoy</p>
          <p className="text-3xl font-bold text-green-600 mt-1">{stats.hoy.entradas}</p>
          <p className="text-xs text-gray-400 mt-1">{stats.hoy.salidas} salidas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Retardos Hoy</p>
          <p className="text-3xl font-bold text-amber-600 mt-1">{stats.hoy.retardos}</p>
          <p className="text-xs text-gray-400 mt-1">despues de tolerancia</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Faltas Hoy</p>
          <p className="text-3xl font-bold text-red-600 mt-1">{stats.hoy.faltas}</p>
          <p className="text-xs text-gray-400 mt-1">sin registro de entrada</p>
        </div>
      </div>

      {/* Second row: weekly/monthly + chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Weekly trend chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Tendencia Semanal</h2>
            <div className="flex gap-4 text-xs text-gray-500">
              <span>Semana: <strong className="text-gray-900">{stats.semana.registros}</strong> reg.</span>
              <span>Mes: <strong className="text-gray-900">{stats.mes.registros}</strong> reg.</span>
            </div>
          </div>
          {stats.tendencia_semanal.length > 0 ? (
            <div className="flex items-end gap-2 h-36">
              {stats.tendencia_semanal.map((d) => (
                <div key={d.fecha} className="flex flex-col items-center flex-1 group relative">
                  <div
                    className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600 min-h-[6px]"
                    style={{ height: `${(d.total / maxBar) * 100}%` }}
                  />
                  <span className="text-[10px] text-gray-500 mt-2 font-medium">{d.dia}</span>
                  <span className="text-[9px] text-gray-400">{d.fecha.slice(5)}</span>
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition whitespace-nowrap pointer-events-none z-10">
                    {d.total} reg. | {d.empleados} emp.
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">Sin datos esta semana</p>
          )}
        </div>

        {/* Faltas panel */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-900">Sin Entrada Hoy</h2>
            {faltas && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">{faltas.sin_entrada}</span>}
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {faltas && faltas.faltantes.length > 0 ? (
              faltas.faltantes.slice(0, 10).map((emp) => (
                <div key={emp.id} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{emp.nombre}</p>
                    <p className="text-[10px] text-gray-400">{emp.numero_empleado} - {emp.puesto || "Sin puesto"}</p>
                  </div>
                  {!emp.tiene_biometrico && (
                    <span className="text-[9px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">Sin bio</span>
                  )}
                </div>
              ))
            ) : (
              <p className="text-green-600 text-sm text-center py-4">Todos presentes</p>
            )}
            {faltas && faltas.faltantes.length > 10 && (
              <p className="text-xs text-gray-400 text-center">+{faltas.faltantes.length - 10} mas...</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent records table */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">Registros de Hoy</h2>
          <span className="text-xs text-gray-400">{registros.length} registros</span>
        </div>
        <div className="overflow-x-auto">
          {registros.length === 0 ? (
            <p className="text-gray-500 text-center py-12 text-sm">No hay registros hoy</p>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empleado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hora</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confianza</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ubicacion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {registros.slice(0, 15).map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{r.empleado_nombre}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.tipo === "entrada" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                        {r.tipo === "entrada" ? "Entrada" : "Salida"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{r.hora?.slice(0, 5)}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{r.confianza_match ? `${r.confianza_match}%` : "--"}</td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${r.dentro_rango ? "text-green-600" : "text-amber-600"}`}>
                        {r.dentro_rango ? "En rango" : "Fuera"}
                      </span>
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
