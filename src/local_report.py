"""Local-only demo data, CSV export, and an offline browser report.

This module never makes network requests. All SQL queries are read-only except
for the explicit synthetic demo builder, and the report omits developer contacts.
"""
import csv
import html
import sqlite3
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from models.AppDetails import AppDetails, Source


COLUMNS = (
    "package_name", "name", "category", "sub_category", "installation_count",
    "average_score", "comment_count", "version", "last_update", "source",
)
MAX_REPORT_ROWS = 1000


def create_demo(db_path: Path) -> int:
    """Create twelve unmistakably fictional apps in a caller-selected database."""
    examples = (
        ("ir.example.demo.weather", "آب‌نمای روز", "آب‌وهوا", 125000, 4.7, "2.4"),
        ("ir.example.demo.notes", "یادداشت‌یار", "بهره‌وری", 83500, 4.5, "3.1"),
        ("ir.example.demo.learn", "کلاس‌خانه", "آموزش", 72000, 4.8, "1.9"),
        ("ir.example.demo.budget", "حساب‌بان", "مالی", 45000, 4.2, "2.2"),
        ("ir.example.demo.maps", "مسیرنما", "سفر", 198000, 4.6, "4.0"),
        ("ir.example.demo.music", "آوای من", "سرگرمی", 335000, 4.4, "2.7"),
        ("ir.example.demo.read", "کتابک", "آموزش", 66500, 4.9, "1.5"),
        ("ir.example.demo.focus", "تمرکز پلاس", "بهره‌وری", 21800, 4.3, "1.4"),
        ("ir.example.demo.food", "آشپزباشی", "سبک زندگی", 164000, 4.5, "3.0"),
        ("ir.example.demo.fit", "تندرست", "سلامت", 57000, 4.7, "2.8"),
        ("ir.example.demo.puzzle", "پازلستان", "سرگرمی", 291000, 4.1, "5.1"),
        ("ir.example.demo.travel", "سفرنامه", "سفر", 38200, 4.6, "1.8"),
    )
    if Path(db_path).exists():
        raise FileExistsError("Demo destination already exists; choose a new --db path")
    for package, name, category, installs, score, version in examples:
        AppDetails(
            package_name=package, name=name, category=category,
            installation_count=installs, average_score=score,
            comment_count=12, version=version, source=Source.MYKET,
            tags=["DEMO", "synthetic"],
            short_description="Synthetic example; not collected from Myket.",
        ).save_to_db(str(db_path))
    return len(examples)


def _read_rows(db_path: Path, limit: int = 0) -> List[Dict]:
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise ValueError("SQLite file does not exist: {}".format(path))
    # Read-only mode: do not create an empty database as a side effect.
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        found = {row[1] for row in connection.execute("PRAGMA table_info(app_details)")}
        missing = set(COLUMNS) - found
        if missing:
            raise ValueError("Database does not contain the expected app_details schema")
        query = "SELECT " + ", ".join(COLUMNS) + " FROM app_details ORDER BY name, package_name"
        if limit:
            rows = connection.execute(query + " LIMIT ?", (limit,)).fetchall()
        else:
            rows = connection.execute(query).fetchall()
    return [dict(row) for row in rows]


def _safe_csv(value) -> str:
    value = "" if value is None else str(value)
    # Protect spreadsheet consumers against formula execution in untrusted names.
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        value = "'" + value
    return value


def export_csv(db_path: Path, output: Path) -> int:
    rows = _read_rows(db_path)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow([_safe_csv(row[column]) for column in COLUMNS])
    return len(rows)


def _format_int(value) -> str:
    return format(int(value or 0), ",")


def _format_date(value) -> str:
    try:
        stamp = int(value or 0)
        if stamp <= 0:
            return "نامشخص"
        return datetime.fromtimestamp(stamp, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, TypeError, ValueError):
        return "نامشخص"


