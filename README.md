# NUVIO GROWTH BOT 🚀
### Enterprise AI Social Media Growth & Management SaaS Platform

**NUVIO GROWTH BOT** es una plataforma SaaS integral para agencias, empresas y creadores que permite administrar múltiples redes sociales desde un único panel centralizado, crear contenido de alto impacto con inteligencia artificial, programar publicaciones con aprobación humana obligatoria y consultar estadísticas reales mediante APIs oficiales.

---

## 🌟 Características Principales

### 1. Panel Principal SaaS Premium
- **Tema Oscuro Elegante** con estética inspirada en Metricool y Linear.
- **Navegación Lateral Dinámica**: 12 módulos funcionales con interfaz 100% responsive.
- **Tarjetas KPI Interactivas**: Cuentas conectadas, seguidores totales, impresiones acumuladas y tasa de interacción.
- **Estados Claros y Transparentes**: Diferenciación estricta entre datos reales de API y modo de demostración.

### 2. Integración Oficial de Redes Sociales
Conexión directa mediante OAuth oficial y endpoints de desarrollador legítimos:
- **Instagram**: Instagram Graph API v20.0 (perfiles comerciales/creadores, publicación de reels/fotos, métricas de engagement).
- **Facebook**: Meta Graph API para Páginas (publicación programada, fotos, enlaces, métricas de alcance).
- **TikTok**: TikTok for Developers Content Posting API (inicialización de subida de video y estadísticas de creador).
- **YouTube**: Google YouTube Data API v3 (subida de videos, metadata, analíticas de canal).
- **Cifrado de Tokens**: Cifrado simétrico AES-256 (Fernet) en base de datos para todas las claves y tokens de acceso.

> **Política de Crecimiento Ético**: Nuvio Growth Bot rechaza y no implementa bots de seguidores falsos, visualizaciones artificiales, comentarios automáticos fraudulentos o spam. El crecimiento se logra mediante contenido de valor, planificación constante y análisis de datos.

### 3. AI Content Studio (Trilingüe)
- **Generación Multilingüe Nativa**: Soporte en **Español (`es`)**, **Inglés (`en`)** y **Kreyòl Ayisyen (`ht`)**.
- **Adaptación por Plataforma**: Hooks breves para TikTok, copys con saltos de línea y emojis para Instagram, debates comunitarios para Facebook y descripciones SEO para YouTube.
- **Herramientas de Copywriting**:
  - *Generación de múltiples variantes editables*
  - *Refinamiento de captions bajo instrucciones personalizadas*
  - *Generador de hashtags estratégicos por nicho*
  - *Traductor automático interlingüístico*
  - *Calendario estratégico de 7 a 30 días basado en pilares de contenido*
- **Soporte OpenAI**: Integración con GPT-4o-mini con motor heurístico de respaldo automático si no hay clave API configurada.

### 4. Sistema de Publicación con Aprobación Humana Obligatoria
- **Flujo Completo de Estados**:
  `Draft` ➔ `Pending Approval` ➔ `Approved` ➔ `Scheduled` ➔ `Publishing` ➔ `Published` / `Failed` / `Rejected`
- **Control de Seguridad Humana**: Ninguna publicación se envía automáticamente sin aprobación previa por un administrador, salvo que se active explícitamente la opción en configuración.
- **Revisión con Feedback**: Los administradores pueden aprobar o rechazar publicaciones adjuntando comentarios.
- **Reintento de Fallos**: Mecanismo seguro para reintentar publicaciones fallidas registrando los errores de cada plataforma.

### 5. Biblioteca Multimedia (Media Library)
- Subida y validación de archivos (imágenes JPG, PNG, WEBP, GIF; videos MP4, MOV, WEBM) de hasta 50MB.
- Organización por carpetas (*General*, *Campañas*, *Logos*, *Reels*).
- Almacenamiento local con abstracción preparada para Amazon S3 / Cloudflare R2 / MinIO.

### 6. Estadísticas y Reportes (Analytics)
- Resumen consolidado: Seguidores, impresiones, alcance, vistas, interacciones y porcentaje de engagement.
- Desglose comparativo por red social.
- Ranking de publicaciones con mejor rendimiento.
- **Exportación CSV** directa para reportes ejecutivos.

### 7. Arquitectura Multi-Tenant & RBAC (SaaS)
- Estricto aislamiento de datos por Organización.
- **Sub-Clientes de Agencia**: Espacios de trabajo dedicados para administrar múltiples marcas de clientes independientes.
- **Control de Acceso por Roles (RBAC)**:
  - `super_admin`: Acceso global a la infraestructura.
  - `agency_admin`: Administrador de la agencia / dueño de la cuenta.
  - `client_admin`: Administrador de marca con permisos de aprobación.
  - `editor`: Redactor y creador de contenidos.
  - `viewer`: Solo lectura de estadísticas y publicaciones.

### 8. Suscripciones y Facturación (Stripe)
- Planes preconfigurados:
  - **Free**: 1 cuenta, 15 publicaciones/mes, 25 créditos IA.
  - **Starter**: 3 cuentas, 75 publicaciones/mes, 150 créditos IA.
  - **Pro**: 10 cuentas, 300 publicaciones/mes, 600 créditos IA, hasta 3 clientes.
  - **Agency**: 35 cuentas, 1,500 publicaciones/mes, 2,500 créditos IA, clientes y equipo extendidos.
- Verificación automática de límites de plan en cada endpoint.
- Soporte para Stripe Checkout y webhooks asíncronos.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
|---|---|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Python-Jose (JWT), Cryptography (AES Fernet), Bcrypt |
| **Base de Datos** | SQLite (desarrollo local) / PostgreSQL (producción) |
| **Frontend** | Single Page Application (SPA), Jinja2, Tailwind/Dark Glass CSS, Lucide SVG Icons, Vanilla JS I18n Engine |
| **Integraciones** | OpenAI API, Stripe SDK, Meta Graph API, TikTok Posting API, Google YouTube Data API |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |
| **DevOps** | Docker, Docker Compose, Redis (scheduler) |

---

## 🚀 Inicio Rápido

### 1. Clonar y configurar entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Variables de entorno
Copia la plantilla y ajusta tus credenciales según corresponda:
```bash
cp .env.example .env
```

### 3. Inicializar base de datos y fixtures de demostración
```bash
python scripts/seed_db.py
```
> Esto creará las tablas, los planes por defecto y una cuenta administradora de demostración:
> - **Email**: `admin@nuviogrowth.com`
> - **Password**: `NuvioGrowth2026!`

### 4. Iniciar el servidor de desarrollo
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Dashboard interactivo: [http://localhost:8000](http://localhost:8000)
- Documentación OpenAPI Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Documentación ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Ejecución de Pruebas

Para ejecutar la suite de pruebas unitarias y de integración:
```bash
pytest -v
```

---

## 🐳 Despliegue con Docker Compose

Para desplegar la aplicación completa con backend FastAPI, base de datos PostgreSQL, Redis y worker de programación:

```bash
docker-compose up --build -d
```

---

## 🔐 Seguridad y Cumplimiento

1. **Protección contra ataques**: Middleware de limitación de tasa (*Rate Limiting* a 120 req/min por IP) y cabeceras de seguridad estrictas (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`).
2. **Cifrado en reposo**: Tokens de OAuth almacenados con cifrado reversible Fernet (AES-128-CBC / SHA256 HMAC).
3. **Contraseñas**: Hasheadas con Bcrypt mediante saltos individuales.
4. **Políticas y Términos**: Endpoints públicos disponibles en `/privacy-policy` y `/terms-of-service`.

