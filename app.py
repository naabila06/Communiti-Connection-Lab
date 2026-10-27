"""
Community Connection Lab - Proyek 07  (SATU BERKAS)
Jalankan:  python -m streamlit run app.py
Dibutuhkan: streamlit, networkx, pandas
"""
from collections import deque
import networkx as nx

# ----------------------------------------------------------------------
# 1. DATA (nyata, sudah ada di dalam NetworkX sehingga tidak perlu internet)
# ----------------------------------------------------------------------
DATASETS = {
    "Zachary Karate Club (pertemanan, 20 anggota)": {
        "kunci": "karate",
        "sumber": (
            "W. W. Zachary (1977), 'An Information Flow Model for Conflict and "
            "Fission in Small Groups', Journal of Anthropological Research 33(4): 452-473. "
            "Sisi = dua anggota klub karate universitas yang berteman di luar klub. "
            "Aplikasi memakai anggota nomor 1-20 dari 34 anggota asli "
            "(subgraf terinduksi) agar sesuai ruang lingkup 10-20 titik."
        ),
        "arti_titik": "anggota klub karate (nomor sesuai artikel Zachary)",
        "arti_sisi": "hubungan pertemanan timbal balik di luar kegiatan klub",
    },
    "Florentine Families (kekerabatan, 15 keluarga)": {
        "kunci": "florentine",
        "sumber": (
            "Padgett & Ansell (1993), 'Robust Action and the Rise of the Medici, "
            "1400-1434', American Journal of Sociology 98(6). Sisi = ikatan "
            "pernikahan antar keluarga bangsawan Florence abad ke-15."
        ),
        "arti_titik": "keluarga bangsawan Florence",
        "arti_sisi": "ikatan pernikahan antar dua keluarga (timbal balik)",
    },
}


def load_dataset(nama: str) -> nx.Graph:
    kunci = DATASETS[nama]["kunci"]
    if kunci == "karate":
        K = nx.karate_club_graph()
        sub = K.subgraph(range(20)).copy()
        return nx.relabel_nodes(sub, {i: f"A{i + 1}" for i in sub.nodes})
    if kunci == "florentine":
        return nx.florentine_families_graph()
    raise ValueError(nama)


def load_from_edgelist(df, kolom_a, kolom_b) -> nx.Graph:
    """Bangun graf dari tabel CSV milik sendiri (data nyata dari kelas, dsb.)."""
    G = nx.Graph()
    for a, b in zip(df[kolom_a].astype(str), df[kolom_b].astype(str)):
        a, b = a.strip(), b.strip()
        if a and b and a != b:
            G.add_edge(a, b)
    return G


# ----------------------------------------------------------------------
# 2. BFS & DFS BUATAN SENDIRI (mencatat setiap langkah untuk animasi)
# ----------------------------------------------------------------------
def traverse(G: nx.Graph, method: str = "BFS", start=None):
    """
    Menelusuri SELURUH graf (semua komponen) dan mencatat setiap langkah.

    Return:
      events     : list dict {step, comp, node, parent, frontier, note}
      components : list of list (urutan kunjungan tiap komponen)
    Titik awal pertama = `start` (jika ada), sisanya urut abjad.
    """
    order = sorted(G.nodes, key=str)
    if start is not None and start in G:
        order.remove(start)
        order.insert(0, start)

    seen, events, components = set(), [], []
    for s in order:
        if s in seen:
            continue
        comp_id = len(components)
        comp = []
        if method == "BFS":
            frontier = deque([(s, None)])      # antrean FIFO
            seen.add(s)                         # BFS menandai saat dimasukkan
            while frontier:
                v, p = frontier.popleft()
                comp.append(v)
                for u in sorted(G[v], key=str):
                    if u not in seen:
                        seen.add(u)
                        frontier.append((u, v))
                events.append(_event(len(events), comp_id, v, p,
                                     [x for x, _ in frontier], "BFS"))
        else:
            frontier = [(s, None)]              # tumpukan LIFO
            done = set()
            while frontier:
                v, p = frontier.pop()
                if v in done:
                    continue
                done.add(v)
                seen.add(v)
                comp.append(v)
                for u in sorted(G[v], key=str, reverse=True):
                    if u not in done:
                        frontier.append((u, v))
                uniq = []
                for x, _ in reversed(frontier):  # puncak tumpukan di depan
                    if x not in done and x not in uniq:
                        uniq.append(x)
                events.append(_event(len(events), comp_id, v, p, uniq, "DFS"))
        components.append(comp)
    return events, components


def _event(step, comp, node, parent, frontier, method):
    wadah = "antrean" if method == "BFS" else "tumpukan"
    if parent is None:
        note = f"Mulai kelompok baru dari {node}."
    else:
        note = f"Kunjungi {node} (lewat {parent})."
    note += f" Isi {wadah}: {frontier if frontier else 'kosong'}"
    return {"step": step, "comp": comp, "node": node, "parent": parent,
            "frontier": list(frontier), "note": note}


def find_components(G, method="BFS"):
    _, comps = traverse(G, method)
    return comps


# ----------------------------------------------------------------------
# 3. STATISTIK
# ----------------------------------------------------------------------
def stats(G: nx.Graph, comps):
    n = G.number_of_nodes()
    sizes = sorted((len(c) for c in comps), reverse=True)
    deg = dict(G.degree())
    top = max(deg, key=deg.get) if deg else None
    return {
        "Jumlah titik": n,
        "Jumlah hubungan": G.number_of_edges(),
        "Jumlah kelompok": len(comps),
        "Ukuran kelompok terbesar": sizes[0] if sizes else 0,
        "Anggota terisolasi (derajat 0)": sum(1 for d in deg.values() if d == 0),
        "Rata-rata derajat": round(2 * G.number_of_edges() / n, 2) if n else 0,
        "Derajat tertinggi": f"{top} ({deg[top]})" if top else "-",
        "Jumlah jembatan": len(list(nx.bridges(G))),
        "Jumlah titik penghubung": len(list(nx.articulation_points(G))),
    }


def connectors(G):
    """Jembatan (sisi) dan titik penghubung (titik) di dalam tiap kelompok."""
    return sorted(nx.bridges(G), key=str), sorted(nx.articulation_points(G), key=str)


# ----------------------------------------------------------------------
# 4. VALIDASI
# ----------------------------------------------------------------------
def validate(G, comps):
    semua = [v for c in comps for v in c]
    cek = {
        "Setiap titik masuk tepat satu kelompok": len(semua) == len(set(semua)) == G.number_of_nodes(),
        "Jumlah ukuran kelompok = jumlah titik": sum(len(c) for c in comps) == G.number_of_nodes(),
        "Sama dengan nx.connected_components": (
            {frozenset(c) for c in comps} == {frozenset(c) for c in nx.connected_components(G)}),
        "Jumlah kelompok sama dengan nx.number_connected_components":
            len(comps) == nx.number_connected_components(G),
        "Jumlah derajat = 2 x jumlah hubungan":
            sum(d for _, d in G.degree()) == 2 * G.number_of_edges(),
    }
    return cek


# ----------------------------------------------------------------------
# 5. PERBANDINGAN SEBELUM vs SESUDAH
# ----------------------------------------------------------------------
def compare(before_comps, after_comps):
    b = [set(c) for c in before_comps]
    a = [set(c) for c in after_comps]
    lapor = []
    for ac in a:
        asal = [bc for bc in b if bc & ac]
        if len(asal) > 1:
            lapor.append(("gabung", sorted(map(len, asal)), len(ac), sorted(ac, key=str)))
    for bc in b:
        hasil = [ac for ac in a if ac & bc]
        if len(hasil) > 1:
            lapor.append(("pecah", len(bc), sorted(map(len, hasil)), sorted(bc, key=str)))
    return lapor


def describe_changes(lapor, log):
    if not log:
        return ["Belum ada perubahan hubungan."]
    if not lapor:
        return ["Perubahan hubungan tidak menggabungkan maupun memecah kelompok "
                "(hanya mengubah derajat / kekuatan koneksi di dalam kelompok)."]
    out = []
    for item in lapor:
        if item[0] == "gabung":
            out.append(f"Kelompok berukuran {item[1]} MENYATU menjadi satu kelompok berukuran {item[2]}.")
        else:
            out.append(f"Kelompok berukuran {item[1]} TERPECAH menjadi kelompok berukuran {item[2]}.")
    return out


# ----------------------------------------------------------------------
# 6. RIWAYAT PERUBAHAN (untuk menjawab: hubungan mana yang menyatukan/memisahkan?)
# ----------------------------------------------------------------------
def apply_change(G, op, a, b):
    """Terapkan satu perubahan. Return (ok, pesan, penjelasan_dampak)."""
    if op == "tambah":
        if a == b:
            return False, "Dua titik harus berbeda.", ""
        if G.has_edge(a, b):
            return False, "Hubungan itu sudah ada.", ""
        beda_kelompok = not nx.has_path(G, a, b)
        G.add_edge(a, b)
        dampak = (f"{a} dan {b} sebelumnya berada di kelompok BERBEDA, sehingga hubungan "
                  f"ini MENYATUKAN dua kelompok (jembatan baru)." if beda_kelompok else
                  f"{a} dan {b} sudah berada di kelompok yang sama; hubungan ini hanya "
                  f"menambah derajat dan memperkuat koneksi di dalam kelompok.")
        return True, f"Menambah hubungan {a} — {b}.", dampak
    if op == "hapus":
        if not G.has_edge(a, b):
            return False, "Hubungan itu tidak ada.", ""
        jembatan = {frozenset(e) for e in nx.bridges(G)}
        G.remove_edge(a, b)
        dampak = (f"{a} — {b} adalah JEMBATAN: menghapusnya MEMECAH satu kelompok menjadi dua."
                  if frozenset((a, b)) in jembatan else
                  f"{a} — {b} bukan jembatan; ada jalur lain sehingga kelompok tetap utuh "
                  f"(hanya derajat yang turun).")
        return True, f"Menghapus hubungan {a} — {b}.", dampak
    return False, "Operasi tidak dikenal.", ""


