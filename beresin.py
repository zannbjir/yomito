#!/usr/bin/env python3
"""
beresin-konflik.py — asisten beresi konflik merge Yomito <-> Kotatsu-Redo 9.8.4

Jalankan dari root folder repo yomito.

    python3 beresin-konflik.py cek        lihat kondisi (tidak mengubah apa pun)
    python3 beresin-konflik.py auto       beresi otomatis sesi yang jelas (aman)
    python3 beresin-konflik.py pakai-kotatsu <file>   ambil versi Kotatsu utk 1 file
    python3 beresin-konflik.py pakai-yomito  <file>   ambil versi Yomito utk 1 file
    python3 beresin-konflik.py gabung     ambil dua sisi utk file tambah-tambah
    python3 beresin-konflik.py tanda      cek penanda konflik yang tertinggal
    python3 beresin-konflik.py cek-widget cek status widget & backup preset
    python3 beresin-konflik.py selesai    tandai semua selesai + commit

Script tidak pernah commit kecuali kamu jalankan 'selesai'.
"""

import re
import subprocess
import sys
from pathlib import Path

G, Y, R, B, N = "\033[0;32m", "\033[0;33m", "\033[0;31m", "\033[0;34m", "\033[0m"


def ok(m):   print(f"{G}  OK  {N} {m}")
def warn(m): print(f"{Y} WARN {N} {m}")
def err(m):  print(f"{R} ERR  {N} {m}")
def info(m): print(f"{B} INFO {N} {m}")


# ----------------------------------------------------------------------------
# git helpers
# ----------------------------------------------------------------------------

def git(*args, check=False):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=check)


def perlu_repo():
    if git("rev-parse", "--git-dir").returncode != 0:
        err("Ini bukan folder git. Jalankan di root folder repo yomito.")
        sys.exit(1)


def merge_aktif():
    return git("rev-parse", "-q", "--verify", "MERGE_HEAD").returncode == 0


def konflik():
    out = git("diff", "--name-only", "--diff-filter=U").stdout
    return [f for f in out.split("\n") if f.strip()]


def baca(rev, path):
    r = git("show", f"{rev}:{path}")
    return r.stdout if r.returncode == 0 else None


def baca_stage(stage, path):
    """stage 2 = ours (Yomito), stage 3 = theirs (Kotatsu)"""
    r = git("show", f":{stage}:{path}")
    return r.stdout if r.returncode == 0 else None


def tandai_selesai(path):
    git("add", "--", path)


def ambil(versi, path):
    """versi: 'kotatsu' (theirs) atau 'yomito' (ours)"""
    flag = "--theirs" if versi == "kotatsu" else "--ours"
    r = git("checkout", flag, "--", path)
    if r.returncode == 0:
        tandai_selesai(path)
        return True
    return False


# ----------------------------------------------------------------------------
# parsing blok konflik
# ----------------------------------------------------------------------------

BLOCK_RE = re.compile(r"^<<<<<<< .*?\n(.*?)^=======\n(.*?)^>>>>>>> .*?$", re.S | re.M)


def blok(path):
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return BLOCK_RE.findall(txt)


def normal(teks):
    return [l.rstrip() for l in teks.split("\n") if l.strip()]


def blok_identik(a, b):
    return normal(a) == normal(b)


def normal_ws(teks):
    """Sama seperti normal() tapi juga menyeragamkan indentasi & spasi dalam baris."""
    return [" ".join(l.split()) for l in teks.split("\n") if l.strip()]


def blok_sama_abai_spasi(a, b):
    """True kalau kedua sisi sama setelah semua spasi/indentasi diabaikan."""
    return normal_ws(a) == normal_ws(b)


def ada_penanda(path):
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "<<<<<<< " in txt or ">>>>>>> " in txt


# ----------------------------------------------------------------------------
# klasifikasi file
# ----------------------------------------------------------------------------

