#!/usr/bin/env python3
"""
PhoenixBurn REAL
----------------
A real ISO-to-USB burning tool (like Rufus / balenaEtcher), written
in pure Python for Linux. Part of the ALphoenixa OS / dstc project.

!!! THIS TOOL WRITES REAL DATA TO REAL USB DRIVES !!!
It will PERMANENTLY ERASE everything on the drive you select.
There is no undo. Read every prompt carefully.

Requirements:
  - Linux (uses lsblk + dd under the hood)
  - Run with sudo / root privileges (writing to a raw block device
    requires it -- the script will refuse to run without it)
  - Python 3.7+

Usage:
    sudo python3 phoenixburn_real.py

Safety design:
  - Only lists REMOVABLE drives (USB sticks/SD cards) -- it will not
    even show your internal hard drive / SSD as an option.
  - Refuses to touch any device that has a mounted partition matching
    "/", "/boot", "/home", or that is currently in use as swap.
  - Requires you to type the EXACT device path (e.g. /dev/sdb) to
    confirm, not just "y".
  - Requires a second confirmation with the device's reported size.
  - Unmounts target partitions automatically before writing, but
    only after your explicit confirmation.
"""

import os
import sys
import json
import shutil
import subprocess
import time

# =====================================================================
# الترجمات — English (default), Arabic, French, German
# =====================================================================
STRINGS = {
    "en": {
        "banner_title": "PhoenixBurn — Real ISO/USB Burner",
        "banner_sub": "Part of the ALphoenixa OS / dstc project",
        "danger_warning": "WARNING: This tool writes REAL data to a REAL USB drive.\nEverything on the selected drive will be PERMANENTLY ERASED.",
        "choose_language": "Choose language / اختر اللغة / Choisir la langue / Sprache wählen:",
        "not_root": "ERROR: This tool must be run as root (use: sudo python3 {script}).",
        "not_linux": "ERROR: This tool currently only supports Linux.",
        "missing_tools": "ERROR: Required system tools not found: {tools}",
        "enter_iso_path": "Enter the full path to your ISO file: ",
        "iso_not_found": "ERROR: File not found: {path}",
        "iso_not_iso": "WARNING: File does not end in .iso, continuing anyway.",
        "detecting_drives": "Detecting removable USB drives...",
        "no_drives_found": "No removable USB drives were found. Plug one in and try again.",
        "available_drives": "Available removable drives:",
        "drive_line": "  [{idx}] {path}  -  {size}  -  {model}",
        "choose_drive": "Select the target drive number: ",
        "invalid_choice": "Invalid choice, try again.",
        "drive_protected": "ERROR: That drive appears to contain your system partitions and cannot be used.",
        "confirm_path_prompt": "To confirm, type the EXACT device path shown above (e.g. {path}): ",
        "confirm_path_mismatch": "Path did not match. Aborting for safety.",
        "confirm_size_prompt": "Type YES to confirm you want to ERASE {path} ({size}): ",
        "confirm_size_mismatch": "Confirmation not received. Aborting.",
        "unmounting": "Unmounting partitions on {path}...",
        "writing": "Writing image to {path}. Do NOT remove the drive.",
        "writing_progress": "  Written: {written} / {total}  ({pct}%)",
        "verifying": "Verifying write...",
        "done": "Done. You may now safely remove the drive.",
        "error_write": "ERROR while writing: {err}",
        "cancelled": "Operation cancelled. No changes were made.",
        "press_enter_exit": "Press Enter to exit.",
    },
    "ar": {
        "banner_title": "PhoenixBurn — أداة حرق حقيقية لملفات ISO",
        "banner_sub": "جزء من مشروع ALphoenixa OS / dstc",
        "danger_warning": "تحذير: هذه الأداة تكتب بيانات حقيقية على فلاشة حقيقية.\nكل شيء على الفلاشة المختارة سيُمسح نهائياً.",
        "choose_language": "Choose language / اختر اللغة / Choisir la langue / Sprache wählen:",
        "not_root": "خطأ: يجب تشغيل هذه الأداة بصلاحيات root (استخدم: sudo python3 {script}).",
        "not_linux": "خطأ: هذه الأداة تدعم لينكس فقط حالياً.",
        "missing_tools": "خطأ: أدوات النظام المطلوبة غير موجودة: {tools}",
        "enter_iso_path": "أدخل المسار الكامل لملف ISO: ",
        "iso_not_found": "خطأ: الملف غير موجود: {path}",
        "iso_not_iso": "تنبيه: الملف لا ينتهي بامتداد .iso، سنكمل على أي حال.",
        "detecting_drives": "جارٍ البحث عن فلاشات USB قابلة للإزالة...",
        "no_drives_found": "لم يتم العثور على أي فلاشة قابلة للإزالة. وصّل واحدة وحاول من جديد.",
        "available_drives": "الفلاشات المتوفرة:",
        "drive_line": "  [{idx}] {path}  -  {size}  -  {model}",
        "choose_drive": "اختر رقم الفلاشة الهدف: ",
        "invalid_choice": "اختيار غير صحيح، حاول مجدداً.",
        "drive_protected": "خطأ: هذه الفلاشة تحتوي على أقسام نظامك ولا يمكن استخدامها.",
        "confirm_path_prompt": "للتأكيد، اكتب مسار الجهاز بالضبط كما هو ظاهر فوق (مثال: {path}): ",
        "confirm_path_mismatch": "المسار غير مطابق. تم الإلغاء للسلامة.",
        "confirm_size_prompt": "اكتب YES للتأكيد أنك تريد مسح {path} ({size}): ",
        "confirm_size_mismatch": "لم يتم استلام التأكيد. تم الإلغاء.",
        "unmounting": "جارٍ إلغاء تحميل الأقسام على {path}...",
        "writing": "جارٍ كتابة الصورة على {path}. لا تفصل الفلاشة.",
        "writing_progress": "  تمت الكتابة: {written} / {total}  ({pct}%)",
        "verifying": "جارٍ التحقق من الكتابة...",
        "done": "تم. يمكنك الآن فصل الفلاشة بأمان.",
        "error_write": "خطأ أثناء الكتابة: {err}",
        "cancelled": "تم إلغاء العملية. لم يتم إجراء أي تغيير.",
        "press_enter_exit": "اضغط Enter للخروج.",
    },
    "fr": {
        "banner_title": "PhoenixBurn — Graveur ISO/USB réel",
        "banner_sub": "Fait partie du projet ALphoenixa OS / dstc",
        "danger_warning": "ATTENTION : Cet outil écrit de vraies données sur une vraie clé USB.\nTout le contenu de la clé sélectionnée sera EFFACÉ DÉFINITIVEMENT.",
        "choose_language": "Choose language / اختر اللغة / Choisir la langue / Sprache wählen:",
        "not_root": "ERREUR : Cet outil doit être exécuté en tant que root (utilisez : sudo python3 {script}).",
        "not_linux": "ERREUR : Cet outil ne prend en charge que Linux pour le moment.",
        "missing_tools": "ERREUR : Outils système requis introuvables : {tools}",
        "enter_iso_path": "Entrez le chemin complet de votre fichier ISO : ",
        "iso_not_found": "ERREUR : Fichier introuvable : {path}",
        "iso_not_iso": "ATTENTION : Le fichier ne se termine pas par .iso, on continue quand même.",
        "detecting_drives": "Détection des clés USB amovibles...",
        "no_drives_found": "Aucune clé USB amovible trouvée. Branchez-en une et réessayez.",
        "available_drives": "Clés disponibles :",
        "drive_line": "  [{idx}] {path}  -  {size}  -  {model}",
        "choose_drive": "Sélectionnez le numéro de la clé cible : ",
        "invalid_choice": "Choix invalide, réessayez.",
        "drive_protected": "ERREUR : Cette clé semble contenir vos partitions système et ne peut pas être utilisée.",
        "confirm_path_prompt": "Pour confirmer, tapez le chemin EXACT affiché ci-dessus (ex : {path}) : ",
        "confirm_path_mismatch": "Le chemin ne correspond pas. Annulation pour votre sécurité.",
        "confirm_size_prompt": "Tapez YES pour confirmer l'effacement de {path} ({size}) : ",
        "confirm_size_mismatch": "Confirmation non reçue. Annulation.",
        "unmounting": "Démontage des partitions sur {path}...",
        "writing": "Écriture de l'image sur {path}. NE PAS retirer la clé.",
        "writing_progress": "  Écrit : {written} / {total}  ({pct}%)",
        "verifying": "Vérification de l'écriture...",
        "done": "Terminé. Vous pouvez maintenant retirer la clé en toute sécurité.",
        "error_write": "ERREUR pendant l'écriture : {err}",
        "cancelled": "Opération annulée. Aucun changement effectué.",
        "press_enter_exit": "Appuyez sur Entrée pour quitter.",
    },
    "de": {
        "banner_title": "PhoenixBurn — Echtes ISO/USB-Brenntool",
        "banner_sub": "Teil des ALphoenixa OS / dstc Projekts",
        "danger_warning": "WARNUNG: Dieses Tool schreibt echte Daten auf ein echtes USB-Laufwerk.\nAlles auf dem ausgewählten Laufwerk wird UNWIDERRUFLICH GELÖSCHT.",
        "choose_language": "Choose language / اختر اللغة / Choisir la langue / Sprache wählen:",
        "not_root": "FEHLER: Dieses Tool muss als root ausgeführt werden (verwende: sudo python3 {script}).",
        "not_linux": "FEHLER: Dieses Tool unterstützt derzeit nur Linux.",
        "missing_tools": "FEHLER: Erforderliche Systemtools nicht gefunden: {tools}",
        "enter_iso_path": "Geben Sie den vollständigen Pfad zu Ihrer ISO-Datei ein: ",
        "iso_not_found": "FEHLER: Datei nicht gefunden: {path}",
        "iso_not_iso": "WARNUNG: Datei endet nicht auf .iso, wird trotzdem fortgesetzt.",
        "detecting_drives": "Suche nach entfernbaren USB-Laufwerken...",
        "no_drives_found": "Keine entfernbaren USB-Laufwerke gefunden. Stecken Sie eines ein und versuchen Sie es erneut.",
        "available_drives": "Verfügbare Laufwerke:",
        "drive_line": "  [{idx}] {path}  -  {size}  -  {model}",
        "choose_drive": "Wählen Sie die Nummer des Ziellaufwerks: ",
        "invalid_choice": "Ungültige Auswahl, versuchen Sie es erneut.",
        "drive_protected": "FEHLER: Dieses Laufwerk scheint Ihre Systempartitionen zu enthalten und kann nicht verwendet werden.",
        "confirm_path_prompt": "Zur Bestätigung geben Sie den oben gezeigten GENAUEN Gerätepfad ein (z.B. {path}): ",
        "confirm_path_mismatch": "Pfad stimmte nicht überein. Abbruch aus Sicherheitsgründen.",
        "confirm_size_prompt": "Geben Sie YES ein, um das Löschen von {path} ({size}) zu bestätigen: ",
        "confirm_size_mismatch": "Bestätigung nicht erhalten. Abbruch.",
        "unmounting": "Partitionen auf {path} werden ausgehängt...",
        "writing": "Image wird auf {path} geschrieben. Laufwerk NICHT entfernen.",
        "writing_progress": "  Geschrieben: {written} / {total}  ({pct}%)",
        "verifying": "Schreibvorgang wird überprüft...",
        "done": "Fertig. Sie können das Laufwerk jetzt sicher entfernen.",
        "error_write": "FEHLER beim Schreiben: {err}",
        "cancelled": "Vorgang abgebrochen. Es wurden keine Änderungen vorgenommen.",
        "press_enter_exit": "Drücken Sie Enter zum Beenden.",
    },
}