# ----------------------------------------------------------------------
# 7. TATA LETAK (posisi stabil, renggang, titik terisolasi dirapikan)
# ----------------------------------------------------------------------
def _longgarkan(pos, dmin, putaran=600):
    """Dorong titik yang terlalu dekat agar jarak minimal antar titik = dmin."""
    import itertools, math
    p = {v: [x, y] for v, (x, y) in pos.items()}
    for _ in range(putaran):
        gerak = False
        for a, b in itertools.combinations(p, 2):
            dx, dy = p[b][0] - p[a][0], p[b][1] - p[a][1]
            d = math.hypot(dx, dy) or 1e-6
            if d < dmin - 1e-9:
                f = (dmin - d) / 2 / d
                p[a][0] -= dx * f; p[a][1] -= dy * f
                p[b][0] += dx * f; p[b][1] += dy * f
                gerak = True
        if not gerak:
            break
    return {v: (x, y) for v, (x, y) in p.items()}


def make_layout(G: nx.Graph, seed: int = 42, spasi: float = 1.0):
    """
    spasi = jarak minimal antar titik (satuan koordinat). Makin besar, makin renggang.
    Kelompok terbesar di tengah; kelompok kecil/terisolasi disusun rapi
    dalam baris di bawahnya agar tidak ada titik yang terlempar jauh.
    """
    comps = sorted(nx.connected_components(G),
                   key=lambda c: (-len(c), str(sorted(c, key=str)[0])))
    pos = {}
    main = comps[0]
    if len(main) > 1:
        p = nx.spring_layout(G.subgraph(main), seed=seed, k=2.4 / len(main) ** 0.5,
                             iterations=500, scale=max(1.3, 2.6 * spasi))
        pos.update(_longgarkan({v: (float(x), float(y)) for v, (x, y) in p.items()}, spasi))
    else:
        pos[next(iter(main))] = (0.0, 0.0)

    xs = [x for x, _ in pos.values()]
    ys = [y for _, y in pos.values()]
    x_min, x_max = min(xs), max(xs)
    x0 = x_min
    batas = max(x_max, x_min + 4 * spasi)
    y = min(ys) - 1.5 * spasi
    cursor = x0
    for c in comps[1:]:
        lebar = 1.4 * spasi if len(c) == 1 else spasi * (1.4 + 0.6 * len(c))
        if cursor + lebar > batas + 1e-9 and cursor > x0:   # baris baru
            cursor, y = x0, y - 1.3 * spasi
        cx = cursor + lebar / 2
        if len(c) == 1:
            pos[next(iter(c))] = (cx, y)
        else:
            p = nx.spring_layout(G.subgraph(c), seed=seed, scale=lebar / 2.4)
            q = {v: (float(px) + cx, float(py) + y) for v, (px, py) in p.items()}
            pos.update(_longgarkan(q, spasi))
        cursor += lebar
    return pos


import json
import networkx as nx

PALETTE = ["#4cc9f0", "#80ed99", "#c77dff", "#ff9f1c", "#f72585",
           "#2ec4b6", "#ffd6a5", "#9bf6ff", "#e0aaff", "#b8f2e6"]
SYMBOLS = ["square", "triangle-up", "diamond", "pentagon", "hexagon",
           "triangle-down", "octagon", "star"]
LOVE_PALETTE = ["#ff8fb8", "#b794f4", "#7dd3fc", "#ffc27a", "#7ee0c8", "#f6a6d6", "#b5e07a", "#ffa98a", "#9fa8ff", "#ff9a9a"]
FORMAL_PALETTE = ["#8fb1d1", "#f2b880", "#9dc99a", "#e59a9c", "#a7cfcb", "#c5a9cf", "#c3a58f", "#ecd88a", "#f2bfc6", "#b8b8b8"]
MODERN_PALETTE = ["#7b9be0", "#6fbfb5", "#8cc58f", "#a58bd1", "#d58fb0", "#93a1b8", "#aac47a", "#8e97d9", "#c19ac9", "#7fb7d6"]
EMOJIS = ["💖", "🌟", "🍀", "🦋", "🌸", "🐱", "🍓", "☁️", "🌈", "🍭"]


def ordered(comps):
    """Kelompok terbesar jadi nomor 1."""
    return sorted(comps, key=lambda c: (-len(c), str(sorted(c, key=str)[0])))


def graph_html(G, pos, comps, *, mode="static", events=None, method="BFS", title="",
               added=(), removed=(), speed_ms=900, scale=1.0, autoplay=True, theme="modern"):
    deg = dict(G.degree())
    comp_of, comps_info = {}, []
    for i, c in enumerate(comps):
        for v in c:
            comp_of[v] = i
        pal = {"love": LOVE_PALETTE, "formal": FORMAL_PALETTE, "modern": MODERN_PALETTE}.get(theme, PALETTE)
        comps_info.append({"name": f"Kelompok {i + 1}", "size": len(c),
                           "color": pal[i % len(pal)],
                           "symbol": SYMBOLS[i % len(SYMBOLS)],
                           "emoji": EMOJIS[i % len(EMOJIS)]})
    nodes = [{"id": str(v), "x": float(pos[v][0]), "y": float(pos[v][1]),
              "deg": int(deg[v]), "comp": comp_of[v]} for v in G.nodes]
    edges = [[str(a), str(b)] for a, b in G.edges]
    bridges = [[str(a), str(b)] for a, b in nx.bridges(G)] if mode == "static" else []
    ev = []
    for e in (events or []):
        ev.append({"node": str(e["node"]),
                   "parent": None if e["parent"] is None else str(e["parent"]),
                   "comp": int(e["comp"]), "frontier": [str(x) for x in e["frontier"]]})
    data = {"theme": theme, "mode": mode, "method": method, "title": title, "nodes": nodes, "edges": edges,
            "bridges": bridges, "events": ev, "comps": comps_info,
            "added": [[str(a), str(b)] for a, b in added if G.has_edge(a, b)],
            "removed": [[str(a), str(b)] for a, b in removed if str(a) in {n["id"] for n in nodes}
                        and str(b) in {n["id"] for n in nodes}],
            "speed": int(speed_ms), "scale": float(scale), "autoplay": bool(autoplay)}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return HTML.replace("__DATA__", payload)


HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{box-sizing:border-box}
:root{--bg:#0b1220;--txt:#e8eefc;--card:#0f1a30;--head:linear-gradient(90deg,#17264a,#0f1a30);--line:#243a63;
 --accent:#ffd166;--sub:#9fb6e6;--btn:#16284a;--btnh:#1f3868;--btnline:#2c4676;--outline:#0b1220;
 --stage:radial-gradient(ellipse at 50% 35%,#16284a 0%,#0b1220 72%);--acc2:#20c997;
 --play:linear-gradient(135deg,#12b886,#0b7285);--playline:#38d9a9;--chip:#ffe9a8;--legbg:rgba(9,15,28,.86)}
body.love{--bg:#fff5fa;--txt:#4a1d44;--card:#ffffff;--head:linear-gradient(90deg,#ffe3f1,#f3e8ff);--line:#f6b8d8;
 --accent:#e0457b;--sub:#a0548a;--btn:#ffe3f1;--btnh:#ffd0e6;--btnline:#f3a6cc;--outline:#ffffff;
 --stage:linear-gradient(160deg,#fff0f6,#f3e8ff 55%,#dff3ff);--acc2:#ff4d8d;
 --play:linear-gradient(135deg,#ff6fa5,#ff4d8d);--playline:#ffb3d1;--chip:#8a1f50;--legbg:rgba(255,255,255,.88)}
body.formal{--bg:#ffffff;--txt:#1f2937;--card:#ffffff;--head:#f3f4f6;--line:#d1d5db;
 --accent:#1e3a8a;--sub:#4b5563;--btn:#f9fafb;--btnh:#e5e7eb;--btnline:#9ca3af;--outline:#ffffff;
 --stage:#fbfbfc;--acc2:#1e3a8a;--play:#1e3a8a;--playline:#1e3a8a;--chip:#1f2937;--legbg:rgba(255,255,255,.96)}
body.modern{--bg:#ffffff;--txt:#243049;--card:#ffffff;--head:#f1f5fb;--line:#dbe2ee;
 --accent:#34558b;--sub:#5d6b85;--btn:#ffffff;--btnh:#eef3fa;--btnline:#c9d3e3;--outline:#ffffff;
 --stage:#f8fafd;--acc2:#34558b;
 --play:#34558b;--playline:#34558b;--chip:#243049;--legbg:rgba(255,255,255,.96)}
html,body{margin:0;height:100%;background:var(--bg);font-family:"Segoe UI",Roboto,Arial,sans-serif;color:var(--txt)}
#app{display:flex;flex-direction:column;height:100vh;gap:8px}
#head{padding:9px 14px;border-radius:12px;background:var(--head);
  border:1px solid var(--line);font-size:15px;line-height:1.4;min-height:42px}
#head b{color:var(--accent)}
#stage{position:relative;flex:1;min-height:220px;border-radius:16px;overflow:hidden;
  border:1px solid var(--line);background:var(--stage)}
svg{position:relative;z-index:1;width:100%;height:100%;display:block;cursor:grab;touch-action:none}
#decor{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:0}
#decor span{position:absolute;bottom:-40px;opacity:.4;animation:fl linear infinite}
@keyframes fl{0%{transform:translateY(0) rotate(0)}100%{transform:translateY(-900px) rotate(30deg);opacity:0}}
#leg{position:absolute;top:10px;left:10px;background:var(--legbg);border:1px solid var(--line);
  border-radius:12px;padding:6px 10px;font-size:13px;max-height:74%;overflow:auto;z-index:3}
#leg summary{cursor:pointer;font-weight:600;color:var(--sub)}
#leg .it{display:flex;align-items:center;gap:7px;margin:5px 0;white-space:nowrap}
#tools{position:absolute;top:10px;right:10px;display:flex;gap:6px;z-index:3}
button,select{font:inherit;color:var(--txt);background:var(--btn);border:1px solid var(--btnline);border-radius:10px;
  padding:6px 11px;cursor:pointer}
button:hover{background:var(--btnh)}
#panel{display:none;gap:6px;flex-direction:column;padding:8px 12px;border-radius:12px;background:var(--card);
  border:1px solid var(--line);font-size:13.5px}
.row{display:flex;align-items:center;gap:6px;overflow-x:auto;white-space:nowrap;padding-bottom:2px}
.row .lab{color:var(--sub);font-weight:600;min-width:120px}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;border:1.5px solid #ffc531;color:var(--chip);
  background:rgba(255,197,49,.14);font-weight:600}
.chip.v{background:rgba(128,128,128,.10)}
.chip.cur{border-color:#ff1744;background:rgba(255,23,68,.14)}
#player{display:none;align-items:center;gap:8px;padding:8px 12px;border-radius:14px;background:var(--card);
  border:1px solid var(--line)}
#play{width:46px;height:46px;border-radius:50%;font-size:18px;color:#fff;background:var(--play);border:2px solid var(--playline)}
#slider{flex:1;accent-color:var(--acc2);min-width:80px}
#cnt{font-size:12px;color:var(--sub);min-width:70px;text-align:center}
.node text{pointer-events:none;font-weight:700;paint-order:stroke;stroke:var(--outline);stroke-width:3.5px;stroke-linejoin:round}
.node text.emo{stroke:none}
.pt{text-anchor:middle;animation:fly 1.2s ease-out forwards;pointer-events:none}
@keyframes fly{0%{transform:translate(0,0) scale(.5);opacity:1}100%{transform:translate(var(--dx),var(--dy)) scale(1.4);opacity:0}}
.spk{transform-box:fill-box;transform-origin:center;animation:tw 2.6s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:0;transform:scale(.3) rotate(0)}50%{opacity:1;transform:scale(1.15) rotate(45deg)}}
.gl{position:absolute;animation:tw2 3.4s ease-in-out infinite;pointer-events:none}
@keyframes tw2{0%,100%{opacity:.06;transform:scale(.6)}50%{opacity:.6;transform:scale(1.25)}}
.shape{transition:fill .3s,stroke .3s}
.body{transition:transform .35s cubic-bezier(.3,1.6,.5,1)}
.ring{fill:none;stroke:#f7c873;stroke-width:2.2;transform-box:fill-box;transform-origin:center;animation:pul 1.2s ease-out infinite}
.ripple{fill:none;stroke:#f27b7b;stroke-width:3;transform-box:fill-box;transform-origin:center;animation:rip .95s ease-out forwards}
@keyframes pul{0%{transform:scale(1);opacity:.95}100%{transform:scale(2);opacity:0}}
@keyframes rip{0%{transform:scale(1);opacity:.95}100%{transform:scale(3.6);opacity:0}}
.clab{font-size:13.5px;font-weight:700;paint-order:stroke;stroke:var(--outline);stroke-width:3px;text-anchor:middle}
</style></head>
<body><div id="app">
 <div id="head"></div>
 <div id="stage">
  <div id="status" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--sub);font-size:14px;z-index:0">Memuat visualisasi…</div><div id="decor"></div><svg id="svg"></svg>
  <details id="leg" open><summary>Legenda</summary><div id="legbody"></div></details>
  <div id="tools"><button id="zin" title="Perbesar">＋</button><button id="zout" title="Perkecil">－</button>
   <button id="zreset" title="Atur ulang tampilan">⌖</button></div>
 </div>
 <div id="panel"><div class="row"><span class="lab" id="qlab"></span><span id="q"></span></div>
  <div class="row"><span class="lab">Urutan dikunjungi:</span><span id="vis"></span></div></div>
 <div id="player">
  <button id="b0" title="Ke awal">⏮</button><button id="bp" title="Langkah mundur">◀</button>
  <button id="play" title="Putar / jeda">▶</button>
  <button id="bn" title="Langkah maju">▶❙</button><button id="b1" title="Ke akhir">⏭</button>
  <input id="slider" type="range" min="0" value="0"><span id="cnt"></span>
  <select id="spd"><option value="0.5">0.5×</option><option value="1" selected>1×</option>
   <option value="1.5">1.5×</option><option value="2">2×</option><option value="3">3×</option></select>
 </div></div>
<noscript><div style="padding:14px;color:#b91c1c">JavaScript nonaktif. Aktifkan "Mode cadangan" di sidebar.</div></noscript>
<script>
function showErr(m, l) { const h = document.getElementById("head"); if (!h) return;
  h.style.color = "#b91c1c"; h.textContent = "Galat tampilan: " + m + (l ? " (baris " + l + ")" : "") + ". Aktifkan 'Mode cadangan' di sidebar."; }
window.onerror = (m, src, l) => { showErr(m, l); };
const D = __DATA__;
const NS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);
const anim = D.mode === "anim", N = D.events.length;
const LOVE = D.theme === "love", FORMAL = D.theme === "formal", MODERN = D.theme === "modern";
const LIGHT = LOVE || FORMAL || MODERN, SHINE = false;
if (LIGHT && document.body) document.body.className = D.theme;
const GLOW = FORMAL ? "" : (MODERN ? "url(#soft)" : "url(#glow)"), HA = FORMAL ? 0 : (MODERN ? 0.5 : 1);
const BRIDGE = "#f97316";
const ADD = LIGHT ? "#4cc38a" : "#69db7c", REM = LIGHT ? "#e66b6b" : "#ff4d6d";
let gDefs = null, GR = {};
function tint(hex, p) { const n = parseInt(hex.slice(1), 16);
  return "#" + [n >> 16, (n >> 8) & 255, n & 255].map(x => Math.round(x + (255 - x) * p).toString(16).padStart(2, "0")).join(""); }
function grad(id, attrs, stops) {
  if (GR[id] || !gDefs) return; GR[id] = 1;
  const g = el("radialGradient", Object.assign({id}, attrs), gDefs);
  stops.forEach(s => el("stop", {offset: s[0], "stop-color": s[1], "stop-opacity": s[2] === undefined ? 1 : s[2]}, g));
}
function paint(color) {            // isi titik: gradien mutiara (berkilau lembut)
  if (!SHINE) return color;
  const id = "g" + color.slice(1);
  grad(id, {cx: 0.36, cy: 0.3, r: 0.82, fx: 0.3, fy: 0.24},
    [[0, "#ffffff", 0.98], [0.26, tint(color, 0.62)], [0.7, color], [1, shade(color, -0.1)]]);
  return `url(#${id})`;
}
function haloPaint(color) {        // cahaya lembut di sekeliling titik
  if (!SHINE) return color;
  const id = "h" + color.slice(1);
  grad(id, {cx: 0.5, cy: 0.5, r: 0.5}, [[0, color, 0.6], [0.55, color, 0.22], [1, color, 0]]);
  return `url(#${id})`;
}
function shade(hex, f) { const n = parseInt(hex.slice(1), 16), k = 1 + f;
  return "#" + [n >> 16, (n >> 8) & 255, n & 255].map(x => Math.max(0, Math.min(255, Math.round(x * k))).toString(16).padStart(2, "0")).join(""); }
const C_UN = LOVE ? "#f0dcef" : FORMAL ? "#e5e7eb" : MODERN ? "#e2e8f0" : "#3b4a63",
  C_UN_S = LOVE ? "#cfa3cc" : FORMAL ? "#9ca3af" : MODERN ? "#94a3b8" : "#8fa3c4",
  C_FR = LOVE ? "#ffd77a" : FORMAL ? "#f7c873" : MODERN ? "#fcd979" : "#ffd166",
  C_CUR = LOVE ? "#ff5c7c" : FORMAL ? "#e66b6b" : MODERN ? "#f27b7b" : "#ff4d6d",
  EDGE = LOVE ? "#e9a9cf" : FORMAL ? "#9ca3af" : MODERN ? "#c3cad8" : "#3a4d78";
const HEART = "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z";
const PRE = LOVE ? "💞 " : "";
let W = 800, H = 560, P = {}, R0 = 12, step = 0, playing = false, timer = null, mult = 1;
let view = {k: 1, tx: 0, ty: 0}, world, gHull, gEdge, gTree, gNode, gFx;
let nodeEls = {}, hullEls = [], treeEls = {}, edgeEls = {};
const byId = {}; D.nodes.forEach(n => byId[n.id] = n);

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function shapePts(sym, r) {
  const reg = (n, rot, rr) => { let s = []; for (let i = 0; i < n; i++) { const a = rot + 2 * Math.PI * i / n; s.push((rr * Math.cos(a)).toFixed(2) + "," + (rr * Math.sin(a)).toFixed(2)); } return s.join(" "); };
  switch (sym) {
    case "square": { const q = r * 0.88; return `${-q},${-q} ${q},${-q} ${q},${q} ${-q},${q}`; }
    case "triangle-up": return reg(3, -Math.PI / 2, r * 1.3);
    case "triangle-down": return reg(3, Math.PI / 2, r * 1.3);
    case "diamond": return reg(4, -Math.PI / 2, r * 1.25);
    case "pentagon": return reg(5, -Math.PI / 2, r * 1.15);
    case "hexagon": return reg(6, 0, r * 1.1);
    case "octagon": return reg(8, Math.PI / 8, r * 1.1);
    case "star": { let s = []; for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + Math.PI * i / 5, rr = i % 2 ? r * 0.6 : r * 1.35; s.push((rr * Math.cos(a)).toFixed(2) + "," + (rr * Math.sin(a)).toFixed(2)); } return s.join(" "); }
  }
  return reg(4, 0, r);
}
function hull(pts) {
  if (pts.length < 3) return pts.slice();
  const p = pts.slice().sort((a, b) => a.x - b.x || a.y - b.y);
  const cr = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lo = []; for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  const up = []; for (const q of p.slice().reverse()) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
  lo.pop(); up.pop(); return lo.concat(up);
}
function fit() {
  const st = $("stage"); W = st.clientWidth || 800; H = st.clientHeight || 560;
  const xs = D.nodes.map(n => n.x), ys = D.nodes.map(n => n.y);
  const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
  const pad = 62, dx = (maxx - minx) || 1, dy = (maxy - miny) || 1;
  const s = Math.min((W - 2 * pad) / dx, (H - 2 * pad) / dy);
  const ox = (W - dx * s) / 2, oy = (H - dy * s) / 2;
  D.nodes.forEach(n => P[n.id] = {x: ox + (n.x - minx) * s, y: oy + (n.y - miny) * s});
  let md = 1e9;
  for (let i = 0; i < D.nodes.length; i++) for (let j = i + 1; j < D.nodes.length; j++) {
    const a = P[D.nodes[i].id], b = P[D.nodes[j].id]; md = Math.min(md, Math.hypot(a.x - b.x, a.y - b.y));
  }
  R0 = Math.max(5, Math.min(11, md * 0.16)) * D.scale;
}
const rad = n => R0 * (0.92 + 0.03 * Math.min(n.deg, 10));
const key = (a, b) => a < b ? a + "|" + b : b + "|" + a;
function applyView() { if (world) world.setAttribute("transform", `translate(${view.tx},${view.ty}) scale(${view.k})`); }

function build() {
  const svg = $("svg"); svg.innerHTML = "";
  const defs = el("defs", {}, svg); gDefs = defs; GR = {};
  const f = el("filter", {id: "glow", x: "-60%", y: "-60%", width: "220%", height: "220%"}, defs);
  el("feGaussianBlur", {stdDeviation: "3.6", result: "b"}, f);
  const m = el("feMerge", {}, f); el("feMergeNode", {in: "b"}, m); el("feMergeNode", {in: "SourceGraphic"}, m);
  const sh = el("filter", {id: "soft", x: "-40%", y: "-40%", width: "180%", height: "180%"}, defs);
  el("feDropShadow", {dx: 0, dy: 2, stdDeviation: 2.6, "flood-color": "#1f2937", "flood-opacity": 0.18}, sh);
  const pat = el("pattern", {id: "grid", width: 42, height: 42, patternUnits: "userSpaceOnUse"}, defs);
  if (LOVE) el("circle", {cx: 21, cy: 21, r: 1.6, fill: "#f6b8d8", opacity: 0.8}, pat);
  else if (MODERN) el("path", {d: "M42 0H0V42", fill: "none", stroke: "#e8edf6", "stroke-width": 1, opacity: 1}, pat);
  else el("path", {d: "M42 0H0V42", fill: "none", stroke: FORMAL ? "#eceff3" : "#18294a", "stroke-width": 1}, pat);
  el("rect", {width: "100%", height: "100%", fill: "url(#grid)"}, svg);
  world = el("g", {}, svg);
  gHull = el("g", {}, world); gEdge = el("g", {}, world); gTree = el("g", {}, world);
  gNode = el("g", {}, world); gFx = el("g", {}, world);
  nodeEls = {}; hullEls = []; treeEls = {}; edgeEls = {};
  D.comps.forEach(c => {
    const path = el("path", {fill: c.color, "fill-opacity": LOVE ? 0.16 : FORMAL ? 0.10 : MODERN ? 0.12 : 0.09, stroke: c.color, "stroke-opacity": LOVE ? 0.26 : FORMAL ? 0.28 : MODERN ? 0.22 : 0.17,
      "stroke-width": R0 * 3.6, "stroke-linejoin": "round", "stroke-linecap": "round", d: ""}, gHull);
    const lab = el("text", {class: "clab", fill: c.color}, gHull); lab.style.opacity = 0;
    hullEls.push({path, lab});
  });
  const brs = new Set(D.bridges.map(e => key(e[0], e[1])));
  D.edges.forEach(e => {
    const a = P[e[0]], b = P[e[1]], isBr = brs.has(key(e[0], e[1]));
    const ln = el("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: isBr ? BRIDGE : EDGE,
      "stroke-width": isBr ? 5 : (LOVE ? 3.6 : (MODERN ? 2.8 : 2.2)), "stroke-linecap": "round", filter: isBr ? GLOW : ""}, gEdge);
    if (LOVE && !isBr) ln.setAttribute("stroke-dasharray", "1 8");
    edgeEls[key(e[0], e[1])] = ln;
  });
  D.removed.forEach(e => {
    const a = P[e[0]], b = P[e[1]];
    el("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: REM, "stroke-width": 3.2,
      "stroke-dasharray": "9 7", "stroke-linecap": "round"}, gEdge);
  });
  D.added.forEach(e => {
    const a = P[e[0]], b = P[e[1]];
    el("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: ADD, "stroke-width": 5,
      "stroke-linecap": "round", filter: GLOW}, gEdge);
  });
  const mid = (a, b, emo, sz) => { const p = P[a], q = P[b];
    const t = el("text", {x: (p.x + q.x) / 2, y: (p.y + q.y) / 2, "text-anchor": "middle", "dominant-baseline": "central", "font-size": sz || 17}, gEdge);
    t.textContent = emo; };
  if (LOVE) { D.bridges.forEach(e => mid(e[0], e[1], "🔗")); D.added.forEach(e => mid(e[0], e[1], "💚", 21)); D.removed.forEach(e => mid(e[0], e[1], "💔", 21)); }
  D.nodes.forEach(n => {
    const r = rad(n), c = D.comps[n.comp];
    const g = el("g", {class: "node", transform: `translate(${P[n.id].x},${P[n.id].y})`}, gNode);
    el("title", {}, g).textContent = `${n.id} · derajat ${n.deg} · ${c.name} (${c.size} anggota)`;
    const halo = el("circle", {r: r * (SHINE ? 2.6 : 2.0), fill: SHINE ? haloPaint(c.color) : c.color, opacity: 0}, g);
    const ring = el("circle", {r: r * 1.35, class: "ring"}, g); ring.style.display = "none";
    const body = el("g", {class: "body"}, g);
    let shape, emo = null;
    if (LOVE) {
      const sc = r * 0.125;
      shape = el("path", {class: "shape", d: HEART, transform: `scale(${sc}) translate(-12,-12.2)`, fill: paint(C_UN), stroke: C_UN_S,
        "stroke-width": 2.4, "vector-effect": "non-scaling-stroke", "stroke-linejoin": "round"}, body);
      emo = el("text", {class: "emo", y: r * 0.08, "text-anchor": "middle", "dominant-baseline": "central", "font-size": r * 1.0}, body);
      emo.textContent = c.emoji;
    } else {
      const isStart = anim && N > 0 && n.id === D.events[0].node, isEnd = anim && N > 0 && n.id === D.events[N - 1].node;
      if (isStart || isEnd)
        shape = el("polygon", {class: "shape", points: isStart ? shapePts("square", r * 1.15) : shapePts("diamond", r * 0.95),
          fill: paint(C_UN), stroke: C_UN_S, "stroke-width": 2.4, "stroke-linejoin": "round"}, body);
      else
        shape = el("circle", {class: "shape", r: r, fill: paint(C_UN), stroke: C_UN_S, "stroke-width": 2.2}, body);
    }
    let spk = null;
    if (SHINE) {   // kilap (specular) + kerlip bintang kecil
      el("ellipse", {cx: -r * 0.3, cy: -r * 0.36, rx: r * 0.32, ry: r * 0.17, fill: "#fff", opacity: 0.75,
        transform: `rotate(-32 ${-r * 0.3} ${-r * 0.36})`}, body);
      const sg = el("g", {transform: `translate(${r * 0.62},${-r * 0.62}) scale(${Math.max(0.7, r / 8)})`}, g);
      spk = el("path", {class: "spk", d: "M0,-5.5 L1.4,-1.4 L5.5,0 L1.4,1.4 L0,5.5 L-1.4,1.4 L-5.5,0 L-1.4,-1.4 Z", fill: "#ffffff"}, sg);
      spk.style.animationDelay = (-Math.random() * 2.6) + "s"; spk.style.display = "none";
    }
    const lab = el("text", {y: -r * 1.55 - 4, "text-anchor": "middle", fill: LOVE ? "#4a1d44" : FORMAL ? "#111827" : MODERN ? "#243049" : "#fff", "font-size": 14}, g);
    lab.textContent = n.id;
    const sub = el("text", {y: r * 1.55 + 13, "text-anchor": "middle", fill: LOVE ? "#a0548a" : FORMAL ? "#4b5563" : MODERN ? "#5d6b85" : "#ffd166", "font-size": 12}, g);
    sub.textContent = "d=" + n.deg;
    nodeEls[n.id] = {g, halo, ring, body, shape, emo, lab, sub, r, spk};
  });
  applyView();
}