def create_report(db_path: Path, output: Path, limit: int = 500) -> int:
    if not 1 <= limit <= MAX_REPORT_ROWS:
        raise ValueError("Report limit must be between 1 and {}".format(MAX_REPORT_ROWS))
    # Fetch only a bounded number of rows for a responsive standalone report.
    rows = _read_rows(db_path, limit + 1)
    truncated = len(rows) > limit
    rows = rows[:limit]
    total = len(rows)
    categories = Counter(str(row.get("category") or "نامشخص") for row in rows)
    installs = sum(int(row.get("installation_count") or 0) for row in rows)
    ratings = [float(row["average_score"]) for row in rows if row.get("average_score")]
    mean = sum(ratings) / len(ratings) if ratings else 0.0

    # The HTML remains a single self-contained, offline file. No external fonts,
    # images, scripts, data sources, or local servers are required.
    resource_dir = Path(__file__).resolve().parent
    template = (resource_dir / "report_template.html").read_text(encoding="utf-8")
    style = (resource_dir / "report_style.css").read_text(encoding="utf-8")
    script = (resource_dir / "report_interactions.js").read_text(encoding="utf-8")

    def fmt(value):
        return html.escape("" if value is None else str(value), quote=True)

    table_rows = []
    for idx, row in enumerate(rows):
        name = str(row.get("name") or "بدون نام")
        package = str(row.get("package_name") or "")
        category = str(row.get("category") or "نامشخص")
        version = str(row.get("version") or "—")
        installs_value = int(row.get("installation_count") or 0)
        rating_value = float(row.get("average_score") or 0)
        rating_text = "{:.1f}".format(rating_value) if rating_value else "—"
        search_text = " ".join((name, package, category, str(row.get("sub_category") or "")))
        table_rows.append(
            '<tr data-name="{name}" data-search="{search}" data-category="{category}" '
            'data-installs="{installs}" data-rating="{rating}">'
            '<td class="app-cell" data-label="اپلیکیشن"><div class="app-details">'
            '<span class="app-monogram tint-{tint}" aria-hidden="true">{initial}</span>'
            '<span><strong class="app-title" dir="auto">{name}</strong>'
            '<small class="app-package" dir="ltr">{package}</small></span></div></td>'
            '<td data-label="دسته‌بندی"><span class="category-pill" dir="auto">{category}</span></td>'
            '<td class="data-num" data-label="نصب">{formatted_installs}</td>'
            '<td data-label="امتیاز"><span class="rating-chip"><span class="rating-star" aria-hidden="true">★</span>{rating_text}</span></td>'
            '<td class="data-num" data-label="نسخه">{version}</td>'
            '<td class="data-num" data-label="به‌روزرسانی">{updated}</td></tr>'.format(
                name=fmt(name),
                search=fmt(search_text),
                category=fmt(category),
                installs=installs_value,
                rating=rating_value,
                tint=idx % 4,
                initial=fmt(name[:1]),
                package=fmt(package),
                formatted_installs=fmt(_format_int(installs_value)),
                rating_text=fmt(rating_text),
                version=fmt(version),
                updated=fmt(_format_date(row.get("last_update"))),
            )
        )

    category_rows = []
    category_options = []
    for category, count in categories.most_common(5):
        percent = (100.0 * count / total) if total else 0
        category_rows.append(
            '<div class="category-row">'
            '<div class="bar-info"><span dir="auto">{category}</span>'
            '<span>{count} برنامه · {percent:.0f}٪</span></div>'
            '<div class="bar-track" role="meter" aria-label="{category}" '
            'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent:.0f}">'
            '<div class="bar-fill" style="--bar:{percent:.1f}%"></div></div></div>'.format(
                category=fmt(category), count=count, percent=percent,
            )
        )
    for category in sorted(categories, key=lambda value: value.casefold()):
        category_options.append('<option value="{0}">{0}</option>'.format(fmt(category)))

    if not category_rows:
        category_rows.append('<p class="section-helper">هنوز برنامه‌ای برای نمایش وجود ندارد.</p>')

    cutoff = (
        "این گزارش تنها {} ردیف نخست را نشان می‌دهد. برای همهٔ داده‌ها از CSV استفاده کنید.".format(limit)
        if truncated else "تمام ردیف‌های موجود در این پایگاه داده نمایش داده می‌شوند."
    )
    # Demo data is always clearly labelled and never presented as live data.
    is_demo = bool(rows) and all(
        str(row.get("package_name") or "").startswith("ir.example.demo.")
        for row in rows
    )
    replacements = (
        ("__REPORT_STYLE__", style),
        ("__REPORT_SCRIPT__", script),
        ("__REPORT_COUNT__", fmt(_format_int(total))),
        ("__REPORT_CATEGORIES__", fmt(_format_int(len(categories)))),
        ("__REPORT_INSTALLS__", fmt(_format_int(installs))),
        ("__REPORT_MEAN__", fmt("{:.1f}".format(mean))),
        ("__REPORT_MODE__", "دموی ساختگی · غیرواقعی" if is_demo else "گزارش داده‌های محلی"),
        ("__REPORT_CUTOFF__", fmt(cutoff)),
        ("__REPORT_CATEGORY_BARS__", "\n".join(category_rows)),
        ("__REPORT_CATEGORY_OPTIONS__", "\n".join(category_options)),
        ("__REPORT_ROWS__", "\n".join(table_rows)),
    )
    page = template
    for token, content in replacements:
        page = page.replace(token, content)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    return total
