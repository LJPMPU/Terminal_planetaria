#!/usr/bin/env python3
"""
Terminal planetaria (solo lectura).
Descarga todos los precios en UNA llamada y escribe un HTML autocontenido
(datos embebidos, sin dependencias externas, funciona offline y desde iCloud/Archivos).

Uso:
    python3 terminal_planetaria.py                     -> terminal_planetaria.html (misma carpeta que el script)
    python3 terminal_planetaria.py /ruta/terminal.html -> ruta personalizada
Requisito: pip install yfinance
"""
import json
import os
import sys
import warnings
from datetime import datetime, timezone

import yfinance as yf

warnings.filterwarnings("ignore")

SECCIONES = [
    ("Digital", [
        ("Bitcoin", "BTC-USD"),
        ("Ethereum", "ETH-USD"),
        ("Tether (USDT)", "USDT-USD"),
        ("Oro tokenizado (PAXG)", "PAXG-USD"),
        ("Oro tokenizado (XAUT)", "XAUT-USD"),
    ]),
    ("Materias primas", [
        ("Oro (spot)", "XAU=X"),
        ("Oro (futuro)", "GC=F"),
        ("Petróleo WTI", "CL=F"),
        ("Gas natural", "NG=F"),
    ]),
    ("Renta variable", [
        ("S&P 500", "^GSPC"),
        ("Euro Stoxx 50", "^STOXX50E"),
        ("IBEX 35", "^IBEX"),
        ("Nikkei 225", "^N225"),
        ("Hang Seng", "^HSI"),
        ("Emergentes (EEM)", "EEM"),
    ]),
    ("Macro", [
        ("VIX", "^VIX"),
        ("Dólar (DXY)", "DX-Y.NYB"),
        ("Bono 10Y EE.UU. (%)", "^TNX"),
        ("EUR/USD", "EURUSD=X"),
    ]),
]


def descargar(tickers):
    """Una sola llamada para todos los tickers; último cierre vs. cierre previo."""
    df = yf.download(
        tickers, period="1mo", interval="1d", group_by="ticker",
        auto_adjust=False, progress=False, threads=True,
    )
    salida = {}
    for t in tickers:
        try:
            serie = df[t]["Close"].dropna()
            if len(serie) < 2:
                raise ValueError("serie corta")
            ultimo, previo = float(serie.iloc[-1]), float(serie.iloc[-2])
            salida[t] = {
                "p": ultimo,
                "d": ultimo - previo,
                "pct": (ultimo / previo - 1) * 100,
                "spark": [round(float(x), 4) for x in serie.tail(30)],
                "fecha": serie.index[-1].strftime("%Y-%m-%d"),
            }
        except Exception:
            salida[t] = None
    return salida


PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Terminal">
<title>Terminal planetaria</title>
<style>
  :root { --bg:#000; --panel:#0a0a0a; --line:#2a2a2a; --amber:#ffa028; --txt:#e8e8e8;
          --dim:#7d7d7d; --up:#00d26a; --down:#ff4d4d; }
  * { box-sizing: border-box; }
  html, body { margin:0; background:var(--bg); color:var(--txt); }
  body { font:14px/1.35 ui-monospace,"SF Mono",Menlo,Consolas,monospace;
         padding: max(14px, env(safe-area-inset-top)) max(14px, env(safe-area-inset-right))
                  max(20px, env(safe-area-inset-bottom)) max(14px, env(safe-area-inset-left));
         max-width: 1100px; margin: 0 auto; }
  header { display:flex; justify-content:space-between; align-items:flex-end; gap:12px;
           border-bottom:2px solid var(--amber); padding-bottom:10px; margin-bottom:14px; }
  h1 { margin:0; font-size:20px; letter-spacing:.04em; color:var(--amber); }
  .sub { color:var(--dim); font-size:12px; margin-top:2px; }
  .reloj { text-align:right; font-size:13px; font-variant-numeric: tabular-nums; }
  .estado { font-size:12px; color:var(--dim); }
  .estado.viejo { color:var(--amber); } .estado.muy-viejo { color:var(--down); }
  main { display:grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap:14px; }
  section { background:var(--panel); border:1px solid var(--line); padding:10px 12px 6px; }
  h2 { margin:0 0 6px; font-size:13px; font-weight:700; color:var(--amber);
       border-bottom:1px solid var(--line); padding-bottom:5px; }
  .fila { display:grid; grid-template-columns: 1fr auto 74px 64px; gap:10px; align-items:center;
          padding:6px 0; border-bottom:1px solid #151515; font-variant-numeric: tabular-nums; }
  .fila:last-child { border-bottom:0; }
  .nom { color:#ffc36b; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .px { text-align:right; color:#fff; }
  .pct { text-align:right; }
  .abs { color:var(--dim); font-size:11px; display:block; }
  .up { color:var(--up); } .down { color:var(--down); } .flat { color:var(--dim); }
  svg.sp { width:64px; height:20px; display:block; }
  .nodata { color:var(--dim); text-align:right; grid-column: 2 / 5; }
  footer { margin-top:16px; color:var(--dim); font-size:11px; text-align:center; }
  .glosario { margin:10px 0 0; font-size:10px; line-height:1.4; color:var(--dim); text-align:left; }
  .glosario dt { color:#b8b8b8; display:inline; font-weight:700; }
  .glosario dd { display:inline; margin:0; }
  .glosario div { margin-bottom:5px; }
  @media (max-width: 420px) { .fila { grid-template-columns: 1fr auto 70px; } svg.sp { display:none; } }
</style>
</head>
<body>
<header>
  <div>
    <h1>TERMINAL PLANETARIA</h1>
    <div class="sub">Solo lectura · precios con retraso (Yahoo Finance) · variación vs. cierre previo · gráfico a la derecha: cierres diarios del último mes</div>
  </div>
  <div class="reloj"><div id="reloj"></div><div id="estado" class="estado"></div></div>
</header>
<main id="paneles"></main>
<footer>
  <div>Informativo. No es asesoramiento. Los datos pueden fallar o llegar con retraso.</div>
  <dl class="glosario">
    <div><dt>Tether (USDT):</dt> <dd>stablecoin emitida por Tether, diseñada para valer 1 dólar. El emisor afirma respaldarla con reservas (efectivo, letras del Tesoro y otros activos). Es el "dólar" más usado en cripto; su precio debería rondar 1,00 y su riesgo es la confianza en el emisor y sus reservas.</dd></div>
    <div><dt>Oro tokenizado (PAXG):</dt> <dd>token PAXG de Paxos (ticker PAXG-USD); cada token equivale a una onza troy fina de oro físico en barras London Good Delivery custodiadas por Paxos en Londres. Cotiza 24/7 en dólares.</dd></div>
    <div><dt>Oro tokenizado (XAUT):</dt> <dd>Tether Gold (ticker XAUT-USD), emitido por TG Commodities, filial de Tether; cada token (ERC-20 en Ethereum) representa una onza troy de oro en barras LBMA Good Delivery custodiadas en Suiza y es redimible por oro físico con condiciones. Lanzado en enero de 2020; cotiza 24/7 en dólares.</dd></div>
    <div><dt>Oro (spot):</dt> <dd>precio del oro físico al contado (ticker XAU=X): dólares por onza troy para entrega inmediata. Es la referencia de mercado del metal y no tiene vencimiento; se diferencia del futuro por el coste de financiación y almacenamiento hasta el vencimiento.</dd></div>
    <div><dt>Oro (futuro):</dt> <dd>futuro del oro de COMEX (ticker GC=F), contrato del primer vencimiento, en dólares por onza troy. Es el precio de un contrato de futuros, no del oro físico al contado.</dd></div>
    <div><dt>Emergentes (EEM):</dt> <dd>iShares MSCI Emerging Markets ETF (BlackRock), fondo cotizado en NYSE Arca que replica el índice MSCI Emerging Markets. Muestra el precio de la participación en dólares, no el nivel del índice.</dd></div>
    <div><dt>Dólar (DXY):</dt> <dd>US Dollar Index de ICE (ticker DX-Y.NYB): valor del dólar frente a una cesta de seis divisas: euro 57,6 %, yen 13,6 %, libra 11,9 %, dólar canadiense 9,1 %, corona sueca 4,2 % y franco suizo 3,6 %. Base 100 en marzo de 1973.</dd></div>
  </dl>
</footer>
<script>
const DATA = __DATA__;
const nf = (v, d) => new Intl.NumberFormat('es-ES', {minimumFractionDigits:d, maximumFractionDigits:d}).format(v);
const dec = p => (Math.abs(p) >= 10 ? 2 : 4);
const cls = v => v > 0 ? 'up' : v < 0 ? 'down' : 'flat';

function spark(a, c) {
  if (!a || a.length < 2) return '';
  const mn = Math.min(...a), mx = Math.max(...a), r = (mx - mn) || 1;
  const pts = a.map((v, i) => (i / (a.length - 1) * 64).toFixed(1) + ',' + (18 - (v - mn) / r * 16).toFixed(1)).join(' ');
  const col = c === 'up' ? '#00d26a' : c === 'down' ? '#ff4d4d' : '#7d7d7d';
  return '<svg class="sp" viewBox="0 0 64 20" aria-hidden="true"><polyline fill="none" stroke="' + col + '" stroke-width="1.5" points="' + pts + '"/></svg>';
}

function fila(nombre, d) {
  if (!d) return '<div class="fila"><span class="nom">' + nombre + '</span><span class="nodata">sin datos</span></div>';
  const c = cls(d.pct), s = d.d >= 0 ? '+' : '';
  return '<div class="fila"><span class="nom">' + nombre + '</span>'
    + '<span class="px">' + nf(d.p, dec(d.p)) + '</span>'
    + '<span class="pct ' + c + '">' + s + nf(d.pct, 2) + '%<span class="abs">' + s + nf(d.d, dec(d.p)) + '</span></span>'
    + spark(d.spark, c) + '</div>';
}

document.getElementById('paneles').innerHTML = DATA.secciones.map(sec =>
  '<section><h2>' + sec.titulo + '</h2>' + sec.items.map(i => fila(i.nombre, i.datos)).join('') + '</section>'
).join('');

const gen = new Date(DATA.generado);
function tick() {
  const ahora = new Date();
  document.getElementById('reloj').textContent = ahora.toLocaleString('es-ES', {dateStyle:'short', timeStyle:'medium'});
  const min = Math.round((ahora - gen) / 60000);
  const el = document.getElementById('estado');
  el.textContent = 'Datos de hace ' + (min < 90 ? min + ' min' : Math.round(min / 60) + ' h');
  el.className = 'estado' + (min > 240 ? ' muy-viejo' : min > 45 ? ' viejo' : '');
}
tick(); setInterval(tick, 1000);
// Recarga la página abierta cada 5 min para recoger la última versión publicada
setInterval(() => location.reload(), 300000);
</script>
</body>
</html>
"""


def main():
    carpeta_script = os.path.dirname(os.path.abspath(__file__))
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(carpeta_script, "terminal_planetaria.html")
    tickers = [t for _, items in SECCIONES for _, t in items]
    datos = descargar(tickers)

    if not any(datos.values()):
        print("ERROR: ningún ticker devolvió datos; no se escribe el archivo.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "secciones": [
            {"titulo": titulo, "items": [{"nombre": n, "datos": datos[t]} for n, t in items]}
            for titulo, items in SECCIONES
        ],
    }
    # Evita cerrar el <script> por accidente si algún texto contuviera "</"
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = PLANTILLA.replace("__DATA__", blob)

    carpeta = os.path.dirname(destino)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)

    faltan = [t for t, v in datos.items() if v is None]
    print(f"OK: {destino} ({len(tickers) - len(faltan)}/{len(tickers)} tickers)")
    if faltan:
        print("Sin datos:", ", ".join(faltan))


if __name__ == "__main__":
    main()
