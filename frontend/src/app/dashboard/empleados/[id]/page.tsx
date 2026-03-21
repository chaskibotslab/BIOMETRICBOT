"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getReporteEmpleado, ReporteEmpleado } from "@/lib/api";
import Link from "next/link";

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0];
}

export default function EmpleadoReportePage() {
  const params = useParams();
  const id = params.id as string;

  const hoy = formatDate(new Date());
  const hace30 = formatDate(new Date(Date.now() - 30 * 86400000));

  const [reporte, setReporte] = useState<ReporteEmpleado | null>(null);
  const [loading, setLoading] = useState(true);
  const [fechaDesde, setFechaDesde] = useState(hace30);
  const [fechaHasta, setFechaHasta] = useState(hoy);

  useEffect(() => {
    loadReport();
  }, [id, fechaDesde, fechaHasta]);

  async function loadReport() {
    setLoading(true);
    try {
      const data = await getReporteEmpleado(id, fechaDesde, fechaHasta);
      setReporte(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function exportCSV() {
    if (!reporte) return;
    const headers = ["Fecha", "Hora", "Tipo", "Retardo", "Confianza %", "Ubicacion", "Distancia (m)"];
    const rows = reporte.registros.map((r) => [
      r.fecha,
      r.hora || "",
      r.tipo === "entrada" ? "Entrada" : "Salida",
      r.retardo ? "SI" : "",
      r.confianza_match != null ? String(r.confianza_match) : "",
      r.dentro_rango === null ? "" : r.dentro_rango ? "En rango" : "Fuera",
      r.distancia_sucursal != null ? String(Math.round(r.distancia_sucursal)) : "",
    ]);
    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reporte_${reporte.empleado.numero_empleado}_${fechaDesde}_${fechaHasta}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading && !reporte) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!reporte) {
    return <p className="text-red-600">No se pudo cargar el reporte</p>;
  }

  const { empleado, sucursal, estadisticas: s } = reporte;
  const asistenciaPct = reporte.periodo.dias_laborales > 0
    ? Math.round((s.dias_asistidos / reporte.periodo.dias_laborales) * 100)
    : 0;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <Link href="/dashboard/empleados" className="text-sm text-blue-600 hover:underline mb-1 inline-block">&larr; Volver a Empleados</Link>
          <h1 className="text-2xl font-bold text-gray-900">{empleado.nombre}</h1>
          <p className="text-sm text-gray-500">#{empleado.numero_empleado} - {empleado.puesto || "Sin puesto"} {empleado.departamento ? `| ${empleado.departamento}` : ""}</p>
        </div>
        <button onClick={exportCSV} className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
          Exportar CSV
        </button>
      </div>

      {/* Date filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Desde</label>
            <input type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Hasta</label>
            <input type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex gap-2">
            {[7, 15, 30, 90].map((d) => (
              <button key={d} onClick={() => { setFechaDesde(formatDate(new Date(Date.now() - d * 86400000))); setFechaHasta(hoy); }}
                className="px-2.5 py-2 text-xs bg-gray-100 hover:bg-blue-100 hover:text-blue-700 rounded-md text-gray-600 transition">
                {d}d
              </button>
            ))}
          </div>
          {loading && <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />}
        </div>
      </div>

      {/* Sucursal info */}
      {sucursal.nombre && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 text-sm">
          <span className="font-medium text-blue-900">Sucursal: {sucursal.nombre}</span>
          <span className="text-blue-700 ml-4">
            Horario: {sucursal.hora_entrada || "--"} a {sucursal.hora_salida || "--"} | Tolerancia: {sucursal.tolerancia_minutos}min
          </span>
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">{asistenciaPct}%</p>
          <p className="text-[10px] text-gray-500 uppercase">Asistencia</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{s.dias_asistidos}</p>
          <p className="text-[10px] text-gray-500 uppercase">Dias Asistidos</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{s.dias_faltados}</p>
          <p className="text-[10px] text-gray-500 uppercase">Faltas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-amber-600">{s.retardos}</p>
          <p className="text-[10px] text-gray-500 uppercase">Retardos</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{s.total_entradas}</p>
          <p className="text-[10px] text-gray-500 uppercase">Entradas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-gray-900">{s.total_salidas}</p>
          <p className="text-[10px] text-gray-500 uppercase">Salidas</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
          <p className="text-2xl font-bold text-purple-600">{s.horas_trabajadas}h</p>
          <p className="text-[10px] text-gray-500 uppercase">Horas ({s.promedio_horas_dia}h/dia)</p>
        </div>
      </div>

      {/* Records table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">Registros Detallados</h2>
          <span className="text-xs text-gray-400">{reporte.registros.length} registros | {reporte.periodo.dias_laborales} dias laborales</span>
        </div>
        <div className="overflow-x-auto">
          {reporte.registros.length === 0 ? (
            <p className="text-gray-500 text-center py-12 text-sm">Sin registros en este periodo</p>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hora</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confianza</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ubicacion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reporte.registros.map((r) => (
                  <tr key={r.id} className={`hover:bg-gray-50 ${r.retardo ? "bg-amber-50/50" : ""}`}>
                    <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{r.fecha}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-medium whitespace-nowrap">{r.hora}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${r.tipo === "entrada" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                        {r.tipo === "entrada" ? "Entrada" : "Salida"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {r.retardo ? (
                        <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">Retardo</span>
                      ) : r.tipo === "entrada" ? (
                        <span className="text-xs text-green-600">A tiempo</span>
                      ) : (
                        <span className="text-xs text-gray-400">--</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{r.confianza_match != null ? `${r.confianza_match}%` : "--"}</td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${r.dentro_rango === null ? "text-gray-400" : r.dentro_rango ? "text-green-600" : "text-amber-600"}`}>
                        {r.dentro_rango === null ? "--" : r.dentro_rango ? "En rango" : "Fuera"}
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
