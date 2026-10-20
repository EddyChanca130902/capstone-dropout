import { ChangeDetectionStrategy, Component, input } from '@angular/core';

/**
 * Esqueleto de carga (skeleton).
 *
 * Sustituye a los spinners: comunica la forma del contenido que va a llegar
 * y reduce la percepcion de espera.
 */
@Component({
  selector: 'app-skeleton',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<span class="hueso" [style.width]="ancho()" [style.height]="alto()"></span>`,
  styles: [
    `
      :host {
        display: block;
      }
      .hueso {
        display: block;
        border-radius: 8px;
        background: linear-gradient(
          90deg,
          #e9eef0 25%,
          #f4f7f8 37%,
          #e9eef0 63%
        );
        background-size: 400% 100%;
        animation: brillo 1.4s ease infinite;
      }
      @keyframes brillo {
        0% {
          background-position: 100% 50%;
        }
        100% {
          background-position: 0 50%;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .hueso {
          animation: none;
        }
      }
    `,
  ],
})
export class Skeleton {
  readonly ancho = input<string>('100%');
  readonly alto = input<string>('1rem');
}
