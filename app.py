"""
Community Connection Lab - Proyek 07
Jalankan:  streamlit run app.py
"""
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core

st.set_page_config(page_title="Community Connection Lab", layout="wide")

PALETTE = ["#1f77b4", "#2ca02c", "#9467bd", "#17becf", "#8c564b",
           "#e377c2", "#7f7f7f", "#bcbd22", "#ff7f0e", "#0b6e4f"]
C_UNSEEN, C_FRONT, C_CURRENT = "#d9d9d9", "#FFC107", "#E53935"


# ======================================================================
# Utilitas gambar
# ======================================================================
def edge_xy(edges, pos):
    xs, ys = [], []
    for a, b in edges:
        xs += [pos[a][0], pos[b][0], None]
        ys += [pos[a][1], pos[b][1], None]
    return xs, ys


def ordered(comps):
    """Kelompok terbesar jadi nomor 1."""
    return sorted(comps, key=lambda c: (-len(c), str(sorted(c, key=str)[0])))


def axis_ranges(pos):
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    px, py = 0.15 * (max(xs) - min(xs) + 1e-9), 0.15 * (max(ys) - min(ys) + 1e-9)
    return [min(xs) - px, max(xs) + px], [min(ys) - py, max(ys) + py]


def base_layout(fig, pos, title, height=540):
    rx, ry = axis_ranges(pos)
    fig.update_layout(
        title=title, height=height, plot_bgcolor="white",
        xaxis=dict(visible=False, range=rx, fixedrange=True),
        yaxis=dict(visible=False, range=ry, fixedrange=True),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", y=-0.02, x=0),
    )


def static_figure(G, comps, pos, title, added=(), removed=()):
    fig = go.Figure()
    bridges = {frozenset(e) for e in nx.bridges(G)}
    normal = [e for e in G.edges if frozenset(e) not in bridges and e not in added
              and (e[1], e[0]) not in added]
    br = [e for e in G.edges if frozenset(e) in bridges]
    x, y = edge_xy(normal, pos)
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Hubungan",
                             line=dict(width=1.6, color="#9aa0a6"), hoverinfo="skip"))
    if br:
        x, y = edge_xy(br, pos)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Jembatan (jika dihapus, kelompok terpecah)",
                                 line=dict(width=3.5, color="#FB8C00"), hoverinfo="skip"))
    if added:
        x, y = edge_xy([e for e in added if G.has_edge(*e)], pos)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Hubungan baru",
                                 line=dict(width=4, color="#2E7D32"), hoverinfo="skip"))
    if removed:
        x, y = edge_xy(removed, pos)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Hubungan dihapus",
                                 line=dict(width=3, color="#C62828", dash="dash"), hoverinfo="skip"))
    deg = dict(G.degree())
    for i, comp in enumerate(ordered(comps)):
        fig.add_trace(go.Scatter(
            x=[pos[v][0] for v in comp], y=[pos[v][1] for v in comp],
            mode="markers+text", text=[str(v) for v in comp], textposition="top center",
            marker=dict(size=[14 + 3 * deg[v] for v in comp], color=PALETTE[i % len(PALETTE)],
                        line=dict(width=1.5, color="white")),
            hovertext=[f"{v} | derajat {deg[v]} | kelompok {i + 1}" for v in comp], hoverinfo="text",
            name=f"Kelompok {i + 1} ({len(comp)} anggota)"))
    base_layout(fig, pos, title)
    return fig


