# Hoja de ruta

Lo que haría falta para pasar de este MVP a un SaaS real, en orden
aproximado de prioridad.

## Para tener usuarios de verdad
- [ ] Autenticación (API keys por usuario/proyecto).
- [ ] Límites de uso y facturación (Stripe u otro), con un plan gratuito
      limitado y planes de pago por volumen de escaneos.
- [ ] Cola de trabajos (Redis + workers) para archivos grandes o picos de
      tráfico, en vez de escaneo síncrono.
- [ ] Persistencia de resultados (base de datos) e historial de escaneos por
      usuario.
- [ ] Panel web con el historial, no solo el formulario de subida.

## Para mejorar la detección
- [ ] Sandbox de análisis dinámico (ejecutar el archivo en un entorno
      aislado y observar su comportamiento) para amenazas que no tienen
      firma todavía.
- [ ] Modelo propio de machine learning entrenado con features estáticas
      (no solo entropía) como señal adicional a ClamAV — necesita un
      dataset etiquetado real, no se puede improvisar sin datos.
- [ ] Integrar más de un motor de firmas (por ejemplo, consultar también
      VirusTotal) y combinar los resultados.

## Para producción
- [ ] Restringir CORS a los orígenes reales (ahora mismo está abierto para
      desarrollo).
- [ ] Límite de tasa (rate limiting) por IP/API key.
- [ ] Logs y métricas (cuántos escaneos, cuántos infectados, latencia).
- [ ] Tests automáticos (unitarios del backend, y un archivo EICAR de
      prueba para verificar que ClamAV lo detecta correctamente).
