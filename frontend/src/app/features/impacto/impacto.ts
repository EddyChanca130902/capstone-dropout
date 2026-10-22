import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { AvisosService } from '../../core/avisos.service';
import { detalleDeError } from '../../core/errors';
import { Intervencion, KpiInforme, KpiValor, traducirVariable } from '../../core/models';
import { EmptyState } from '../../shared/empty-state';
import { Icon } from '../../shared/icon';
import { Skeleton } from '../../shared/skeleton';

interface TarjetaKpi {
  clave: keyof KpiInforme;
  titulo: string;
  concepto: string;
  valor: KpiValor;
}

@Component({
  selector: 'app-impacto',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, Icon, EmptyState, Skeleton],
  templateUrl: './impacto.html',
  styleUrl: './impacto.scss',
})
export class Impacto implements OnInit {
  private readonly api = inject(ApiService);
  private readonly avisos = inject(AvisosService);

  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly informe = signal<KpiInforme | null>(null);
  readonly intervenciones = signal<Intervencion[]>([]);
  readonly guardando = signal(false);

  // Formulario de derivacion
  dni = '';
  nombre = '';
  canal = 'TUTORIA';
  accion = '';
  responsable = '';
  fechaInicio = '';
  estado: Intervencion['estado'] = 'DERIVADA';
  mostrarFormulario = false;

  async ngOnInit(): Promise<void> {
    await this.cargar();
  }

  async cargar(): Promise<void> {
    this.cargando.set(true);
    this.error.set(null);
    try {
      const [informe, intervenciones] = await Promise.all([
        this.api.kpisImpacto(),
        this.api.listarIntervenciones({ limite: 100 }),
      ]);
      this.informe.set(informe);
      this.intervenciones.set(intervenciones.datos);
    } catch (error) {
      const detalle =
        typeof error === 'object' && error !== null && 'error' in error
          ? ((error as { error?: { detail?: unknown } }).error?.detail ?? '')
          : '';
      this.error.set(
        typeof detalle === 'string' && detalle
          ? detalle
          : 'No se pudo cargar el informe de impacto.',
      );
    } finally {
      this.cargando.set(false);
    }
  }

  get tarjetas(): TarjetaKpi[] {
    const informe = this.informe();
    if (!informe) {
      return [];
    }
    return [
      {
        clave: 'kpi_cobertura_intervencion',
        titulo: 'Tasa de cobertura de intervención',
        concepto:
          'Estudiantes derivados a acompañamiento sobre los detectados en alto riesgo.',
        valor: informe.kpi_cobertura_intervencion,
      },
      {
        clave: 'kpi_reduccion_riesgo',
        titulo: 'Tasa de variación del nivel de riesgo',
        concepto:
          'Estudiantes que disminuyeron su nivel de riesgo tras la intervención, sobre los que recibieron acompañamiento.',
        valor: informe.kpi_reduccion_riesgo,
      },
      {
        clave: 'kpi_resolucion_variables',
        titulo: 'Índice de resolución de variables modificables',
        concepto:
          'Variables en alerta (académicas y psicosociales) que mejoraron tras la intervención.',
        valor: informe.kpi_resolucion_variables,
      },
      {
        clave: 'kpi_tiempo_respuesta',
        titulo: 'Tiempo de respuesta para acompañamiento',
        concepto:
          'Días entre la detección del sistema y el inicio de la intervención.',
        valor: informe.kpi_tiempo_respuesta,
      },
    ];
  }

  async derivar(): Promise<void> {
    if (this.dni.trim().length < 5) {
      this.avisos.error(
        'Falta el DNI',
        'El documento de identidad debe tener al menos 5 caracteres.',
      );
      return;
    }
    if (this.accion.trim().length < 3) {
      this.avisos.error('Falta la acción', 'Describe la acción correctiva aplicada.');
      return;
    }
    this.guardando.set(true);
    try {
      await this.api.crearIntervencion({
        dni: this.dni.trim(),
        nombre: this.nombre.trim() || null,
        canal: this.canal as Intervencion['canal'],
        accion: this.accion.trim(),
        responsable: this.responsable.trim() || null,
        estado: this.estado,
        fecha_inicio: this.fechaInicio ? new Date(this.fechaInicio).toISOString() : null,
        variables_en_alerta: [],
      });
      this.avisos.exito('Derivación registrada', `${this.dni.trim()} derivado a acompañamiento.`);
      this.dni = '';
      this.nombre = '';
      this.accion = '';
      this.fechaInicio = '';
      this.estado = 'DERIVADA';
      this.mostrarFormulario = false;
      await this.cargar();
    } catch (error) {
      const detalle = detalleDeError(error);
      this.avisos.error(
        'No se pudo registrar la derivación',
        detalle ?? 'Revisa los datos e inténtalo de nuevo.',
      );
    } finally {
      this.guardando.set(false);
    }
  }

  async cambiarEstado(intervencion: Intervencion, estado: Intervencion['estado']): Promise<void> {
    try {
      await this.api.actualizarIntervencion(intervencion.id, { estado });
      this.avisos.exito('Estado actualizado', `${intervencion.dni} · ${estado}`);
      await this.cargar();
    } catch {
      this.avisos.error('No se pudo actualizar el estado');
    }
  }

  async eliminar(intervencion: Intervencion): Promise<void> {
    if (!confirm(`¿Eliminar la derivación de ${intervencion.dni}?`)) {
      return;
    }
    try {
      await this.api.eliminarIntervencion(intervencion.id);
      this.avisos.exito('Derivación eliminada');
      await this.cargar();
    } catch {
      this.avisos.error('No se pudo eliminar la derivación');
    }
  }

  valor(kpi: KpiValor): string {
    if (!kpi.disponible || kpi.valor === null) {
      return '—';
    }
    if (kpi.unidad === 'días') {
      return `${kpi.valor} d`;
    }
    return `${kpi.valor} %`;
  }

  formula(kpi: KpiValor): string {
    return `${kpi.numerador.toFixed(0)} / ${kpi.denominador.toFixed(0)}`;
  }

  fecha(iso?: string | null): string {
    if (!iso) {
      return '—';
    }
    const d = new Date(iso);
    return isNaN(d.getTime())
      ? '—'
      : d.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  estadoClase(estado: string): string {
    return estado === 'CERRADA' ? 'cerrada' : estado === 'EN_PROCESO' ? 'proceso' : 'derivada';
  }

  protected readonly traducirVariable = traducirVariable;
}