function stateAt(k) {
  const done = {}, order = [], tree = []; let cur = null, front = [];
  for (let i = 0; i < k; i++) {
    const e = D.events[i]; done[e.node] = {comp: e.comp, order: i + 1}; order.push(e.node);
    if (e.parent !== null) tree.push([e.parent, e.node, e.comp]);
    cur = e.node; front = e.frontier;
  }
  return {done, order, tree, cur, front};
}
function addTree(p, c, color, animate) {
  const a = P[p], b = P[c];
  const ln = el("line", {x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: LIGHT ? shade(color, -0.15) : color, "stroke-width": FORMAL ? 3.5 : 4.5,
    "stroke-linecap": "round", filter: GLOW}, gTree);
  if (animate) {
    const L = Math.hypot(b.x - a.x, b.y - a.y);
    ln.style.strokeDasharray = L; ln.style.strokeDashoffset = L; ln.getBoundingClientRect();
    ln.style.transition = "stroke-dashoffset .5s ease-out"; ln.style.strokeDashoffset = 0;
    if (LOVE) travel(a, b);
  }
  return ln;
}
function travel(a, b) {
  const t = el("text", {x: a.x, y: a.y, "text-anchor": "middle", "dominant-baseline": "central", "font-size": 20}, gFx);
  t.textContent = "💗"; const t0 = performance.now();
  (function f(now) { const u = Math.min(1, (now - t0) / 520);
    t.setAttribute("x", a.x + (b.x - a.x) * u); t.setAttribute("y", a.y + (b.y - a.y) * u - Math.sin(u * Math.PI) * 14);
    if (u < 1) requestAnimationFrame(f); else t.remove(); })(t0);
}
function hullFor(idx, ids, label) {
  const h = hullEls[idx]; if (!h) return;
  if (!ids.length) { h.path.setAttribute("d", ""); h.lab.style.opacity = 0; return; }
  const pts = ids.map(i => P[i]), hp = hull(pts);
  let d;
  if (hp.length === 1) d = `M${hp[0].x},${hp[0].y} l0.01,0`;
  else if (hp.length === 2) d = `M${hp[0].x},${hp[0].y} L${hp[1].x},${hp[1].y}`;
  else d = "M" + hp.map(p => p.x + "," + p.y).join(" L") + " Z";
  h.path.setAttribute("d", d);
  const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length, top = Math.min(...pts.map(p => p.y));
  h.lab.setAttribute("x", cx); h.lab.setAttribute("y", top - R0 * 3.3);
  h.lab.textContent = label; h.lab.style.opacity = 0.95;
}
function ripple(id) {
  const n = nodeEls[id], p = P[id]; if (!n) return;
  const c = el("circle", {cx: p.x, cy: p.y, r: n.r * 1.3, class: "ripple"}, gFx);
  c.addEventListener("animationend", () => c.remove());
  if (LOVE) {
    const em = ["❤️", "💕", "💗", "✨", "💖", "💞"];
    for (let i = 0; i < 7; i++) {
      const t = el("text", {x: p.x, y: p.y, class: "pt", "font-size": 14 + Math.random() * 8}, gFx);
      t.textContent = em[i % em.length];
      t.style.setProperty("--dx", (Math.random() * 90 - 45) + "px"); t.style.setProperty("--dy", (-40 - Math.random() * 50) + "px");
      t.addEventListener("animationend", () => t.remove());
    }
  }
}
function render(k, fx) {
  if (!anim) {
    D.nodes.forEach(n => {
      const e = nodeEls[n.id], c = D.comps[n.comp];
      e.shape.setAttribute("fill", paint(c.color)); e.shape.setAttribute("stroke", LIGHT ? shade(c.color, -0.22) : "#fff");
      e.shape.setAttribute("filter", GLOW); e.halo.setAttribute("opacity", 0);
      if (e.spk) e.spk.style.display = "";
      if (e.emo) { e.emo.textContent = c.emoji; e.emo.style.opacity = 1; }
    });
    D.comps.forEach((c, i) => hullFor(i, D.nodes.filter(n => n.comp === i).map(n => n.id), `${c.name} · ${c.size} anggota`));
    return;
  }
  const S = stateAt(k), fr = new Set(S.front);
  D.nodes.forEach(n => {
    const e = nodeEls[n.id], c = D.comps[n.comp], d = S.done[n.id];
    let fill = C_UN, stroke = C_UN_S, sc = 1, ring = false, halo = 0, filt = "";
    if (n.id === S.cur) { fill = C_CUR; stroke = LIGHT ? shade(C_CUR, -0.22) : "#fff"; sc = 1.55; halo = 0.3 * HA; filt = GLOW; }
    else if (d) { fill = c.color; stroke = LIGHT ? shade(c.color, -0.22) : "#fff"; halo = 0; filt = GLOW; }
    else if (fr.has(n.id)) { fill = C_FR; stroke = "#fff3c4"; ring = true; sc = 1.12; }
    e.shape.setAttribute("fill", paint(fill)); e.shape.setAttribute("stroke", stroke);
    e.shape.setAttribute("filter", filt); e.body.style.transform = `scale(${sc})`;
    e.ring.style.display = ring ? "" : "none";
    e.halo.setAttribute("opacity", SHINE ? (n.id === S.cur ? 0.9 : (d ? 0.6 : (fr.has(n.id) ? 0.45 : 0))) : halo);
    e.halo.setAttribute("fill", SHINE ? haloPaint(n.id === S.cur ? C_CUR : (d ? c.color : (fr.has(n.id) ? C_FR : c.color))) : (n.id === S.cur ? C_CUR : c.color));
    if (e.spk) e.spk.style.display = (d || n.id === S.cur) ? "" : "none";
    if (e.emo) {
      e.emo.textContent = n.id === S.cur ? "😍" : (d ? c.emoji : (fr.has(n.id) ? "👋" : c.emoji));
      e.emo.style.opacity = (d || n.id === S.cur || fr.has(n.id)) ? 1 : 0.5;
    }
    const tag = n.id === D.events[0].node ? "MULAI · " : (n.id === D.events[N - 1].node ? "TERAKHIR · " : "");
    e.sub.textContent = tag + (d ? `#${d.order} · d=${n.deg}` : (fr.has(n.id) ? "menunggu" : "d=" + n.deg));
  });
  const want = {}; S.tree.forEach(t => want[key(t[0], t[1])] = t);
  for (const kk in treeEls) if (!want[kk]) { treeEls[kk].remove(); delete treeEls[kk]; }
  for (const kk in want) if (!treeEls[kk]) treeEls[kk] = addTree(want[kk][0], want[kk][1], D.comps[want[kk][2]].color, fx);
  D.comps.forEach((c, i) => {
    const ids = D.nodes.filter(n => n.comp === i && S.done[n.id]).map(n => n.id);
    hullFor(i, ids, `${c.name} · ${ids.length}/${c.size}`);
  });
  if (fx && S.cur) ripple(S.cur);
  // panel
  const q = $("q"); q.innerHTML = "";
  if (!S.front.length) { q.textContent = k ? "kosong" : "—"; }
  S.front.forEach((id, i) => { const s = document.createElement("span"); s.className = "chip"; s.textContent = id; q.appendChild(s); q.appendChild(document.createTextNode(" ")); });
  const v = $("vis"); v.innerHTML = "";
  S.order.forEach(id => { const s = document.createElement("span"); const c = D.comps[S.done[id].comp];
    s.className = "chip v" + (id === S.cur ? " cur" : ""); s.style.borderColor = c.color; s.textContent = id;
    v.appendChild(s); v.appendChild(document.createTextNode(" ")); });
  // header
  const wadah = D.method === "BFS" ? "antrean (FIFO)" : "tumpukan (LIFO)";
  const head = $("head");
  if (k === 0) head.innerHTML = `${PRE}<b>${D.method}</b> siap dimulai · ${N} langkah · ${D.comps.length} kelompok (${D.comps.map(c => c.size).join(", ")} anggota). Tekan ▶ atau geser slider. Titik kuning akan menunggu di ${wadah}. Titik awal dan titik terakhir ditandai bentuk khusus (lihat legenda).`;
  else {
    const e = D.events[k - 1], prev = k > 1 && D.events[k - 2].comp === e.comp ? D.events[k - 2].frontier.filter(x => x !== e.node) : [];
    const baru = e.frontier.filter(x => !prev.includes(x) && x !== e.node);
    const aksi = D.method === "BFS" ? "diambil dari DEPAN antrean" : "diambil dari PUNCAK tumpukan";
    let t = e.parent === null ? `Kelompok baru dimulai dari <b>${e.node}</b>. ` : `<b>${e.node}</b> ${aksi} (ditemukan lewat ${e.parent}). `;
    t += baru.length ? `Tetangga baru masuk ${wadah}: <b>${baru.join(", ")}</b>.` : `Tidak ada tetangga baru.`;
    if (!e.frontier.length) t += ` ✔ ${wadah} kosong → kelompok ${e.comp + 1} selesai.`;
    head.innerHTML = `${PRE}<b>${D.method} · langkah ${k}/${N}</b> — ` + t;
  }
  $("cnt").textContent = `${k} / ${N}`;
}
function legend() {
  const b = $("legbody"); b.innerHTML = "";
  const item = (svgInner, text) => { const d = document.createElement("div"); d.className = "it";
    d.innerHTML = `<svg width="22" height="22" viewBox="-11 -11 22 22">${svgInner}</svg><span>${text}</span>`; b.appendChild(d); };
  const poly = (sym, fill, stroke) => LOVE
    ? `<path d="${HEART}" transform="scale(.52) translate(-12,-12.2)" fill="${paint(fill)}" stroke="${stroke || "#fff"}" stroke-width="1.6" vector-effect="non-scaling-stroke"/>`
    : `<circle r="6.5" fill="${paint(fill)}" stroke="${stroke || "#fff"}" stroke-width="1.5"/>`;
  if (anim) {
    const w = D.method === "BFS" ? "antrean" : "tumpukan";
    item(poly("circle", C_UN, C_UN_S), "Belum ditemukan");
    item(poly("circle", C_FR, "#fff3c4"), `Menunggu di ${w}`);
    item(poly("circle", C_CUR), "Sedang diproses");
    item(`<polygon points="${shapePts("square", 6.2)}" fill="#cbd5e1" stroke="#64748b" stroke-width="1.5" stroke-linejoin="round"/>`, "Titik awal");
    item(`<polygon points="${shapePts("diamond", 5.4)}" fill="#cbd5e1" stroke="#64748b" stroke-width="1.5" stroke-linejoin="round"/>`, "Titik terakhir");
  }
  D.comps.forEach(c => item(poly(c.symbol, c.color), `${LOVE ? c.emoji + " " : ""}${c.name} (${c.size} anggota)`));
  if (LOVE && D.bridges.length) item(`<text y="5" text-anchor="middle" font-size="15">🔗</text>`, "Jembatan penghubung");
  if (LOVE && D.added.length) item(`<text y="5" text-anchor="middle" font-size="15">💚</text>`, "Pertemanan baru");
  if (LOVE && D.removed.length) item(`<text y="5" text-anchor="middle" font-size="15">💔</text>`, "Pertemanan putus");
  if (anim) item(`<line x1="-9" y1="0" x2="9" y2="0" stroke="#4cc9f0" stroke-width="4"/>`, "Sisi pohon penelusuran");
  if (D.bridges.length) item(`<line x1="-9" y1="0" x2="9" y2="0" stroke="${BRIDGE}" stroke-width="4.5"/>`, "Jembatan");
  if (D.added.length) item(`<line x1="-9" y1="0" x2="9" y2="0" stroke="${ADD}" stroke-width="4"/>`, "Hubungan baru");
  if (D.removed.length) item(`<line x1="-9" y1="0" x2="9" y2="0" stroke="${REM}" stroke-width="3" stroke-dasharray="4 3"/>`, "Hubungan dihapus");
  const d = document.createElement("div"); d.style.cssText = "color:var(--sub);margin-top:4px"; d.textContent = "d = derajat (jumlah hubungan)"; b.appendChild(d);
}
function go(k, fx) { step = Math.max(0, Math.min(N, k)); $("slider").value = step; render(step, fx); }
function stop() { playing = false; clearTimeout(timer); $("play").textContent = "▶"; }
function tick() {
  if (!playing) return;
  if (step >= N) { stop(); return; }
  go(step + 1, true);
  if (step >= N) { stop(); return; }
  timer = setTimeout(tick, D.speed / mult);
}
function play() { if (step >= N) go(0, false); playing = true; $("play").textContent = "⏸"; timer = setTimeout(tick, 350); }
function zoomBy(f) { const nk = Math.min(6, Math.max(0.4, view.k * f)), ff = nk / view.k;
  view.tx = W / 2 - (W / 2 - view.tx) * ff; view.ty = H / 2 - (H / 2 - view.ty) * ff; view.k = nk; applyView(); }