def animation_figure(G, events, pos, method, speed_ms):
    nodes = list(G.nodes)
    wadah = "antrean (FIFO)" if method == "BFS" else "tumpukan (LIFO)"

    def state(k):
        """Keadaan setelah k langkah (k=0: belum mulai)."""
        done, tree, cur, front = {}, [], None, []
        for e in events[:k]:
            done[e["node"]] = e["comp"]
            if e["parent"] is not None:
                tree.append((e["parent"], e["node"]))
            cur, front = e["node"], e["frontier"]
        return done, tree, cur, front

    def traces_at(k):
        done, tree, cur, front = state(k)
        colors, sizes, lines = [], [], []
        for v in nodes:
            if v == cur:
                colors.append(C_CURRENT); sizes.append(30)
            elif v in done:
                colors.append(PALETTE[done[v] % len(PALETTE)]); sizes.append(22)
            elif v in front:
                colors.append(C_FRONT); sizes.append(22)
            else:
                colors.append(C_UNSEEN); sizes.append(22)
        tx, ty = edge_xy(tree, pos)
        t_edges = go.Scatter(x=tx, y=ty, mode="lines", line=dict(width=5, color="#263238"),
                             hoverinfo="skip", showlegend=False)
        t_nodes = go.Scatter(x=[pos[v][0] for v in nodes], y=[pos[v][1] for v in nodes],
                             mode="markers+text", text=[str(v) for v in nodes],
                             textposition="top center",
                             marker=dict(size=sizes, color=colors, line=dict(width=2, color="white")),
                             hoverinfo="text", showlegend=False)
        return t_edges, t_nodes

    def title_at(k):
        if k == 0:
            return f"{method} — siap dimulai ({len(events)} langkah)"
        return f"{method} langkah {k}/{len(events)}: " + events[k - 1]["note"]

    all_edges = go.Scatter(x=edge_xy(G.edges, pos)[0], y=edge_xy(G.edges, pos)[1],
                           mode="lines", line=dict(width=1.5, color="#c9ccd1"),
                           hoverinfo="skip", showlegend=False)
    t0e, t0n = traces_at(0)
    fig = go.Figure(data=[all_edges, t0e, t0n])
    # Legenda (jejak bayangan, hanya untuk keterangan warna)
    for nama, warna in [("Belum ditemukan", C_UNSEEN), (f"Menunggu di {wadah}", C_FRONT),
                        ("Sedang diproses", C_CURRENT), ("Sudah dikunjungi (warna = kelompok)", PALETTE[0])]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=nama,
                                 marker=dict(size=14, color=warna)))
    fig.frames = [go.Frame(name=str(k), data=list(traces_at(k)), traces=[1, 2],
                           layout=go.Layout(title=dict(text=title_at(k))))
                  for k in range(len(events) + 1)]
    play = dict(frame=dict(duration=speed_ms, redraw=True), fromcurrent=True,
                transition=dict(duration=0), mode="immediate")
    fig.update_layout(
        updatemenus=[dict(type="buttons", direction="left", x=0.0, y=-0.08, xanchor="left", yanchor="top",
                          buttons=[
                              dict(label="▶ Putar", method="animate", args=[None, play]),
                              dict(label="⏸ Jeda", method="animate",
                                   args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                      mode="immediate", transition=dict(duration=0))]),
                              dict(label="⟲ Ulang", method="animate",
                                   args=[["0"], dict(frame=dict(duration=0, redraw=True),
                                                     mode="immediate", transition=dict(duration=0))]),
                          ])],
        sliders=[dict(active=0, x=0.30, y=-0.08, len=0.70, xanchor="left", yanchor="top",
                      currentvalue=dict(prefix="Langkah: "),
                      steps=[dict(method="animate", label=str(k),
                                  args=[[str(k)], dict(mode="immediate",
                                                       frame=dict(duration=0, redraw=True),
                                                       transition=dict(duration=0))])
                             for k in range(len(events) + 1)])])
    base_layout(fig, pos, title_at(0), height=640)
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=90), legend=dict(orientation="h", y=1.0, x=0, yanchor="bottom"))
    return fig


# ======================================================================
# State
# ======================================================================
def init_graph(G, label, info):
    st.session_state.G0 = G.copy()
    st.session_state.G1 = G.copy()
    st.session_state.log = []
    st.session_state.info = info
    st.session_state.label = label
    st.session_state.pos = nx.spring_layout(G, seed=42, k=1.4 / max(len(G), 1) ** 0.5, iterations=200)


