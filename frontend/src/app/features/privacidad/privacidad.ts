import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from '../../shared/icon';

interface Seccion {
  titulo: string;
  icono: string;
  contenido: string[];
  puntos?: string[];
}

@Component({
  selector: 'app-privacidad',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, Icon],
  templateUrl: './privacidad.html',
  styleUrl: './privacidad.scss',
})
export class Privacidad {
  readonly actualizado = '20 de octubre de 2026';

  readonly secciones: Seccion[] = [
    {
      titulo: 'Responsable del tratamiento',
      icono: 'usuarios',
      contenido: [
        'EarlySign es un sistema de apoyo al orientador académico. El responsable del tratamiento es la institución de educación superior que opera la plataforma, a través de la unidad de orientación y bienestar estudiantil.',
        'El tratamiento se realiza en nombre propio de la institución y conforme a la normativa vigente de protección de datos personales.',
      ],
    },
    {
      titulo: 'Qué datos se registran',
      icono: 'base_datos',
      contenido: [
        'El orientador introduce en el formulario los siguientes datos del estudiante:',
      ],
      puntos: [
        'Identificativos: documento de identidad (DNI) y nombre completo.',
        'Sociodemográficos: edad al matricularse, género, área de estudios, condición de becario, situación de deuda, estado de la matrícula y condición de desplazado.',
        'Académicos: asignaturas matriculadas, aprobadas y nota media de cada semestre.',
      ],
    },
    {
      titulo: 'Para qué se utilizan',
      icono: 'grafico',
      contenido: [
        'Los datos se utilizan exclusivamente para estimar la probabilidad de abandono académico y priorizar el acompañamiento del estudiante. La evaluación es una estimación estadística que apoya el criterio profesional del orientador: en ningún caso la plataforma decide, sanciona ni exonera a un estudiante.',
        'No se realizan decisiones automatizadas con efectos jurídicos sobre los estudiantes, ni se utilizan los datos para fijar precios, servicios o condiciones de matrícula.',
      ],
    },
    {
      titulo: 'Modelo predictivo y transferencia de datos',
      icono: 'cpu',
      contenido: [
        'El modelo de predicción fue entrenado con un conjunto de datos público de la Universidad de Minho (Portugal), disponible en el repositorio UCI: datos históricos de matrícula de estudiantes, sin relación con personas identificables.',
        'Ninguno de los datos que introduces en la plataforma se envía a ese conjunto de entrenamiento ni se incorpora a él. El modelo se aplica en modo de inferencia: solo recibe los valores del formulario y devuelve una probabilidad.',
        'La precisión del modelo en la población de referencia es de aproximadamente 0.93 de AUC. Aplicado a una población distinta, su capacidad predictiva puede ser menor: por eso el resultado se presenta siempre como estimación y no como veredicto.',
      ],
    },
    {
      titulo: 'Dónde se almacenan y cómo se protegen',
      icono: 'candado',
      contenido: [
        'Los datos se almacenan en una base de datos PostgreSQL alojada en Supabase, con cifrado en tránsito (TLS) y en reposo. El acceso a la base de datos se realiza exclusivamente desde el servidor de la aplicación.',
        'Cada fila de evaluación queda asociada al orientador que la registra. La base de datos aplica políticas de seguridad a nivel de fila (Row Level Security), de modo que un orientador solo puede consultar y modificar sus propias evaluaciones; el aislamiento no depende del código de la aplicación, sino de la propia base de datos.',
        'Las credenciales de acceso al servidor y a la base de datos se guardan cifradas en el gestor de secretos de la plataforma de despliegue y nunca se incluyen en el código.',
      ],
    },
    {
      titulo: 'Acceso y cesión a terceros',
      icono: 'escudo',
      contenido: [
        'El acceso a la plataforma está restringido a personal de orientación autenticado mediante correo electrónico y contraseña gestionados por un proveedor de identidad.',
        'No se ceden datos a terceros con fines comerciales. Los subencargados técnicos (hosting de la base de datos y de la aplicación) tratan los datos únicamente por cuenta de la institución, conforme a contrato.',
      ],
    },
    {
      titulo: 'Conservación',
      icono: 'reloj',
      contenido: [
        'Las evaluaciones se conservan durante el periodo de seguimiento académico del estudiante y, tras su cierre, por el plazo máximo que la institución fije para la conservación de expedientes académicos.',
        'El sistema no realiza copias de seguridad propias: la política de respaldo y restauración es responsabilidad de la institución a través de su proveedor de infraestructura.',
      ],
    },
    {
      titulo: 'Derechos de los estudiantes',
      icono: 'check',
      contenido: [
        'Los estudiantes pueden ejercer, ante la institución, los derechos de acceso, rectificación, supresión, oposición y limitación del tratamiento, así como retirar el consentimiento en cualquier momento.',
        'Para ejercerlos basta con dirigirse a la unidad de orientación y bienestar estudiantil. En ese proceso, la institución podrá identificar la evaluación correspondiente a partir del DNI registrado.',
      ],
    },
    {
      titulo: 'Cookies y sesión',
      icono: 'info',
      contenido: [
        'La aplicación no utiliza cookies publicitarias ni de seguimiento. El token de sesión se almacena en el almacenamiento local del navegador y se elimina al cerrar sesión. No se instalan herramientas de analítica de terceros.',
      ],
    },
  ];
}
