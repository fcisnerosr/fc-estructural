# f'c estructural — Portafolio de modelos 3D

Sitio estático (GitHub Pages) con modelos estructurales 3D interactivos, replicados con un
**motor propio** de análisis y visualización (OpenSeesPy + Plotly). Normativa mexicana
(CFE y NTC-2023).

**Sitio:** https://fcisnerosr.github.io/fc-estructural/

## Contenido

- `index.html` — landing con las tarjetas de cada modelo.
- `modelos/<slug>/` — por proyecto: `visor_modelo.html` (visor 3D), `visor_modos.html`
  (formas modales), `memoria_calculo.pdf` y las imágenes.
- `assets/` — estilos, logo y códigos QR.

> Modelos de **demostración**. No representan proyectos entregados a clientes; su fin es
> mostrar las capacidades de la herramienta. Los muros se modelan como carga sin rigidez
> lateral, por lo que los periodos pueden diferir de la estructura real con muros rígidos.
