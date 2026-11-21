# Aplicación web de ATLAS

React 19 + TypeScript + Vite, Tailwind CSS 4 y componentes al estilo shadcn/ui sobre Radix.
Reglas del repositorio: [README](../README.md#reglas).

La aplicación usa y muestra solo lo que el backend implementa.

## Estructura

| Carpeta | Contenido |
|---|---|
| `src/api` | Contrato generado (`esquema.ts`), cliente tipado (`openapi-fetch`), consultas y mutaciones (TanStack Query), cargas con URL prefirmada y directorio de nombres |
| `src/lib` | Sesión (Cognito sin SDK o token local), catálogos del dominio, formatos y validación de formatos canónicos (Zod) |
| `src/componentes` | Componentes base (`ui/`), piezas del dominio (sugerido frente a validado, estados) y visor de documentos (pdf.js, cargado aparte) |
| `src/paginas` | Inicio, trámites, espacio del trámite (resumen, documentos y datos, vínculos y controles, consulta, revisión, historial), tareas, evidencia de la decisión y administración |
| `e2e` | Recorridos críticos con Playwright contra el stack local |

## Contrato de la API

Los tipos salen del OpenAPI real. Después de cambiar la API:

```bash
cd backend && .venv/bin/python -m atlas.herramientas.exportar_openapi ../frontend/openapi.json
cd ../frontend && npm run tipos
```

Una prueba del backend falla si `openapi.json` quedó desactualizado.

## Desarrollo local

Con el backend local corriendo (`backend/README.md`) y moto preparado:

```bash
npm ci
cp .env.example .env.local
npm run dev            # http://localhost:5173 (la API se reenvía por /api)
```

Para tener datos, la **semilla local** recorre el escenario de la cadena de evidencia por la API con el
**procesamiento simulado** (las sugerencias quedan rotuladas «Simulación local»; no es IA real):

```bash
cd ../backend && .venv/bin/python -m atlas.herramientas.sembrar_local
```

Imprime un token por rol para ingresar en modo local (se pega en la pantalla de ingreso).

## Demo

La aplicación corre en la máquina del presentador contra API Gateway; no se crean recursos
AWS para el frontend. En `.env.local`: `VITE_ATLAS_API_URL` (salida `url_api` de Terraform),
`VITE_ATLAS_AUTENTICACION=cognito`, `VITE_ATLAS_COGNITO_CLIENTE`. Luego:

```bash
npm run build && npm run preview     # http://localhost:4173
```

El origen `http://localhost:4173` debe estar en `origenes_web` (raíz `demo`) y en
`origenes_cors` (raíz `persistent`) del Terraform que aplica el operador.

## Hospedaje en S3 + CloudFront

La raíz Terraform `web` sirve la aplicación en `https://<id>.cloudfront.net`, con el bucket
privado (OAC), rutas de React resueltas a `index.html` y encabezados de seguridad (CSP, HSTS).
La aplicación lee `configuracion.json` al iniciar (URL de la API y cliente de Cognito); sin
ese archivo usa las variables `VITE_*`, así que el desarrollo local no cambia. Publicación,
solo por el operador:

```bash
infra/web/publicar.sh --aplicacion      # compila y sube (al cambiar el frontend)
infra/web/publicar.sh --configuracion   # en cada sesión, después de aplicar demo
```

## Verificaciones

```bash
npm run lint && npm run tipado && npm test && npm run build
```

Recorridos E2E (stack local levantado y semilla local):

```bash
npx playwright install chromium     # una vez
ATLAS_E2E_TOKEN_RESPONSABLE="<token del responsable>" npm run e2e
```
