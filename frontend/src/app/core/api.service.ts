import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Estudiante, Evaluacion, Prediccion, Resumen } from './models';

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
    return firstValueFrom(this.http.get<{ total: number; datos: Evaluacion[] }>(`${this.base}/evaluaciones`, { params: httpParams }));
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
}
