import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ApiService } from './core/api.service';
import { Avisos } from './shared/avisos';

@Component({
  imports: [RouterOutlet, Avisos],
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <router-outlet />
    <app-avisos />
  `,
})
export class App {
  private readonly api = inject(ApiService);

  constructor() {
    // El hosting gratuito duerme tras 15 min sin trafico y su primer arranque
    // tarda ~20 s: despertar la API aqui evita que el usuario espere a que
    // cargue el panel.
    void this.api.despertar();
  }
}
