# NextLetter 🔐
**La carta de los que van un paso por delante**
 
Newsletter mensual automatizada de ciberseguridad y tecnología para LOGNEXT.
Publicada en [nextletter.lognext.com](https://nextletter.lognext.com) · Distribuida el primer lunes de cada mes a las 10:00h.
 
---
 
## ¿Cómo funciona?
 
El primer lunes de cada mes a las 09:00h, GitHub Actions ejecuta automáticamente el pipeline:
 
1. **Scraper** — Lee RSS de INCIBE, CCN-CERT, El País Tech, Xataka, Bleeping Computer, The Hacker News, Hispasec
2. **Claude API** — Selecciona las noticias más relevantes y redacta el contenido con tono cercano y sin tecnicismos
3. **GitHub Pages** — Publica la edición en `nextletter.lognext.com/XX` automáticamente
4. **Mailer** — Envía el borrador a Miguel (revisor) vía Microsoft Graph API a las 09:00h
5. **Tú a las 10:00h** — Revisas el borrador y envías el correo de presentación desde Outlook
---
 
## Secciones del NextLetter
 
| Sección | Descripción | Tipo |
|---------|-------------|------|
| 🗞️ **Esto Pasó** | La noticia más impactante del mes — ancho completo | Dinámico |
| 😱 **El Caso del Mes** | Un incidente real narrado como episodio de serie | Dinámico |
| 💡 **El Consejo** | Un consejo práctico aplicable hoy mismo | Dinámico |
| 🎯 **El Reto** | Una acción concreta para el mes | Dinámico |
| 📡 **En el Radar** | 4 titulares reales de fuentes oficiales | Dinámico |
| 🤖 **IA al Día** | Lo más relevante en IA este mes — ancho completo | Dinámico |
| 🎯 **Test de Phishing** | Prueba interactiva mensual con feedback educativo | Estático |
| 🔗 **Por si queréis caer** | Artículo, vídeo y quiz de interés | Dinámico |
 
---
 
## Diseño
 
- **Tipografía:** Space Grotesk + JetBrains Mono (Google Fonts)
- **Colores:** Branding oficial LOGNEXT (`#000029` navy, `#FA3C0F` rojo + paleta secundaria)
- **Layout:** Grid responsive — 1100px desktop / adaptado tablet y móvil
- **Favicon:** Símbolo LOGNEXT en SVG (X con paralelogramos naranjas sobre fondo transparente)
- **Logo LOGNEXT:** Logotipo negativo completo en SVG incrustado en la topbar
- **Cursor personalizado:** Símbolo LOGNEXT animado con glow rojo (solo desktop)
- **Fondo nebulosa:** Nubes de color animadas + estrellas parpadeantes + estrellas fugaces
- **Hover effects:** Cards con elevación y glow, botones con color explícito por sección
- **Google Analytics GA4:** Tracking de secciones leídas, clics y resultados del test
- **Footer:** 3 columnas (marca, ediciones, contacto) con enlaces interactivos
- **Scrollbar:** Personalizada en rojo LOGNEXT
---
 
## Fuentes de noticias
 
### 🔴 Fuentes oficiales (prioridad alta)
- **INCIBE** — incibe.es (Instituto Nacional de Ciberseguridad)
- **CCN-CERT** — ccn-cert.cni.es (Centro Criptológico Nacional)
### 📰 Medios especializados
- **The Hacker News** — thehackernews.com
- **Bleeping Computer** — bleepingcomputer.com
- **Hispasec / Una al día** — unaaldia.hispasec.com
### 🇪🇸 Medios en español
- **El País Tecnología** — elpais.com/tecnologia
- **Xataka** — xataka.com
- **El Mundo Tecnología** — elmundo.es
Para añadir fuentes: edita el array `SOURCES` en `scraper.py`.
 
---
 
## Google Analytics — Eventos trackeados
 
| Evento | Descripción |
|--------|-------------|
| `section_read` | Qué secciones visita cada usuario |
| `outbound_click` | Qué enlaces externos generan más interés |
| `phishing_test` | Resultados del test mensual (correct / incorrect) |
 
Para activarlo: sustituye `G-XXXXXXXXXX` en `generator.py` por tu ID real de GA4.
 
---
 
## Configuración inicial
 
### 1. GitHub Secrets
`Settings → Secrets and variables → Actions → New repository secret`
 
| Secret | Descripción |
|--------|-------------|
| `ANTHROPIC_API_KEY` | API Key de Anthropic (console.anthropic.com) |
| `MS_TENANT_ID` | Azure AD → Overview → Directory (tenant) ID |
| `MS_CLIENT_ID` | Azure AD → Registros de aplicaciones → NextLetter → Application ID |
| `MS_CLIENT_SECRET` | Azure AD → NextLetter → Certificados y secretos → valor del secreto |
| `MS_SENDER_EMAIL` | `sistemas@lognext.com` |
| `REVIEWER_EMAIL` | `miguel.aparicio@lognext.com` |
 
### 2. Azure AD — App NextLetter
1. portal.azure.com → **Registros de aplicaciones** → **Nuevo registro**
2. Nombre: `NextLetter` · Tipos de cuenta: Solo inquilino único: Lognext
3. **Permisos de API** → Microsoft Graph → Permisos de aplicación → `Mail.Send`
4. **Conceder consentimiento de administrador**
5. **Certificados y secretos** → Nuevo secreto → copiar el **Valor**
### 3. GitHub Pages
1. `Settings → Pages → Source: Deploy from a branch`
2. Branch: `main` · Folder: `/ (root)`
3. Custom domain: `nextletter.lognext.com` → Save
4. ✅ Enforce HTTPS
### 4. DNS interno (Windows Server)
Consola DNS → Zonas de búsqueda directa → `lognext.com` → Nuevo alias (CNAME):
```
Nombre:  nextletter
Destino: lognextcode.github.io
```
 
### 5. DNS externo (Acens)
```
Tipo:    CNAME
Nombre:  nextletter
Valor:   lognextcode.github.io
```
 
---
 
## Cadencia de publicación
 
```
Cron: "0 8 1-7 * 1"
→ Primer lunes de cada mes a las 09:00h (08:00 UTC verano)
 
09:00h → Borrador llega a miguel.aparicio@lognext.com
10:00h → Revisión y envío manual desde Outlook a toda la empresa
```
 
---
 
## Estructura del proyecto
 
```
nextletter/
├── .github/
│   └── workflows/
│       └── monthly.yml      # Cron job + publicación en Pages
├── main.py                  # Orquestador principal
├── scraper.py               # Extrae noticias via RSS
├── generator.py             # Genera HTML con Claude API + diseño oficial
├── mailer.py                # Envía borrador vía Microsoft Graph API
├── requirements.txt         # anthropic, feedparser, requests
└── README.md
```
 
---
 
## Roadmap
 
| Fase | Descripción | Estado |
|------|-------------|--------|
| ✅ 1 | Repositorio GitHub + archivos base | Completado |
| ✅ 2 | Azure AD + 6 Secrets GitHub | Completado |
| ✅ 3 | Pipeline probado — email recibido en Outlook | Completado |
| ✅ 3b | GitHub Pages + DNS externo (Acens) + DNS interno (Windows Server) | Completado |
| ✅ 4 | Diseño final — nebulosa, cursor LOGNEXT, logo, favicon, footer, IA al día | Completado |
| ✅ 5 | generator.py integrado con diseño oficial | Completado |
| 🔄 6 | Lanzamiento NextLetter #01 — Lunes 4 mayo 2026 | En curso |
| ⏳ 7 | GoPhish — campañas de phishing simulado (pendiente aprobación dirección) | Planificado |
 
---
 
## Contacto
 
**Departamento IT — LOGNEXT S.L.**
sistemas@lognext.com · +34 636 668 059 · lognext.com
