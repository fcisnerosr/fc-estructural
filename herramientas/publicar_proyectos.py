#!/usr/bin/env python3
"""
Publica en el sitio los proyectos del despacho: visor 3D, planos en PDF, QR y portada.

Lee cada expediente de ~/github/despacho (o de $DESPACHO) y escribe en modelos/<slug>/:

  · modelo.js   la geometría del visor 3D. Los visores de los expedientes son de uso interno:
                cada pieza trae sus fuentes, dudas y pendientes. Aquí se publica solo su clave
                (PB-C01), su familia (Columnas) y su sección (20 × 40 cm), y nada más.
  · index.html  la página del visor; el dibujo lo hacen modelos/visor.js y modelos/visor.css.
  · planos.pdf  los planos entregados, en un solo PDF, con el propietario y la dirección exacta
                tapados. Se tapa POR ZONA: este repositorio es público, así que aquí no se escribe
                ningún nombre. Las zonas se midieron sobre cada formato de lámina.
  · img/portada.webp  la imagen de la tarjeta (con --portadas; necesita Chrome y Playwright).

y assets/qr/<slug>.png, que abre el visor en el celular.

    python3 herramientas/publicar_proyectos.py              # todos
    python3 herramientas/publicar_proyectos.py 009 014      # solo esos expedientes
    python3 herramientas/publicar_proyectos.py --portadas   # y además la portada de cada tarjeta
"""
import base64
import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import fitz
import numpy as np
import qrcode
from qrcode.image.pil import PilImage

SITIO = Path(__file__).resolve().parent.parent
DESPACHO = Path(os.environ.get("DESPACHO", "~/github/despacho")).expanduser()
URL = "https://fcisnerosr.github.io/fc-estructural/"
NAVY = "#14294a"

# ── Colores por familia: los mismos en todos los proyectos ──────────────────────────────────────
COLUMNAS, CASTILLOS, TRABES, CONTRATRABES = "#1f3a5f", "#3f8a8b", "#2f6fb0", "#6d4c41"
LOSAS, MAMPOSTERIA, MUROS_CONCRETO = "#9db4cc", "#c9a27e", "#7d8b99"
CIMENTACION, ACERO, PLACAS = "#8d6e63", "#a33a3a", "#455a64"
CANCEL, RELLENO, EQUIPO, PANELES = "#8fc5e8", "#d8c37c", "#dfe6ee", "#3b6ea5"

CAJETIN_011 = [(1184, 2425, 1345, 2434),       # propietario
               (1184, 2467, 1302, 2475),       # ubicación, líneas 1 y 2 (queda la ciudad)
               (1184, 2480, 1262, 2489),
               (1062, 2377, 1150, 2443),       # logo del cliente, a la derecha de su etiqueta y debajo;
               (1025, 2385, 1062, 2443)]       # quedan «PROYECTO ESTRUCTURAL», la firma y la cédula
CAJETIN_DET = [(2036, 1571, 2262, 1588),       # lo mismo en las láminas de detalle (900 × 600, texto en trazos)
               (2036, 1613, 2262, 1638),
               (1912, 1526, 1995, 1593), (1878, 1534, 1912, 1593)]

