# NextLetter 🔐
**La carta de los que van un paso por delante**

Newsletter mensual automatizada de ciberseguridad y tecnología para LOGNEXT.

---

## ¿Cómo funciona?

El día 1 de cada mes, GitHub Actions ejecuta automáticamente el pipeline:

1. **Scraper** — Lee RSS de INCIBE, CCN-CERT, El País Tech, Xataka, El Mundo
2. **Claude API** — Selecciona noticias, redacta el contenido con tono cercano y humor
3. **Mailer** — Envía el borrador a ti (revisor) vía Microsoft Graph API
4. **Tú** — Revisas, editas si quieres, y envías desde Outlook

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
| `MS_SENDER_EMAIL` | Email desde el que se envía (ej: it@lognext.com) |
| `REVIEWER_EMAIL` | Tu email personal para recibir el borrador |

### 2. Registro de app en Azure AD

1. Ve a **portal.azure.com** → Azure Active Directory → App registrations → New registration
2. Nombre: `NextLetter`
3. En **API permissions** añade: `Mail.Send` (Application permission)
4. Haz clic en **Grant admin consent**
5. Crea un **Client secret** y cópialo como secret de GitHub

### 3. Activar el repositorio

```bash
git clone https://github.com/tu-org/nextletter.git
cd nextletter
# Configura los secrets en GitHub
# El workflow se ejecutará automáticamente el día 1 del mes
```

---

## Ejecución manual

Desde GitHub → **Actions → NextLetter → Run workflow**

Puedes especificar el número de edición manualmente si es necesario.

---

## Estructura del proyecto

```
nextletter/
├── .github/
│   └── workflows/
│       └── monthly.yml      # Cron job mensual
├── main.py                  # Orquestador principal
├── scraper.py               # Lee RSS de fuentes de noticias
├── generator.py             # Genera el contenido con Claude API
├── mailer.py                # Envía via Microsoft Graph API
├── requirements.txt
└── README.md
```

---

## Fuentes de noticias configuradas

- 🔴 **INCIBE** — Instituto Nacional de Ciberseguridad
- 🔴 **CCN-CERT** — Centro Criptológico Nacional
- 📰 **El País Tecnología**
- 📰 **Xataka**
- 📰 **El Mundo Tecnología**
- 📰 **Bleeping Computer**

Para añadir más fuentes, edita el array `SOURCES` en `scraper.py`.

---

## El NextLetter incluye cada mes

| Sección | Descripción |
|---------|-------------|
| 🗞️ **Esto Pasó** | La noticia más impactante del mes |
| 😱 **El Caso del Mes** | Un incidente real contado como serie |
| 💡 **El Consejo** | Un consejo práctico aplicable hoy |
| 🎯 **El Reto** | Una acción concreta para el mes |
| 🔗 **Agujero** | 2 enlaces de interés |

---

*by LOGNEXT · Equipo IT*
