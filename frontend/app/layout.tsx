import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisScan",
  description: "Escaneo de archivos con ClamAV, explicado en lenguaje llano por IA.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
