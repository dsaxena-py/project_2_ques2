import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Möbius Transformation Decomposition", layout="wide")

st.title("Möbius Transformation Decomposition: f(z) = (az+b)/(cz+d)")
st.write("Any Möbius transformation decomposes as: **Translate → Invert (1/z) → Scale → Translate** (when c≠0).")

# ── Sidebar controls ──────────────────────────────────────────────────────────
st.sidebar.header("Coefficients")

preset = st.sidebar.selectbox(
    "Preset",
    ["Custom", "1/z  (inversion)", "2z+1  (affine)", "(z+1)/(z−1)", "(z−i)/(z+i)  Cayley"],
)

preset_vals = {
    "1/z  (inversion)":   ("0", "1", "1", "0"),
    "2z+1  (affine)":     ("2", "1", "0", "1"),
    "(z+1)/(z−1)":        ("1", "1", "1", "-1"),
    "(z−i)/(z+i)  Cayley":("1", "-i", "1", "i"),
}

if preset != "Custom" and preset in preset_vals:
    da, db, dc, dd = preset_vals[preset]
else:
    da, db, dc, dd = "1+i", "1", "1", "1-i"

a_val = st.sidebar.text_input("a", value=da)
b_val = st.sidebar.text_input("b", value=db)
c_val = st.sidebar.text_input("c", value=dc)
d_val = st.sidebar.text_input("d", value=dd)

