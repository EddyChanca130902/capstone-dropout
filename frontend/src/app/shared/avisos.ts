import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { AvisosService } from '../core/avisos.service';
import { Icon } from './icon';

@Component({
  selector: 'app-avisos',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon],
  template: `
    <div class="contenedor" role="status" aria-live="polite">
      @for (aviso of avisos.avisos(); track aviso.id) {
        <div class="aviso" [class]="'aviso ' + aviso.tipo">
          <app-icon
            [nombre]="aviso.tipo === 'exito' ? 'check' : aviso.tipo === 'error' ? 'alerta' : 'info'"
            [size]="18"
          />
          <div class="texto">
            <strong>{{ aviso.texto }}</strong>
            @if (aviso.detalle) {
              <small>{{ aviso.detalle }}</small>
            }
          </div>
          <button type="button" class="cerrar" (click)="avisos.cerrar(aviso.id)" aria-label="Cerrar">
            <app-icon nombre="info" [size]="14" />
          </button>
        </div>
      }
    </div>
  `,
  styles: [
    `
      .contenedor {
        position: fixed;
        right: 1.2rem;
        bottom: 1.2rem;
        z-index: 90;
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
        max-width: min(380px, calc(100vw - 2.4rem));
      }
      .aviso {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.8rem 0.9rem;
        border-radius: 14px;
        background: var(--surface);
        border: 1px solid var(--line);
        box-shadow: 0 12px 30px rgba(24, 43, 58, 0.16);
        animation: entrar 0.22s ease;
      }
      @keyframes entrar {
        from {
          opacity: 0;
          transform: translateY(8px);
        }
      }
      .texto {
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
        flex: 1;
      }
      .texto strong {
        font-size: 0.9rem;
        line-height: 1.35;
      }
      .texto small {
        color: var(--muted);
        font-size: 0.78rem;
        word-break: break-word;
      }
      .exito {
        border-left: 3px solid var(--risk-low);
      }
      .exito app-icon {
        color: var(--risk-low);
      }
      .error {
        border-left: 3px solid var(--risk-high);
      }
      .error app-icon {
        color: var(--risk-high);
      }
      .info {
        border-left: 3px solid var(--brand);
      }
      .info app-icon {
        color: var(--brand);
      }
      .cerrar {
        background: transparent;
        border: none;
        color: var(--muted);
        padding: 0.1rem;
        line-height: 0;
      }
      .cerrar:hover {
        background: transparent;
        color: var(--ink);
      }
      @media (prefers-reduced-motion: reduce) {
        .aviso {
          animation: none;
        }
      }
    `,
  ],
})
export class Avisos {
  readonly avisos = inject(AvisosService);
}
