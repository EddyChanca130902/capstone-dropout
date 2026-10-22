/**
 * Mensajes de error accionables segun el tipo de fallo.
 *
 * El caso habitual del hosting gratuito es el arranque en frio: la primera
 * peticion tras 15 min de inactividad tarda ~20 s. El usuario debe saber que
 * no es un fallo de la aplicacion.
 */
export function mensajeDeError(error: unknown, que: string): string {
  const status = (error as { status?: number })?.status ?? 0;

  if (status === 0) {
    return (
      `No se pudo conectar con la API para cargar ${que}. Si es la primera visita, ` +
      'el servidor puede estar activandose (el hosting gratuito se duerme tras 15 ' +
      'minutos sin trafico): espera unos segundos y pulsa Reintentar.'
    );
  }
  if (status === 401) {
    return 'Tu sesion ha caducado. Vuelve a iniciar sesion.';
  }
  if (status === 503) {
    return (
      'El servicio no esta disponible en este momento (posiblemente falta aplicar ' +
      'una migracion de la base de datos). Revisa el estado en /health.'
    );
  }
  const detalle =
    typeof error === 'object' && error !== null && 'error' in error
      ? ((error as { error?: { detail?: unknown } }).error?.detail ?? '')
      : '';
  return typeof detalle === 'string' && detalle
    ? detalle
    : `No se pudo cargar ${que}. Intentalo de nuevo en unos segundos.`;
}
