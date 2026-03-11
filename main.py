import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Inversion f(z) = 1/z", layout="wide")

st.title("Inversion: f(z) = 1/z")
st.write("Choose a shape on the left. Its image under **f(z) = 1/z** is shown on the right.")

shape = st.selectbox(
    "Shape",
    options=[
        "circle_no_origin",
        "circle_through_origin",
        "line_through_origin",
        "line_no_origin",
        "unit_circle",
        "all",
    ],
    format_func=lambda x: {
        "circle_no_origin":      "Circle NOT through origin",
        "circle_through_origin": "Circle THROUGH origin",
        "line_through_origin":   "Line THROUGH origin",
        "line_no_origin":        "Line NOT through origin",
        "unit_circle":           "Unit Circle",
        "all":                   "Show All",
    }[x],
)

html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; background: #fff; margin: 8px; color: #222; }}
  .container {{ display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap; }}
  canvas {{ border: 1px solid #999; background: #fafafa; }}
  .label {{ text-align: center; font-size: 13px; margin-top: 4px; font-weight: bold; }}
  .info {{ max-width: 280px; font-size: 12px; line-height: 1.8; }}
  .info h3 {{ margin: 6px 0 3px; color: #555; font-size: 13px; }}
</style>
</head>
<body>
<div class="container">
  <div>
    <canvas id="cvLeft"  width="300" height="300"></canvas>
    <div class="label">Input z-plane</div>
  </div>
  <div>
    <canvas id="cvRight" width="300" height="300"></canvas>
    <div class="label">Output w-plane &nbsp; w = 1/z</div>
  </div>
  <div class="info">
    <h3>Key Facts about f(z) = 1/z</h3>
    <span style="color:blue">&#9644;</span> Original shape<br>
    <span style="color:red">&#9644;</span> Image under 1/z<br>
    <span style="color:#ccaa00">- - -</span> Unit circle<br><br>
    <b>Circle NOT through 0</b> &rarr; Circle<br>
    <b>Circle THROUGH 0</b> &rarr; Straight line<br>
    <b>Line THROUGH 0</b> &rarr; Line through 0<br>
    <b>Line NOT through 0</b> &rarr; Circle through 0<br>
    <b>Unit circle |z|=1</b> &rarr; Itself (fixed)<br>
    <b>Inside unit disk &harr; Outside</b>
  </div>
</div>

<script>
const W = 300, H = 300;
const SCALE = 62;
const OX = W/2, OY = H/2;

const SELECTED = "{shape}";

function toScreen(x, y) {{ return [OX + x*SCALE, OY - y*SCALE]; }}

function invertPt(x, y) {{
  const d = x*x + y*y;
  if (d < 1e-12) return null;
  return [x/d, -y/d];
}}

function setupCanvas(cv) {{
  const ctx = cv.getContext('2d');
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle = '#fafafa'; ctx.fillRect(0,0,W,H);
  ctx.strokeStyle = '#e0e0e0'; ctx.lineWidth = 1;
  for (let i = -4; i <= 4; i++) {{
    const [sx] = toScreen(i, 0); ctx.beginPath(); ctx.moveTo(sx,0); ctx.lineTo(sx,H); ctx.stroke();
    const [,sy] = toScreen(0, i); ctx.beginPath(); ctx.moveTo(0,sy); ctx.lineTo(W,sy); ctx.stroke();
  }}
  ctx.strokeStyle = '#aaa'; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(0,OY); ctx.lineTo(W,OY); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(OX,0); ctx.lineTo(OX,H); ctx.stroke();
  ctx.fillStyle = '#999'; ctx.font = '10px Arial';
  for (let i=-3; i<=3; i++) {{ if (!i) continue;
    const [sx] = toScreen(i,0); ctx.fillText(i, sx-4, OY+12);
    const [,sy] = toScreen(0,i); ctx.fillText(i, OX+4, sy+4);
  }}
  ctx.strokeStyle = '#ccaa00'; ctx.lineWidth = 1; ctx.setLineDash([4,3]);
  ctx.beginPath(); ctx.arc(OX, OY, SCALE, 0, 2*Math.PI); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#666'; ctx.beginPath(); ctx.arc(OX,OY,3,0,2*Math.PI); ctx.fill();
  return ctx;
}}

function drawCurve(ctx, pts, color, lw=2) {{
  ctx.strokeStyle = color; ctx.lineWidth = lw;
  ctx.beginPath();
  let started = false;
  for (const [x,y] of pts) {{
    if (!isFinite(x)||!isFinite(y)||x>8||x<-8||y>8||y<-8) {{ started=false; continue; }}
    const [sx,sy] = toScreen(x,y);
    if (!started) {{ ctx.moveTo(sx,sy); started=true; }}
    else ctx.lineTo(sx,sy);
  }}
  ctx.stroke();
}}

function sampleAndInvert(pts) {{
  return pts.map(([x,y]) => {{
    const r = invertPt(x,y);
    return r ? r : [Infinity, Infinity];
  }});
}}

const shapes = {{
  circle_no_origin: () => {{
    const pts = []; const N=300;
    for (let i=0;i<=N;i++) {{ const t=i*2*Math.PI/N; pts.push([1.2+0.7*Math.cos(t), 0.5+0.7*Math.sin(t)]); }}
    return pts;
  }},
  circle_through_origin: () => {{
    const pts = []; const N=300;
    for (let i=0;i<=N;i++) {{ const t=i*2*Math.PI/N; pts.push([0.8+0.8*Math.cos(t), 0.8*Math.sin(t)]); }}
    return pts;
  }},
  line_through_origin: () => {{
    const pts = [];
    for (let t=-4; t<=4; t+=0.02) pts.push([t, t]);
    return pts;
  }},
  line_no_origin: () => {{
    const pts = [];
    for (let t=-4; t<=4; t+=0.02) pts.push([1.5, t]);
    return pts;
  }},
  unit_circle: () => {{
    const pts = []; const N=300;
    for (let i=0;i<=N;i++) {{ const t=i*2*Math.PI/N; pts.push([Math.cos(t), Math.sin(t)]); }}
    return pts;
  }}
}};

const allKeys = Object.keys(shapes);
const colors  = ['blue','green','purple','orange','darkred'];

function render() {{
  const ctxL = setupCanvas(document.getElementById('cvLeft'));
  const ctxR = setupCanvas(document.getElementById('cvRight'));
  const keys  = SELECTED === 'all' ? allKeys : [SELECTED];
  keys.forEach((key, ki) => {{
    const color = SELECTED === 'all' ? colors[ki] : 'blue';
    const pts = shapes[key]();
    drawCurve(ctxL, pts, color);
    drawCurve(ctxR, sampleAndInvert(pts), 'red');
  }});
  if (SELECTED !== 'all') {{
    const labels = {{
      circle_no_origin:      "Circle NOT through origin: center (1.2, 0.5), r=0.7",
      circle_through_origin: "Circle THROUGH origin: center (0.8, 0), r=0.8",
      line_through_origin:   "Line THROUGH origin: y = x",
      line_no_origin:        "Line NOT through origin: x = 1.5",
      unit_circle:           "Unit circle |z| = 1",
    }};
    const ctxL2 = document.getElementById('cvLeft').getContext('2d');
    ctxL2.fillStyle = '#333'; ctxL2.font = '10px Arial';
    ctxL2.fillText(labels[SELECTED] || '', 4, 13);
  }}
}}

render();
</script>
</body>
</html>
"""

components.html(html_code, height=360)

st.markdown("---")
st.markdown("""
**Summary of transformation rules for f(z) = 1/z:**

| Original shape | Image under 1/z |
|---|---|
| Circle **not** through origin | Circle (not through origin) |
| Circle **through** origin | Straight line |
| Line **through** origin | Line through origin |
| Line **not** through origin | Circle through origin |
| Unit circle \\|z\\| = 1 | Itself (unchanged) |
| Inside unit disk | Outside unit disk |
""")