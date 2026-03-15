"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { realizarCheckin, CheckInResponse } from "@/lib/api";

interface GeoLocation {
  lat: number;
  lon: number;
  acc: number;
}

export default function CheckinPage() {
  const [location, setLocation] = useState<GeoLocation | null>(null);
  const [gpsError, setGpsError] = useState("");
  const [cameraReady, setCameraReady] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<CheckInResponse | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [dateTime, setDateTime] = useState("");

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    initCamera();
    initGPS();
    const timer = setInterval(() => {
      const now = new Date();
      setDateTime(
        now.toLocaleDateString("es", { weekday: "long", day: "numeric", month: "long" }) +
        " - " +
        now.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      );
    }, 1000);
    return () => {
      clearInterval(timer);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  async function initCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute("playsinline", "true");
        videoRef.current.setAttribute("muted", "true");
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
          if (canvasRef.current && videoRef.current) {
            canvasRef.current.width = videoRef.current.videoWidth;
            canvasRef.current.height = videoRef.current.videoHeight;
          }
          setCameraReady(true);
        };
      }
    } catch {
      alert("No se pudo acceder a la camara. Verifica los permisos en Ajustes > Safari > Camara.");
    }
  }

  function initGPS() {
    if (!navigator.geolocation) {
      setGpsError("GPS no disponible");
      return;
    }
    // First try getCurrentPosition for iOS (faster permission prompt)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          acc: pos.coords.accuracy,
        });
        setGpsError("");
      },
      (err) => {
        if (err.code === 1) {
          setGpsError("Permiso denegado. Activa ubicacion en Ajustes.");
        } else if (err.code === 2) {
          setGpsError("GPS no disponible");
        } else {
          setGpsError("Obteniendo ubicacion...");
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
    // Then watch for updates
    navigator.geolocation.watchPosition(
      (pos) => {
        setLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          acc: pos.coords.accuracy,
        });
        setGpsError("");
      },
      (err) => {
        if (!location) {
          if (err.code === 1) setGpsError("Permiso denegado. Activa ubicacion en Ajustes.");
          else setGpsError("Error GPS. Reintentando...");
        }
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 30000 }
    );
  }

  const capture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return "";
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return "";
    ctx.drawImage(videoRef.current, 0, 0);
    return canvasRef.current.toDataURL("image/jpeg", 0.85);
  }, []);

  const doCheckin = async (tipo: "entrada" | "salida") => {
    if (!cameraReady) return;
    setProcessing(true);
    setShowResult(false);

    try {
      const img = capture();
      const res = await realizarCheckin({
        imagen_base64: img,
        latitud: location?.lat ?? 0,
        longitud: location?.lon ?? 0,
        precision_gps: location?.acc ?? 9999,
        tipo_registro: tipo,
        dispositivo_id: "pwa_" + Date.now(),
      });
      setResult(res);
      setShowResult(true);
    } catch (err: unknown) {
      setResult({
        success: false,
        message: err instanceof Error ? err.message : "Error de conexion",
        empleado_id: null,
        empleado_nombre: null,
        confianza_facial: null,
        distancia_metros: null,
        dentro_rango: null,
        registro_id: null,
        timestamp: null,
      });
      setShowResult(true);
    } finally {
      setProcessing(false);
    }
  };

  const ready = cameraReady;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1e3a5f] to-[#0f172a] text-white">
      <div className="max-w-md mx-auto px-4 py-6">
        {/* Header */}
        <div className="text-center mb-4">
          <h1 className="text-2xl font-bold">Check-In</h1>
          <p className="text-sm text-gray-300 mt-1">{dateTime || "Cargando..."}</p>
        </div>

        {/* Camera */}
        <div className="bg-black rounded-2xl overflow-hidden relative aspect-[3/4] max-h-[400px] mb-4">
          <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          <canvas ref={canvasRef} className="hidden" />
          <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-44 h-56 border-3 rounded-[50%] transition-colors ${ready ? "border-green-400 border-solid" : "border-white/40 border-dashed"}`} />
        </div>

        {/* Location */}
        <div className="bg-white/10 rounded-xl p-4 mb-4 text-sm">
          <div className="flex justify-between mb-2">
            <span className="text-gray-300">Ubicacion:</span>
            <span>{location ? "OK" : (gpsError || "Obteniendo...")}</span>
          </div>
          <div className="flex justify-between mb-2">
            <span className="text-gray-300">Lat:</span>
            <span>{location ? location.lat.toFixed(6) : "--"}</span>
          </div>
          <div className="flex justify-between mb-2">
            <span className="text-gray-300">Lon:</span>
            <span>{location ? location.lon.toFixed(6) : "--"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-300">Precision:</span>
            <span>{location ? `${Math.round(location.acc)}m` : "--"}</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => doCheckin("entrada")}
            disabled={!ready || processing}
            className="bg-green-500 hover:bg-green-600 disabled:opacity-40 text-white py-4 rounded-xl font-semibold text-lg transition"
          >
            {processing ? "..." : "Entrada"}
          </button>
          <button
            onClick={() => doCheckin("salida")}
            disabled={!ready || processing}
            className="bg-red-500 hover:bg-red-600 disabled:opacity-40 text-white py-4 rounded-xl font-semibold text-lg transition"
          >
            {processing ? "..." : "Salida"}
          </button>
        </div>

        {/* Admin link */}
        <div className="text-center mt-6">
          <a href="/" className="text-sm text-gray-400 hover:text-white transition">
            Panel Admin
          </a>
        </div>
      </div>

      {/* Processing overlay */}
      {processing && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-white/30 border-t-white" />
        </div>
      )}

      {/* Result modal */}
      {showResult && result && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center text-gray-900">
            <div className="text-6xl mb-4">{result.success ? "\u2705" : "\u274C"}</div>
            <h3 className="text-xl font-bold mb-2">
              {result.success ? "Registrado!" : "Error"}
            </h3>
            <p className="text-gray-600 mb-2">
              {result.success ? result.empleado_nombre || "Usuario" : result.message}
            </p>
            {result.success && (
              <p className="text-sm text-gray-500">
                Confianza: {result.confianza_facial || "--"}%
                {result.distancia_metros !== null && ` | Distancia: ${Math.round(result.distancia_metros)}m`}
              </p>
            )}
            <button
              onClick={() => setShowResult(false)}
              className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium transition"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
