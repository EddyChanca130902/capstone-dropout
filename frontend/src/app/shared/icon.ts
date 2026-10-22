import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * Set de iconos en SVG (estilo lineal, trazo 1.75).
 *
 * Se usan SVG en lugar de emojis por tres motivos: se ven nítidos en
 * cualquier resolucion, heredan el color del texto y no dependen de la
 * fuente del sistema (los emojis varia entre Windows, macOS y Android).
 */
const ICONOS: Record<string, string[]> = {
  panel: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z'],
  evaluar: ['M9 4H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2', 'M9 4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2', 'M9 4h6', 'M9 11h6', 'M9 15h4'],
  historial: ['M3 12a9 9 0 1 0 3-6.7L3 8', 'M3 3v5h5', 'M12 7v5l3 2'],
  privacidad: ['M12 7v14', 'M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z'],
  salir: ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'M16 17l5-5-5-5', 'M21 12H9'],
  ojo: ['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  'ojo-tachado': [
    'M10.6 5.1A9.8 9.8 0 0 1 12 5c6.5 0 10 7 10 7a17.9 17.9 0 0 1-3.1 4',
    'M6.2 6.2A17.7 17.7 0 0 0 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6',
    'M9.9 9.9a3 3 0 0 0 4.2 4.2',
    'M3 3l18 18',
  ],
  mas: ['M12 5v14', 'M5 12h14'],
  cerrar: ['M18 6 6 18', 'M6 6l12 12'],
  derecha: ['M5 12h14', 'M12 5l7 7-7 7'],
  izquierda: ['M19 12H5', 'M12 19l-7-7 7-7'],
  check: ['M20 6 9 17l-5-5'],
  alerta: ['M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z', 'M12 9v4', 'M12 17h.01'],
  info: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 16v-4', 'M12 8h.01'],
  basura: ['M3 6h18', 'M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2', 'M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6'],
  grafico: ['M3 3v18h18', 'M7 15l4-5 3 3 5-7'],
  torta: ['M21 12A9 9 0 1 1 12 3v9z'],
  escudo: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z', 'M9 12l2 2 4-4'],
  candado: ['M5 11h14v10H5z', 'M8 11V7a4 4 0 0 1 8 0v4'],
  usuarios: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M22 21v-2a4 4 0 0 0-3-3.9'],
  base_datos: ['M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3Z', 'M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5', 'M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3'],
  cpu: ['M9 3v3', 'M15 3v3', 'M9 18v3', 'M15 18v3', 'M3 9h3', 'M3 15h3', 'M18 9h3', 'M18 15h3', 'M6 6h12v12H6z', 'M10 10h4v4h-4z'],
  birrete: ['M22 10 12 5 2 10l10 5 10-5Z', 'M6 12v5c0 1 2.7 3 6 3s6-2 6-3v-5'],
  bandeja: ['M22 12h-6l-2 3h-4l-2-3H2', 'M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1Z'],
  filtro: ['M3 4h18l-7 8v6l-4 2v-8z'],
  refrescar: ['M21 12a9 9 0 1 1-3-6.7L21 8', 'M21 3v5h-5'],
  buscar: ['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z', 'M21 21l-4.3-4.3'],
  externo: ['M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6', 'M15 3h6v6', 'M10 14 21 3'],
  reloj: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 6v6l4 2'],
  sorpresa: ['M12 3l1.9 4.6L19 8.5l-3.6 3.2.9 4.8-4.3-2.5-4.3 2.5.9-4.8L5 8.5l5.1-.9z', 'M12 18h.01'],
  flecha: ['M12 5v14', 'M5 12l7 7 7-7'],
};

@Component({
  selector: 'app-icon',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg
      [attr.width]="size()"
      [attr.height]="size()"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      [attr.stroke-width]="grosor()"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      @for (d of trazos(); track $index) {
        <path [attr.d]="d" />
      }
    </svg>
  `,
  styles: [
    `
      :host {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        line-height: 0;
        flex: none;
      }
    `,
  ],
})
export class Icon {
  readonly nombre = input.required<string>();
  readonly size = input<number>(20);
  readonly grosor = input<number>(1.75);

  readonly trazos = computed(() => ICONOS[this.nombre()] ?? ICONOS['info']);
}
