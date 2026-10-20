import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';

/** Adjunta el access token y reintenta una vez tras refrescarlo. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.token();

  const request = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401 || !token) {
        return throwError(() => error);
      }
      return from(auth.refrescar()).pipe(
        switchMap((ok) => {
          if (!ok) {
            auth.logout();
            return throwError(() => error);
          }
          const nuevo = auth.token();
          return next(req.clone({ setHeaders: { Authorization: `Bearer ${nuevo}` } }));
        }),
      );
    }),
  );
};
