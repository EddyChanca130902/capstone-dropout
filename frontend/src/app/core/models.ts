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

export interface Evaluacion {
  id: number;
  dni: string;
  nombre: string;
  area_estudios: string;
  probabilidad: number;
  nivel: string;
  modelo_version?: string | null;
  entradas?: Record<string, unknown> | null;
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
