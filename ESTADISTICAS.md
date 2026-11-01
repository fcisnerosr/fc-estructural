# Estadísticas de visitas del sitio

El sitio cuenta sus visitas con **GoatCounter**: no usa cookies ni guarda datos personales, así
que no necesita aviso de cookies. GitHub Pages no registra visitantes por su cuenta, y la pestaña
*Insights → Traffic* del repositorio cuenta a quien abre el repo en github.com, **no** a quien
visita la página.

Se instaló el **2026-10-30**. Las visitas anteriores a esa fecha no se registraron y no se pueden
recuperar.

## Dónde ver las cifras

| | |
|---|---|
| **Panel** | https://fc-estructural.goatcounter.com |
| **Cuenta (Account name)** | `fc-estructural` |
| **Site domain** | `fcisnerosr.github.io` |
| **Correo de acceso** | fcisnerosr@outlook.es (verificado) |
| **Contraseña** | la del gestor de contraseñas; **nunca se escribe aquí**: este repositorio es público |
| **Sitio que se mide** | https://fcisnerosr.github.io/fc-estructural/ |

En el panel:

- **Periodo** (arriba a la izquierda): *day*, *week*, *month*… o las fechas a mano.
- **Pages**: qué páginas se vieron. `/fc-estructural/` es la principal; `/fc-estructural/modelos/<proyecto>/` son los visores 3D.
- **Referrers**: de dónde llegaron (WhatsApp, Google, LinkedIn…). Las que dicen **qr** llegaron escaneando el QR de una tarjeta.
- **Browsers, Systems, Sizes, Locations**: navegador, sistema, celular o computadora, y país.

## Configuración de la cuenta

En ⚙️ **Settings**:

- **Timezone → America/Mexico_City.** Sin esto el panel usa hora UTC: después de las 18:00 de México las visitas caen en el día siguiente.
- *Languages* está desactivado: no hace falta.

## Qué se cuenta

**Visitas** de la página principal (`index.html`) y de los siete visores (`modelos/<proyecto>/index.html`).

**Clics**, que aparecen en la lista de *Pages* con estos nombres:

| Nombre | Botón |
|---|---|
| `planos-casa-cedros`, `planos-auditorio-escolar`, `planos-casa-el-dorado`, `planos-local-comercial`, `planos-muro-de-contencion` | «Planos (PDF)» de cada proyecto, en su tarjeta o en su visor |
| `platica-tipos-de-falla` | PDF de la plática del 2026-10-30 |
| `curso-modulo2`, `curso-modulo2-resumen` | PDF del curso del Módulo 2 y su resumen |
| `whatsapp` | cualquiera de los tres botones de WhatsApp |
| `correo` | los enlaces de correo |

**QR**: el QR de cada tarjeta abre el visor con `?ref=qr` al final, y GoatCounter cuenta esa visita
con origen *qr*.

## Cómo está instalado

Una línea al final de cada página, antes de `</body>`:

```html
<script data-goatcounter="https://fc-estructural.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
```

- En `index.html`, puesta a mano.
- En los visores la escribe `herramientas/publicar_proyectos.py` (plantilla `PAGINA`): al regenerar un proyecto se conserva sola.
- Un clic se cuenta agregando al enlace `data-goatcounter-click="nombre"`. En los botones de planos de los visores lo pone el mismo script (`BOTON_PLANOS`).

**Una página nueva no se cuenta** si no lleva esa línea.

## No contar las visitas propias

Abrir una vez, en **cada** navegador y en el celular:

```
https://fcisnerosr.github.io/fc-estructural/#toggle-goatcounter
```

Sale un aviso de que el conteo quedó *disabled* en ese navegador. Abrirlo otra vez lo reactiva.

## Por qué una visita puede no aparecer

- **Bloqueadores.** Brave (con sus escudos) y extensiones como uBlock bloquean GoatCounter. Esas visitas no se cuentan: la cifra real es algo mayor que la del panel.
- **Navegadores automatizados.** Las pruebas con Playwright o con un navegador sin ventana se marcan como bot (`b=` en la petición) y GoatCounter las descarta.
- **Zona horaria.** Ver *Configuración de la cuenta*.
- **El propio navegador excluido** con `#toggle-goatcounter`.

Para probar que cuenta: abrir el sitio desde el celular, sin Brave, y revisar el panel con el periodo *day*.

## Lo instalado por terminal

GoatCounter no necesita instalar nada. Lo que sí se instaló es lo que usa
`herramientas/publicar_proyectos.py` para generar los visores, los planos, los QR y las portadas:

| Paquete | Versión | Para qué |
|---|---|---|
| `pymupdf` | 1.28.0 | unir los planos y tapar propietario y dirección |
| `numpy` | 2.4.3 | aristas de los modelos y recorte de las portadas |
| `qrcode` | 8.2 | los QR de las tarjetas |
| `pillow` | 12.2.0 | imágenes de QR y portadas |
| `playwright` | 1.62.0 | capturar las portadas (solo con `--portadas`) |
| Google Chrome | 154 | el navegador que usa Playwright (`/usr/bin/google-chrome`) |

En una máquina nueva:

```
pip install pymupdf numpy qrcode pillow playwright
```

Playwright usa el Chrome del sistema; si está en otro lugar, se indica con `CHROME=/ruta/al/chrome`.