function decor() {
  const d = $("decor");
  if (false) {
    const cols = ["#8ea7ff", "#7fd1e8", "#c3a6f5", "#f5a9d0", "#8fd9b6", "#ffc98a"];
    for (let i = 0; i < 22; i++) { const s = document.createElement("span"); s.className = "gl";
      s.textContent = i % 3 ? "✦" : "✧"; s.style.left = (Math.random() * 96) + "%"; s.style.top = (Math.random() * 92) + "%";
      s.style.color = cols[i % cols.length]; s.style.fontSize = (9 + Math.random() * 12) + "px";
      s.style.animationDelay = (-Math.random() * 3.4) + "s"; s.style.animationDuration = (2.6 + Math.random() * 2.4) + "s"; d.appendChild(s); }
    return;
  }
  if (!LOVE || d.children.length) return;
  const em = ["💗", "✨", "🌸", "💕", "🦋", "💖", "⭐", "🍀"];
  for (let i = 0; i < 16; i++) { const s = document.createElement("span"); s.textContent = em[i % em.length];
    s.style.left = (Math.random() * 96) + "%"; s.style.animationDuration = (9 + Math.random() * 10) + "s";
    s.style.animationDelay = (-Math.random() * 15) + "s"; s.style.fontSize = (14 + Math.random() * 16) + "px"; d.appendChild(s); }
}
function init() {
  fit(); build(); legend();
  if (anim) { $("panel").style.display = "flex"; $("player").style.display = "flex";
    $("qlab").textContent = D.method === "BFS" ? "Antrean (depan → belakang):" : "Tumpukan (puncak → dasar):";
    $("slider").max = N; }
  else { $("head").innerHTML = D.title ? `${PRE}<b>${D.title}</b>` : ""; }
  decor();
  if (W < 650) $("leg").open = false;
  render(step, false);
}
let first = true;
function boot() {
  init();
  if (first) {
    first = false;
    const svg = $("svg");
    svg.addEventListener("wheel", e => { e.preventDefault(); const r = svg.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top, f = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      const nk = Math.min(6, Math.max(0.4, view.k * f)), ff = nk / view.k;
      view.tx = px - (px - view.tx) * ff; view.ty = py - (py - view.ty) * ff; view.k = nk; applyView(); }, {passive: false});
    let drag = null;
    svg.addEventListener("pointerdown", e => { drag = {x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty}; svg.style.cursor = "grabbing"; });
    window.addEventListener("pointermove", e => { if (drag) { view.tx = drag.tx + e.clientX - drag.x; view.ty = drag.ty + e.clientY - drag.y; applyView(); } });
    window.addEventListener("pointerup", () => { drag = null; svg.style.cursor = "grab"; });
    svg.addEventListener("dblclick", () => { view = {k: 1, tx: 0, ty: 0}; applyView(); });
    $("zin").onclick = () => zoomBy(1.25); $("zout").onclick = () => zoomBy(0.8);
    $("zreset").onclick = () => { view = {k: 1, tx: 0, ty: 0}; applyView(); };
    $("play").onclick = () => playing ? stop() : play();
    $("bn").onclick = () => { stop(); go(step + 1, true); };
    $("bp").onclick = () => { stop(); go(step - 1, false); };
    $("b0").onclick = () => { stop(); go(0, false); };
    $("b1").onclick = () => { stop(); go(N, false); };
    $("slider").oninput = e => { stop(); go(+e.target.value, false); };
    $("spd").onchange = e => { mult = +e.target.value; };
    let rt = null;
    window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { const keep = step; init(); go(keep, false); }, 150); });
    if (anim && D.autoplay && N > 0) setTimeout(play, 700);
  }
}
try { boot(); const stt = document.getElementById("status"); if (stt) stt.remove(); }
catch (e) { showErr(e && e.message ? e.message : String(e)); }
</script></body></html>
"""


# ======================================================================
# MODE CADANGAN: grafik murni Streamlit (st.graphviz_chart), tanpa JavaScript buatan sendiri
# ======================================================================
GV_SHAPES = ["circle"] * 8


def _q(v):
    return '"' + str(v).replace('"', '\\"') + '"'


def dot_static(G, comps, added=(), removed=()):
    pal = MODERN_PALETTE
    comp_of = {v: i for i, c in enumerate(comps) for v in c}
    br = {frozenset(e) for e in nx.bridges(G)}
    add = {frozenset(e) for e in added}
    L = ["graph G {", 'graph [overlap=false, splines=true, bgcolor="transparent"];',
         'node [style=filled, fontname="Helvetica", fontsize=12, fontcolor="#1e2a44", color="white", penwidth=1.5];',
         'edge [color="#94a3b8", penwidth=1.6];']
    for v in G.nodes:
        i = comp_of[v]
        L.append(f'{_q(v)} [shape={GV_SHAPES[i % 8]}, fillcolor="{pal[i % len(pal)]}", tooltip="derajat {G.degree(v)}"];')
    for a, b in G.edges:
        k = frozenset((a, b))
        extra = ' [color="#4cc38a", penwidth=4]' if k in add else (' [color="#f97316", penwidth=4]' if k in br else "")
        L.append(f"{_q(a)} -- {_q(b)}{extra};")
    for a, b in removed:
        if not G.has_edge(a, b):
            L.append(f'{_q(a)} -- {_q(b)} [color="#e66b6b", style=dashed, penwidth=2.5];')
    L.append("}")
    return "\n".join(L)


def dot_state(G, events, k):
    pal = MODERN_PALETTE
    done, tree, cur, front = {}, [], None, []
    for e in events[:k]:
        done[e["node"]] = e["comp"]
        if e["parent"] is not None:
            tree.append(frozenset((e["parent"], e["node"])))
        cur, front = e["node"], e["frontier"]
    comp_of = {e["node"]: e["comp"] for e in events}
    L = ["graph G {", 'graph [overlap=false, splines=true, bgcolor="transparent"];',
         'node [style=filled, fontname="Helvetica", fontsize=12, color="white", penwidth=1.5];',
         'edge [color="#cbd5e1", penwidth=1.5];']
    for v in G.nodes:
        i = comp_of.get(v, 0)
        if v == cur:
            fill, fc = "#f27b7b", "#1e2a44"
        elif v in done:
            fill, fc = pal[done[v] % len(pal)], "#1e2a44"
        elif v in front:
            fill, fc = "#fcd979", "#1e2a44"
        else:
            fill, fc = "#e2e8f0", "#1e2a44"
        shp = "box" if (events and v == events[0]["node"]) else ("diamond" if (events and v == events[-1]["node"]) else "circle")
        L.append(f'{_q(v)} [shape={shp}, fillcolor="{fill}", fontcolor="{fc}"];')
    ts = set(tree)
    for a, b in G.edges:
        extra = ' [color="#1e2a44", penwidth=4]' if frozenset((a, b)) in ts else ""
        L.append(f"{_q(a)} -- {_q(b)}{extra};")
    L.append("}")
    return "\n".join(L)


# ======================================================================
# APLIKASI STREAMLIT
# ======================================================================
import time

import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


VERSI = "v17 · tampilan tenang dan profesional"
st.set_page_config(page_title="Community Connection Lab", layout="wide")


def init_graph(G, label, info):
    st.session_state.G0 = G.copy()
    st.session_state.G1 = G.copy()
    st.session_state.log = []
    st.session_state.info = info
    st.session_state.label = label


# ======================================================================
# Sidebar
# ======================================================================
with st.sidebar:
    st.header("Pengaturan")
    pilihan = list(DATASETS) + ["Unggah CSV sendiri (data nyata milik Anda)"]
    nama = st.selectbox("Dataset", pilihan)
    if nama in DATASETS:
        if st.session_state.get("label") != nama:
            init_graph(load_dataset(nama), nama, DATASETS[nama])
    else:
        up = st.file_uploader("CSV dengan 2 kolom (titik A, titik B)", type="csv")
        if up is None:
            st.info("Unggah CSV untuk memakai data sendiri.")
            st.stop()
        df = pd.read_csv(up)
        ca = st.selectbox("Kolom titik A", df.columns, index=0)
        cb = st.selectbox("Kolom titik B", df.columns, index=min(1, len(df.columns) - 1))
        key = f"upload:{up.name}:{ca}:{cb}"
        if st.session_state.get("label") != key:
            init_graph(load_from_edgelist(df, ca, cb), key,
                       {"sumber": f"Berkas {up.name}", "arti_titik": "sesuai data Anda",
                        "arti_sisi": "sesuai data Anda"})

    G0, G1 = st.session_state.G0, st.session_state.G1
    THEME = "modern"
    algo = st.radio("Algoritma penelusuran", ["BFS", "DFS"], horizontal=True)
    titik = sorted(G1.nodes, key=str)
    start = st.selectbox("Titik awal penelusuran", titik)
    speed = st.slider("Jeda dasar animasi (ms/langkah)", 300, 2500, 1000, 100,
                      help="Kecepatan juga bisa diubah langsung di pemutar (0.5× – 3×).")
    autoplay = st.checkbox("Putar animasi otomatis saat dibuka", value=True)
    spasi = st.slider("Kerenggangan titik", 0.4, 2.5, 1.4, 0.1,
                      help="Makin besar, makin renggang jarak antar titik.")
    ukuran = st.slider("Ukuran titik", 0.5, 1.6, 1.1, 0.1)
    aman = st.checkbox("Mode cadangan (tanpa JavaScript)", value=False,
                       help="Aktifkan bila grafik tampil kosong. Grafik digambar langsung oleh Streamlit.")

    st.divider()
    st.subheader("Ubah hubungan")
    op = st.radio("Aksi", ["Tambah hubungan", "Hapus hubungan"], horizontal=True)
    if op == "Tambah hubungan":
        a = st.selectbox("Titik A", titik, key="add_a")
        b = st.selectbox("Titik B", titik, index=min(1, len(titik) - 1), key="add_b")
        pair, kode = (a, b), "tambah"
    else:
        edges = sorted((tuple(sorted(e, key=str)) for e in G1.edges), key=str)
        pair = st.selectbox("Pilih hubungan", edges, format_func=lambda e: f"{e[0]} — {e[1]}") if edges else None
        kode = "hapus"
    if st.button("Terapkan perubahan", type="primary", disabled=pair is None):
        ok, pesan, dampak = apply_change(st.session_state.G1, kode, *pair)
        if ok:
            st.session_state.log.append((kode, pair[0], pair[1], pesan, dampak))
            st.rerun()
        else:
            st.warning(pesan)
    if st.button("Kembalikan ke kondisi awal"):
        st.session_state.G1 = st.session_state.G0.copy()
        st.session_state.log = []
        st.rerun()
    for _, _, _, pesan, _ in st.session_state.log:
        st.caption("• " + pesan)
    st.divider()
    with st.expander("Info teknis"):
        st.code(__file__)

# ======================================================================
# Perhitungan utama
# ======================================================================
pos = make_layout(G0, spasi=spasi)
log = st.session_state.log
comps0 = find_components(G0, algo)
comps1 = find_components(G1, algo)
added = [(a, b) for k, a, b, _, _ in log if k == "tambah" and G1.has_edge(a, b)]
removed = [(a, b) for k, a, b, _, _ in log if k == "hapus" and not G1.has_edge(a, b)]


def show(G, comps, title, height, **kw):
    if aman:
        st.markdown(f"**{title}**")
        st.graphviz_chart(dot_static(G, ordered(comps), kw.get("added", ()), kw.get("removed", ())))
        return
    components.html(graph_html(G, pos, ordered(comps), mode="static", title=title,
                                   scale=ukuran, theme=THEME, **kw), height=height)


if THEME in ("formal", "modern"):
    _h1 = "color:#2b4670;"
    st.markdown(f"<h1 style='margin-bottom:0;{_h1}'>Community Connection Lab</h1>"
                "<p style='font-size:1.05rem;margin-top:2px'>Analisis Komponen Terhubung pada Jaringan "
                "Pertemanan menggunakan Algoritma BFS dan DFS</p>", unsafe_allow_html=True)
else:
    _grad = ("linear-gradient(90deg,#ff4d8d,#c77dff,#4cc9f0)" if THEME == "love"
             else "linear-gradient(90deg,#4cc9f0,#c77dff,#f72585)")
    _judul = "💞 Community Connection Lab 💞" if THEME == "love" else "Community Connection Lab"
    st.markdown(
        f"<h1 style='background:{_grad};-webkit-background-clip:text;"
        f"-webkit-text-fill-color:transparent;margin-bottom:0'>{_judul}</h1>", unsafe_allow_html=True)
st.caption(f"Ubah hubungan pertemanan, lalu amati kelompok yang bergabung atau terpisah. "
           f"Algoritma: BFS & DFS.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1 · Model & data", "2 · Kelompok & derajat", "3 · Sebelum vs sesudah",
    "4 · Animasi BFS/DFS", "5 · Validasi & tafsir", "6 · Tentang algoritma"])

# ---------------------------------------------------------------- Tab 1
with tab1:
    info = st.session_state.info
    st.subheader("Masalah dan model graf")
    st.markdown(f"""
