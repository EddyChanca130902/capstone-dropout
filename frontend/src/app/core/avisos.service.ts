import { Injectable, signal } from '@angular/core';

export type TipoAviso = 'exito' | 'error' | 'info';

export interface Aviso {
  id: number;
  tipo: TipoAviso;
  texto: string;
  detalle?: string;
}

/** Notificaciones flotantes (toasts) para confirmaciones y errores. */
@Injectable({ providedIn: 'root' })
export class AvisosService {
  private readonly _avisos = signal<Aviso[]>([]);
  private contador = 0;

  readonly avisos = this._avisos.asReadonly();

  exito(texto: string, detalle?: string): void {
    this.añadir('exito', texto, detalle);
  }

  error(texto: string, detalle?: string): void {
    this.añadir('error', texto, detalle);
  }

  info(texto: string, detalle?: string): void {
    this.añadir('info', texto, detalle);
  }

  cerrar(id: number): void {
    this._avisos.update((lista) => lista.filter((a) => a.id !== id));
  }

  private añadir(tipo: TipoAviso, texto: string, detalle?: string): void {
    const id = ++this.contador;
    this._avisos.update((lista) => [...lista, { id, tipo, texto, detalle }]);
    setTimeout(() => this.cerrar(id), tipo === 'error' ? 7000 : 4000);
  }
}
