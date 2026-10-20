import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { Nivel } from '../core/models';

@Component({
  selector: 'app-risk-badge',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <span class="badge" [class]="'badge ' + clase()">
      <span class="punto"></span>{{ nivel() }}
    </span>
  `,
  styles: [
    `
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.22rem 0.6rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        border: 1px solid transparent;
      }
      .punto {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: currentColor;
      }
      .alto {
        color: var(--risk-high);
        background: #fdeceb;
        border-color: #f2c7c3;
      }
      .medio {
        color: var(--risk-medium);
        background: #fdf4e6;
        border-color: #f0dcb8;
      }
      .bajo {
        color: var(--risk-low);
        background: #eaf5ef;
        border-color: #c8e2d5;
      }
    `,
  ],
})
export class RiskBadge {
  readonly nivel = input.required<Nivel | string>();
  readonly clase = computed(() => {
    const valor = String(this.nivel()).toUpperCase();
    return valor === 'ALTO' ? 'alto' : valor === 'MEDIO' ? 'medio' : 'bajo';
  });
}