# ── Los proyectos ───────────────────────────────────────────────────────────────────────────────
# capas: (nombre público, color, opacidad, claves de origen). Lo que no aparece aquí no se publica.
# tapar: por patrón de archivo, los rectángulos (pt) que se tapan en cada hoja.
PROYECTOS = [
    dict(exp="009", slug="casa-cedros", titulo="Casa Cedros", lugar="Veracruz, Ver.",
         tipo="Diseño estructural · obra nueva",
         visor=dict(fuente="cedros"),
         capas=[("Muros de mampostería", MAMPOSTERIA, .85, ["m_"]),
                ("Muros de concreto", MUROS_CONCRETO, 1, ["mc_"]),
                ("Columnas", COLUMNAS, 1, ["col_"]),
                ("Trabes", TRABES, 1, ["trabe_"]),
                ("Contratrabes", CONTRATRABES, 1, ["ct_PB"]),
                ("Losa de cimentación", CIMENTACION, .9, ["ct_PB_losa"]),
                ("Losas", LOSAS, .45, ["Losa de PA", "Losa de azotea", "Techo del cuarto de azotea"]),
                ("Cancelería", CANCEL, .3, ["Planta baja · vidrios", "Azotea · vidrios"])],
         planos=[("05_entregables/*_PlanosEstructurales_REV0_*/E-0*.pdf",
                  [(2530, 1549, 2725, 1572),       # proyecto arquitectónico: el nombre
                   (2492, 1728, 2760, 2005),       # croquis de localización
                   (2514, 2051, 2733, 2066)])]),   # ubicación: lote y calle (queda el fraccionamiento)
    dict(exp="014", slug="auditorio-escolar", titulo="Auditorio escolar", lugar="Veracruz, Ver.",
         tipo="Diseño estructural · concreto y acero",
         visor=dict(fuente="piezas", html="04_calculo/visor/visor_3d.html"),
         capas=[("Columnas de concreto", COLUMNAS, 1, ["columnas"]),
                ("Castillos", CASTILLOS, 1, ["castillos"]),
                ("Trabes y dalas", TRABES, 1, ["trabes"]),
                ("Losa de la marquesina", LOSAS, .55, ["losas"]),
                ("Muros de tabique", MAMPOSTERIA, .85, ["muros"]),
                ("Trabes metálicas", ACERO, 1, ["vigas_acero"]),
                ("Largueros", "#b5651d", 1, ["largueros"]),
                ("Contraventeo de cubierta", "#e0a400", 1, ["tirones"]),
                ("Placas base", PLACAS, 1, ["placas"]),
                ("Contratrabes", CONTRATRABES, 1, ["contratrabes"]),
                ("Zapatas y dados", CIMENTACION, 1, ["zapatas", "dados"]),
                ("Cancel", CANCEL, .3, ["cerramientos"])],
         planos=[("05_entregables/*_ultima_version_E-?.pdf",
                  [(1184, 2425, 1325, 2434),       # propietario
                   (1184, 2466, 1375, 2476),       # ubicación, líneas 1 y 2 (queda la ciudad)
                   (1184, 2480, 1300, 2490)])]),
    dict(exp="016", slug="casa-el-dorado", titulo="Casa El Dorado", lugar="Boca del Río, Ver.",
         tipo="Ampliación a segundo nivel",
         # Lo que queda: la casa existente que se conserva, la estructura de la ampliación y los muros
         # nuevos. Fuera, lo que se demuele y lo del proyecto anterior.
         visor=dict(fuente="piezas", html="04_calculo/visor/visor_3d.html",
                    estados={"hoy", "apolinar", "nuevo"}),
         capas=[("Columnas de concreto", COLUMNAS, 1, ["columnas"]),
                ("Columnas de acero", "#6a1b9a", 1, ["columnas_acero"]),
                ("Castillos", CASTILLOS, 1, ["castillos"]),
                ("Trabes y dalas", TRABES, 1, ["trabes"]),
                ("Trabes de acero", ACERO, 1, ["vigas_acero"]),
                ("Losas", LOSAS, .45, ["losas"]),
                ("Muros de tabique", MAMPOSTERIA, .8, ["muros"]),
                ("Muros de concreto", MUROS_CONCRETO, 1, ["muros_concreto"]),
                ("Escalera", "#bcaaa4", 1, ["escaleras"]),
                ("Cimentación", CIMENTACION, 1, ["zapatas", "contratrabes", "dados", "placas"])],
         planos=[("05_entregables/* - E-2.pdf", [(2056, 2424, 2280, 2443), (2056, 2465, 2280, 2481)]),
                 ("05_entregables/* - E-5.pdf", [(2056, 1574, 2280, 1593), (2056, 1615, 2280, 1631)]),
                 ("05_entregables/* - E-6.pdf", [(2056, 1574, 2280, 1593), (2056, 1615, 2280, 1631)]),
                 ("05_entregables/* - E-8.pdf", [(2042, 1091, 2262, 1109), (2042, 1131, 2262, 1148)])]),
    dict(exp="011", slug="local-comercial", titulo="Local comercial", lugar="Poza Rica, Ver.",
         tipo="Revisión y rehabilitación estructural",
         visor=dict(fuente="cajas", html="04_calculo/visor/visor_3d.html", clave="grupos_rehab"),
         capas=[("Columnas", COLUMNAS, 1, ["Columnas PB", "Columnas PA"]),
                ("Encamisado de columnas", "#5c7fa3", 1, ["Camisas (de diseño)", "Dados de remate (de diseño)",
                                                          "Apoyos nuevos (de diseño)"]),
                ("Trabes", TRABES, 1, ["Trabes de azotea", "Borde del entrepiso (por definir)",
                                       "Trabe de fachada nueva (de diseño)"]),
                ("Castillos nuevos", CASTILLOS, 1, ["Castillos nuevos (de diseño)"]),
                ("Losa de azotea", LOSAS, .45, ["Losa de azotea"]),
                ("Muros", MAMPOSTERIA, .8, ["Muros PB (supuesto)", "Muros PA (supuesto)"]),
                ("Muros de concreto adosados", MUROS_CONCRETO, 1, ["Encamisado de muros (de diseño)",
                                                                   "Remates de muros (de diseño)"]),
                ("Vigas de acero", ACERO, 1, ["Vigas de acero nuevas (de diseño)"]),
                ("Marquesina", "#e0a400", 1, ["Soporte de la marquesina (de diseño)",
                                              "Placas ahogadas de la marquesina (de diseño)",
                                              "Contraventeo de la marquesina (de diseño)"]),
                ("Zapatas", CIMENTACION, 1, ["Zapatas nuevas (de dibujo)"])],
         planos=[("05_entregables/proyecto_rehabilitacion/planos/011_planos_de_obra_E-1.pdf",
                  CAJETIN_011 + [(413, 1072, 563, 1081), (71, 1083, 105, 1092)]),   # nota 1: a quién se copia
                 ("05_entregables/proyecto_rehabilitacion/planos/011_planos_de_obra_E-2.pdf",
                  CAJETIN_011 + [(1031, 2296, 1108, 2303)]),                        # quién hace la visita
                 ("05_entregables/proyecto_rehabilitacion/planos/011_planos_de_obra_E-[3-8].pdf", CAJETIN_011),
                 ("05_entregables/proyecto_rehabilitacion/planos/011_laminas_detalle_DET-0[1-4].pdf", CAJETIN_DET),
                 ("05_entregables/proyecto_rehabilitacion/planos/011_laminas_detalle_DET-05.pdf",
                  CAJETIN_DET + [(1835, 745.5, 2027, 757)]),                        # el mismo párrafo de la E-1
                 ("05_entregables/proyecto_rehabilitacion/planos/011_laminas_detalle_DET-0[6-9].pdf", CAJETIN_DET),
                 ("05_entregables/proyecto_rehabilitacion/planos/011_laminas_detalle_DET-1?.pdf", CAJETIN_DET)]),
    dict(exp="010", slug="muro-de-contencion", titulo="Muro de contención", lugar="Coatepec, Ver.",
         tipo="Diseño estructural · anteproyecto",
         visor=dict(fuente="piezas", html="04_calculo/visor/visor_3d.html"),
         capas=[("Pantalla de concreto", MUROS_CONCRETO, 1, ["pantalla"]),
                ("Zapata y dentellón", CIMENTACION, 1, ["zapata"]),
                ("Barda", MAMPOSTERIA, .9, ["barda"]),
                ("Castillos y dala", CASTILLOS, 1, ["castillos"]),
                ("Filtro de grava", CANCEL, .45, ["filtro"]),
                ("Relleno", RELLENO, .22, ["relleno", "punta"])],
         planos=[("05_entregables/planos/010_plano_anteproyecto_muro_E-?.pdf",
                  [(1184, 2425, 1300, 2434),       # propietario
                   (1184, 2466, 1410, 2476),       # ubicación, líneas 1 y 2 (queda la ciudad)
                   (1184, 2480, 1300, 2490)])]),
    dict(exp="008", slug="estacion-de-carburacion", titulo="Estación de carburación",
         lugar="San Andrés Tuxtla, Ver.", tipo="Dictamen estructural",
         visor=dict(fuente="piezas", html="04_calculo/visor/visor_3d.html"),
         capas=[("Losa de apoyo", LOSAS, 1, ["losa"]),
                ("Silletas del tanque", COLUMNAS, 1, ["silletas"]),
                ("Muro de protección", MUROS_CONCRETO, 1, ["muro"]),
                ("Caseta", MAMPOSTERIA, .9, ["caseta"]),
                ("Azotea de la caseta", LOSAS, .55, ["azotea"]),
                ("Castillo", CASTILLOS, 1, ["castillo"]),
                ("Cunas y amarre de acero", ACERO, 1, ["acero"]),
                ("Refuerzo propuesto", "#2e7d32", .6, ["propuesta"]),
                ("Tanque (5 000 L)", EQUIPO, .35, ["tanque"])],
         planos=None),
    dict(exp="001", slug="losa-paneles-solares", titulo="Losa para paneles solares", lugar="Veracruz, Ver.",
         tipo="Dictamen estructural",
         # Desde el lado de la losa: del otro, la barda de celosía la tapa entera.
         visor=dict(fuente="plotly", html="02_levantamiento/outputs/visor_losa.html",
                    vista={"x": -1.25, "y": 1.6, "z": 1.05}),
         capas=[("Columnas", COLUMNAS, 1, ["Columnas"]),
                ("Muros de carga", MAMPOSTERIA, .9, ["Muros de carga"]),
                ("Trabes", TRABES, 1, ["Trabes inferiores"]),
                ("Contratrabes", CONTRATRABES, 1, ["Contratrabes"]),
                ("Losa", LOSAS, .55, ["Losa de ampliación", "Losa original", "Volados"]),
                ("Pretil", MUROS_CONCRETO, 1, ["Pretil"]),
                ("Barda de celosía", "#b0a89a", .35, ["Barda de celosía · 1.80 m sobre la losa"]),
                ("Paneles solares", PANELES, 1, ["Módulos FV"]),
                ("Estructura de soporte", ACERO, 1, ["Herrería de soporte"])],
         planos=None),
]


