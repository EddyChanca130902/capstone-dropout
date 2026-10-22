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


/**
 * Extrae el mensaje de error de la API.
 *
 * FastAPI devuelve `detail` como texto en los errores de negocio, pero como
 * **array de objetos** en los 422 de validacion de Pydantic. Sin esto, el
 * usuario ve un mensaje generico y no sabe que campo corregir.
 */
export function detalleDeError(error: unknown): string | null {
  const bruto = (error as { error?: { detail?: unknown } })?.error?.detail;
  if (typeof bruto === 'string') {
    return bruto;
  }
  if (Array.isArray(bruto) && bruto.length > 0) {
    const primero = bruto[0] as { loc?: unknown[]; msg?: string };
    const campo = Array.isArray(primero.loc) ? String(primero.loc[primero.loc.length - 1]) : '';
    const mensaje = primero.msg ?? 'valor invalido';
    return campo ? `${campo}: ${mensaje}` : mensaje;
  }
  return null;
}
