import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AvisosService } from '../../core/avisos.service';
import { detalleDeError } from '../../core/errors';
import {
  CandidatoDerivacion,
  Intervencion,
  KpiInforme,
  KpiValor,
  traducirVariable,
} from '../../core/models';
import { EmptyState } from '../../shared/empty-state';
import { Icon } from '../../shared/icon';
import { RiskBadge } from '../../shared/risk-badge';
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
  imports: [FormsModule, Icon, EmptyState, Skeleton, RiskBadge],
  templateUrl: './impacto.html',
  styleUrl: './impacto.scss',
})
export class Impacto implements OnInit {
  private readonly api = inject(ApiService);
  private readonly avisos = inject(AvisosService);
  private readonly ruta = inject(ActivatedRoute);

  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly informe = signal<KpiInforme | null>(null);
  readonly intervenciones = signal<Intervencion[]>([]);
  readonly candidatos = signal<CandidatoDerivacion[]>([]);
  readonly guardando = signal(false);
  readonly errorForm = signal<string | null>(null);
  readonly exitoForm = signal<string | null>(null);
  readonly ultimoRegistro = signal<Intervencion | null>(null);

  // Formulario de derivacion: se elige entre los estudiantes ya evaluados.
  readonly seleccion = signal('');
  dni = '';
  nombre = '';
  canal = 'TUTORIA';
  accion = '';
  responsable = '';
  fechaInicio = '';
  estado: Intervencion['estado'] = 'DERIVADA';
  mostrarFormulario = false;

  readonly candidatoSeleccionado = computed<CandidatoDerivacion | null>(() => {
    const id = this.seleccion() ? Number(this.seleccion()) : null;
    if (id === null || Number.isNaN(id)) {
      return null;
    }
    return this.candidatos().find((c) => Number(c.evaluacion_id) === id) ?? null;
  });

  async ngOnInit(): Promise<void> {
    await this.cargar();
    // Flujo evaluación -> derivación: si venimos del resultado de una
    // evaluación, se abre el formulario con ese estudiante ya elegido.
    const pedido = this.ruta.snapshot.queryParamMap.get('evaluacion');
    const id = pedido ? Number(pedido) : NaN;
    if (!Number.isNaN(id) && this.candidatos().some((c) => Number(c.evaluacion_id) === id)) {
      this.mostrarFormulario = true;
      this.elegirCandidato(String(id));
    }
  }

  async cargar(): Promise<void> {
    this.cargando.set(true);
    this.error.set(null);
    try {
      const [informe, intervenciones, candidatos] = await Promise.all([
        this.api.kpisImpacto(),
        this.api.listarIntervenciones({ limite: 100 }),
        this.api.candidatosDerivacion().catch(() => ({ total: 0, datos: [] })),
      ]);
      this.informe.set(informe);
      this.intervenciones.set(intervenciones.datos);
      this.candidatos.set(candidatos.datos);
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
          'Estudiantes derivados a acompañamiento sobre los detectados en alto riesgo en alguna evaluación (aunque después hayan mejorado).',
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

  etiquetaCandidato(candidato: CandidatoDerivacion): string {
    const porcentaje = Math.round((candidato.probabilidad ?? 0) * 100);
    const base = `${candidato.nivel} · ${candidato.dni} · ${candidato.nombre ?? 'Sin nombre'} · ${porcentaje} %`;
    return candidato.derivado ? `${base} · ya derivado` : base;
  }

  elegirCandidato(valor: string): void {
    this.seleccion.set(valor ?? '');
    this.errorForm.set(null);
    this.exitoForm.set(null);
    const candidato = this.candidatoSeleccionado();
    this.dni = candidato?.dni ?? '';
    this.nombre = candidato?.nombre ?? '';
  }

  async derivar(): Promise<void> {
    this.errorForm.set(null);
    this.exitoForm.set(null);
    const candidato = this.candidatoSeleccionado();
    if (!candidato) {
      this.errorForm.set('Selecciona un estudiante evaluado: la derivación nace de una evaluación.');
      this.avisos.error('Falta el estudiante', 'Elige a quién derivas de la lista de evaluados.');
      return;
    }
    if (candidato.derivado) {
      this.errorForm.set(
        `${candidato.dni} ya tiene una derivación registrada: cambia su estado en la tabla.`,
      );
      this.avisos.error('Ya está derivado', `${candidato.dni} ya tiene una derivación.`);
      return;
    }
    if (this.accion.trim().length < 3) {
      this.errorForm.set('Describe la acción correctiva aplicada.');
      this.avisos.error('Falta la acción', 'Describe la acción correctiva aplicada.');
      return;
    }
    this.guardando.set(true);
    try {
      const registrada = await this.api.crearIntervencion({
        dni: candidato.dni,
        nombre: candidato.nombre ?? null,
        evaluacion_id: candidato.evaluacion_id,
        fecha_deteccion: candidato.creado_en ?? null,
        canal: this.canal as Intervencion['canal'],
        accion: this.accion.trim(),
        responsable: this.responsable.trim() || null,
        estado: this.estado,
        fecha_inicio: this.fechaInicio ? new Date(this.fechaInicio).toISOString() : null,
        variables_en_alerta: candidato.variables_en_alerta,
      });
      this.ultimoRegistro.set(registrada);
      this.exitoForm.set(
        `Derivación registrada (${registrada.dni}) desde la evaluación #${candidato.evaluacion_id}. ` +
          'Ya se refleja en los KPI de impacto.',
      );
      this.avisos.exito('Derivación registrada', `${candidato.dni} derivado a acompañamiento.`);
      this.seleccion.set('');
      this.dni = '';
      this.nombre = '';
      this.accion = '';
      this.fechaInicio = '';
      this.estado = 'DERIVADA';
      // El formulario se mantiene abierto: el registro recien guardado se
      // muestra debajo y el toast puede pasar inadvertido.
      await this.cargar();
    } catch (error) {
      const detalle = detalleDeError(error);
      const status = (error as { status?: number })?.status ?? 0;
      const mensaje =
        status === 401
          ? 'Tu sesión ha caducado: vuelve a iniciar sesión e inténtalo de nuevo.'
          : (detalle ?? 'Revisa los datos e inténtalo de nuevo.');
      this.errorForm.set(mensaje);
      this.avisos.error('No se pudo registrar la derivación', mensaje);
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