# File yang Yomito hanya punya versi lebih lama -> pakai Kotatsu.
FILE_KOTATSU = {
    # preset (Yomito backport dari Kotatsu, Kotatsu sudah lebih lengkap)
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/data/SourcePreset.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/data/SourcePresetEntity.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/ui/preset/SourcePresetAdapter.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/ui/preset/SourcePresetEditViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/ui/preset/SourcePresetListActivity.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/ui/preset/SourcePresetListViewModel.kt",
    "app/src/main/res/layout/activity_preset_edit.xml",
    "app/src/main/res/layout/item_preset.xml",
    # cloudflare / captcha
    "app/src/main/kotlin/org/koitharu/kotatsu/browser/cloudflare/CloudFlareHiddenActivity.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/exceptions/resolve/CaptchaAutoResolveCoordinator.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/network/webview/CloudFlareDetection.kt",
    # e-ink / misk
    "app/src/main/kotlin/org/koitharu/kotatsu/core/prefs/EInkFlashColor.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/ui/util/ForegroundActivityHolder.kt",
    # reader double page
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/ui/pager/doublepage/DoublePageScalingFrame.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/ui/pager/doublepage/DoublePageHolder.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/ui/pager/doublepage/Utils.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/ui/pager/doublepage/DoubleReaderFragment.kt",
    # tracker
    "app/src/main/kotlin/org/koitharu/kotatsu/tracker/domain/TrackerUnstuckMigrationUseCase.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/tracker/data/TracksDao.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/tracker/domain/CheckNewChaptersUseCase.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/tracker/domain/TrackingRepository.kt",
    # history (Yomito ubah utk widget, Kotatsu jauh lebih baru)
    "app/src/main/kotlin/org/koitharu/kotatsu/history/data/HistoryRepository.kt",
    # misc yang Yomito cuma versi lama
    "app/src/main/kotlin/org/koitharu/kotatsu/main/ui/MainNavigationDelegate.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/list/ui/adapter/MangaGridItemAD.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/remotelist/ui/RemoteListViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/settings/work/WorkScheduleManager.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/network/webview/RequestInterceptorWebViewClient.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/network/webview/WebViewExecutor.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/network/webview/WebViewRequestInterceptorExecutor.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/prefs/SourceSettings.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/parser/MangaLinkResolver.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/model/Manga.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/list/ui/adapter/LoadingStateAD.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/list/ui/model/LoadingState.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/settings/sources/catalog/SourceCatalogItem.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/util/ext/Throwable.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/details/domain/ProgressUpdateUseCase.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/details/ui/DetailsErrorObserver.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/domain/PageLoader.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/ui/ReaderViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/alternatives/ui/AlternativesViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/alternatives/domain/AlternativesUseCase.kt",
    "app/src/main/res/layout/fragment_reader_double.xml",
    "app/src/main/res/values-fr/plurals.xml",
    "app/src/main/res/values-fr/strings.xml",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/exceptions/resolve/ExceptionResolver.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/reader/ui/ReaderActivity.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/browser/cloudflare/CloudFlareActivity.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/browser/cloudflare/CloudFlareInterceptClient.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/prefs/AppSettings.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/explore/ui/ExploreViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/search/ui/multi/SearchViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/settings/sources/catalog/SourcesCatalogViewModel.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/main/ui/MainActivity.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/ui/widgets/SlidingBottomNavigationView.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/db/MangaDatabase.kt",
}

# File yang harus GABUNG (kedua sisi menambah hal berbeda).
FILE_GABUNG = {
    "app/src/main/res/xml/pref_appearance.xml",
    "app/src/main/res/xml/pref_about.xml",
    "app/src/main/res/xml/pref_reader.xml",
    "app/src/main/res/xml/pref_source.xml",
    "app/src/main/res/values/colors.xml",
    "app/src/main/res/values/dimens.xml",
    "app/src/main/res/values/styles.xml",
    "app/src/main/res/values/themes.xml",
    "app/src/main/res/values/strings.xml",
    "app/src/main/res/layout/activity_main.xml",
    "app/src/main/res/layout/activity_details.xml",
    "app/src/main/res/layout/item_explore_buttons.xml",
    "app/src/main/res/layout/item_manga_grid.xml",
    "app/src/main/kotlin/org/koitharu/kotatsu/backups/domain/BackupSection.kt",
    "app/src/main/kotlin/org/koitharu/kotatsu/backups/ui/restore/BackupSectionModel.kt",
}

