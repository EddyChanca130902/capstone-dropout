import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Sesion, Usuario } from './models';

const CLAVE_ACCESO = 'alertatemprana.access_token';
const CLAVE_REFRESH = 'alertatemprana.refresh_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly _token = signal<string | null>(localStorage.getItem(CLAVE_ACCESO));
  private readonly _usuario = signal<Usuario | null>(null);

  readonly token = this._token.asReadonly();
  readonly usuario = this._usuario.asReadonly();
  readonly autenticado = computed(() => !!this._token());

  constructor(
    private readonly http: HttpClient,
    private readonly router: Router,
  ) {}

  async login(email: string, password: string): Promise<void> {
    const sesion = await firstValueFrom(
      this.http.post<Sesion>(`${environment.apiUrl}/auth/login`, { email, password }),
    );
    this._token.set(sesion.access_token);
    this._usuario.set({ id: sesion.usuario?.id ?? '', email: sesion.usuario?.email ?? email, rol: 'orientador' });
    localStorage.setItem(CLAVE_ACCESO, sesion.access_token);
    if (sesion.refresh_token) {
      localStorage.setItem(CLAVE_REFRESH, sesion.refresh_token);
    }
  }

  async refrescar(): Promise<boolean> {
    const refresh = localStorage.getItem(CLAVE_REFRESH);
    if (!refresh) {
      return false;
    }
    try {
      const sesion = await firstValueFrom(
        this.http.post<Sesion>(`${environment.apiUrl}/auth/refresh`, { refresh_token: refresh }),
      );
      this._token.set(sesion.access_token);
      localStorage.setItem(CLAVE_ACCESO, sesion.access_token);
      if (sesion.refresh_token) {
        localStorage.setItem(CLAVE_REFRESH, sesion.refresh_token);
      }
      return true;
    } catch {
      return false;
    }
  }

  async cargarPerfil(): Promise<void> {
    if (!this._token()) {
      return;
    }
    try {
      const usuario = await firstValueFrom(
        this.http.get<Usuario>(`${environment.apiUrl}/auth/me`),
      );
      this._usuario.set(usuario);
    } catch {
      this.logout();
    }
  }

  logout(): void {
    this._token.set(null);
    this._usuario.set(null);
    localStorage.removeItem(CLAVE_ACCESO);
    localStorage.removeItem(CLAVE_REFRESH);
    void this.router.navigate(['/login']);
  }
}
