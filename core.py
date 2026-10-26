"""
core.py - Logika inti Community Connection Lab (tanpa Streamlit/Plotly).
Berisi: pemuatan data nyata, BFS/DFS buatan sendiri, statistik, validasi, perbandingan.
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


if __name__ == "__main__":
    for nama in DATASETS:
        G = load_dataset(nama)
        for m in ("BFS", "DFS"):
            ev, comps = traverse(G, m)
            ok = all(validate(G, comps).values())
            print(nama[:20], m, [len(c) for c in comps], "valid:", ok, "langkah:", len(ev))


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
