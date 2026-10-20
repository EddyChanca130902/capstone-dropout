import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Resumen } from '../../core/models';
import { RiskBadge } from '../../shared/risk-badge';

@Component({
  selector: 'app-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RiskBadge, DecimalPipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  readonly usuario = this.auth.usuario;
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly resumen = signal<Resumen | null>(null);

  readonly totalNivel = computed(() => {
    const r = this.resumen();
    if (!r) {
      return 0;
    }
    return Object.values(r.por_nivel).reduce((a, b) => a + b, 0);
  });

  async ngOnInit(): Promise<void> {
    try {
      this.resumen.set(await this.api.resumen());
    } catch {
      this.error.set('No se pudo cargar el panel.');
    } finally {
      this.cargando.set(false);
    }
  }

  porcentaje(valor: number): number {
    const total = this.totalNivel();
    return total ? Math.round((valor / total) * 100) : 0;
  }

  maxArea(): number {
    const areas = this.resumen()?.por_area ?? [];
    return areas.length ? Math.max(...areas.map((a) => a.total)) : 0;
  }

  porcentajeArea(valor: number): number {
    const max = this.maxArea();
    return max ? Math.round((valor / max) * 100) : 0;
  }

  formatoFecha(fecha?: string | null): string {
    if (!fecha) {
      return '—';
    }
    const d = new Date(fecha);
    return isNaN(d.getTime())
      ? '—'
      : d.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }
}