# ── Embed canvas ───────────────────────────────────────────────────────────────
html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; background:#fff; margin:6px; color:#222; }}
  .row {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:8px; align-items:center; }}
  .col {{ text-align:center; }}
  canvas {{ border:1px solid #bbb; background:#fafafa; display:block; }}
  .lbl {{ font-size:11px; margin-top:3px; font-weight:bold; color:#444; white-space:pre-line; }}
  .arrow {{ font-size:24px; color:#888; line-height:200px; }}
  .formula {{ font-family:monospace; background:#f4f4f4; padding:6px 10px;
              border-radius:4px; font-size:12px; line-height:1.8;
              margin-bottom:8px; display:inline-block; max-width:100%; }}
  .err {{ color:red; font-size:13px; }}
</style>
</head>
<body>
<div id="formulaDiv" class="formula">Computing…</div>
<div class="row" id="stepsRow"></div>

<script>
// ── Complex helpers ────────────────────────────────────────────────────────────
function parseC(s) {{
  s = (s||'').replace(/\\s/g,'');
  if (s===''||s===undefined) return [0,0];
  if (s==='i'||s==='+i') return [0,1];
  if (s==='-i') return [0,-1];
  if (/^[+-]?[\\d.]+$/.test(s)) return [parseFloat(s),0];
  if (/^[+-]?[\\d.]*i$/.test(s)) {{
    const n=s.replace('i','');
    return [0, n===''||n==='+'?1:n==='-'?-1:parseFloat(n)];
  }}
  let m=s.match(/^([+-]?[\\d.]+)([+-][\\d.]*i)$/);
  if (m) {{
    const im=m[2].replace('i','');
    return [parseFloat(m[1]), im===''||im==='+'?1:im==='-'?-1:parseFloat(im)];
  }}
  m=s.match(/^([+-]?[\\d.]+)([+-]i)$/);
  if (m) return [parseFloat(m[1]), m[2]==='+i'?1:-1];
  return [0,0];
}}
const cmul=([a,b],[c,d])=>[a*c-b*d,a*d+b*c];
const cadd=([a,b],[c,d])=>[a+c,b+d];
const csub=([a,b],[c,d])=>[a-c,b-d];
const cdiv=([a,b],[c,d])=>{{const s=c*c+d*d;if(s<1e-20)return[1e9,1e9];return[(a*c+b*d)/s,(b*c-a*d)/s];}};
const cnorm=([a,b])=>Math.sqrt(a*a+b*b);
const cfmt=([a,b])=>{{
  const ra=a.toFixed(3),rb=Math.abs(b).toFixed(3);
  if(Math.abs(b)<0.0005)return ra;
  if(Math.abs(a)<0.0005)return(b<0?'-':'')+rb+'i';
  return ra+(b<0?'-':'+')+rb+'i';
}};

// ── Canvas helpers ─────────────────────────────────────────────────────────────
const SZ=190, SCALE=38, OX=SZ/2, OY=SZ/2;
const toSc=(x,y)=>[OX+x*SCALE, OY-y*SCALE];

function drawBase(ctx) {{
  ctx.fillStyle='#fafafa'; ctx.fillRect(0,0,SZ,SZ);
  ctx.strokeStyle='#ebebeb'; ctx.lineWidth=1;
  for(let i=-5;i<=5;i++){{
    const[sx]=toSc(i,0);ctx.beginPath();ctx.moveTo(sx,0);ctx.lineTo(sx,SZ);ctx.stroke();
    const[,sy]=toSc(0,i);ctx.beginPath();ctx.moveTo(0,sy);ctx.lineTo(SZ,sy);ctx.stroke();
  }}
  ctx.strokeStyle='#bbb';ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(0,OY);ctx.lineTo(SZ,OY);ctx.stroke();
  ctx.beginPath();ctx.moveTo(OX,0);ctx.lineTo(OX,SZ);ctx.stroke();
  ctx.strokeStyle='#ddaa00';ctx.lineWidth=1;ctx.setLineDash([3,3]);
  ctx.beginPath();ctx.arc(OX,OY,SCALE,0,2*Math.PI);ctx.stroke();
  ctx.setLineDash([]);
}}

function drawShape(ctx,pts,color){{
  ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();
  let ok=false;
  for(const[x,y]of pts){{
    if(!isFinite(x)||!isFinite(y)||Math.abs(x)>7||Math.abs(y)>7){{ok=false;continue;}}
    const[sx,sy]=toSc(x,y);
    if(!ok){{ctx.moveTo(sx,sy);ok=true;}}else ctx.lineTo(sx,sy);
  }}
  ctx.stroke();
}}

// ── Test shapes ────────────────────────────────────────────────────────────────
function getTestShapes(){{
  const N=200, shapes=[];
  const c1=[];
  for(let i=0;i<=N;i++){{const t=i*2*Math.PI/N;c1.push([0.8+0.6*Math.cos(t),0.3+0.6*Math.sin(t)]);}}
  shapes.push({{pts:c1,color:'#2266cc'}});
  const l1=[];
  for(let x=-3.5;x<=3.5;x+=0.05)l1.push([x,1.2]);
  shapes.push({{pts:l1,color:'#228844'}});
  return shapes;
}}

function applyFn(shapes,fn){{
  return shapes.map(s=>({{...s,pts:s.pts.map(([x,y])=>{{const r=fn([x,y]);return r||[1e9,1e9];}})}})  );
}}

// ── Build ──────────────────────────────────────────────────────────────────────
function makeCanvas(label){{
  const div=document.createElement('div');div.className='col';
  const cv=document.createElement('canvas');cv.width=SZ;cv.height=SZ;
  const lbl=document.createElement('div');lbl.className='lbl';lbl.textContent=label;
  div.appendChild(cv);div.appendChild(lbl);
  return{{div,cv}};
}}
function makeArrow(){{
  const d=document.createElement('div');d.className='arrow';d.textContent='→';return d;
}}

(function go(){{
  const a=parseC("{a_val}");
  const b=parseC("{b_val}");
  const c=parseC("{c_val}");
  const d=parseC("{d_val}");
  const det=csub(cmul(a,d),cmul(b,c));
  const fDiv=document.getElementById('formulaDiv');
  const row=document.getElementById('stepsRow');
  row.innerHTML='';

  if(cnorm(det)<1e-8){{
    fDiv.innerHTML='<span class="err">ad − bc = 0 — not a valid Möbius transformation.</span>';
    return;
  }}

  const testShapes=getTestShapes();
  const cNorm=cnorm(c);
  let steps;

  if(cNorm<1e-6){{
    const ad=cdiv(a,d),bd=cdiv(b,d);
    steps=[
      {{label:'z\\n(original)',fn:z=>z}},
      {{label:`Step 1: Scale/Rotate\\n× ${{cfmt(ad)}}`,fn:z=>cmul(ad,z)}},
      {{label:`Step 2 = f(z)\\nTranslate + ${{cfmt(bd)}}`,fn:z=>cadd(cmul(ad,z),bd)}},
    ];
    fDiv.innerHTML=
      `f(z) = <b>(${{cfmt(a)}})z + (${{cfmt(b)}})</b> &nbsp;[c = 0 → affine]<br>`+
      `= ${{cfmt(ad)}} · z + ${{cfmt(bd)}}<br>`+
      `Decomposition: <b>Scale/Rotate → Translate</b>`;
  }}else{{
    const dc=cdiv(d,c),ac=cdiv(a,c),k=cdiv(det,cmul(c,c));
    steps=[
      {{label:'z\\n(original)',fn:z=>z}},
      {{label:`Step 1: Translate\\nz + d/c = z + ${{cfmt(dc)}}`,fn:z=>cadd(z,dc)}},
      {{label:`Step 2: Invert\\n1 / (z + d/c)`,fn:z=>cdiv([1,0],cadd(z,dc))}},
      {{label:`Step 3: Scale\\n× −(ad−bc)/c²`,fn:z=>{{
        const w=cadd(z,dc),inv=cdiv([1,0],w);
        return cmul([-k[0],-k[1]],inv);
      }}}},
      {{label:`Step 4 = f(z)\\nTranslate + a/c`,fn:z=>{{
        const w=cadd(z,dc),inv=cdiv([1,0],w),scl=cmul([-k[0],-k[1]],inv);
        return cadd(scl,ac);
      }}}},
    ];
    fDiv.innerHTML=
      `f(z) = <b>(${{cfmt(a)}})z+(${{cfmt(b)}}) / (${{cfmt(c)}})z+(${{cfmt(d)}})</b><br>`+
      `= a/c − (ad−bc)/c² · 1/(z + d/c)<br>`+
      `d/c = ${{cfmt(dc)}}, &nbsp; a/c = ${{cfmt(ac)}}, &nbsp; −(ad−bc)/c² = ${{cfmt([-k[0],-k[1]])}}<br>`+
      `Decomposition: <b>Translate → Invert → Scale → Translate</b>`;
  }}

  steps.forEach((step,i)=>{{
    if(i>0)row.appendChild(makeArrow());
    const{{div,cv}}=makeCanvas(step.label);
    const ctx=cv.getContext('2d');
    drawBase(ctx);
    applyFn(testShapes,step.fn).forEach(({{pts,color}})=>drawShape(ctx,pts,color));
    row.appendChild(div);
  }});
}})();
</script>
</body>
</html>
"""

components.html(html_code, height=320, scrolling=True)

st.markdown("---")
st.markdown("""
**How the decomposition works (c ≠ 0):**

$$f(z) = \\frac{az+b}{cz+d} = \\frac{a}{c} - \\frac{ad-bc}{c^2} \\cdot \\frac{1}{z + d/c}$$

| Step | Operation | Formula |
|------|-----------|---------|
| 1 | Translate | $z \\mapsto z + d/c$ |
| 2 | Invert | $z \\mapsto 1/z$ |
| 3 | Scale / Rotate | $z \\mapsto -\\frac{ad-bc}{c^2} \\cdot z$ |
| 4 | Translate | $z \\mapsto z + a/c$ |

If **c = 0** the transformation is affine: $f(z) = \\frac{a}{d}z + \\frac{b}{d}$ (scale/rotate then translate).
""")