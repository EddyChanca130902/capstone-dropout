import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly detalle = signal<string | null>(null);
  readonly mostrarClave = signal(false);

  readonly formulario = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(4)]],
  });

  async entrar(): Promise<void> {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.error.set('Revisa el correo y la contraseña.');
      return;
    }
    this.cargando.set(true);
    this.error.set(null);
    this.detalle.set(null);
    try {
      // Eltrim evita el error mas comun: un espacio pegado al final.
      const { email, password } = this.formulario.getRawValue();
      await this.auth.login(email.trim(), password);
      await this.router.navigate(['/panel']);
    } catch (error) {
      const { mensaje, detalle } = this.traducirError(error);
      this.error.set(mensaje);
      this.detalle.set(detalle);
    } finally {
      this.cargando.set(false);
    }
  }

  /** Traduce la respuesta de la API a un mensaje accionable en español. */
  private traducirError(error: unknown): { mensaje: string; detalle: string | null } {
    const status = (error as { status?: number })?.status ?? 0;
    const bruto = (error as { error?: { detail?: unknown } })?.error?.detail;
    const detalle = typeof bruto === 'string' ? bruto : null;

    if (status === 401) {
      return {
        mensaje: 'Correo o contraseña incorrectos.',
        detalle: detalle ?? 'La API respondió 401 (credenciales no válidas).',
      };
    }
    if (status === 429) {
      return {
        mensaje: 'Demasiados intentos. Espera un momento y vuelve a intentarlo.',
        detalle: detalle,
      };
    }
    if (status === 0) {
      return {
        mensaje: 'No se pudo conectar con la API. Revisa tu conexión.',
        detalle: detalle,
      };
    }
    return {
      mensaje: 'No se pudo iniciar sesión. Inténtalo de nuevo.',
      detalle: detalle,
    };
  }
}