# ── Utilidades de malla ─────────────────────────────────────────────────────────────────────────
def r3(v):
    return round(float(v), 3)


def aristas_vivas(V, F, grados=20.0):
    """Aristas que se dibujan: las de borde y las que separan caras con más de `grados` entre sí.
    Antes se sueldan los vértices repetidos, para que la diagonal de un rectángulo no cuente."""
    V = np.asarray(V, float)
    llave = {}
    mapa = np.empty(len(V), int)
    for n, p in enumerate(np.round(V, 4)):
        mapa[n] = llave.setdefault(tuple(p), len(llave))
    W = np.zeros((len(llave), 3))
    W[mapa] = V
    F = mapa[np.asarray(F, int)]
    nor = np.cross(W[F[:, 1]] - W[F[:, 0]], W[F[:, 2]] - W[F[:, 0]])
    lon = np.linalg.norm(nor, axis=1)
    nor[lon > 0] /= lon[lon > 0, None]
    caras = {}
    for c, (a, b, d) in enumerate(F):
        for e in ((a, b), (b, d), (d, a)):
            if e[0] != e[1]:
                caras.setdefault((min(e), max(e)), []).append(c)
    lim = np.cos(np.radians(grados))
    salida = []
    for (a, b), cs in caras.items():
        if len(cs) != 2 or np.dot(nor[cs[0]], nor[cs[1]]) < lim:
            salida.append((W[a], W[b]))
    return salida


