import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { Login } from './features/login/login';
import { Dashboard } from './features/dashboard/dashboard';
import { Evaluar } from './features/evaluar/evaluar';
import { Historial } from './features/historial/historial';
import { Shell } from './shared/shell';

export const routes: Routes = [
  { path: 'login', component: Login, title: 'Iniciar sesión · AlertaTemprana' },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'panel' },
      { path: 'panel', component: Dashboard, title: 'Panel · AlertaTemprana' },
      { path: 'evaluar', component: Evaluar, title: 'Evaluar estudiante · AlertaTemprana' },
      { path: 'historial', component: Historial, title: 'Historial · AlertaTemprana' },
    ],
  },
  { path: '**', redirectTo: '' },
];
