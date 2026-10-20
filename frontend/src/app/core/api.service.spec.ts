import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { Estudiante } from './models';
import { environment } from '../../environments/environment';

const ESTUDIANTE: Estudiante = {
  dni: '70123456',
  nombre: 'María Quispe',
  edad: 19,
  genero: 'Femenino',
  area_estudios: 'Ciencias de la Salud',
  becario: 'No',
  deudor: 'No',
  matricula_al_dia: 'Sí',
  desplazado: 'No',
  cu1_matriculadas: 6,
  cu1_aprobadas: 1,
  cu1_nota: 6,
  cu2_matriculadas: 6,
  cu2_aprobadas: 0,
  cu2_nota: 5,
};

describe('ApiService', () => {
  let servicio: ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ApiService, provideHttpClient(), provideHttpClientTesting()],
    });
    servicio = TestBed.inject(ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('predecir envia el estudiante y devuelve la prediccion', async () => {
    const promesa = servicio.predecir(ESTUDIANTE);
    const peticion = http.expectOne(`${environment.apiUrl}/predict`);
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body.dni).toBe('70123456');
    peticion.flush({ probabilidad: 0.82, nivel: 'ALTO', modelo_version: 'v1', umbrales: {}, tiempo_ms: 4 });
    const resultado = await promesa;
    expect(resultado.probabilidad).toBe(0.82);
    expect(resultado.nivel).toBe('ALTO');
  });

  it('listarEvaluaciones aplica los filtros', async () => {
    const promesa = servicio.listarEvaluaciones({ limite: 10, nivel: 'ALTO' });
    const peticion = http.expectOne(
      (req) => req.url === `${environment.apiUrl}/evaluaciones`,
    );
    expect(peticion.request.params.get('limite')).toBe('10');
    expect(peticion.request.params.get('nivel')).toBe('ALTO');
    peticion.flush({ total: 1, datos: [] });
    await promesa;
  });

  it('eliminarEvaluacion llama al endpoint de borrado', async () => {
    const promesa = servicio.eliminarEvaluacion(7);
    const peticion = http.expectOne(`${environment.apiUrl}/evaluaciones/7`);
    expect(peticion.request.method).toBe('DELETE');
    peticion.flush({ eliminado: true });
    await promesa;
  });
});