with st.sidebar:
    st.header("⚙️ Pengaturan")
    pilihan = list(core.DATASETS) + ["Unggah CSV sendiri (data nyata milik Anda)"]
    nama = st.selectbox("Dataset", pilihan)
    if nama in core.DATASETS:
        if st.session_state.get("label") != nama:
            init_graph(core.load_dataset(nama), nama, core.DATASETS[nama])
    else:
        up = st.file_uploader("CSV dengan 2 kolom (titik A, titik B)", type="csv")
        if up is not None:
            df = pd.read_csv(up)
            ca = st.selectbox("Kolom titik A", df.columns, index=0)
            cb = st.selectbox("Kolom titik B", df.columns, index=min(1, len(df.columns) - 1))
            key = f"upload:{up.name}:{ca}:{cb}"
            if st.session_state.get("label") != key:
                init_graph(core.load_from_edgelist(df, ca, cb), key,
                           {"sumber": f"Berkas {up.name}", "arti_titik": "sesuai data Anda",
                            "arti_sisi": "sesuai data Anda"})
        else:
            st.info("Unggah CSV untuk memakai data sendiri.")
            st.stop()

    G0, G1, pos = st.session_state.G0, st.session_state.G1, st.session_state.pos
    algo = st.radio("Algoritma penelusuran", ["BFS", "DFS"], horizontal=True)
    titik = sorted(G1.nodes, key=str)
    start = st.selectbox("Titik awal penelusuran", titik)
    speed = st.slider("Kecepatan animasi (ms/langkah)", 200, 2000, 800, 100)

    st.divider()
    st.subheader("✏️ Ubah hubungan")
    op = st.radio("Aksi", ["Tambah hubungan", "Hapus hubungan"], horizontal=True)
    if op == "Tambah hubungan":
        a = st.selectbox("Titik A", titik, key="add_a")
        b = st.selectbox("Titik B", titik, index=min(1, len(titik) - 1), key="add_b")
        pair = (a, b)
        kode = "tambah"
    else:
        edges = sorted((tuple(sorted(e, key=str)) for e in G1.edges), key=str)
        if edges:
            pair = st.selectbox("Pilih hubungan", edges, format_func=lambda e: f"{e[0]} — {e[1]}")
        else:
            pair = None
        kode = "hapus"
    if st.button("Terapkan perubahan", type="primary", disabled=pair is None):
        ok, pesan, dampak = core.apply_change(st.session_state.G1, kode, *pair)
        if ok:
            st.session_state.log.append((kode, pair[0], pair[1], pesan, dampak))
            st.rerun()
        else:
            st.warning(pesan)
    if st.button("↩️ Kembalikan ke kondisi awal"):
        st.session_state.G1 = st.session_state.G0.copy()
        st.session_state.log = []
        st.rerun()
    for _, _, _, pesan, _ in st.session_state.log:
        st.caption("• " + pesan)

# ======================================================================
# Perhitungan utama
# ======================================================================
log = st.session_state.log
comps0 = core.find_components(G0, algo)
comps1 = core.find_components(G1, algo)

added = [(a, b) for k, a, b, _, _ in log if k == "tambah" and G1.has_edge(a, b)]
removed = [(a, b) for k, a, b, _, _ in log if k == "hapus" and not G1.has_edge(a, b)]

st.title("🕸️ Community Connection Lab")
st.caption("Ubah hubungan pertemanan, lalu amati kelompok yang bergabung atau terpisah. "
           "Algoritma: BFS & DFS untuk mencari komponen terhubung.")

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

