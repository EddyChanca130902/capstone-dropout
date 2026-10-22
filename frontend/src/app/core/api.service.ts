import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { catchError, firstValueFrom, map } from 'rxjs';
import { environment } from '../../environments/environment';
import { Estudiante, Evaluacion, Intervencion, KpiInforme, Prediccion, Resumen } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  predecir(estudiante: Estudiante): Promise<Prediccion> {
    return firstValueFrom(this.http.post<Prediccion>(`${this.base}/predict`, estudiante));
  }

  crearEvaluacion(estudiante: Estudiante): Promise<Evaluacion> {
    return firstValueFrom(this.http.post<Evaluacion>(`${this.base}/evaluaciones`, estudiante));
  }

  listarEvaluaciones(params: { limite?: number; area?: string; nivel?: string } = {}): Promise<{
    total: number;
    datos: Evaluacion[];
  }> {
    let httpParams = new HttpParams().set('limite', params.limite ?? 100);
    if (params.area) {
      httpParams = httpParams.set('area', params.area);
    }
    if (params.nivel) {
      httpParams = httpParams.set('nivel', params.nivel);
    }
    return firstValueFrom(
      this.http.get<{ total: number; datos: Evaluacion[] }>(`${this.base}/evaluaciones`, { params: httpParams }),
    );
  }

  actualizarEvaluacion(id: number, cambios: Partial<Evaluacion>): Promise<Evaluacion> {
    return firstValueFrom(this.http.patch<Evaluacion>(`${this.base}/evaluaciones/${id}`, cambios));
  }

  eliminarEvaluacion(id: number): Promise<{ eliminado: boolean }> {
    return firstValueFrom(this.http.delete<{ eliminado: boolean }>(`${this.base}/evaluaciones/${id}`));
  }

  resumen(): Promise<Resumen> {
    return firstValueFrom(this.http.get<Resumen>(`${this.base}/dashboard/resumen`));
  }

  // --- Intervenciones de acompanamiento ---------------------------------
  listarIntervenciones(params: { limite?: number; dni?: string } = {}): Promise<{
    total: number;
    datos: Intervencion[];
  }> {
    let httpParams = new HttpParams().set('limite', params.limite ?? 100);
    if (params.dni) {
      httpParams = httpParams.set('dni', params.dni);
    }
    return firstValueFrom(
      this.http.get<{ total: number; datos: Intervencion[] }>(`${this.base}/intervenciones`, { params: httpParams }),
    );
  }

  crearIntervencion(intervencion: Partial<Intervencion>): Promise<Intervencion> {
    return firstValueFrom(this.http.post<Intervencion>(`${this.base}/intervenciones`, intervencion));
  }

  actualizarIntervencion(id: number, cambios: Partial<Intervencion>): Promise<Intervencion> {
    return firstValueFrom(this.http.patch<Intervencion>(`${this.base}/intervenciones/${id}`, cambios));
  }

  eliminarIntervencion(id: number): Promise<{ eliminado: boolean }> {
    return firstValueFrom(this.http.delete<{ eliminado: boolean }>(`${this.base}/intervenciones/${id}`));
  }

  kpisImpacto(): Promise<KpiInforme> {
    return firstValueFrom(this.http.get<KpiInforme>(`${this.base}/kpis/impacto`));
  }

  /**
   * Despierta el servicio con un ping barato a /health.
   *
   * El hosting gratuito duerme tras 15 min sin trafico y su primer arranque
   * tarda ~20 s. Llamar a /health al entrar en la app "despierta" la API
   * mientras el usuario esta introduciendo sus credenciales, de modo que la
   * primera peticion de datos ya encuentre el servicio caliente.
   */
  despertar(): Promise<boolean> {
    const url = this.base.replace(/\/api\/v1$/, '/health');
    return firstValueFrom(
      this.http.get<{ estado: string }>(url).pipe(map((r) => r.estado === 'ok')),
    ).catch(() => false);
  }
}