CAJA_F = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
          (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
CAJA_E = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


def caja(c):
    x0, y0, z0, x1, y1, z1 = c
    return [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]


class Capa:
    """Una capa del visor: una sola malla con todas sus piezas, y sus aristas."""

    def __init__(self, nombre, color, opacidad):
        self.n, self.c, self.o = nombre, color, opacidad
        self.V, self.F, self.T, self.E = [], [], [], []

    def pieza(self, V, F, etiqueta, E=None):
        base = len(self.V)
        self.V += [tuple(map(float, p)) for p in V]
        self.F += [(a + base, b + base, c + base) for a, b, c in F]
        self.T += [etiqueta] * len(V)
        if E is None:
            self.E += aristas_vivas(V, F)
        else:
            self.E += [(V[a], V[b]) for a, b in E]

    def json(self, etiquetas):
        if not self.V:
            return None
        V = self.V
        g = {"n": self.n, "c": self.c, "o": self.o,
             "x": [r3(p[0]) for p in V], "y": [r3(p[1]) for p in V], "z": [r3(p[2]) for p in V],
             "i": [f[0] for f in self.F], "j": [f[1] for f in self.F], "k": [f[2] for f in self.F],
             "t": [etiquetas.setdefault(t, len(etiquetas)) for t in self.T],
             "ex": [], "ey": [], "ez": []}
        for a, b in self.E:
            for k, e in zip("xyz", range(3)):
                g["e" + k] += [r3(a[e]), r3(b[e]), None]
        return g


# ── Etiqueta pública de una pieza: clave, familia y sección. Nada más. ──────────────────────────
CLAVE = re.compile(r"^[A-Z]{1,3}(?:-[A-Z]{1,3})?-?\d{1,3}[A-Z]?$")
SECCION = re.compile(r"(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*(cm|m)\b")


def etiqueta(clave, familia, texto=""):
    clave = (clave or "").strip()
    partes = [f"<b>{html.escape(clave)}</b>"] if CLAVE.match(clave) else []
    partes.append(html.escape(familia))
    s = SECCION.search(re.sub(r"<[^>]+>", " ", texto or ""))
    if s:
        partes.append(f"{s.group(1)} × {s.group(2)} {s.group(3)}")
    return " · ".join(partes)


def datos_D(ruta):
    s = ruta.read_text(encoding="utf-8")
    i = s.index("const D = ") + len("const D = ")
    return json.JSONDecoder().raw_decode(s[i:])[0]


def figura_plotly(ruta):
    s = ruta.read_text(encoding="utf-8")
    i = s.index("[", s.index("Plotly.newPlot("))
    return json.JSONDecoder().raw_decode(s[i:])[0]


def arreglo(v):
    """Plotly guarda a veces los arreglos en binario: {"dtype": "f8", "bdata": "..."}."""
    if isinstance(v, dict) and "bdata" in v:
        return np.frombuffer(base64.b64decode(v["bdata"]), dtype=np.dtype(v["dtype"])).tolist()
    return list(v)


def capas_de(p, carpeta):
    """Las capas públicas del visor de un expediente."""
    vis, capas = p["visor"], [Capa(n, c, o) for n, c, o, _ in p["capas"]]

    def destino(clave, exacta=True):
        for capa, (_, _, _, origen) in zip(capas, p["capas"]):
            if any(clave == o if exacta else clave.startswith(o) for o in origen):
                return capa
        return None

    if vis["fuente"] == "piezas":
        D = datos_D(carpeta / vis["html"])
        estados = vis.get("estados")
        for pz in D["piezas"]:
            if estados and D.get("estado", {}).get(pz["id"]) not in estados:
                continue
            capa = destino(pz["grupo"])
            if capa:
                capa.pieza(pz["v"], pz["f"], etiqueta(pz.get("id"), capa.n, pz.get("t", "")), pz.get("e"))
    elif vis["fuente"] == "cajas":
        D = datos_D(carpeta / vis["html"])
        for grupo, piezas in D[vis["clave"]].items():
            capa = destino(grupo)
            for pz in piezas if capa else ():
                capa.pieza(caja(pz["c"]), CAJA_F, etiqueta(pz.get("id"), capa.n, pz.get("t", "")), CAJA_E)
    elif vis["fuente"] == "plotly":
        for t in figura_plotly(carpeta / vis["html"]):
            if t.get("type") != "mesh3d":
                continue
            capa = destino(t.get("name", ""), exacta=False)
            if capa:
                V = list(zip(arreglo(t["x"]), arreglo(t["y"]), arreglo(t["z"])))
                F = list(zip(arreglo(t["i"]), arreglo(t["j"]), arreglo(t["k"])))
                capa.pieza(V, F, html.escape(capa.n))
    elif vis["fuente"] == "cedros":
        # El 009 no guarda su visor: se arma la figura con el generador del expediente, sin escribir nada.
        gen = carpeta / "04_calculo/visor/generar_visor_3d.py"
        spec = importlib.util.spec_from_file_location("visor_cedros", gen)
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(gen.parent))
        spec.loader.exec_module(mod)
        fig, _ = mod.construir()
        for t in fig.data:
            if t.type != "mesh3d":
                continue
            grupo = t.legendgroup or t.name or ""
            capa = destino(grupo) or destino(grupo, exacta=False)
            if not capa:
                continue
            V = list(zip(t.x, t.y, t.z))
            F = list(zip(t.i, t.j, t.k))
            textos = t.hovertext if t.hovertext is not None and not isinstance(t.hovertext, str) else None
            if textos is not None and len(textos) == len(V):
                # Una traza junta varias piezas: se separan por su etiqueta para dar a cada una la suya.
                por = {}
                for f in F:
                    por.setdefault(textos[f[0]], []).append(f)
                for txt, fs in por.items():
                    usados = sorted({v for f in fs for v in f})
                    nuevo = {v: n for n, v in enumerate(usados)}
                    m = re.match(r"\s*<b>([^<]+)</b>", txt or "")
                    capa.pieza([V[v] for v in usados], [tuple(nuevo[v] for v in f) for f in fs],
                               etiqueta(m.group(1) if m else "", capa.n, txt))
            else:
                capa.pieza(V, F, html.escape(capa.n))
    return capas


