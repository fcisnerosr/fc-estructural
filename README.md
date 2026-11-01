# f'c estructural — Portafolio de proyectos

Sitio estático (GitHub Pages) con proyectos del despacho: cada uno con su modelo estructural
en 3D, que se explora en el navegador, y sus planos estructurales en PDF.

**Sitio:** https://fcisnerosr.github.io/fc-estructural/

## Contenido

- `index.html` — landing con la tarjeta de cada proyecto.
- `modelos/<slug>/` — por proyecto: `index.html` (el visor 3D), `modelo.js` (su geometría),
  `planos.pdf` y `img/portada.webp` (la imagen de la tarjeta).
- `modelos/visor.js`, `modelos/visor.css` — el visor, el mismo para todos los proyectos.
- `assets/` — estilos, logo y códigos QR.
- `herramientas/publicar_proyectos.py` — genera todo lo de `modelos/<slug>/` y el QR a partir
  del expediente en `~/github/despacho`.
- `ESTADISTICAS.md` — las visitas del sitio: dónde verlas (GoatCounter), qué se cuenta y cómo está
  instalado.

## Publicar o actualizar un proyecto

```
python3 herramientas/publicar_proyectos.py 014              # un expediente
python3 herramientas/publicar_proyectos.py --portadas       # todos, con su portada
```

Necesita PyMuPDF, NumPy, qrcode y Pillow; las portadas, además, Playwright y Chrome. Para un
proyecto nuevo se agrega su entrada en `PROYECTOS`, dentro del script, y su tarjeta en
`index.html`.

> **Este repositorio es público.** Del expediente se publica solo la geometría de cada pieza
> con su clave, su familia y su sección: nunca las notas, fuentes ni dudas del visor interno.
> En los planos se tapan el propietario y la dirección exacta **por zona** (rectángulos medidos
> sobre cada formato de lámina), para que ningún nombre quede escrito en el script. Si cambia
> el formato de una lámina, hay que volver a medir su zona y revisar el PDF antes de subirlo.