# File yang HARUS dibuka manual (branding, parser, build config).
FILE_MANUAL = {
    "app/build.gradle",
    "app/proguard-rules.pro",
    "gradle/libs.versions.toml",
    "app/src/main/AndroidManifest.xml",
    "app/src/main/res/values/constants.xml",
    "app/src/main/kotlin/org/koitharu/kotatsu/core/db/MangaDatabase.kt",
}


def kategori(path):
    if path in FILE_MANUAL:
        return "manual"
    if path in FILE_GABUNG:
        return "gabung"
    if path in FILE_KOTATSU:
        return "kotatsu"
    # default: kalau semua blok identik (termasuk abai spasi) -> kotatsu
    b = blok(path)
    if b and all(blok_sama_abai_spasi(a, c) for a, c in b):
        return "kotatsu"
    return "manual"


# ----------------------------------------------------------------------------
# aksi: gabung (buang penanda, simpan dua sisi)
# ----------------------------------------------------------------------------

def gabung_blok(path, hanya_identik=False, abai_spasi=False):
    p = Path(path)
    try:
        txt = p.read_text(encoding="utf-8")
    except OSError:
        return False

    def repl(m):
        a, b = m.group(1), m.group(2)
        # Kedua sisi sama persis -> pakai versi Kotatsu
        if blok_identik(a, b):
            return b
        # Sama kalau spasi diabaikan -> pakai versi Kotatsu juga
        if abai_spasi and blok_sama_abai_spasi(a, b):
            return b
        if hanya_identik:
            return m.group(0)
        # Benar-benar beda -> simpan dua sisi (Kotatsu dulu, lalu Yomito)
        return b + a

    baru = BLOCK_RE.sub(repl, txt)
    if baru == txt:
        return False
    p.write_text(baru, encoding="utf-8")
    return True


# ----------------------------------------------------------------------------
# perintah
# ----------------------------------------------------------------------------

def cmd_cek():
    perlu_repo()
    print()
    if not merge_aktif():
        warn("Tidak ada merge yang sedang berjalan.")
        print("  Belum mulai?  git merge upstream/devel")
        print("  Sudah selesai? git log --oneline -3")
        return

    ks = konflik()
    if not ks:
        ok("Tidak ada file konflik tersisa!")
        print("\n  Langkah berikutnya:")
        print('    git add -A && git commit -m "Merge Kotatsu-Redo 9.8.4 into Yomito"')
        return

    buckets = {"kotatsu": [], "gabung": [], "manual": []}
    for f in ks:
        buckets[kategori(f)].append(f)

    print(f"  Total file konflik: {Y}{len(ks)}{N}\n")
    for label, key, desc in [
        ("PAKAI VERSI KOTATSU", "kotatsu", "Yomito cuma punya versi lebih lama"),
        ("GABUNG DUA SISI", "gabung", "kedua sisi menambah hal berbeda"),
        ("PERLU KEPUTUSANMU", "manual", "branding/parser/build config"),
    ]:
        print(f"  {B}{label}{N} — {desc} ({len(buckets[key])} file)")
        for f in buckets[key]:
            nb = len(blok(f))
            print(f"      {f}  [{nb} blok]")
        print()

    print("  Langkah berikutnya:")
    if buckets["kotatsu"]:
        print("    python3 beresin-konflik.py auto        # beresi yang otomatis")
    if buckets["manual"]:
        print("    # sisanya buka manual di Android Studio")


