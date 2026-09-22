"use client";

import { useState, useCallback, DragEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Heuristicas = {
  entropia: number;
  entropia_alta: boolean;
  extension: string;
  tipo_mime_detectado: string;
  extension_sospechosa: boolean;
  tamano_bytes: number;
};

type ResultadoEscaneo = {
  nombre_archivo: string;
  sha256: string;
  veredicto: "limpio" | "sospechoso" | "infectado" | "error";
  firma_clamav: string | null;
  heuristicas: Heuristicas;
  explicacion_ia: string | null;
};

export default function Home() {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoEscaneo | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function escanear() {
    if (!archivo) return;
    setCargando(true);
    setError(null);
    setResultado(null);

    const formData = new FormData();
    formData.append("archivo", archivo);

    try {
      const respuesta = await fetch(`${API_URL}/scan`, {
        method: "POST",
        body: formData,
      });
      if (!respuesta.ok) {
        const detalle = await respuesta.json().catch(() => null);
        throw new Error(detalle?.detail || `Error ${respuesta.status}`);
      }
      const datos: ResultadoEscaneo = await respuesta.json();
      setResultado(datos);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo completar el escaneo.");
    } finally {
      setCargando(false);
    }
  }

  const onDrop = useCallback((e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setArrastrando(false);
    const soltado = e.dataTransfer.files?.[0];
    if (soltado) {
      setArchivo(soltado);
      setResultado(null);
      setError(null);
    }
  }, []);

  const onDragOver = useCallback((e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setArrastrando(true);
  }, []);

  const onDragLeave = useCallback(() => setArrastrando(false), []);

  return (
    <main>
      <h1>AegisScan</h1>
      <p style={{ color: "var(--texto-suave)" }}>
        Sube un archivo para escanearlo con ClamAV. La IA te explica el
        resultado en lenguaje llano — nunca se le envía el contenido del
        archivo, solo los datos del escaneo.
      </p>

      <div className="tarjeta">
        <label
          className={`zona-drop${arrastrando ? " arrastrando" : ""}`}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
        >
          <input
            type="file"
            style={{ display: "none" }}
            onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
          />
          {archivo ? archivo.name : "Arrastra un archivo aquí o haz clic para elegirlo"}
        </label>

        <div style={{ marginTop: 16 }}>
          <button className="boton" onClick={escanear} disabled={!archivo || cargando}>
            {cargando && <span className="spinner" aria-hidden="true" />}
            {cargando ? "Escaneando…" : "Escanear archivo"}
          </button>
        </div>

        {error && (
          <p style={{ color: "var(--peligro)", marginTop: 16 }}>{error}</p>
        )}

        {resultado && (
          <div className={`resultado ${resultado.veredicto}`}>
            <span className={`etiqueta ${resultado.veredicto}`}>
              {resultado.veredicto}
            </span>
            <p style={{ marginTop: 12 }}>{resultado.explicacion_ia}</p>
            <p style={{ fontSize: 13, color: "var(--texto-suave)" }}>
              {resultado.nombre_archivo} · {resultado.heuristicas.tamano_bytes} bytes
              {resultado.firma_clamav ? ` · Firma: ${resultado.firma_clamav}` : ""}
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
