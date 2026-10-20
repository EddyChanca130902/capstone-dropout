import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { EmptyState } from './empty-state';
import { Icon } from './icon';
import { Skeleton } from './skeleton';

describe('Icon', () => {
  beforeEach(() => TestBed.configureTestingModule({ imports: [Icon] }));

  it('dibuja las trazas del icono pedido', () => {
    const fixture = TestBed.createComponent(Icon);
    fixture.componentRef.setInput('nombre', 'panel');
    fixture.detectChanges();
    const svg = fixture.nativeElement.querySelector('svg');
    expect(svg).toBeTruthy();
    expect(svg.querySelectorAll('path').length).toBe(4);
  });

  it('cae en un icono por defecto si el nombre no existe', () => {
    const fixture = TestBed.createComponent(Icon);
    fixture.componentRef.setInput('nombre', 'no-existe');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('path').length).toBeGreaterThan(0);
  });
});

describe('EmptyState', () => {
  beforeEach(() => TestBed.configureTestingModule({ imports: [EmptyState], providers: [provideRouter([])] }));

  it('muestra titulo y mensaje', () => {
    const fixture = TestBed.createComponent(EmptyState);
    fixture.componentRef.setInput('titulo', 'Sin datos');
    fixture.componentRef.setInput('mensaje', 'Todavia no hay nada');
    fixture.detectChanges();
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Sin datos');
    expect(texto).toContain('Todavia no hay nada');
  });

  it('solo muestra el boton de accion si hay ruta', () => {
    const fixture = TestBed.createComponent(EmptyState);
    fixture.componentRef.setInput('titulo', 'Sin datos');
    fixture.componentRef.setInput('textoAccion', 'Crear');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button')).toBeNull();

    fixture.componentRef.setInput('rutaAccion', '/evaluar');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button')).toBeTruthy();
  });
});

describe('Skeleton', () => {
  beforeEach(() => TestBed.configureTestingModule({ imports: [Skeleton] }));

  it('aplica el ancho y alto indicados', () => {
    const fixture = TestBed.createComponent(Skeleton);
    fixture.componentRef.setInput('ancho', '80px');
    fixture.componentRef.setInput('alto', '2rem');
    fixture.detectChanges();
    const hueso = fixture.nativeElement.querySelector('.hueso');
    expect(hueso.style.width).toBe('80px');
    expect(hueso.style.height).toBe('2rem');
  });
});
