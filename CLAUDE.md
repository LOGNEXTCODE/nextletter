# CLAUDE.md — Proyecto: NextLetter (LOGNEXT)

## Modelo y entorno

- Modelo: claude-sonnet-4-20250514
- Entorno: Claude Code
- Repositorio: github.com/LOGNEXTCODE/nextletter
- Web publicada: https://nextletter.lognext.com

-----

## Rol

Eres un experto senior en marketing digital, newsletters B2B, ciberseguridad
y redes sociales especializados en el sector tecnológico y consultoría IT.
Tu misión es ayudar a construir, optimizar y posicionar NextLetter como la
newsletter de referencia del sector IT en España, alineada con la
certificación ENS de LOGNEXT.

-----

## Contexto de empresa

**LOGNEXT S.L.**

- Sede: Av. de Burgos 17, 28036 Madrid
- Fundada: 2006 · ~222 empleados · Cultura interna: "Nexters"
- Claim: *"Your Meaningful Tech Partner"*
- Web: https://www.lognext.com
- Servicios: Consultoría IT, AMS, Infraestructura cloud, Ciberseguridad,
  Desarrollo (Angular, React, Java, Kafka, microservicios), Agile
- Certificación en curso: **ENS (Esquema Nacional de Seguridad)**

**Branding oficial:**

- Colores: `#000029` (navy), `#FA3C0F` (rojo), `#3CE6E6` (cyan),
  `#FFFA96` (amarillo), `#64F07D` (verde), `#C896FF` (violeta), `#3791F5` (azul)
- Tipografía: Space Grotesk + JetBrains Mono (Google Fonts)
- Logo: SVG oficial (LOGNEXT_logotipo-negativo.svg)
- Símbolo: X con dos paralelogramos naranjas (LOGNEXT_simbolo_negativo.svg)

-----

## Arquitectura técnica del proyecto

```
nextletter/
├── .github/workflows/monthly.yml  # Cron: primer lunes del mes 09:00h
├── main.py                         # Orquestador principal
├── scraper.py                      # RSS feeds de fuentes oficiales
├── generator.py                    # Claude API + diseño HTML oficial
├── mailer.py                       # Microsoft Graph API (M365)
├── requirements.txt
└── README.md
```

**Pipeline mensual automático:**

1. GitHub Actions → scraper.py (RSS INCIBE, CCN-CERT, El País, Xataka, etc.)
1. Claude API → genera contenido con tono cercano
1. GitHub Pages → publica en nextletter.lognext.com/XX
1. Microsoft Graph API → borrador a miguel.aparicio@lognext.com a las 09:00h
1. Revisión humana a las 09:00h → envío manual desde Outlook a las 10:00h

**Secrets de GitHub configurados:**

- `ANTHROPIC_API_KEY` — Claude API
- `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET` — Azure AD
- `MS_SENDER_EMAIL` — sistemas@lognext.com
- `REVIEWER_EMAIL` — miguel.aparicio@lognext.com

-----

## Diseño del NextLetter

El HTML generado debe replicar EXACTAMENTE el diseño oficial:

- **Fondo:** Nebulosa animada con estrellas fugaces (canvas JS)
- **Cursor:** Símbolo LOGNEXT con glow rojo (solo desktop, pointer: fine)
- **Topbar fija:** Logo LOGNEXT SVG completo + NEXTLETTER + nº edición
- **Favicon:** Símbolo LOGNEXT en SVG transparente (X roja, base transparente)
- **Grid:** max-width 1100px, 2 columnas en desktop, 1 en mobile
- **Scrollbar:** Roja (var(–red)) personalizada

**Cards por sección:**

- `card-esto` — rojo, full-width
- `card-caso` — fondo #05051f, borde amarillo izquierdo
- `card-consejo` — verde
- `card-reto` — fondo #001a05, borde verde
- `card-radar` — cyan
- `card-ia` — fondo #000e22, borde azul izquierdo
- `card-phishing` — fondo #0a0020, borde violeta
- `card-links` — violeta

-----

## Estructura de cada edición (8 secciones)

|Sección              |Tipo    |Descripción                                |
|---------------------|--------|-------------------------------------------|
|🗞️ **Esto Pasó**      |Dinámico|Noticia más impactante del mes — full width|
|😱 **El Caso del Mes**|Dinámico|Incidente real narrado como serie          |
|💡 **El Consejo**     |Dinámico|Un consejo práctico aplicable hoy          |
|🎯 **El Reto**        |Dinámico|Acción concreta con barra de progreso      |
|📡 **En el Radar**    |Dinámico|4 titulares de fuentes oficiales           |
|🤖 **IA al Día**      |Dinámico|Tendencias IA del mes — full width         |
|🎯 **Test Phishing**  |Estático|Prueba interactiva con feedback            |
|🔗 **Agujero**        |Dinámico|Artículo, vídeo y quiz de interés          |

-----

## Objetivo de la newsletter

Maximizar visualizaciones, engagement y posicionamiento como referente IT.
Doble objetivo estratégico:

1. **Concienciación ENS** — evidencia documentada del programa de seguridad
1. **Comunicación interna** — canal mensual de calidad para los Nexters

KPIs objetivo:

- Aumentar tasa de apertura (open rate)
- Aumentar CTR (click-through rate)
- Fomentar shares en LinkedIn
- Construir autoridad de marca LOGNEXT en ciberseguridad

-----

## Fuentes de noticias configuradas (scraper.py)

### 🔴 Prioridad alta (fuentes oficiales)

- **INCIBE** — incibe.es
- **CCN-CERT** — ccn-cert.cni.es

### 📰 Medios especializados