- **Titik** : {info['arti_titik']}
- **Sisi** : {info['arti_sisi']} (graf tak berarah, tanpa bobot)
- **Pertanyaan** : siapa saja anggota tiap kelompok, siapa yang paling banyak terhubung,
  dan hubungan mana yang menyatukan atau memisahkan kelompok?
- **Sumber data** : {info['sumber']}
""")
    st.info("Data ini adalah data jaringan nyata yang dipublikasikan peneliti, bukan data buatan. "
            "Derajat dan komponen hanya merangkum struktur hubungan yang tercatat; "
            "keduanya tidak membuktikan pengaruh sosial seseorang.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Titik", G0.number_of_nodes())
    c2.metric("Hubungan awal", G0.number_of_edges())
    c3.metric("Kelompok awal", len(comps0))
    st.dataframe(pd.DataFrame(sorted(G0.edges, key=str), columns=["Titik A", "Titik B"]),
                 use_container_width=True, height=250)
    with st.expander("Alur presentasi yang disarankan"):
        st.markdown("""
1. **Model dan data** (tab ini): jelaskan arti titik dan sisi, sumber data, serta batasannya.
2. **Animasi** (tab 4): jalankan BFS, lalu DFS. Tunjukkan titik awal, titik terakhir, dan kelompok yang tumbuh.
3. **Kelompok dan derajat** (tab 2): tunjukkan jembatan (oranye) dan titik berderajat tertinggi.
4. **Ubah satu hubungan** di sidebar, lalu buka **Sebelum vs sesudah** (tab 3).
5. **Validasi dan tafsir** (tab 5): tunjukkan semua centang hijau dan batas kesimpulan.
""")

# ---------------------------------------------------------------- Tab 2
with tab2:
    st.caption("Roda mouse = zoom · seret = geser · klik dua kali = atur ulang · arahkan kursor ke titik untuk detail.")
    show(G1, comps1, "Kelompok pertemanan (kondisi saat ini)", 640, added=added, removed=removed)
    ord1 = ordered(comps1)
    ukur = pd.DataFrame([{"Kelompok": i + 1, "Anggota": len(c),
                          "Daftar anggota": ", ".join(map(str, sorted(c, key=str)))} for i, c in enumerate(ord1)])
    deg = dict(G1.degree())
    komp_no = {v: i + 1 for i, c in enumerate(ord1) for v in c}
    tabel_deg = pd.DataFrame({"Titik": list(G1.nodes), "Derajat": [deg[v] for v in G1.nodes],
                              "Kelompok": [komp_no[v] for v in G1.nodes]}).sort_values(
        ["Derajat", "Titik"], ascending=[False, True])
    cA, cB = st.columns([3, 2])
    cA.markdown("**Ukuran tiap kelompok**")
    cA.dataframe(ukur, use_container_width=True, hide_index=True)
    cB.markdown("**Derajat tiap titik**")
    cB.dataframe(tabel_deg, use_container_width=True, hide_index=True, height=300)
    br, ap = connectors(G1)
    st.markdown("**Penghubung di dalam kelompok** (titik/hubungan yang jika hilang memecah kelompok)")
    st.write("Jembatan:", ", ".join(f"{a}—{b}" for a, b in br) or "tidak ada")
    st.write("Titik penghubung:", ", ".join(map(str, ap)) or "tidak ada")

# ---------------------------------------------------------------- Tab 3
with tab3:
    cL, cR = st.columns(2)
    with cL:
        show(G0, comps0, "SEBELUM", 560)
    with cR:
        show(G1, comps1, "SESUDAH", 560, added=added, removed=removed)
    s0, s1 = stats(G0, comps0), stats(G1, comps1)
    tbl = pd.DataFrame({"Sebelum": {k: str(v) for k, v in s0.items()},
                        "Sesudah": {k: str(v) for k, v in s1.items()}})
    tbl["Berubah?"] = ["Ya" if tbl.loc[k, "Sebelum"] != tbl.loc[k, "Sesudah"] else "" for k in tbl.index]
    st.dataframe(tbl, use_container_width=True)
    st.markdown("### Apa yang terjadi?")
    for t in describe_changes(compare(comps0, comps1), log):
        st.success(t)
    for _, _, _, pesan, dampak in log:
        st.markdown(f"- **{pesan}** {dampak}")
    d0, d1 = dict(G0.degree()), dict(G1.degree())
    ubah = [{"Titik": v, "Derajat sebelum": d0[v], "Derajat sesudah": d1[v]} for v in G0.nodes if d0[v] != d1[v]]
    if ubah:
        st.markdown("**Titik yang derajatnya berubah (penghubung perubahan)**")
        st.dataframe(pd.DataFrame(ubah), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- Tab 4
with tab4:
    pilih = st.radio("Graf yang dianimasikan", ["Sesudah perubahan", "Sebelum perubahan"], horizontal=True)
    Gt = G1 if pilih.startswith("Sesudah") else G0
    if log and pilih.startswith("Sesudah"):
        st.info(f"Animasi ini memakai graf SETELAH {len(log)} perubahan hubungan, sehingga jumlah kelompok "
                f"({len(comps1)}) bisa berbeda dari data awal ({len(comps0)}). "
                f"Pilih 'Sebelum perubahan' di atas atau klik 'Kembalikan ke kondisi awal' di sidebar untuk melihat data asli.")
    events, comps_t = traverse(Gt, algo, start)
    wadah = "antrean (queue, FIFO)" if algo == "BFS" else "tumpukan (stack, LIFO)"
    st.markdown(
        f"Animasi berjalan otomatis. Pakai **▶/⏸**, langkah **◀ ▶❙**, **slider**, dan pilihan kecepatan. "
        f"**{algo}** memakai **{wadah}**. Kuning = menunggu giliran, merah = sedang diproses, "
        f"garis tebal = sisi pohon penelusuran, area berwarna = kelompok yang sedang tumbuh. "
        f"Titik awal dan titik terakhir penelusuran ditandai dengan bentuk khusus (lihat legenda). "
        f"Roda mouse untuk zoom, seret untuk menggeser.")
    if aman:
        n_langkah = len(events)
        k = st.slider("Langkah", 0, n_langkah, 0)
        tempat = st.empty()
        tempat.graphviz_chart(dot_state(Gt, events, k))
        if k:
            st.caption(events[k - 1]["note"])
        if st.button("Putar otomatis"):
            for kk in range(n_langkah + 1):
                tempat.graphviz_chart(dot_state(Gt, events, kk))
                time.sleep(speed / 1000)
    else:
        components.html(graph_html(Gt, pos, comps_t, mode="anim", events=events, method=algo,
                                       speed_ms=speed, scale=ukuran, autoplay=autoplay, theme=THEME), height=820)
    st.markdown("**Log langkah penelusuran**")
    st.dataframe(pd.DataFrame([{"Langkah": e["step"] + 1, "Kelompok": e["comp"] + 1, "Dikunjungi": e["node"],
                                "Lewat": e["parent"] or "(awal)",
                                "Isi " + algo + " setelahnya": ", ".join(map(str, e["frontier"])) or "kosong"}
                               for e in events]), use_container_width=True, hide_index=True, height=300)

# ---------------------------------------------------------------- Tab 5
with tab5:
    st.subheader("Validasi otomatis")
    for label, g, comps in [("Sebelum", G0, comps0), ("Sesudah", G1, comps1)]:
        st.markdown(f"**{label}** (BFS/DFS buatan sendiri vs fungsi NetworkX)")
        for k, v in validate(g, comps).items():
            (st.success if v else st.error)(("✔ " if v else "✘ ") + k)
    same = {frozenset(c) for c in find_components(G1, "BFS")} == {frozenset(c) for c in find_components(G1, "DFS")}
    (st.success if same else st.error)(("✔ " if same else "✘ ") + "BFS dan DFS menghasilkan kelompok yang sama (hanya urutan kunjungan yang berbeda)")
    st.subheader("Tafsir dan batas kesimpulan")
    st.markdown("""