# ---------------------------------------------------------------- Tab 2
with tab2:
    st.plotly_chart(static_figure(G1, comps1, pos, "Kelompok pertemanan (kondisi saat ini)",
                                  added, removed), use_container_width=True)
    ukuran = pd.DataFrame([{"Kelompok": i + 1, "Anggota": len(c), "Daftar anggota": ", ".join(map(str, sorted(c, key=str)))}
                           for i, c in enumerate(ordered(comps1))])
    deg = dict(G1.degree())
    komp_no = {v: i + 1 for i, c in enumerate(ordered(comps1)) for v in c}
    tabel_deg = pd.DataFrame({"Titik": list(G1.nodes), "Derajat": [deg[v] for v in G1.nodes],
                              "Kelompok": [komp_no[v] for v in G1.nodes]}).sort_values(
        ["Derajat", "Titik"], ascending=[False, True])
    cA, cB = st.columns([3, 2])
    cA.markdown("**Ukuran tiap kelompok**")
    cA.dataframe(ukuran, use_container_width=True, hide_index=True)
    cB.markdown("**Derajat tiap titik**")
    cB.dataframe(tabel_deg, use_container_width=True, hide_index=True, height=300)
    br, ap = core.connectors(G1)
    st.markdown("**Penghubung di dalam kelompok** (titik/hubungan yang jika hilang memecah kelompok)")
    st.write("Jembatan:", ", ".join(f"{a}—{b}" for a, b in br) or "tidak ada")
    st.write("Titik penghubung:", ", ".join(map(str, ap)) or "tidak ada")

# ---------------------------------------------------------------- Tab 3
with tab3:
    cL, cR = st.columns(2)
    cL.plotly_chart(static_figure(G0, comps0, pos, "SEBELUM"), use_container_width=True)
    cR.plotly_chart(static_figure(G1, comps1, pos, "SESUDAH", added, removed), use_container_width=True)
    s0, s1 = core.stats(G0, comps0), core.stats(G1, comps1)
    tbl = pd.DataFrame({"Sebelum": {k: str(v) for k, v in s0.items()},
                        "Sesudah": {k: str(v) for k, v in s1.items()}})
    tbl["Berubah?"] = ["✅ ya" if tbl.loc[k, "Sebelum"] != tbl.loc[k, "Sesudah"] else "" for k in tbl.index]
    st.dataframe(tbl, use_container_width=True)

    st.markdown("### Apa yang terjadi?")
    for t in core.describe_changes(core.compare(comps0, comps1), log):
        st.success(t)
    # replay: dampak tiap perubahan, dihitung pada saat perubahan dilakukan
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
    events, comps_t = core.traverse(Gt, algo, start)
    wadah = "antrean (queue, FIFO)" if algo == "BFS" else "tumpukan (stack, LIFO)"
    st.markdown(
        f"Tekan **▶ Putar**, **⏸ Jeda**, **⟲ Ulang**, atau geser **slider** untuk maju/mundur satu langkah. "
        f"Algoritma **{algo}** memakai **{wadah}**. Warna kuning = menunggu giliran, merah = sedang diproses, "
        f"garis tebal gelap = sisi pohon penelusuran. Setiap kali penelusuran terhenti dan masih ada titik "
        f"yang belum dikunjungi, titik itu memulai **kelompok baru** (warna baru).")
    st.plotly_chart(animation_figure(Gt, events, pos, algo, speed), use_container_width=True)
    st.markdown("**Log langkah penelusuran**")
    st.dataframe(pd.DataFrame([{"Langkah": e["step"] + 1, "Kelompok": e["comp"] + 1, "Dikunjungi": e["node"],
                                "Lewat": e["parent"] or "(awal)", "Isi " + algo + " setelahnya": ", ".join(map(str, e["frontier"])) or "kosong"}
                               for e in events]), use_container_width=True, hide_index=True, height=300)

# ---------------------------------------------------------------- Tab 5
with tab5:
    st.subheader("Validasi otomatis")
    for label, g, comps in [("Sebelum", G0, comps0), ("Sesudah", G1, comps1)]:
        st.markdown(f"**{label}** (BFS/DFS buatan sendiri vs fungsi NetworkX)")
        for k, v in core.validate(g, comps).items():
            (st.success if v else st.error)(("✔ " if v else "✘ ") + k)
    same = {frozenset(c) for c in core.find_components(G1, "BFS")} == {frozenset(c) for c in core.find_components(G1, "DFS")}
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
    for t in core.describe_changes(core.compare(comps0, comps1), log):
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