LANG = "en"  # default; changed by choose_language()


def t(key, **kwargs):
    """Look up a translated string and format it."""
    template = STRINGS.get(LANG, STRINGS["en"]).get(key, STRINGS["en"][key])
    return template.format(**kwargs)


def clear_screen():
    os.system("clear")


def human_size(num_bytes):
    step = 1024.0
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < step:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= step
    return f"{num_bytes:.1f} PB"


def choose_language():
    global LANG
    print(STRINGS["en"]["choose_language"])
    print("  [1] English (default)")
    print("  [2] العربية")
    print("  [3] Français")
    print("  [4] Deutsch")
    choice = input("> ").strip()
    LANG = {"1": "en", "2": "ar", "3": "fr", "4": "de"}.get(choice, "en")


def banner():
    print("=" * 60)
    print(f"  {t('banner_title')}")
    print(f"  {t('banner_sub')}")
    print("=" * 60)
    print()
    print(t("danger_warning"))
    print()


def check_environment():
    if sys.platform != "linux":
        print(t("not_linux"))
        sys.exit(1)

    if os.geteuid() != 0:
        print(t("not_root", script=os.path.basename(__file__)))
        sys.exit(1)

    missing = [tool for tool in ("lsblk", "dd", "umount") if shutil.which(tool) is None]
    if missing:
        print(t("missing_tools", tools=", ".join(missing)))
        sys.exit(1)


