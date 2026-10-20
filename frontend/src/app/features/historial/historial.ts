import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AvisosService } from '../../core/avisos.service';
import { AREAS, Evaluacion } from '../../core/models';
import { EmptyState } from '../../shared/empty-state';
import { Icon } from '../../shared/icon';
import { RiskBadge } from '../../shared/risk-badge';
import { Skeleton } from '../../shared/skeleton';

@Component({
  selector: 'app-historial',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RiskBadge, Skeleton, EmptyState, Icon, DecimalPipe],
  templateUrl: './historial.html',
  styleUrl: './historial.scss',
})
export class Historial implements OnInit {
  private readonly api = inject(ApiService);
  private readonly avisos = inject(AvisosService);

  readonly areas = AREAS;
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly filas = signal<Evaluacion[]>([]);
  readonly guardando = signal<number | null>(null);

  filtroArea = '';
  filtroNivel = '';

  async ngOnInit(): Promise<void> {
    await this.cargar();
  }

  async cargar(): Promise<void> {
    this.cargando.set(true);
    this.error.set(null);
    try {
      const respuesta = await this.api.listarEvaluaciones({
        limite: 200,
        area: this.filtroArea || undefined,
        nivel: this.filtroNivel || undefined,
      });
      this.filas.set(respuesta.datos);
    } catch {
      this.error.set('No se pudo cargar el historial. Revisa tu conexión e inténtalo de nuevo.');
    } finally {
      this.cargando.set(false);
    }
  }

  hayFiltros(): boolean {
    return !!this.filtroArea || !!this.filtroNivel;
  }

  limpiarFiltros(): void {
    this.filtroArea = '';
    this.filtroNivel = '';
    void this.cargar();
  }

  async eliminar(fila: Evaluacion): Promise<void> {
    if (!confirm(`¿Eliminar la evaluación de ${fila.nombre}? Esta acción no se puede deshacer.`)) {
      return;
    }
    this.guardando.set(fila.id);
    try {
      await this.api.eliminarEvaluacion(fila.id);
      this.avisos.exito('Evaluación eliminada', `${fila.nombre} ya no figura en el historial.`);
      await this.cargar();
    } catch {
      this.avisos.error('No se pudo eliminar', 'Inténtalo de nuevo en unos segundos.');
    } finally {
      this.guardando.set(null);
    }
  }

  async corregir(fila: Evaluacion, nivel: string): Promise<void> {
    if (nivel === fila.nivel) {
      return;
    }
    this.guardando.set(fila.id);
    try {
      await this.api.actualizarEvaluacion(fila.id, { nivel: nivel as 'BAJO' | 'MEDIO' | 'ALTO' });
      this.avisos.exito('Nivel actualizado', `${fila.nombre} pasa a ${nivel}.`);
      await this.cargar();
    } catch {
      this.avisos.error('No se pudo actualizar', 'Inténtalo de nuevo en unos segundos.');
    } finally {
      this.guardando.set(null);
    }
  }

  formatoFecha(fecha?: string | null): string {
    if (!fecha) {
      return '—';
    }
    const d = new Date(fecha);
    return isNaN(d.getTime())
      ? '—'
      : d.toLocaleString('es-PE', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
  }
}