# ── Página del visor ────────────────────────────────────────────────────────────────────────────
PAGINA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} — f'c estructural</title>
<meta name="description" content="{titulo} ({lugar}): modelo estructural en 3D{y_planos}. f'c estructural.">
<link rel="stylesheet" href="../visor.css?v={v}">
<script>
(function(){{try{{
  var s=localStorage.getItem('theme');
  var d=s||((window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light');
  document.documentElement.setAttribute('data-theme',d);
}}catch(e){{document.documentElement.setAttribute('data-theme','light');}}}})();
</script>
</head>
<body>
<header class="vh">
  <a class="marca" href="../../#proyectos" title="Volver a los proyectos">
    <img src="../../assets/logo_fcr_nav.png" alt="f'c estructural">
    <span><b>f'c estructural</b><small>Análisis y diseño estructural</small></span>
  </a>
  <span class="sep"></span>
  <div class="proy">
    <small>{tipo}</small>
    <h1>{titulo}</h1>
    <div class="lugar">📍 {lugar}</div>
  </div>
  <div class="acc">
{boton_planos}    <button class="boton ico" id="tema" type="button" aria-label="Cambiar tema" title="Tema claro / oscuro">🌙</button>
    <a class="boton" href="../../#proyectos" aria-label="Volver a los proyectos">←<span class="txt"> Proyectos</span></a>
  </div>
</header>
<main class="vm">
  <section class="lienzo">
    <div id="plot" role="img" aria-label="Modelo 3D de {titulo}"></div>
    <p class="ayuda">Arrastra para girar · rueda para acercar · pasa el cursor sobre un elemento</p>
    <nav class="vistas" aria-label="Vistas">
      <button type="button" data-vista="iso" class="on">3D</button>
      <button type="button" data-vista="planta">Planta</button>
      <button type="button" data-vista="frente">Frente</button>
      <button type="button" data-vista="lado">Lado</button>
      <button type="button" class="capas-btn">Capas</button>
    </nav>
  </section>
  <aside class="panel" aria-label="Capas del modelo">
    <button class="cerrar" type="button" aria-label="Cerrar">×</button>
    <h2>Capas del modelo <span id="cuenta"></span></h2>
    <div id="capas"></div>
    <div class="todo"><button type="button" id="todas">Mostrar todas</button><button type="button" id="ninguna">Ocultar todas</button></div>
    <p class="nota">Modelo de consulta: se explora en línea y no se descarga.</p>
  </aside>
</main>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script src="modelo.js?v={v}"></script>
<script src="../visor.js?v={v}"></script>
</body>
</html>
"""
BOTON_PLANOS = ('    <a class="boton prim" href="planos.pdf?v={v}" target="_blank" rel="noopener">'
                '📄 Planos<span class="txt"> (PDF)</span></a>\n')


def escribir_visor(p, capas, salida, v):
    etiquetas = {}
    grupos = [g for g in (c.json(etiquetas) for c in capas) if g]
    modelo = {"etiquetas": sorted(etiquetas, key=etiquetas.get), "grupos": grupos}
    if p["visor"].get("vista"):
        modelo["vista"] = p["visor"]["vista"]
    (salida / "modelo.js").write_text(
        "/* Generado por herramientas/publicar_proyectos.py — no se edita a mano. */\n"
        "window.MODELO=" + json.dumps(modelo, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    hay_planos = (salida / "planos.pdf").exists()
    (salida / "index.html").write_text(PAGINA.format(
        titulo=html.escape(p["titulo"]), lugar=html.escape(p["lugar"]), tipo=html.escape(p["tipo"]), v=v,
        y_planos=" y planos estructurales en PDF" if hay_planos else "",
        boton_planos=BOTON_PLANOS.format(v=v) if hay_planos else ""), encoding="utf-8")
    piezas = sum(len(set(c.T)) for c in capas)
    print(f"  visor: {len(grupos)} capas, {len(etiquetas)} etiquetas, "
          f"{(salida / 'modelo.js').stat().st_size / 1e3:.0f} kB ({piezas} piezas distintas)")


# ── Planos ──────────────────────────────────────────────────────────────────────────────────────
# Un decimal de punto es 0.035 mm en el papel; a 400 dpi no se distingue del original.
DECIMALES = int(os.environ.get("DECIMALES", "1"))
# Una cadena literal (se copia tal cual) o los operandos de un trazo: m, l, c, v, y, re. Solo esos:
# un número de una matriz (cm) o de un tamaño de letra cambia de escala todo lo que viene después.
TOKEN = re.compile(rb"(\((?:\\.|[^\\)])*\))|((?:-?(?:\d+\.?\d*|\.\d+)\s+){2,6})(m|l|c|v|y|re)\b")
DECIMAL = re.compile(rb"(-?\d*\.\d{%d})\d+" % DECIMALES)
IMAGEN_EN_LINEA = re.compile(rb"(?:^|\s)BI\s")


def aligerar(doc):
    """Recorta los decimales de las coordenadas de los trazos: los planos traen 6 (0.0004 mm) y con
    eso pesan el doble. Los números dentro de una cadena de texto no se tocan, y un flujo con una
    imagen en línea (BI … EI, binaria) se deja entero."""
    def corto(m):
        return m.group(1) or DECIMAL.sub(rb"\1", m.group(2)) + m.group(3)
    flujos = {x for pag in doc for x in pag.get_contents()}
    flujos |= {x for x in range(1, doc.xref_length())
               if doc.xref_is_stream(x) and doc.xref_get_key(x, "Subtype")[1] == "/Form"}
    for x in sorted(flujos):
        s = doc.xref_stream(x)
        if not s or IMAGEN_EN_LINEA.search(s):
            continue
        doc.update_stream(x, TOKEN.sub(corto, s))


def escribir_planos(p, carpeta, salida):
    if not p.get("planos"):
        return
    junto = fitz.open()
    for patron, tapar in p["planos"]:
        hojas = sorted(carpeta.glob(patron))
        if not hojas:
            raise SystemExit(f"  ✗ {p['exp']}: ninguna hoja con {patron}")
        for h in hojas:
            d = fitz.open(h)
            for pag in d:
                for r in tapar:
                    pag.add_redact_annot(fitz.Rect(r), fill=(1, 1, 1))
                pag.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS,
                                     graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                                     text=fitz.PDF_REDACT_TEXT_REMOVE)
            junto.insert_pdf(d)
    junto.set_metadata({"title": f"{p['titulo']} — planos estructurales", "author": "f'c estructural",
                        "subject": p["tipo"], "creator": "f'c estructural", "producer": "", "keywords": ""})
    junto.del_xml_metadata()
    aligerar(junto)
    junto.save(salida / "planos.pdf", garbage=4, deflate=True, clean=True)
    print(f"  planos: {junto.page_count} hojas, {(salida / 'planos.pdf').stat().st_size / 1e6:.1f} MB")


# ── QR y portada ────────────────────────────────────────────────────────────────────────────────
def escribir_qr(p):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    q.add_data(f"{URL}modelos/{p['slug']}/")
    q.make(fit=True)
    q.make_image(image_factory=PilImage, fill_color=NAVY, back_color="white").save(
        SITIO / "assets" / "qr" / f"{p['slug']}.png")


def escribir_portadas(lista):
    from PIL import Image
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"),
                                 args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pag = nav.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=1)
        for p in lista:
            carpeta = SITIO / "modelos" / p["slug"]
            (carpeta / "img").mkdir(exist_ok=True)
            pag.goto((carpeta / "index.html").as_uri() + "?captura")
            pag.wait_for_function("document.querySelector('#plot .gl-container canvas') !== null", timeout=60000)
            pag.wait_for_timeout(2500)
            png = carpeta / "img" / "portada.png"
            pag.locator("#plot").screenshot(path=str(png))
            # Se recorta al modelo, con un margen, y se centra en el 4:3 de la tarjeta.
            im = Image.open(png).convert("RGB")
            png.unlink()
            gris = np.asarray(im.convert("L"))
            filas, cols = np.where(gris < 240)
            x0, x1, y0, y1 = cols.min(), cols.max(), filas.min(), filas.max()
            lado = max((x1 - x0) * 1.12, (y1 - y0) * 1.12 * 4 / 3)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            caja = (cx - lado / 2, cy - lado * 3 / 8, cx + lado / 2, cy + lado * 3 / 8)
            lienzo = Image.new("RGB", (round(lado), round(lado * 3 / 4)), "white")
            lienzo.paste(im, (round(-caja[0]), round(-caja[1])))
            lienzo.resize((1200, 900), Image.LANCZOS).save(carpeta / "img" / "portada.webp", "WEBP",
                                                           quality=82, method=6)
            print(f"  portada: modelos/{p['slug']}/img/portada.webp")
        nav.close()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lista = [p for p in PROYECTOS if not args or p["exp"] in args]
    v = os.environ.get("VERSION", "1")
    for p in lista:
        carpeta = next(DESPACHO.glob(p["exp"] + "_*"))
        salida = SITIO / "modelos" / p["slug"]
        salida.mkdir(parents=True, exist_ok=True)
        print(f"{p['exp']} → modelos/{p['slug']}/")
        escribir_planos(p, carpeta, salida)
        escribir_visor(p, capas_de(p, carpeta), salida, v)
        escribir_qr(p)
    if "--portadas" in sys.argv:
        escribir_portadas(lista)


if __name__ == "__main__":
    main()
