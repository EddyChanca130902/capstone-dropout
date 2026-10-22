/** Contratos compartidos con la API (FastAPI). */

export type Nivel = 'BAJO' | 'MEDIO' | 'ALTO';

export type Area =
  | 'Ingeniería y Tecnología'
  | 'Ciencias de la Salud'
  | 'Ciencias Sociales y Humanidades'
  | 'Administración y Negocios'
  | 'Arte y Diseño';

export interface Estudiante {
  dni: string;
  nombre: string;
  edad: number;
  genero: 'Masculino' | 'Femenino';
  area_estudios: Area;
  becario: 'Sí' | 'No';
  deudor: 'Sí' | 'No';
  matricula_al_dia: 'Sí' | 'No';
  desplazado: 'Sí' | 'No';
  cu1_matriculadas: number;
  cu1_aprobadas: number;
  cu1_nota: number;
  cu2_matriculadas: number;
  cu2_aprobadas: number;
  cu2_nota: number;
}

export interface Prediccion {
  probabilidad: number;
  nivel: Nivel;
  modelo_version: string;
  umbrales: { alto: number; medio: number };
  tiempo_ms: number | null;
}

export interface FactorClave {
  variable: string;
  contribucion: number;
  direccion: 'aumenta_riesgo' | 'reduce_riesgo';
  valor: unknown;
}

export interface Evaluacion {
  id: number;
  dni: string;
  nombre: string;
  area_estudios: string;
  probabilidad: number;
  nivel: string;
  modelo_version?: string | null;
  entradas?: Record<string, unknown> | null;
  factores_clave?: FactorClave[] | null;
  variables_en_alerta?: string[] | null;
  creado_en?: string | null;
  actualizado_en?: string | null;
}

export interface Resumen {
  estudiantes_evaluados: number;
  evaluaciones_realizadas: number;
  en_riesgo_alto: number;
  probabilidad_promedio: number | null;
  por_nivel: Record<string, number>;
  por_area: { area: string; total: number }[];
  recientes: Evaluacion[];
}

export type EstadoIntervencion = 'DERIVADA' | 'EN_PROCESO' | 'CERRADA';
export type Canal = 'TUTORIA' | 'ORIENTACION' | 'BECATEO' | 'DERIVACION' | 'OTRO';

export interface Intervencion {
  id: number;
  dni: string;
  nombre?: string | null;
  evaluacion_id?: number | null;
  fecha_deteccion?: string | null;
  fecha_derivacion?: string | null;
  fecha_inicio?: string | null;
  responsable?: string | null;
  canal?: Canal | null;
  accion?: string | null;
  estado: EstadoIntervencion;
  variables_en_alerta: string[];
  resultado?: string | null;
  creado_en?: string | null;
}

export interface KpiValor {
  valor: number | null;
  unidad: string;
  numerador: number;
  denominador: number;
  formula: string;
  disponible: boolean;
  nota?: string | null;
}

export interface KpiInforme {
  generado_en: string;
  kpi_cobertura_intervencion: KpiValor;
  kpi_reduccion_riesgo: KpiValor;
  kpi_resolucion_variables: KpiValor;
  kpi_tiempo_respuesta: KpiValor;
  detalle: Record<string, unknown>;
}

export interface Usuario {
  id: string;
  email: string;
  rol: string;
}

export interface Sesion {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
  usuario?: { id: string; email: string };
}

export const AREAS: Area[] = [
  'Ingeniería y Tecnología',
  'Ciencias de la Salud',
  'Ciencias Sociales y Humanidades',
  'Administración y Negocios',
  'Arte y Diseño',
];

/** Traduccion de las variables del modelo a lenguaje del orientador. */
export const TRADUCCION_VARIABLES: Record<string, string> = {
  'Tuition fees up to date': 'Matrícula al día',
  'Curricular units 1st sem (approved)': 'Aprobadas 1.º semestre',
  'Curricular units 1st sem (grade)': 'Nota 1.º semestre',
  'Curricular units 2nd sem (approved)': 'Aprobadas 2.º semestre',
  'Curricular units 2nd sem (grade)': 'Nota 2.º semestre',
  'Curricular units 1st sem (enrolled)': 'Matriculadas 1.º semestre',
  'Curricular units 2nd sem (enrolled)': 'Matriculadas 2.º semestre',
  Debtor: 'Deuda',
  'Scholarship holder': 'Beca',
  'Age at enrollment': 'Edad',
  Gender: 'Género',
  Course: 'Área de estudios',
  Displaced: 'Desplazado',
  'Previous qualification (grade)': 'Nota de acceso',
  'Admission grade': 'Nota de admisión',
  'Mother\'s occupation': 'Ocupación de la madre',
  'Application mode': 'Vía de acceso',
};

export function traducirVariable(variable: string): string {
  return TRADUCCION_VARIABLES[variable] ?? variable;
}
