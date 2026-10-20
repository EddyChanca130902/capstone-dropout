import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-shell',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './shell.html',
  styleUrl: './shell.scss',
})
export class Shell {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly usuario = this.auth.usuario;

  readonly enlaces = [
    { ruta: '/panel', icono: '📊', titulo: 'Panel principal' },
    { ruta: '/evaluar', icono: '📝', titulo: 'Evaluar estudiante' },
    { ruta: '/historial', icono: '📋', titulo: 'Historial' },
  ];

  readonly anio = new Date().getFullYear();

  cerrarSesion(): void {
    this.auth.logout();
    void this.router.navigate(['/login']);
  }
}