def cmd_auto():
    perlu_repo()
    if not merge_aktif():
        err("Tidak ada merge yang sedang berjalan.")
        sys.exit(1)
    print()
    info("Memberesi otomatis...")

    # 1) file kategori kotatsu -> ambil versi Kotatsu
    n1 = 0
    for f in konflik():
        if kategori(f) == "kotatsu":
            if ambil("kotatsu", f):
                ok(f)
                n1 += 1

    # 2) file gabung -> buang penanda, simpan dua sisi
    n2 = 0
    for f in konflik():
        if kategori(f) == "gabung":
            if gabung_blok(f):
                tandai_selesai(f)
                ok(f"{f}  (digabung)")
                n2 += 1

    # 3) sisa file: beresi blok yang identik saja
    n3 = 0
    for f in konflik():
        if gabung_blok(f, hanya_identik=True):
            if not ada_penanda(f):
                tandai_selesai(f)
                ok(f"{f}  (blok identik)")
                n3 += 1

    # 4) buang duplikat yang muncul akibat penggabungan
    n4 = 0
    for f in sorted(Path("app/src/main/res").rglob("values*/*.xml")):
        n4 += beresi_duplikat_values(str(f))

    print()
    ok(f"Selesai: {n1} pakai Kotatsu, {n2} digabung, {n3} blok identik, {n4} duplikat dibuang.")
    print("\n  Lanjut: python3 beresin-konflik.py duplikat   # periksa")


def cmd_pilih(versi, path):
    perlu_repo()
    if not path:
        err("Sebutkan file-nya. Contoh: python3 beresin-konflik.py pakai-kotatsu app/build.gradle")
        sys.exit(1)
    if path not in konflik():
        err(f"{path} tidak sedang konflik.")
        sys.exit(1)
    if ambil(versi, path):
        ok(f"{path} -> versi {versi}")
    else:
        err(f"Gagal mengambil {path}")


def cmd_gabung():
    perlu_repo()
    print()
    info("Menggabungkan semua file kategori 'gabung'...")
    n = 0
    for f in konflik():
        if kategori(f) == "gabung" and gabung_blok(f):
            tandai_selesai(f)
            ok(f)
            n += 1
    print()
    ok(f"Selesai: {n} file digabung.")


def cmd_tanda():
    perlu_repo()
    print()
    info("Mencari penanda konflik yang tertinggal...")
    hasil = []
    for f in git("ls-files").stdout.split("\n"):
        if not f.strip():
            continue
        if f.endswith((".kt", ".xml", ".toml", ".pro", ".gradle", ".properties", ".json")):
            if ada_penanda(f) and f not in hasil:
                hasil.append(f)
    if hasil:
        err("Masih ada penanda konflik di:")
        for f in hasil:
            print(f"      {f}")
    else:
        ok("Bersih — tidak ada penanda konflik tertinggal.")

    print()
    sisa = konflik()
    if sisa:
        warn(f"Masih ada {len(sisa)} file belum ditandai selesai:")
        for f in sisa:
            print(f"      {f}")
    else:
        ok("Semua file konflik sudah ditandai selesai.")
        print("\n  Langkah terakhir:")
        print('    git add -A && git commit -m "Merge Kotatsu-Redo 9.8.4 into Yomito"')


def cmd_selesai():
    perlu_repo()
    sisa = konflik()
    if sisa:
        err(f"Masih ada {len(sisa)} file konflik. Beresi dulu.")
        for f in sisa:
            print(f"      {f}")
        sys.exit(1)
    print()
    info("Menandai semua selesai...")
    git("add", "-A")
    r = git("commit", "-m", "Merge Kotatsu-Redo 9.8.4 into Yomito")
    if r.returncode == 0:
        ok("Merge selesai dan sudah di-commit.")
        print()
        print(git("log", "--oneline", "-3").stdout.rstrip())
    else:
        err("Commit gagal:")
        print(r.stdout + r.stderr)




# ----------------------------------------------------------------------------
# deteksi & perbaikan duplikat akibat penggabungan otomatis
# ----------------------------------------------------------------------------

TOP_TAGS = ("string", "plurals", "string-array", "integer-array", "dimen",
            "color", "integer", "bool", "style", "array", "attr")


def duplikat_values(path):
    """Kembalikan daftar (tag, nama) yang muncul lebih dari sekali di file values XML."""
    import re
    from collections import Counter
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    names = re.findall(
        r'<(' + "|".join(TOP_TAGS) + r')\s+name="([^"]+)"', txt
    )
    c = Counter(names)
    return [(t, n) for (t, n), v in c.items() if v > 1]


