"use client";

import { useEffect, useState, useCallback } from "react";
import {
  buscarAsistencia,
  getResumenAsistencia,
  getEmpleados,
  RegistroAsistencia,
  ResumenAsistencia,
  Empleado,
} from "@/lib/api";

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0];
}

function quickRange(days: number): { desde: string; hasta: string } {
  const hasta = new Date();
  const desde = new Date();
  desde.setDate(desde.getDate() - days);
  return { desde: formatDate(desde), hasta: formatDate(hasta) };
}

export default function AsistenciaPage() {
  const hoy = formatDate(new Date());
  const hace7 = formatDate(new Date(Date.now() - 7 * 86400000));

  const [registros, setRegistros] = useState<RegistroAsistencia[]>([]);
  const [resumen, setResumen] = useState<ResumenAsistencia | null>(null);
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [loading, setLoading] = useState(true);

  const [fechaDesde, setFechaDesde] = useState(hace7);
  const [fechaHasta, setFechaHasta] = useState(hoy);
  const [empleadoId, setEmpleadoId] = useState("");
  const [tipo, setTipo] = useState("");
  const [buscar, setBuscar] = useState("");
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [regs, stats] = await Promise.all([
        buscarAsistencia({
          fecha_desde: fechaDesde,
          fecha_hasta: fechaHasta,
          empleado_id: empleadoId || undefined,
          tipo: tipo || undefined,
          buscar: buscar || undefined,
        }),
        getResumenAsistencia(fechaDesde, fechaHasta),
      ]);
      setRegistros(regs);
      setResumen(stats);
    } catch (err) {
      console.error("Error cargando asistencia:", err);
    } finally {
      setLoading(false);
    }
  }, [fechaDesde, fechaHasta, empleadoId, tipo, buscar]);

  useEffect(() => {
    getEmpleados().then(setEmpleados).catch(console.error);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function handleSearch(value: string) {
    setBuscar(value);
    if (searchTimeout) clearTimeout(searchTimeout);
    setSearchTimeout(setTimeout(() => {}, 400));
  }

  function applyQuickRange(days: number) {
    const r = quickRange(days);
    setFechaDesde(r.desde);
    setFechaHasta(r.hasta);
  }

  function exportCSV() {
    if (registros.length === 0) return;
    const headers = ["Fecha", "Hora", "Empleado", "Tipo", "Confianza %", "Ubicacion", "Distancia (m)"];
    const rows = registros.map((r) => [
      r.fecha,
      r.hora?.slice(0, 5) || "",
      r.empleado_nombre || "",
      r.tipo === "entrada" ? "Entrada" : "Salida",
      r.confianza_match != null ? String(r.confianza_match) : "",
      r.dentro_rango === null ? "" : r.dentro_rango ? "En rango" : "Fuera",
      r.distancia_sucursal != null ? String(Math.round(r.distancia_sucursal)) : "",
    ]);
    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `asistencia_${fechaDesde}_${fechaHasta}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const maxBarValue = resumen?.por_dia?.length
    ? Math.max(...resumen.por_dia.map((d) => d.total), 1)
    : 1;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reportes de Asistencia</h1>
        <div className="flex gap-2">
          <button onClick={loadData} className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 transition">
            Actualizar
          </button>
          <button onClick={exportCSV} disabled={registros.length === 0} className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-40 transition">
            Exportar CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
          {/* Date From */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Desde</label>
            <input
              type="date"
              value={fechaDesde}
              onChange={(e) => setFechaDesde(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          {/* Date To */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Hasta</label>
            <input
              type="date"
              value={fechaHasta}
              onChange={(e) => setFechaHasta(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          {/* Employee */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Empleado</label>
            <select
              value={empleadoId}
              onChange={(e) => setEmpleadoId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              {empleados.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.nombre} {emp.apellido_paterno}
                </option>
              ))}
            </select>
          </div>
          {/* Type */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Tipo</label>
            <select
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="entrada">Entrada</option>
              <option value="salida">Salida</option>
            </select>
          </div>
          {/* Search */}
          <div className="lg:col-span-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Buscar</label>
            <input
              type="text"
              value={buscar}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Nombre, apellido, # empleado..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        {/* Quick ranges */}
        <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-400 self-center mr-1">Rapido:</span>
          {[
            { label: "Hoy", days: 0 },
            { label: "7 dias", days: 7 },
            { label: "15 dias", days: 15 },
            { label: "30 dias", days: 30 },
            { label: "90 dias", days: 90 },
          ].map((r) => (
            <button
              key={r.days}
              onClick={() => {
                if (r.days === 0) {
                  setFechaDesde(hoy);
                  setFechaHasta(hoy);
                } else {
                  applyQuickRange(r.days);
                }
              }}
              className="px-2.5 py-1 text-xs bg-gray-100 hover:bg-blue-100 hover:text-blue-700 rounded-md text-gray-600 transition"
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{resumen.total_registros}</p>
            <p className="text-xs text-gray-500">Total Registros</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{resumen.entradas}</p>
            <p className="text-xs text-gray-500">Entradas</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-red-600">{resumen.salidas}</p>
            <p className="text-xs text-gray-500">Salidas</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{resumen.empleados_unicos}</p>
            <p className="text-xs text-gray-500">Empleados</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-purple-600">{resumen.dias_con_registro}</p>
            <p className="text-xs text-gray-500">Dias Activos</p>
          </div>
        </div>
      )}

      {/* Daily Chart */}
      {resumen && resumen.por_dia.length > 1 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Registros por Dia</h2>
          <div className="flex items-end gap-1 h-32 overflow-x-auto">
            {resumen.por_dia.map((d) => (
              <div key={d.fecha} className="flex flex-col items-center min-w-[28px] flex-1 group relative">
                <div
                  className="w-full bg-blue-500 rounded-t-sm transition-all hover:bg-blue-600 min-h-[4px]"
                  style={{ height: `${(d.total / maxBarValue) * 100}%` }}
                />
                <span className="text-[9px] text-gray-400 mt-1 whitespace-nowrap">
                  {d.fecha.slice(5)}
                </span>
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition whitespace-nowrap pointer-events-none">
                  {d.total} reg. | {d.empleados} emp.
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">
            Registros {loading && <span className="text-gray-400 font-normal ml-2">cargando...</span>}
          </h2>
          <span className="text-xs text-gray-400">{registros.length} resultados</span>
        </div>
        <div className="overflow-x-auto">
          {registros.length === 0 && !loading ? (
            <p className="text-gray-500 text-center py-12">No se encontraron registros con los filtros seleccionados</p>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hora</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empleado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confianza</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ubicacion</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Distancia</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {registros.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{r.fecha}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-medium whitespace-nowrap">{r.hora?.slice(0, 5)}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{r.empleado_nombre}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${r.tipo === "entrada" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                        {r.tipo === "entrada" ? "Entrada" : "Salida"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{r.confianza_match != null ? `${r.confianza_match}%` : "--"}</td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${r.dentro_rango === null ? "text-gray-400" : r.dentro_rango ? "text-green-600" : "text-amber-600"}`}>
                        {r.dentro_rango === null ? "--" : r.dentro_rango ? "En rango" : "Fuera"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {r.distancia_sucursal != null ? `${Math.round(r.distancia_sucursal)}m` : "--"}
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