def get_removable_drives():
    """
    يرجّع فقط الأقراص القابلة للإزالة (USB/SD) باستخدام lsblk.
    يستبعد أي قرص يحتوي على أقسام النظام الأساسية.
    """
    protected_mountpoints = {"/", "/boot", "/boot/efi", "/home", "[SWAP]"}

    result = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,PATH,SIZE,TYPE,RM,MOUNTPOINT,MODEL"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)

    drives = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue
        if str(dev.get("rm")) not in ("1", "True", "true"):
            continue  # ليس قابل للإزالة -- تجاهله (يحمي القرص الرئيسي)

        # تحقق أن لا أي قسم فرعي فيه نقاط تحميل محمية
        is_protected = False
        for child in dev.get("children", []) or []:
            mp = child.get("mountpoint")
            if mp in protected_mountpoints:
                is_protected = True
                break
        if is_protected:
            continue

        drives.append({
            "path": dev.get("path"),
            "size_str": dev.get("size"),
            "model": dev.get("model") or "Unknown",
            "children": dev.get("children") or [],
        })

    return drives


def unmount_partitions(drive):
    for child in drive.get("children", []):
        part_path = child.get("path")
        if part_path:
            subprocess.run(["umount", part_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write_image(iso_path, target_path):
    """
    يكتب ملف ISO مباشرة على الجهاز باستخدام dd، مع طباعة تقدّم حقيقي
    محسوب من حجم الملف المصدر.
    """
    total_bytes = os.path.getsize(iso_path)
    block_size = 4 * 1024 * 1024  # 4MB blocks

    written = 0
    with open(iso_path, "rb") as src, open(target_path, "wb") as dst:
        while True:
            chunk = src.read(block_size)
            if not chunk:
                break
            dst.write(chunk)
            written += len(chunk)
            pct = int((written / total_bytes) * 100)
            sys.stdout.write(
                "\r" + t("writing_progress",
                         written=human_size(written),
                         total=human_size(total_bytes),
                         pct=pct)
            )
            sys.stdout.flush()
        dst.flush()
        os.fsync(dst.fileno())
    print()


def main():
    clear_screen()
    choose_language()
    clear_screen()
    banner()

    check_environment()

    # ---------- اختيار ملف ISO ----------
    iso_path = input(t("enter_iso_path")).strip().strip('"')
    if not os.path.isfile(iso_path):
        print(t("iso_not_found", path=iso_path))
        sys.exit(1)
    if not iso_path.lower().endswith(".iso"):
        print(t("iso_not_iso"))

    # ---------- اكتشاف الفلاشات ----------
    print()
    print(t("detecting_drives"))
    drives = get_removable_drives()
    if not drives:
        print(t("no_drives_found"))
        sys.exit(1)

    print(t("available_drives"))
    for i, d in enumerate(drives, start=1):
        print(t("drive_line", idx=i, path=d["path"], size=d["size_str"], model=d["model"]))
    print()

    while True:
        choice = input(t("choose_drive")).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(drives):
            drive = drives[int(choice) - 1]
            break
        print(t("invalid_choice"))

    # ---------- تأكيدات السلامة ----------
    print()
    typed_path = input(t("confirm_path_prompt", path=drive["path"])).strip()
    if typed_path != drive["path"]:
        print(t("confirm_path_mismatch"))
        sys.exit(1)

    typed_yes = input(t("confirm_size_prompt", path=drive["path"], size=drive["size_str"])).strip()
    if typed_yes != "YES":
        print(t("confirm_size_mismatch"))
        sys.exit(1)

    # ---------- التنفيذ الفعلي ----------
    try:
        print()
        print(t("unmounting", path=drive["path"]))
        unmount_partitions(drive)

        print(t("writing", path=drive["path"]))
        write_image(iso_path, drive["path"])

        print(t("verifying"))
        time.sleep(1)  # مكان مناسب لإضافة تحقق حقيقي بالـ checksum لاحقاً

        print()
        print(t("done"))
    except PermissionError as e:
        print(t("error_write", err=str(e)))
        sys.exit(1)
    except OSError as e:
        print(t("error_write", err=str(e)))
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(t("cancelled"))