def beresi_duplikat_values(path):
    """Buang elemen top-level duplikat: yang PERTAMA dipertahankan."""
    import re
    p = Path(path)
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    head_end = txt.index(">", txt.index("<resources"))
    head = txt[:head_end + 1]
    body = txt[head_end + 1: txt.rindex("</resources>")]
    tail = "\n</resources>\n"

    blk_re = re.compile(
        r'<(' + "|".join(TOP_TAGS) + r')\s+name="[^"]+".*?</\1>', re.S
    )
    seen = set()
    kept = []
    dupes = 0
    for m in blk_re.finditer(body):
        blk = m.group(0)
        tag = m.group(1)
        name = re.search(r'name="([^"]+)"', blk).group(1)
        key = (tag, name)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        kept.append(blk)

    if dupes:
        p.write_text(head + "\n" + "\n".join(kept) + tail, encoding="utf-8")
    return dupes


def cmd_duplikat():
    perlu_repo()
    print()
    info("Mencari elemen duplikat di res/values/*.xml ...")
    total = 0
    for f in sorted(Path("app/src/main/res").rglob("values*/*.xml")):
        d = duplikat_values(str(f))
        if d:
            print(f"  {Y}{f}{N} — {len(d)} duplikat")
            for t, n in d[:8]:
                print(f"        <{t} name=\"{n}\">")
            total += len(d)
    if total == 0:
        ok("Bersih — tidak ada duplikat.")
    else:
        warn(f"Total {total} elemen duplikat. Perbaiki dengan:")
        print("    python3 beresin-konflik.py dedup")


def cmd_dedup():
    perlu_repo()
    print()
    info("Membuang elemen duplikat (yang pertama dipertahankan) ...")
    n = 0
    for f in sorted(Path("app/src/main/res").rglob("values*/*.xml")):
        d = beresi_duplikat_values(str(f))
        if d:
            ok(f"{f}  ({d} duplikat dibuang)")
            n += d
    print()
    if n:
        ok(f"Selesai: {n} elemen duplikat dibuang.")
    else:
        ok("Tidak ada duplikat yang perlu dibuang.")
    print()
    warn("PERIKSA hasilnya: nilai yang dipakai sekarang adalah elemen PERTAMA")
    warn("(biasanya versi Kotatsu). Untuk app_name, pastikan masih 'Yomito'.")


