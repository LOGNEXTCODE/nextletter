# NextLetter 🔐
**La carta de los que van un paso por delante**

Newsletter mensual automatizada de ciberseguridad y tecnología para LOGNEXT. Publicada en [nextletter.lognext.com](https://nextletter.lognext.com) y distribuida por correo corporativo el día 1 de cada mes.

---

## ¿Cómo funciona?

El día 1 de cada mes, GitHub Actions ejecuta automáticamente el pipeline:

1. **Scraper** — Lee RSS de INCIBE, CCN-CERT, El País Tech, Xataka, El Mundo, The Hacker News, Hispasec, Bleeping Computer
2. **Claude API** — Selecciona noticias, redacta el contenido con tono cercano y humor
3. **GitHub Pages** — Publica la edición en nextletter.lognext.com/XX automáticamente
4. **Mailer** — Envía el borrador a ti (revisor) vía Microsoft Graph API
5. **Tú** — Revisas, editas si quieres, y envías desde Outlook

---

## El NextLetter incluye cada mes

| Sección | Descripción |
|---------|-------------|
| 🗞️ **Esto Pasó** | La noticia más impactante del mes — ancho completo |
| 😱 **El Caso del Mes** | Un incidente real contado como serie |
| 💡 **El Consejo** | Un consejo práctico aplicable hoy |
| 🎯 **El Reto** | Una acción concreta para el mes |
| 📡 **En el Radar** | 4 titulares rápidos de fuentes oficiales |
| 🎯 **Test de Phishing** | Prueba interactiva mensual con feedback |
| 🔗 **Agujero** | Artículo, vídeo y quiz de interés |

---

## Diseño y tecnología

- **Tipografía:** Space Grotesk + JetBrains Mono
- **Colores:** Branding oficial LOGNEXT (`#000029`, `#FA3C0F` + paleta secundaria)
- **Layout:** Grid responsive — 1100px desktop / adaptado tablet y móvil
- **Cursor personalizado** animado (solo desktop)
- **Efecto parallax** en el fondo
- **Google Analytics GA4** integrado — tracking por sección, clics y test phishing
- **Test phishing interactivo** con feedback educativo
- **Topbar fija** con logo LOGNEXT al hacer scroll

---

## Fuentes de noticias configuradas

### 🔴 Fuentes oficiales (máxima prioridad)
- **INCIBE** — incibe.es (Instituto Nacional de Ciberseguridad)
- **CCN-CERT** — ccn-cert.cni.es (Centro Criptológico Nacional)
- **ENISA** — enisa.europa.eu (Agencia Europea de Ciberseguridad)

### 📰 Medios especializados
- **The Hacker News** — thehackernews.com
- **Bleeping Computer** — bleepingcomputer.com
- **Hispasec / Una al día** — unaaldia.hispasec.com
- **Krebs on Security** — krebsonsecurity.com

### 🇪🇸 Medios en español
- **El País Tecnología**
- **Xataka**
- **El Mundo Tecnología**

Para añadir más fuentes, edita el array `SOURCES` en `scraper.py`.

---

## Google Analytics

El sistema trackea automáticamente:
- `section_read` — qué secciones lee cada usuario
- `outbound_click` — qué enlaces externos generan más interés
- `phishing_test` — resultados del test mensual (correct / incorrect)

Para activarlo, sustituye `G-XXXXXXXXXX` en el HTML generado por tu ID real de GA4.

---

## Configuración inicial

### 1. GitHub Secrets
Ve a tu repositorio → **Settings → Secrets and variables → Actions** y añade:

| Secret | Descripción |
|--------|-------------|
| `ANTHROPIC_API_KEY` | API Key de Anthropic (console.anthropic.com) |
| `MS_TENANT_ID` | Azure AD → Overview → Tenant ID |
| `MS_CLIENT_ID` | Azure AD → App registrations → tu app → Application ID |
| `MS_CLIENT_SECRET` | Azure AD → tu app → Certificates & secrets → New secret |
| `MS_SENDER_EMAIL` | Email desde el que se envía (sistemas@lognext.com) |
| `REVIEWER_EMAIL` | Email del revisor (miguel.aparicio@lognext.com) |

### 2. Registro de app en Azure AD

1. Ve a **portal.azure.com** → Registros de aplicaciones → Nuevo registro
2. Nombre: `NextLetter`
3. En **Permisos de API** añade: `Mail.Send` (Permiso de aplicación)
4. Haz clic en **Conceder consentimiento de administrador**
5. Crea un **Secreto de cliente** y cópialo como secret de GitHub

### 3. GitHub Pages

1. Settings → Pages → Source: **GitHub Actions**
2. Custom domain: `nextletter.lognext.com`
3. Marcar ✅ Enforce HTTPS
4. En tu DNS (Acens): registro CNAME `nextletter` → `lognextcode.github.io`

---

## Ejecución manual

Desde GitHub → **Actions → NextLetter — Generación mensual → Run workflow**

Puedes especificar el número de edición manualmente si es necesario.

---

## Estructura del proyecto

```
nextletter/
├── .github/
│   └── workflows/
│       └── monthly.yml      # Cron job mensual + publicación Pages
├── main.py                  # Orquestador principal
├── scraper.py               # Lee RSS de fuentes de noticias
├── generator.py             # Genera el contenido con Claude API
├── mailer.py                # Envía borrador vía Microsoft Graph API
├── requirements.txt
└── README.md
```

---

## Roadmap

| Fase | Descripción | Estado |
|------|-------------|--------|
| ✅ 1 | Configuración Azure AD y GitHub | Completado |
| ✅ 2 | API Keys y Secrets | Completado |
| ✅ 3 | Prueba y verificación pipeline | Completado |
| ✅ 3b | GitHub Pages + DNS personalizado | Completado |
| 🔄 4 | Lanzamiento NextLetter #01 | En curso |
| ⏳ 5 | Campaña phishing simulado (GoPhish) | Planificado |

---

*by LOGNEXT · Departamento IT · sistemas@lognext.com*