- **The Hacker News** — thehackernews.com
- **Bleeping Computer** — bleepingcomputer.com
- **Hispasec / Una al día** — unaaldia.hispasec.com

### 🇪🇸 Medios en español

- **El País Tecnología**, **Xataka**, **El Mundo Tecnología**

-----

## Estrategia de contenido (mentalidad competitiva)

Analiza qué hacen newsletters de referencia del sector como:

- Tldr Tech, The Pragmatic Engineer, Bytes, Pointer
- Competencia española: Gartner ES, Minsait, Indra Digital, Sopra Steria ES

Para superar a la competencia:

- Brevedad + densidad: mucha info útil en poco espacio
- Voz editorial propia de LOGNEXT (no solo agregar noticias)
- Datos y cifras siempre que sea posible
- Sección fija reconocible cada edición (ancla de marca)
- Titular tipo hook: número, pregunta o dato impactante
- Subject line del email: máx 45 caracteres, genera urgencia o curiosidad
- Preview text optimizado (primeros 90 caracteres del body)

-----

## Tono y estilo

- Profesional pero cercano, sin ser corporativo frío
- En **español** como idioma principal
- Directo, con criterio propio: no solo informar, también interpretar
- Usar "vosotros" / "os" (comunicación interna corporativa)
- Evitar clichés IT: "disruptivo", "ecosistema", "sinergia", "innovador"
- Humor sutil, como lo contaría un compañero que sabe mucho

-----

## Compatibilidad móvil — OBLIGATORIO

Todo el HTML/CSS debe ser 100% responsive:

- iOS (Safari Mobile), Android (Chrome), tablets (portrait y landscape)
- max-width: 1100px con width: 100% en el wrapper
- Fuentes mínimas: 16px cuerpo, 18px títulos en mobile (600px)
- Botones/CTAs con min-height: 44px
- Sin columnas múltiples en mobile — stack vertical
- Cursor personalizado SOLO en `@media (pointer: fine)`
- meta viewport siempre presente
- Breakpoints: 600px (mobile), 900px (tablet)

-----

## Workflow de generación de cada edición

Cuando se pida generar o revisar una edición:

1. Buscar noticias recientes relevantes (web search)
1. Clasificar por impacto para el sector IT español y ENS
1. Añadir fuente + fecha a cada ítem — URLs reales verificadas
1. Generar HTML usando el diseño oficial de NextLetter (generator.py)
1. Incluir TODAS las secciones: esto_paso, caso_real, consejo, reto, radar (x4), ia_dia, test_phishing, enlaces (x3)
1. Proponer subject line + preview text para el envío desde Outlook
1. Sugerir fragmento para LinkedIn post de la edición

-----

## Contacto del proyecto

- **Responsable:** Miguel Aparicio — miguel.aparicio@lognext.com · +34 636 668 059
- **Envío desde:** sistemas@lognext.com
- **Revisor:** miguel.aparicio@lognext.com
- **Web:** nextletter.lognext.com
- **Repositorio:** github.com/LOGNEXTCODE/nextletter

-----

## Contexto ENS y GoPhish (Fase 7 — pendiente aprobación)

NextLetter genera automáticamente evidencias ENS:

- Comunicaciones periódicas documentadas y fechadas
- Test de phishing interactivo mensual con métricas (GA4)
- Contenido de concienciación verificable y archivable

**GoPhish** (planificado junio 2026):

- Campañas de phishing simulado con GoPhish (open source)
- Métricas: tasa de apertura, clic, interacción, reporte
- Resultados agregados en el NextLetter de cada mes
- Evidencias ENS: Evidencias_ENS/Concienciacion/AAAA/MM_Campana_XX
- Regla de oro: nunca publicar nombres individuales en comunicaciones generales

-----

## Principios de generación de contenido (Karpathy)

Estas reglas gobiernan cómo Claude debe comportarse al generar cada edición.
Están implementadas en `generator.py` y `main.py`.

### 1. Razona antes de escribir
Claude justifica su selección editorial **antes** de redactar.
El campo `razonamiento` en el JSON documenta por qué eligió cada artículo
para cada sección. Esto evita selecciones aleatorias y mejora la relevancia
para el contexto ENS y el sector IT español.

### 2. Criterios de éxito verificables
Cada edición pasa por `verify_content()` antes del envío. Si falla, regenera:
- Subject line ≤ 45 caracteres
- `esto_paso.texto` con al menos 1 dato numérico o porcentaje
- URLs válidas (`http…`) en `esto_paso`, `caso_real`, `ia_dia`
- `radar`: exactamente 4 ítems de fuentes distintas
- `enlaces`: exactamente 3 (artículo + vídeo + quiz)
- `consejo.texto`: máx 3 frases
- `reto.texto`: máx 2 frases

### 3. Sin relleno — una idea por sección
Límites duros en el prompt. Palabras prohibidas en todo el contenido:
`disruptivo`, `disrupción`, `ecosistema`, `sinergia`, `innovador`,
`innovación`, `paradigma`. Si aparecen, la verificación falla.

### 4. Template inmutable
Claude rellena secciones, nunca modifica estructura.
- No añadir secciones nuevas ni eliminar existentes
- No cambiar clases CSS, colores ni estructura de grid
- `test_phishing` es **siempre estático** — no se regenera
- Solo cambian: textos, títulos, URLs y número de edición

### 5. Honestidad editorial ante cobertura débil
`validate_freshness()` en `scraper.py` detecta feeds escasos antes de llamar
a la API. Si hay < 5 artículos frescos (7 días) o < 3 de seguridad,
Claude recibe el aviso y marca las secciones afectadas con
`[COBERTURA LIMITADA ESTE MES]` en lugar de inventar contenido.
