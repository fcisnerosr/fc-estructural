/* ===== f'c estructural — visor 3D de los proyectos =====
   Lee window.MODELO (de modelos/<proyecto>/modelo.js) y lo dibuja con Plotly.
   El modelo trae sus capas ya armadas: cada una es una malla (x, y, z, i, j, k)
   con sus aristas (ex, ey, ez, cortadas con null) y, por vértice, el índice de
   su etiqueta en MODELO.etiquetas. Lo genera herramientas/publicar_proyectos.py. */
(function(){
  var M=window.MODELO, div=document.getElementById('plot');
  if(!M||!div||!window.Plotly)return;
  var raiz=document.documentElement;
  if(/[?&]captura\b/.test(location.search)) raiz.classList.add('captura');

  function oscuro(){return raiz.getAttribute('data-theme')==='dark';}

  /* ---- trazas: por capa, la malla y sus aristas (las aristas no responden al cursor) ---- */
  var trazas=[], deCapa=[];
  M.grupos.forEach(function(g,n){
    var idx=[];
    if(g.i&&g.i.length){
      idx.push(trazas.length);
      trazas.push({
        type:'mesh3d',name:g.n,x:g.x,y:g.y,z:g.z,i:g.i,j:g.j,k:g.k,
        color:g.c,opacity:g.o==null?1:g.o,flatshading:true,
        lighting:{ambient:.62,diffuse:.7,specular:.08,roughness:.9,fresnel:.1},
        lightposition:{x:1e4,y:-6e3,z:1.4e4},
        text:g.t.map(function(e){return M.etiquetas[e];}),
        hovertemplate:'%{text}<extra></extra>',showscale:false
      });
    }
    if(g.ex&&g.ex.length){
      idx.push(trazas.length);
      trazas.push({
        type:'scatter3d',mode:'lines',name:g.n,x:g.ex,y:g.ey,z:g.ez,
        line:{color:'rgba(20,30,45,.55)',width:g.o!=null&&g.o<.5?1:2},
        hoverinfo:'skip',showlegend:false
      });
    }
    deCapa[n]=idx;
  });

  /* ---- escena ---- */
  var VISTAS={
    iso:{eye:{x:1.35,y:-1.55,z:1.05},up:{x:0,y:0,z:1}},
    planta:{eye:{x:0,y:-0.0001,z:2.6},up:{x:0,y:1,z:0}},
    frente:{eye:{x:0,y:-2.6,z:.12},up:{x:0,y:0,z:1}},
    lado:{eye:{x:2.6,y:0,z:.12},up:{x:0,y:0,z:1}}
  };
  if(M.vista) VISTAS.iso.eye=M.vista;
  function eje(t){
    var o=oscuro();
    if(raiz.classList.contains('captura')) return {visible:false};   /* la portada es solo el modelo */
    return {title:{text:t,font:{size:11,color:o?'#9aa6b4':'#6b7480'}},
      showbackground:false,gridcolor:o?'#26323f':'#e3e7ee',zerolinecolor:o?'#33414f':'#cfd6df',
      tickfont:{size:10,color:o?'#9aa6b4':'#6b7480'},ticksuffix:' m',showspikes:false};
  }
  function camara(v){
    var c=VISTAS[v];
    return {eye:c.eye,up:c.up,center:{x:0,y:0,z:0},projection:{type:'orthographic'}};
  }
  /* Proporción de la escena: la de los datos (como aspectmode 'data'), pero más chica en una
     pantalla angosta, para que el modelo quepa a lo ancho del celular. */
  function proporcion(){
    var lo=[Infinity,Infinity,Infinity], hi=[-Infinity,-Infinity,-Infinity];
    M.grupos.forEach(function(g){[g.x,g.y,g.z].forEach(function(a,e){
      for(var n=0;n<a.length;n++){if(a[n]<lo[e])lo[e]=a[n];if(a[n]>hi[e])hi[e]=a[n];}
    });});
    /* Plotly, en 'data', normaliza por la media geométrica de los tres lados */
    var d=[0,1,2].map(function(e){return Math.max(hi[e]-lo[e],1e-3);}), m=Math.cbrt(d[0]*d[1]*d[2]);
    var s=Math.max(.38,Math.min(1,.8*div.clientWidth/Math.max(div.clientHeight,1)));
    return {x:d[0]/m*s,y:d[1]/m*s,z:d[2]/m*s};
  }
  function diseno(){
    var o=oscuro(), cap=raiz.classList.contains('captura');
    return {
      paper_bgcolor:cap?'#ffffff':'rgba(0,0,0,0)',margin:{l:0,r:0,t:0,b:0},showlegend:false,
      hoverlabel:{bgcolor:o?'#15202b':'#ffffff',bordercolor:o?'#26323f':'#cfd6df',
        font:{family:'Inter, -apple-system, Segoe UI, sans-serif',size:13,color:o?'#e6ebf2':'#1b1f24'}},
      scene:{aspectmode:'manual',aspectratio:proporcion(),camera:camara('iso'),dragmode:'turntable',
        xaxis:eje('X'),yaxis:eje('Y'),zaxis:eje('Z')}
    };
  }
  Plotly.newPlot(div,trazas,diseno(),{displaylogo:false,displayModeBar:false,responsive:true,scrollZoom:true});

  /* ---- vistas de cámara ---- */
  var botones=document.querySelectorAll('.vistas [data-vista]');
  function marcar(v){for(var b=0;b<botones.length;b++) botones[b].classList.toggle('on',botones[b].getAttribute('data-vista')===v);}
  for(var b=0;b<botones.length;b++) botones[b].addEventListener('click',function(){
    var v=this.getAttribute('data-vista');
    Plotly.relayout(div,{'scene.camera':camara(v)});
    marcar(v);
  });
  div.on('plotly_relayout',function(e){ if(e&&e['scene.camera']&&!e['scene.camera'].projection) marcar(null); });

  /* ---- capas ---- */
  var lista=document.getElementById('capas'), cuenta=document.getElementById('cuenta');
  var vis=M.grupos.map(function(){return true;});
  function contar(){
    var n=vis.filter(Boolean).length;
    if(cuenta) cuenta.textContent=n+'/'+vis.length+' visibles';
  }
  function poner(n,v){
    vis[n]=v;
    var fila=lista.children[n];
    fila.classList.toggle('off',!v);
    fila.querySelector('input').checked=v;
  }
  function aplicar(cuales){
    var idx=[], val=[];
    cuales.forEach(function(n){deCapa[n].forEach(function(t){idx.push(t);val.push(vis[n]);});});
    if(idx.length) Plotly.restyle(div,{visible:val},idx);
    contar();
  }
  if(lista){
    M.grupos.forEach(function(g,n){
      var l=document.createElement('label');
      l.className='capa';
      l.innerHTML='<input type="checkbox" checked><i></i><span></span>';
      l.querySelector('i').style.background=g.c;
      l.querySelector('span').textContent=g.n;
      l.querySelector('input').addEventListener('change',function(){poner(n,this.checked);aplicar([n]);});
      lista.appendChild(l);
    });
    var todas=M.grupos.map(function(_,n){return n;});
    document.getElementById('todas').addEventListener('click',function(){todas.forEach(function(n){poner(n,true);});aplicar(todas);});
    document.getElementById('ninguna').addEventListener('click',function(){todas.forEach(function(n){poner(n,false);});aplicar(todas);});
    contar();
  }

  /* ---- panel de capas en el celular: se abre desde la barra de vistas ---- */
  var panel=document.querySelector('.panel');
  var abrir=document.querySelector('.capas-btn'), cerrar=document.querySelector('.panel .cerrar');
  if(abrir) abrir.addEventListener('click',function(){panel.classList.toggle('abierto');});
  if(cerrar) cerrar.addEventListener('click',function(){panel.classList.remove('abierto');});

  /* ---- tema claro / oscuro, el mismo que guarda el sitio ---- */
  var tema=document.getElementById('tema');
  function icono(){if(tema) tema.textContent=oscuro()?'☀️':'🌙';}
  icono();
  if(tema) tema.addEventListener('click',function(){
    var t=oscuro()?'light':'dark';
    raiz.setAttribute('data-theme',t);
    try{localStorage.setItem('theme',t);}catch(e){}
    icono();
    var d=diseno(); delete d.scene.camera;   /* el cambio de tema no mueve la cámara */
    Plotly.relayout(div,{paper_bgcolor:d.paper_bgcolor,hoverlabel:d.hoverlabel,
      'scene.xaxis':d.scene.xaxis,'scene.yaxis':d.scene.yaxis,'scene.zaxis':d.scene.zaxis});
  });
})();
