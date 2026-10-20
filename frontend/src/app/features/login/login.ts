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

  readonly formulario = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(4)]],
  });

  async entrar(): Promise<void> {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    this.cargando.set(true);
    this.error.set(null);
    try {
      const { email, password } = this.formulario.getRawValue();
      await this.auth.login(email, password);
      await this.router.navigate(['/panel']);
    } catch (error) {
      const detalle =
        typeof error === 'object' && error !== null && 'error' in error
          ? ((error as { error?: { detail?: string } }).error?.detail ?? '')
          : '';
      this.error.set(detalle || 'No se pudo iniciar sesión. Revisa tus credenciales.');
    } finally {
      this.cargando.set(false);
    }
  }
}