def cmd_widget():
    """Cek status fitur khas Yomito (widget Lanjut Baca + backup preset)."""
    perlu_repo()
    print()
    info("Memeriksa fitur khas Yomito ...")
    print()

    # 1. file widget
    wdir = Path("app/src/main/kotlin/org/koitharu/kotatsu/widget")
    wajib = [
        wdir / "continuereading/ContinueReadingWidget.kt",
        wdir / "common/WidgetEntryPoint.kt",
        wdir / "common/WidgetCoverLoader.kt",
        wdir / "common/WidgetIntents.kt",
        wdir / "common/WidgetScope.kt",
        wdir / "common/WidgetSizes.kt",
        Path("app/src/main/res/layout/widget_continue_reading.xml"),
        Path("app/src/main/res/layout/widget_continue_reading_empty.xml"),
        Path("app/src/main/res/layout/widget_continue_reading_small.xml"),
        Path("app/src/main/res/xml/widget_continue_reading.xml"),
    ]
    hilang = [f for f in wajib if not f.exists()]
    if hilang:
        err(f"File widget HILANG ({len(hilang)}):")
        for f in hilang:
            print(f"      {f}")
    else:
        ok(f"File widget lengkap ({len(wajib)} file)")

    # 2. manifest
    man = Path("app/src/main/AndroidManifest.xml")
    if man.exists() and "ContinueReadingWidget" in man.read_text(encoding="utf-8", errors="replace"):
        ok("Widget terdaftar di AndroidManifest.xml")
    else:
        err("Widget TIDAK terdaftar di AndroidManifest.xml")

    # 3. hook nudgeAll
    print()
    hits = []
    for f in Path("app/src/main/kotlin").rglob("*.kt"):
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "nudgeAll(" in t and "fun nudgeAll" not in t:
            hits.append(f)
    if hits:
        ok(f"Hook nudgeAll terpasang di {len(hits)} file:")
        for f in hits:
            print(f"      {f}")
    else:
        warn("Hook nudgeAll BELUM terpasang.")
        print("      Pasang di ReaderActivity.kt dan MainActivity.kt")
        print("      Lihat panduan 'lanjutan-dari-dedup' bagian B.")

    # 4. WidgetUpdater
    upd = wdir / "WidgetUpdater.kt"
    if upd.exists():
        t = upd.read_text(encoding="utf-8", errors="replace")
        if "ContinueReadingWidget" in t:
            ok("WidgetUpdater terhubung ke widget")
        else:
            warn("WidgetUpdater belum menyertakan ContinueReadingWidget (opsional)")

    # 5. preset backup
    print()
    dao = Path("app/src/main/kotlin/org/koitharu/kotatsu/explore/data/SourcePresetsDao.kt")
    if dao.exists():
        t = dao.read_text(encoding="utf-8", errors="replace")
        punya_dump = "fun dump(" in t
        punya_upsert = "fun upsert(" in t
        if punya_dump and punya_upsert:
            ok("SourcePresetsDao punya dump() + upsert()")
        else:
            warn("SourcePresetsDao belum lengkap:")
            print(f"      dump()   : {'ada' if punya_dump else 'BELUM'}")
            print(f"      upsert() : {'ada' if punya_upsert else 'BELUM'}")
    else:
        err("SourcePresetsDao.kt tidak ditemukan")

    model = Path("app/src/main/kotlin/org/koitharu/kotatsu/backups/data/model/SourcePresetBackup.kt")
    if model.exists():
        ok("SourcePresetBackup.kt ada")
    else:
        warn("SourcePresetBackup.kt tidak ada")

    # 6. branding
    print()
    st = Path("app/src/main/res/values/strings.xml")
    if st.exists():
        import re
        m = re.search(r'<string name="app_name"[^>]*>([^<]+)</string>', st.read_text(encoding="utf-8", errors="replace"))
        nama = m.group(1) if m else "?"
        if nama.strip() == "Yomito":
            ok(f"app_name = {nama}")
        else:
            err(f"app_name = {nama}  (harusnya Yomito)")

    const = Path("app/src/main/res/values/constants.xml")
    if const.exists():
        t = const.read_text(encoding="utf-8", errors="replace")
        if "zannbjir/yomito" in t:
            ok("Branding url_github/github_updates_repo = zannbjir/yomito")
        else:
            warn("Branding url_github belum menunjuk ke zannbjir/yomito")

    bgradle = Path("app/build.gradle")
    if bgradle.exists():
        t = bgradle.read_text(encoding="utf-8", errors="replace")
        if "yomito-parsers" in t:
            ok("app/build.gradle pakai yomito-parsers")
        else:
            err("app/build.gradle TIDAK pakai yomito-parsers (sumber webmu hilang!)")

    tv = Path("gradle/libs.versions.toml")
    if tv.exists():
        import re
        m = re.search(r'^parsers\s*=\s*"([^"]+)"', tv.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            val = m.group(1)
            if val.startswith("52a02475d8") or val != "b3c0000245":
                ok(f"libs.versions.toml parsers = {val}")
            else:
                err(f"parsers = {val}  (ini punya Kotatsu, sumber webmu hilang!)")

    print()

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    c = a[0]
    if c == "cek":
        cmd_cek()
    elif c == "auto":
        cmd_auto()
    elif c == "pakai-kotatsu":
        cmd_pilih("kotatsu", a[1] if len(a) > 1 else None)
    elif c == "pakai-yomito":
        cmd_pilih("yomito", a[1] if len(a) > 1 else None)
    elif c == "gabung":
        cmd_gabung()
    elif c == "tanda":
        cmd_tanda()
    elif c == "cek-widget":
        cmd_widget()
    elif c == "dedup":
        cmd_dedup()
    elif c == "duplikat":
        cmd_duplikat()
    elif c == "selesai":
        cmd_selesai()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
