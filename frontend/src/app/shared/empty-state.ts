import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from './icon';

/**
 * Estado vacio: explica que falta y ofrece la accion para resolverlo.
 * Un empty state sin accion deja al usuario en un callejon sin salida.
 */
@Component({
  selector: 'app-empty-state',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [Icon, RouterLink],
  template: `
    <div class="vacio">
      <div class="icono"><app-icon [nombre]="icono()" [size]="28" /></div>
      <h3>{{ titulo() }}</h3>
      @if (mensaje()) {
        <p>{{ mensaje() }}</p>
      }
      @if (textoAccion() && rutaAccion()) {
        <a [routerLink]="rutaAccion()">
          <button type="button" class="accion">
            <app-icon [nombre]="iconoAccion()" [size]="16" />
            {{ textoAccion() }}
          </button>
        </a>
      }
    </div>
  `,
  styles: [
    `
      .vacio {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 2.6rem 1.5rem;
        gap: 0.35rem;
      }
      .icono {
        width: 56px;
        height: 56px;
        display: grid;
        place-items: center;
        border-radius: 18px;
        background: var(--brand-soft);
        color: var(--brand);
        margin-bottom: 0.7rem;
      }
      h3 {
        font-size: 1.05rem;
        margin: 0;
      }
      p {
        max-width: 44ch;
        font-size: 0.9rem;
        margin: 0.2rem 0 0.9rem;
      }
      .accion {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
      }
    `,
  ],
})
export class EmptyState {
  readonly icono = input<string>('bandeja');
  readonly titulo = input.required<string>();
  readonly mensaje = input<string>('');
  readonly textoAccion = input<string>('');
  readonly rutaAccion = input<string>('');
  readonly iconoAccion = input<string>('mas');
}
