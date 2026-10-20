import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { Icon } from './icon';

@Component({
  selector: 'app-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive, RouterOutlet, Icon],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
})
export class Shell {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly usuario = this.auth.usuario;

  readonly enlaces = [
    { ruta: '/panel', icono: 'panel', titulo: 'Panel principal' },
    { ruta: '/evaluar', icono: 'evaluar', titulo: 'Evaluar estudiante' },
    { ruta: '/historial', icono: 'historial', titulo: 'Historial' },
  ];

  readonly version = '1.0.0';

  cerrarSesion(): void {
    this.auth.logout();
    void this.router.navigate(['/login']);
  }
}
