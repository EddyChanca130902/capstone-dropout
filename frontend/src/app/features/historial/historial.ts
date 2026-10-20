import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AREAS, Evaluacion } from '../../core/models';
import { RiskBadge } from '../../shared/risk-badge';

@Component({
  selector: 'app-historial',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RiskBadge, DecimalPipe],
  templateUrl: './historial.html',
  styleUrl: './historial.scss',
})
export class Historial implements OnInit {
  private readonly api = inject(ApiService);

  readonly areas = AREAS;
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly aviso = signal<string | null>(null);
  readonly filas = signal<Evaluacion[]>([]);

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
      this.error.set('No se pudo cargar el historial.');
    } finally {
      this.cargando.set(false);
    }
  }

  async eliminar(id: number): Promise<void> {
    if (!confirm('¿Eliminar esta evaluación? La acción no se puede deshacer.')) {
      return;
    }
    try {
      await this.api.eliminarEvaluacion(id);
      this.aviso.set('Evaluación eliminada.');
      await this.cargar();
    } catch {
      this.error.set('No se pudo eliminar la evaluación.');
    }
  }

  async corregir(fila: Evaluacion, nivel: string): Promise<void> {
    try {
      await this.api.actualizarEvaluacion(fila.id, { nivel: nivel as 'BAJO' | 'MEDIO' | 'ALTO' });
      this.aviso.set(`Nivel de ${fila.nombre} actualizado.`);
      await this.cargar();
    } catch {
      this.error.set('No se pudo actualizar la evaluación.');
    }
  }

  formatoFecha(fecha?: string | null): string {
    if (!fecha) {
      return '—';
    }
    const d = new Date(fecha);
    return isNaN(d.getTime())
      ? '—'
      : d.toLocaleString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
}
