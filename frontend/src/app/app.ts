import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Avisos } from './shared/avisos';

@Component({
  imports: [RouterOutlet, Avisos],
  selector: 'app-root',
  template: `
    <router-outlet />
    <app-avisos />
  `,
})
export class App {}
