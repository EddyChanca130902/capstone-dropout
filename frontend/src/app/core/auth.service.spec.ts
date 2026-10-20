import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { Component } from '@angular/core';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

@Component({ template: '' })
class StubComponent {}

describe('AuthService', () => {
  let servicio: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'login', component: StubComponent }]),
      ],
    });
    servicio = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('arranca sin sesion', () => {
    expect(servicio.autenticado()).toBe(false);
  });

  it('guarda el token tras un login correcto', async () => {
    const promesa = servicio.login('orientador@alertatemprana.pe', 'clave');
    const peticion = http.expectOne(`${environment.apiUrl}/auth/login`);
    expect(peticion.request.method).toBe('POST');
    peticion.flush({
      access_token: 'token-abc',
      refresh_token: 'refresh-xyz',
      usuario: { id: 'u1', email: 'orientador@alertatemprana.pe' },
    });
    await promesa;

    expect(servicio.autenticado()).toBe(true);
    expect(servicio.token()).toBe('token-abc');
    expect(localStorage.getItem('alertatemprana.access_token')).toBe('token-abc');
    expect(servicio.usuario()?.email).toBe('orientador@alertatemprana.pe');
  });

  it('propaga el error si las credenciales son invalidas', async () => {
    const promesa = servicio.login('a@b.com', 'mala');
    http.expectOne(`${environment.apiUrl}/auth/login`).flush(
      { detail: 'Invalid login credentials' },
      { status: 401, statusText: 'Unauthorized' },
    );
    await expect(promesa).rejects.toBeTruthy();
    expect(servicio.autenticado()).toBe(false);
  });

  it('logout limpia el estado y el almacenamiento', () => {
    localStorage.setItem('alertatemprana.access_token', 'x');
    localStorage.setItem('alertatemprana.refresh_token', 'y');
    servicio.logout();
    expect(servicio.autenticado()).toBe(false);
    expect(localStorage.getItem('alertatemprana.access_token')).toBeNull();
  });
});