- **Kelompok (komponen terhubung)** = himpunan titik yang saling bisa dicapai lewat rangkaian hubungan.
- **Derajat** = banyaknya hubungan langsung seseorang di data.
- **Jembatan / titik penghubung** = bagian yang jika hilang memutus kelompok; inilah penghubung antarkelompok.
- **Batas**: hanya struktur hubungan yang *tercatat* yang dianalisis. Derajat tinggi tidak otomatis berarti
  berpengaruh; hubungan tak tercatat tidak terlihat; dan data bersifat potret satu waktu.
""")
    st.subheader("Jawaban pertanyaan presentasi (otomatis dari perubahan Anda)")
    if not log:
        st.write("Lakukan minimal satu perubahan di sidebar untuk melihat jawabannya.")
    for t in describe_changes(compare(comps0, comps1), log):
        st.write("• " + t)
    for _, _, _, pesan, dampak in log:
        st.write(f"• {pesan} {dampak}")

# ---------------------------------------------------------------- Tab 6
with tab6:
    st.markdown("""
### BFS vs DFS
| | BFS (Breadth-First Search) | DFS (Depth-First Search) |
|---|---|---|
| Struktur data | antrean (FIFO) | tumpukan (LIFO) |
| Urutan | melebar, per lapisan jarak | mendalam, ikuti satu jalur sampai buntu |
| Kompleksitas | O(V + E) | O(V + E) |
| Hasil komponen | sama | sama |

### Mencari komponen terhubung
1. Tandai semua titik "belum dikunjungi".
2. Ambil titik belum dikunjungi, telusuri dengan BFS/DFS → semua titik yang terjangkau = **satu kelompok**.
3. Ulangi langkah 2 sampai semua titik dikunjungi. Banyaknya pengulangan = banyaknya kelompok.

### Jembatan
Sisi yang jika dihapus menambah jumlah kelompok. Pada graf tak berarah, sisi adalah jembatan jika tidak berada pada siklus apa pun.
""")

st.divider()
st.caption("Sumber data: " + st.session_state.info["sumber"])