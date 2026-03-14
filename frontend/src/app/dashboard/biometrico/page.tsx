"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { getEmpleados, registrarBiometrico, Empleado } from "@/lib/api";

export default function BiometricoPage() {
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [capturing, setCapturing] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [cameraActive, setCameraActive] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    getEmpleados().then(setEmpleados).catch(console.error).finally(() => setLoading(false));
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 640, height: 480 },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (err) {
      console.error("Error camara:", err);
      setResult({ success: false, message: "No se pudo acceder a la camara" });
    }
  }, []);

  const capture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return "";
    const canvas = canvasRef.current;
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";
    ctx.drawImage(videoRef.current, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.85);
  }, []);

  const handleRegister = async () => {
    if (!selectedId) {
      setResult({ success: false, message: "Selecciona un empleado" });
      return;
    }
    setCapturing(true);
    setResult(null);

    try {
      const img = capture();
      if (!img) {
        setResult({ success: false, message: "No se pudo capturar la imagen" });
        return;
      }
      const res = await registrarBiometrico({
        empleado_id: selectedId,
        imagen_base64: img,
        dispositivo: "web_admin",
      });
      setResult({ success: res.success, message: res.message });
      if (res.success) {
        getEmpleados().then(setEmpleados);
      }
    } catch (err: unknown) {
      setResult({ success: false, message: err instanceof Error ? err.message : "Error" });
    } finally {
      setCapturing(false);
    }
  };

  const sinBiometrico = empleados.filter((e) => !e.tiene_biometrico);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Registro Biometrico</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Camera */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Captura Facial</h2>

          <div className="bg-black rounded-xl overflow-hidden aspect-[4/3] relative mb-4">
            <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
            <canvas ref={canvasRef} className="hidden" />
            {cameraActive && (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-52 border-2 border-dashed border-white/50 rounded-[50%]" />
            )}
            {!cameraActive && (
              <div className="absolute inset-0 flex items-center justify-center">
                <button onClick={startCamera} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition">
                  Activar Camara
                </button>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seleccionar empleado...</option>
              {empleados.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.numero_empleado} - {emp.nombre} {emp.apellido_paterno} {emp.tiene_biometrico ? "(ya registrado)" : ""}
                </option>
              ))}
            </select>

            <button
              onClick={handleRegister}
              disabled={!cameraActive || !selectedId || capturing}
              className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-medium transition disabled:opacity-50"
            >
              {capturing ? "Procesando..." : "Registrar Rostro"}
            </button>
          </div>

          {result && (
            <div className={`mt-4 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
              {result.message}
            </div>
          )}
        </div>

        {/* Right: Pending list */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Pendientes de Registro ({sinBiometrico.length})
          </h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {sinBiometrico.length === 0 ? (
              <p className="text-gray-500 text-sm py-4 text-center">Todos los empleados tienen registro biometrico</p>
            ) : (
              sinBiometrico.map((emp) => (
                <button
                  key={emp.id}
                  onClick={() => setSelectedId(emp.id)}
                  className={`w-full text-left px-4 py-3 rounded-lg border transition text-sm ${selectedId === emp.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:bg-gray-50"}`}
                >
                  <p className="font-medium text-gray-900">{emp.nombre} {emp.apellido_paterno}</p>
                  <p className="text-gray-500 text-xs">{emp.numero_empleado} - {emp.puesto || "Sin puesto"}</p>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
