import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DecimalPipe } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AvisosService } from '../../core/avisos.service';
import { AREAS, Area, Estudiante, Prediccion } from '../../core/models';
import { Icon } from '../../shared/icon';
import { RiskBadge } from '../../shared/risk-badge';

@Component({
  selector: 'app-evaluar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, RouterLink, RiskBadge, Icon, DecimalPipe],
  templateUrl: './evaluar.html',
  styleUrl: './evaluar.scss',
})
export class Evaluar {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly avisos = inject(AvisosService);

  readonly areas = AREAS;
  readonly paso = signal<1 | 2>(1);
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly resultado = signal<Prediccion | null>(null);
  readonly guardado = signal(false);

  readonly personal = this.fb.nonNullable.group({
    dni: ['', [Validators.required, Validators.minLength(5)]],
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    edad: [18, [Validators.required, Validators.min(16), Validators.max(60)]],
    genero: ['Masculino' as 'Masculino' | 'Femenino', Validators.required],
    area_estudios: ['Ciencias de la Salud' as Area, Validators.required],
    becario: ['No' as 'Sí' | 'No', Validators.required],
    deudor: ['No' as 'Sí' | 'No', Validators.required],
    matricula_al_dia: ['Sí' as 'Sí' | 'No', Validators.required],
    desplazado: ['No' as 'Sí' | 'No', Validators.required],
  });

  readonly academico = this.fb.nonNullable.group({
    cu1_matriculadas: [5, [Validators.required, Validators.min(0), Validators.max(30)]],
    cu1_aprobadas: [3, [Validators.required, Validators.min(0), Validators.max(30)]],
    cu1_nota: [12, [Validators.required, Validators.min(0), Validators.max(20)]],
    cu2_matriculadas: [5, [Validators.required, Validators.min(0), Validators.max(30)]],
    cu2_aprobadas: [3, [Validators.required, Validators.min(0), Validators.max(30)]],
    cu2_nota: [12, [Validators.required, Validators.min(0), Validators.max(20)]],
  });

  avanzar(): void {
    this.error.set(null);
    if (this.personal.invalid) {
      this.personal.markAllAsTouched();
      this.error.set('Completa los datos personales: DNI y nombre son obligatorios.');
      return;
    }
    this.paso.set(2);
  }

  retroceder(): void {
    this.error.set(null);
    this.paso.set(1);
  }

  async calcular(): Promise<void> {
    this.error.set(null);
    this.resultado.set(null);
    this.guardado.set(false);

    if (this.academico.invalid) {
      this.academico.markAllAsTouched();
      this.error.set('Revisa los datos de rendimiento académico.');
      return;
    }

    const estudiante: Estudiante = {
      ...this.personal.getRawValue(),
      ...this.academico.getRawValue(),
    };

    if (
      estudiante.cu1_aprobadas > estudiante.cu1_matriculadas ||
      estudiante.cu2_aprobadas > estudiante.cu2_matriculadas
    ) {
      this.error.set('No se pueden aprobar más asignaturas de las matriculadas.');
      return;
    }

    this.cargando.set(true);
    try {
      const prediccion = await this.api.predecir(estudiante);
      this.resultado.set(prediccion);
      await this.api.crearEvaluacion(estudiante);
      this.guardado.set(true);
      this.avisos.exito(
        'Evaluación guardada',
        `${estudiante.nombre} · ${prediccion.nivel} · ${(prediccion.probabilidad * 100).toFixed(1)} %`,
      );
    } catch (error) {
      const detalle =
        typeof error === 'object' && error !== null && 'error' in error
          ? ((error as { error?: { detail?: unknown } }).error?.detail ?? '')
          : '';
      const mensaje =
        typeof detalle === 'string' && detalle
          ? detalle
          : 'No se pudo completar la evaluación. Inténtalo de nuevo.';
      this.error.set(mensaje);
      this.avisos.error('No se pudo completar la evaluación', mensaje);
    } finally {
      this.cargando.set(false);
    }
  }

  reiniciar(): void {
    this.resultado.set(null);
    this.guardado.set(false);
    this.error.set(null);
    this.paso.set(1);
  }
}
