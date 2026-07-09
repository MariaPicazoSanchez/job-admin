import json
import threading
import webbrowser
from datetime import date
from pathlib import Path
from tkinter import StringVar

import customtkinter as ctk

from search import search_jobs
from search.aggregator import search_jobs_streaming
from search.models import Job
from search.adzuna import is_configured as adzuna_configured
from search import store
from search.store import SavedJob, ESTADOS, INTERES, make_id

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Tipografía global (Segoe UI: limpia y profesional en Windows) ─────────────
APP_FONT  = "Segoe UI"
ICON_FONT = "Segoe MDL2 Assets"   # iconos vectoriales nítidos de Windows 10/11
try:
    ctk.ThemeManager.theme["CTkFont"]["family"] = APP_FONT
except Exception:
    pass

# Glifos de iconos (Segoe MDL2 Assets)
ICON = {
    "back":      "",
    "search":    "",
    "profile":   "",
    "list":      "",
    "calendar":  "",
    "delete":    "",
    "link":      "",
    "close":     "",
    "check":     "",
}


def icon_font(size: int = 16):
    return ctk.CTkFont(family=ICON_FONT, size=size)


# ── Paleta (oscura, profesional, con acento vivo) ─────────────────────────────
ACCENT       = "#6d6cff"   # índigo vibrante
ACCENT_HOVER = "#5a59f0"
BG           = "#0e0f1a"
BG_SIDE      = "#0a0b14"
SURFACE      = "#1b1d31"
SURFACE_2    = "#23263f"
BORDER       = "#2c2f4a"
TEXT         = "#ececf6"
TEXT_DIM     = "#a6a8c8"
TEXT_MUTE    = "#74769a"

CONFIG_FILE = Path(__file__).parent / "config.json"

PAISES = [
    "Cualquier país", "España", "México", "Argentina", "Colombia",
    "Chile", "Estados Unidos", "Reino Unido", "Alemania", "Francia",
    "Países Bajos", "Canadá", "Australia", "Brasil", "Uruguay",
]
EXPERIENCIA = [
    "Cualquier nivel", "Sin experiencia", "Junior (0-2 años)",
    "Mid (2-5 años)", "Senior (5-10 años)", "Lead / Principal (10+ años)",
]
MONEDAS = ["EUR", "USD", "MXN", "ARS", "COP", "CLP", "BRL"]

TAG_COLORS = {
    "Remoto":     ("#1d4ed8", "#93c5fd"),
    "Híbrido":    ("#7c3aed", "#c4b5fd"),
    "Presencial": ("#0f766e", "#5eead4"),
}
SENIORITY_COLORS = {
    "Prácticas": ("#7f1d1d", "#fca5a5"),
    "Junior":    ("#713f12", "#fde68a"),
    "Mid":       ("#1e3a5f", "#93c5fd"),
    "Senior":    ("#1a2e1a", "#86efac"),
    "Lead":      ("#2e1065", "#ddd6fe"),
}
SOURCE_COLORS = {
    "Remotive":    ("#065f46", "#6ee7b7"),
    "Adzuna":      ("#92400e", "#fcd34d"),
    "Arbeitnow":   ("#1e3a8a", "#93c5fd"),
    "Computrabajo":("#4c1d95", "#ddd6fe"),
    "LinkedIn":    ("#0a3254", "#7dd3fc"),
}
STATUS_COLORS = {
    "Guardada":             ("#374151", "#d1d5db"),
    "Pendiente de aplicar": ("#1e3a5f", "#93c5fd"),
    "Solicitud enviada":    ("#1e3a8a", "#93c5fd"),
    "CV revisado":          ("#3730a3", "#c4b5fd"),
    "Respuesta recibida":   ("#155e75", "#67e8f9"),
    "Entrevista HR":        ("#5b21b6", "#ddd6fe"),
    "Entrevista técnica":   ("#6d28d9", "#ddd6fe"),
    "Prueba técnica":       ("#7c3aed", "#e9d5ff"),
    "Oferta recibida":      ("#14532d", "#86efac"),
    "Rechazada":            ("#7f1d1d", "#fca5a5"),
    "Aceptada":             ("#166534", "#86efac"),
    "Ghosted":              ("#44403c", "#a8a29e"),
}
INTEREST_COLORS = {
    "Bajo":  ("#374151", "#9ca3af"),
    "Medio": ("#1e3a5f", "#93c5fd"),
    "Alto":  ("#14532d", "#86efac"),
}


# ──────────────────────────────────────────────────────────────
#  Job Card
# ──────────────────────────────────────────────────────────────
class JobCard(ctk.CTkFrame):
    def __init__(self, parent, job: Job, on_click=None, **kwargs):
        super().__init__(parent, corner_radius=10, fg_color="#1e1e2e", **kwargs)
        self.configure(border_width=1, border_color="#3a3a5c")
        self.columnconfigure(0, weight=1)
        self._job = job
        self._on_click = on_click

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header.columnconfigure(0, weight=1)

        title_btn = ctk.CTkButton(
            header, text=job.title,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="transparent", hover_color="#2a2a3e",
            anchor="w", cursor="hand2",
            command=self._handle_click,
        )
        title_btn.grid(row=0, column=0, sticky="w")

        salary_color = "#4ade80" if (job.salary_min or job.salary_max) else "#6b6b8a"
        ctk.CTkLabel(
            header, text=job.salary_display,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=salary_color, anchor="e",
        ).grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Meta
        meta = ctk.CTkFrame(self, fg_color="transparent")
        meta.grid(row=1, column=0, sticky="ew", padx=16, pady=2)

        ctk.CTkLabel(
            meta, text=f"🏢  {job.company or '—'}",
            font=ctk.CTkFont(size=12), text_color="#a0a0c0",
        ).pack(side="left")
        ctk.CTkLabel(
            meta, text=f"  •  📍 {job.location or '—'}",
            font=ctk.CTkFont(size=12), text_color="#a0a0c0",
        ).pack(side="left")

        # Tags + source badge
        tags_frame = ctk.CTkFrame(self, fg_color="transparent")
        tags_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 14))

        # Badge de seniority inferido
        if job.seniority_label:
            sb_bg, sb_fg = SENIORITY_COLORS.get(job.seniority_label, ("#374151", "#d1d5db"))
            ctk.CTkLabel(
                tags_frame, text=f"  {job.seniority_label}  ",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=sb_bg, text_color=sb_fg, corner_radius=6,
            ).pack(side="left", padx=(0, 6))

        for tag in job.tags:
            bg, fg = TAG_COLORS.get(tag, ("#374151", "#d1d5db"))
            ctk.CTkLabel(
                tags_frame, text=f"  {tag}  ",
                font=ctk.CTkFont(size=11),
                fg_color=bg, text_color=fg, corner_radius=6,
            ).pack(side="left", padx=(0, 6))

        # Source badge (right-aligned via separate label)
        src_bg, src_fg = SOURCE_COLORS.get(job.source, ("#374151", "#d1d5db"))
        ctk.CTkLabel(
            tags_frame, text=f"  {job.source}  ",
            font=ctk.CTkFont(size=10),
            fg_color=src_bg, text_color=src_fg, corner_radius=6,
        ).pack(side="right")

    def _handle_click(self):
        if self._on_click:
            self._on_click(self._job)
        else:
            self._open_url()

    def _open_url(self):
        if self._job.url:
            webbrowser.open(self._job.url)




# ──────────────────────────────────────────────────────────────
#  Job Intelligence Panel
# ──────────────────────────────────────────────────────────────
_SIGNAL_COLORS = {
    "danger":   ("#5c1c1c", "#fca5a5"),
    "warning":  ("#5c3c0e", "#fde68a"),
    "positive": ("#0f3320", "#86efac"),
    "info":     ("#162640", "#93c5fd"),
}


class JobDetailPanel(ctk.CTkFrame):
    """Panel lateral con análisis inteligente de la oferta seleccionada."""

    WIDTH = 460

    def __init__(self, parent, on_close, on_save=None, **kwargs):
        super().__init__(
            parent, width=self.WIDTH, corner_radius=0,
            fg_color="#0a0a17",
            border_width=1, border_color="#1e1e3a",
            **kwargs,
        )
        self.grid_propagate(False)
        self._on_close = on_close
        self._on_save = on_save
        self._job = None
        self._country = "España"
        self._market = None
        self._build()

    # ── Estructura base ───────────────────────────────────
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Cabecera fija
        hdr = ctk.CTkFrame(self, fg_color="#13132a", corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(0, weight=1)

        self._lbl_title = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w", justify="left", wraplength=360,
        )
        self._lbl_title.grid(row=0, column=0, padx=16, pady=(14, 2), sticky="ew")

        self._lbl_meta = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont(size=11), text_color="#8080a0",
            anchor="w", wraplength=380,
        )
        self._lbl_meta.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="w")

        ctk.CTkButton(
            hdr, text="✕", width=30, height=30,
            fg_color="transparent", hover_color="#1e1e3a",
            font=ctk.CTkFont(size=13),
            command=self._on_close,
        ).grid(row=0, column=1, padx=(0, 10), pady=(10, 0))

        # Cuerpo con scroll
        self._body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#2a2a4a",
        )
        self._body.grid(row=1, column=0, sticky="nsew")
        self._body.columnconfigure(0, weight=1)

    # ── Pública: cargar oferta ────────────────────────────
    def show(self, job, country="España", market=None):
        self._job = job
        self._country = country
        self._market = market
        self._lbl_title.configure(text=job.title)
        self._lbl_meta.configure(
            text=f"🏢 {job.company or '—'}   •   📍 {job.location or '—'}"
        )
        self._populate(job)
        # Scroll al inicio
        try:
            self._body._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    # ── Construcción del cuerpo ───────────────────────────
    def _populate(self, job):
        for w in self._body.winfo_children():
            w.destroy()

        from search.analyzer import analyze_job
        ana = analyze_job(job, self._country)

        r = 0

        # ── Badges rápidos (salario + modalidad + seniority) ──
        badges = ctk.CTkFrame(self._body, fg_color="transparent")
        badges.grid(row=r, column=0, sticky="w", padx=16, pady=(14, 6))
        salary_fg = "#4ade80" if (job.salary_min or job.salary_max) else "#6b6b8a"
        salary_bg = "#0f3320" if (job.salary_min or job.salary_max) else "#18181f"
        self._pill(badges, job.salary_display, salary_fg, salary_bg)
        type_map = {
            "remote":  ("Remoto",     "#93c5fd", "#1d4ed8"),
            "hybrid":  ("Híbrido",    "#c4b5fd", "#7c3aed"),
            "onsite":  ("Presencial", "#5eead4", "#0f766e"),
        }
        if job.job_type in type_map:
            lbl, fg, bg = type_map[job.job_type]
            self._pill(badges, lbl, fg, bg)
        if job.seniority_label:
            sb_bg, sb_fg = SENIORITY_COLORS.get(job.seniority_label, ("#374151", "#d1d5db"))
            self._pill(badges, ana.seniority_detail or job.seniority_label, sb_fg, sb_bg)
        r += 1

        # ── Análisis rápido (resumen IA) ──────────────────
        if ana.ai_summary:
            r = self._section(r, "💡  Análisis rápido")
            card = ctk.CTkFrame(self._body, fg_color="#13132a", corner_radius=8)
            card.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 4))
            card.columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card, text=ana.ai_summary,
                font=ctk.CTkFont(size=12), text_color="#b0b0d0",
                wraplength=400, justify="left", anchor="w",
            ).grid(row=0, column=0, padx=14, pady=12, sticky="ew")
            r += 1

        # ── Salary Intelligence ───────────────────────────
        if ana.salary_estimate:
            est = ana.salary_estimate
            r = self._section(r, "💰  Estimación salarial")
            scard = ctk.CTkFrame(self._body, fg_color="#13132a", corner_radius=8)
            scard.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 4))
            scard.columnconfigure(0, weight=1)
            ctk.CTkLabel(
                scard, text=est.range_display,
                font=ctk.CTkFont(size=18, weight="bold"), text_color="#4ade80",
                anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(12, 0), sticky="w")
            ctk.CTkLabel(
                scard, text=f"≈ bruto anual  ·  {est.basis}",
                font=ctk.CTkFont(size=10), text_color="#6b6b8a", anchor="w",
            ).grid(row=1, column=0, padx=14, pady=(0, 4), sticky="w")
            if est.comparison:
                cmp_color = {
                    "positive": "#86efac", "negative": "#fca5a5", "neutral": "#93c5fd",
                }.get(est.comparison_kind, "#a0a0c0")
                ctk.CTkLabel(
                    scard, text=f"Esta oferta: {est.comparison}",
                    font=ctk.CTkFont(size=11, weight="bold"), text_color=cmp_color,
                    anchor="w",
                ).grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")
            else:
                ctk.CTkLabel(
                    scard, text="Estimación orientativa (heurística, no dato real)",
                    font=ctk.CTkFont(size=10), text_color="#4a4a6a", anchor="w",
                ).grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")
            r += 1

        # ── Señales ───────────────────────────────────────
        if ana.signals:
            r = self._section(r, "🔎  Señales detectadas")
            for sig in ana.signals:
                bg, fg = _SIGNAL_COLORS.get(sig.kind, ("#1e1e2e", "#d1d5db"))
                sc = ctk.CTkFrame(self._body, fg_color=bg, corner_radius=8)
                sc.grid(row=r, column=0, sticky="ew", padx=16, pady=2)
                sc.columnconfigure(1, weight=1)
                ctk.CTkLabel(sc, text=sig.emoji,
                             font=ctk.CTkFont(size=15)).grid(row=0, column=0, padx=(10, 5), pady=8)
                ctk.CTkLabel(sc, text=sig.label,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=fg, anchor="w").grid(row=0, column=1, sticky="w")
                if sig.detail:
                    ctk.CTkLabel(
                        sc, text=sig.detail,
                        font=ctk.CTkFont(size=11), text_color=fg,
                        wraplength=380, justify="left", anchor="w",
                    ).grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 8), sticky="w")
                r += 1

        # ── Hard skills ───────────────────────────────────
        if ana.hard_skills:
            r = self._section(r, "🛠️  Hard skills")
            sf = ctk.CTkFrame(self._body, fg_color="transparent")
            sf.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 4))
            for i, sk in enumerate(ana.hard_skills):
                ctk.CTkLabel(
                    sf, text=f"  {sk}  ",
                    font=ctk.CTkFont(size=11),
                    fg_color="#162640", text_color="#93c5fd", corner_radius=6,
                ).grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky="w")
            r += 1

        # ── Soft skills ───────────────────────────────────
        if ana.soft_skills:
            r = self._section(r, "🤝  Soft skills")
            sf2 = ctk.CTkFrame(self._body, fg_color="transparent")
            sf2.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 4))
            for i, sk in enumerate(ana.soft_skills):
                ctk.CTkLabel(
                    sf2, text=f"  {sk}  ",
                    font=ctk.CTkFont(size=11),
                    fg_color="#1a2030", text_color="#7dd3fc", corner_radius=6,
                ).grid(row=i // 2, column=i % 2, padx=3, pady=3, sticky="w")
            r += 1

        # ── Insights de mercado ───────────────────────────
        if self._market and self._market.total > 1:
            r = self._market_section(r, self._market)

        # ── Descripción (por bloques si se detectan) ──────
        block_icons = {
            "Responsabilidades": "🎯",
            "Requisitos":        "✅",
            "Beneficios":        "🎁",
            "Sobre la empresa":  "🏢",
        }
        if ana.description_blocks:
            for label in ("Responsabilidades", "Requisitos", "Beneficios", "Sobre la empresa"):
                body_txt = ana.description_blocks.get(label)
                if not body_txt:
                    continue
                icon = block_icons.get(label, "📄")
                r = self._section(r, f"{icon}  {label}")
                bcard = ctk.CTkFrame(self._body, fg_color="#13132a", corner_radius=8)
                bcard.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 4))
                bcard.columnconfigure(0, weight=1)
                ctk.CTkLabel(
                    bcard, text=body_txt,
                    font=ctk.CTkFont(size=11), text_color="#9090b0",
                    wraplength=400, justify="left", anchor="nw",
                ).grid(row=0, column=0, padx=14, pady=12, sticky="ew")
                r += 1
        elif ana.has_rich_description:
            r = self._section(r, "📄  Descripción")
            dcard = ctk.CTkFrame(self._body, fg_color="#13132a", corner_radius=8)
            dcard.grid(row=r, column=0, sticky="ew", padx=16, pady=(0, 4))
            dcard.columnconfigure(0, weight=1)
            snippet = ana.clean_description[:700]
            if len(ana.clean_description) > 700:
                snippet += "\n…"
            ctk.CTkLabel(
                dcard, text=snippet,
                font=ctk.CTkFont(size=11), text_color="#808098",
                wraplength=400, justify="left", anchor="nw",
            ).grid(row=0, column=0, padx=14, pady=12, sticky="ew")
            r += 1
        else:
            r = self._section(r, "📄  Descripción")
            ctk.CTkLabel(
                self._body,
                text="Descripción no disponible — abre la oferta para ver todos los detalles.",
                font=ctk.CTkFont(size=11), text_color="#4a4a6a",
                wraplength=400, justify="left",
            ).grid(row=r, column=0, padx=16, pady=(0, 8), sticky="w")
            r += 1

        # ── Botón guardar en Mis Ofertas ──────────────────
        already = store.is_saved(job.url, job.title)
        self._save_btn = ctk.CTkButton(
            self._body,
            text=("✓  Guardada en Mis Ofertas" if already else "Guardar oferta"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#163524" if already else SURFACE,
            hover_color="#11301f" if already else SURFACE_2,
            text_color="#86efac" if already else TEXT,
            command=self._handle_save,
        )
        self._save_btn.grid(row=r, column=0, padx=16, pady=(12, 6), sticky="ew")
        r += 1

        # ── Botón aplicar ─────────────────────────────────
        ctk.CTkButton(
            self._body,
            text="Ver oferta completa",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=lambda: webbrowser.open(job.url) if job.url else None,
        ).grid(row=r, column=0, padx=16, pady=(0, 24), sticky="ew")

    def _handle_save(self):
        if self._job and self._on_save:
            self._on_save(self._job)
            self._save_btn.configure(
                text="✓  Guardada en Mis Ofertas",
                fg_color="#163524", hover_color="#11301f", text_color="#86efac",
            )

    # ── Sección de mercado ────────────────────────────────
    def _market_section(self, row: int, market) -> int:
        row = self._section(row, f"📊  Mercado · {market.total} ofertas similares")
        card = ctk.CTkFrame(self._body, fg_color="#13132a", corner_radius=8)
        card.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 4))
        card.columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        inner.columnconfigure(0, weight=1)
        ir = 0

        # Resumen mediana salarial + años medios
        bits = []
        if market.median_salary:
            bits.append(f"Mediana estimada: {market.median_salary:,} {market.salary_currency}".replace(",", "."))
        if market.avg_years is not None:
            bits.append(f"Experiencia media pedida: {market.avg_years} años")
        if bits:
            ctk.CTkLabel(
                inner, text="   ·   ".join(bits),
                font=ctk.CTkFont(size=11), text_color="#c0c0e0", anchor="w",
                wraplength=400, justify="left",
            ).grid(row=ir, column=0, sticky="w", pady=(0, 8))
            ir += 1

        # Tecnologías más demandadas con barra de %
        if market.top_skills:
            ctk.CTkLabel(
                inner, text="Tecnologías más demandadas:",
                font=ctk.CTkFont(size=10, weight="bold"), text_color="#7070a0", anchor="w",
            ).grid(row=ir, column=0, sticky="w", pady=(0, 4))
            ir += 1
            for skill, pct in market.top_skills[:6]:
                rowf = ctk.CTkFrame(inner, fg_color="transparent")
                rowf.grid(row=ir, column=0, sticky="ew", pady=1)
                rowf.columnconfigure(1, weight=1)
                ctk.CTkLabel(
                    rowf, text=skill, font=ctk.CTkFont(size=11),
                    text_color="#a0a0c0", anchor="w", width=110,
                ).grid(row=0, column=0, sticky="w")
                bar = ctk.CTkProgressBar(
                    rowf, height=8, corner_radius=4,
                    fg_color="#1e1e3a", progress_color="#6d6cff",
                )
                bar.set(pct / 100)
                bar.grid(row=0, column=1, sticky="ew", padx=(6, 6))
                ctk.CTkLabel(
                    rowf, text=f"{pct}%", font=ctk.CTkFont(size=10),
                    text_color="#7070a0", width=34, anchor="e",
                ).grid(row=0, column=2, sticky="e")
                ir += 1

        return row + 1

    # ── Utilidades ────────────────────────────────────────
    def _section(self, row: int, text: str) -> int:
        ctk.CTkLabel(
            self._body, text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#5a5a80", anchor="w",
        ).grid(row=row, column=0, padx=16, pady=(14, 4), sticky="w")
        return row + 1

    @staticmethod
    def _pill(parent, text: str, fg: str, bg: str):
        ctk.CTkLabel(
            parent, text=f"  {text}  ",
            font=ctk.CTkFont(size=11),
            fg_color=bg, text_color=fg, corner_radius=6,
        ).pack(side="left", padx=(0, 5))


# ──────────────────────────────────────────────────────────────
#  Selector de fecha (calendario sin dependencias)
# ──────────────────────────────────────────────────────────────
import calendar as _calendar

_MONTHS_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
_DAYS_ES = ["L", "M", "X", "J", "V", "S", "D"]


class DatePicker(ctk.CTkToplevel):
    """Mini-calendario emergente. Abre en el mes/año actual por defecto."""

    def __init__(self, parent, entry):
        super().__init__(parent)
        self.title("Seleccionar fecha")
        self.geometry("300x340")
        self.resizable(False, False)
        self.configure(fg_color="#12121f")
        self._entry = entry

        today = date.today()
        try:
            y, m, _ = map(int, entry.get().strip().split("-"))
            self._year, self._month = y, m
        except Exception:
            self._year, self._month = today.year, today.month

        self._grid_frame = None
        self._build()

        self.transient(parent)
        self.after(50, self._focus)

    def _focus(self):
        try:
            self.grab_set()
            self.lift()
            self.focus()
        except Exception:
            pass

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(14, 6))
        ctk.CTkButton(
            hdr, text="◀", width=36, fg_color="#1e1e2e", hover_color="#2a2a3e",
            command=self._prev_month,
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text=f"{_MONTHS_ES[self._month - 1]} {self._year}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            hdr, text="▶", width=36, fg_color="#1e1e2e", hover_color="#2a2a3e",
            command=self._next_month,
        ).pack(side="right")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=12, pady=4)
        for i, d in enumerate(_DAYS_ES):
            ctk.CTkLabel(
                grid, text=d, width=34, text_color="#6b6b8a",
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=i, padx=1, pady=2)

        today = date.today()
        cal = _calendar.Calendar(firstweekday=0)   # lunes
        rownum = 1
        for week in cal.monthdayscalendar(self._year, self._month):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                is_today = (day == today.day and self._month == today.month
                            and self._year == today.year)
                ctk.CTkButton(
                    grid, text=str(day), width=34, height=30,
                    font=ctk.CTkFont(size=12, weight="bold" if is_today else "normal"),
                    fg_color="#6d6cff" if is_today else "#1e1e2e",
                    hover_color="#5a59f0",
                    command=lambda d=day: self._pick(d),
                ).grid(row=rownum, column=col, padx=1, pady=1)
            rownum += 1

        ctk.CTkButton(
            self, text="Hoy", fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._pick(today.day, today.month, today.year),
        ).pack(fill="x", padx=12, pady=(8, 14))

    def _prev_month(self):
        self._month -= 1
        if self._month < 1:
            self._month, self._year = 12, self._year - 1
        self._build()

    def _next_month(self):
        self._month += 1
        if self._month > 12:
            self._month, self._year = 1, self._year + 1
        self._build()

    def _pick(self, day, month=None, year=None):
        y = year or self._year
        m = month or self._month
        self._entry.delete(0, "end")
        self._entry.insert(0, f"{y:04d}-{m:02d}-{day:02d}")
        self.destroy()


# ──────────────────────────────────────────────────────────────
#  Mis Ofertas — gestión de candidaturas
# ──────────────────────────────────────────────────────────────
class MyJobsView(ctk.CTkFrame):
    """Vista a pantalla completa para gestionar candidaturas guardadas."""

    def __init__(self, parent, on_back, **kwargs):
        super().__init__(parent, fg_color="#12121f", corner_radius=0, **kwargs)
        self._on_back = on_back
        self._mode = "tabla"          # "tabla" | "kanban"
        self._selected_id = None
        self._jobs: list[SavedJob] = []
        self._build()

    # ── Estructura ────────────────────────────────────────
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)   # panel de edición
        self.rowconfigure(2, weight=1)

        # Barra superior: volver + título + toggle vista
        top = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=0, height=64)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        top.grid_propagate(False)
        top.columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text=ICON["back"], width=44, height=40,
            font=icon_font(16),
            fg_color=SURFACE, hover_color=SURFACE_2, text_color=TEXT,
            command=self._on_back,
        ).grid(row=0, column=0, padx=(20, 12), pady=12)

        ctk.CTkLabel(
            top, text="Mis Ofertas",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#ececf6",
        ).grid(row=0, column=1, sticky="w")

        toggle = ctk.CTkSegmentedButton(
            top, values=["Tabla", "Kanban"],
            command=self._set_mode,
            fg_color="#1e1e2e", selected_color="#6d6cff",
            selected_hover_color="#5a59f0", unselected_color="#1e1e2e",
        )
        toggle.set("Tabla")
        toggle.grid(row=0, column=2, padx=20, pady=12)

        # Barra de estadísticas
        self._stats_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._stats_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=24, pady=(14, 6))

        # Contenido (tabla o kanban)
        self.content_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#3a3a5c", orientation="vertical",
        )
        self.content_scroll.grid(row=2, column=0, sticky="nsew", padx=(24, 12), pady=(0, 16))
        self.content_scroll.columnconfigure(0, weight=1)

        # Panel de edición (oculto hasta seleccionar)
        self._edit_panel = ctk.CTkFrame(
            self, width=380, corner_radius=0, fg_color="#0a0a17",
            border_width=1, border_color="#1e1e3a",
        )
        self._edit_panel.grid_propagate(False)
        self._edit_panel.columnconfigure(0, weight=1)
        self._edit_panel.rowconfigure(0, weight=1)
        self.edit_scroll = ctk.CTkScrollableFrame(
            self._edit_panel, fg_color="transparent",
            scrollbar_button_color="#2a2a4a",
        )
        self.edit_scroll.grid(row=0, column=0, sticky="nsew")
        self.edit_scroll.columnconfigure(0, weight=1)

    # ── Refresco general ──────────────────────────────────
    def refresh(self):
        self._jobs = store.load_all()
        self._render_stats()
        self._render_content()
        if self._selected_id and not any(j.id == self._selected_id for j in self._jobs):
            self._selected_id = None
            self._edit_panel.grid_remove()
        elif self._selected_id:
            self._render_edit()

    def _set_mode(self, value):
        self._mode = value.lower()
        self._render_content()

    # ── Estadísticas ──────────────────────────────────────
    def _render_stats(self):
        for w in self._stats_bar.winfo_children():
            w.destroy()
        s = store.compute_stats(self._jobs)
        cards = [
            ("Guardadas",   s["total"],       "#93c5fd"),
            ("Enviadas",    s["enviadas"],     "#c4b5fd"),
            ("Entrevistas", s["entrevistas"],  "#ddd6fe"),
            ("Activas",     s["activas"],      "#86efac"),
            ("% Respuesta", f"{s['ratio']}%",  "#fcd34d"),
        ]
        for i, (label, value, color) in enumerate(cards):
            c = ctk.CTkFrame(self._stats_bar, fg_color="#1a1a2e", corner_radius=8)
            c.grid(row=0, column=i, padx=(0, 10), sticky="w")
            ctk.CTkLabel(
                c, text=str(value), font=ctk.CTkFont(size=20, weight="bold"),
                text_color=color,
            ).grid(row=0, column=0, padx=18, pady=(8, 0))
            ctk.CTkLabel(
                c, text=label, font=ctk.CTkFont(size=11), text_color="#8080a0",
            ).grid(row=1, column=0, padx=18, pady=(0, 8))

    # ── Contenido: tabla / kanban ─────────────────────────
    def _render_content(self):
        for w in self.content_scroll.winfo_children():
            w.destroy()
        if not self._jobs:
            self._render_empty()
        elif self._mode == "kanban":
            self._render_kanban()
        else:
            self._render_table()

    def _render_empty(self):
        frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        frame.grid(row=0, column=0, pady=100)
        ctk.CTkLabel(frame, text="📭", font=ctk.CTkFont(size=48)).pack(pady=(0, 12))
        ctk.CTkLabel(
            frame, text="Aún no has guardado ofertas",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#4a4a6a",
        ).pack()
        ctk.CTkLabel(
            frame, text="Vuelve al buscador y pulsa «⭐ Guardar oferta» en una oferta.",
            font=ctk.CTkFont(size=13), text_color="#3a3a5a",
        ).pack(pady=(8, 0))

    # — Tabla (estilo hoja de cálculo) —
    _TABLE_COLS = [
        ("Empresa", 3), ("Puesto", 4), ("Localidad", 2), ("Experiencia", 2),
        ("Estado", 3), ("Interés", 2), ("Aplicado", 2), ("Observaciones", 3),
    ]
    # límite de caracteres por columna (para truncar con "…")
    _TABLE_TRUNC = {0: 22, 1: 30, 2: 16, 3: 14, 6: 12, 7: 26}

    def _render_table(self):
        # Contenedor con fondo oscuro → los huecos entre filas parecen líneas de rejilla
        table = ctk.CTkFrame(self.content_scroll, fg_color="#0a0a14", corner_radius=8)
        table.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        table.columnconfigure(0, weight=1)

        # Cabecera
        header = ctk.CTkFrame(table, fg_color="#1a1a2e", corner_radius=0, height=38)
        header.grid(row=0, column=0, sticky="ew", padx=1, pady=(1, 1))
        for i, (name, w) in enumerate(self._TABLE_COLS):
            header.columnconfigure(i, weight=w, uniform="tcol")
            ctk.CTkLabel(
                header, text=name.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#7070a0", anchor="w",
            ).grid(row=0, column=i, padx=12, pady=10, sticky="w")

        # Filas
        for ri, job in enumerate(self._jobs):
            selected = (job.id == self._selected_id)
            zebra = "#16162a" if ri % 2 == 0 else "#1b1b30"
            base = "#26264a" if selected else zebra
            rowf = ctk.CTkFrame(table, fg_color=base, corner_radius=0, cursor="hand2")
            rowf.grid(row=ri + 1, column=0, sticky="ew", padx=1, pady=(0, 1))
            for i, (_, w) in enumerate(self._TABLE_COLS):
                rowf.columnconfigure(i, weight=w, uniform="tcol")

            cells = [rowf]   # widgets que comparten hover/click

            notes_one_line = " ".join((job.notes or "").split())

            # 0 Empresa
            cells.append(self._cell_text(rowf, 0, self._trunc(job.company or "—", 0),
                                         "#ececf6", bold=True))
            # 1 Puesto
            cells.append(self._cell_text(rowf, 1, self._trunc(job.title, 1), "#c0c0e0"))
            # 2 Localidad
            cells.append(self._cell_text(rowf, 2, self._trunc(job.location or "—", 2), "#a0a0c0"))
            # 3 Experiencia
            cells.append(self._cell_text(rowf, 3, self._trunc(job.seniority or "—", 3), "#a0a0c0"))
            # 4 Estado (badge)
            cells.append(self._cell_badge(rowf, 4, job.status,
                                          STATUS_COLORS.get(job.status, ("#374151", "#d1d5db")), bold=True))
            # 5 Interés (badge)
            cells.append(self._cell_badge(rowf, 5, job.interest,
                                          INTEREST_COLORS.get(job.interest, ("#374151", "#9ca3af"))))
            # 6 Aplicado
            cells.append(self._cell_text(rowf, 6, self._trunc(job.applied_date or "—", 6), "#a0a0c0"))
            # 7 Observaciones
            obs = notes_one_line if notes_one_line else "—"
            cells.append(self._cell_text(rowf, 7, self._trunc(obs, 7),
                                         "#c0c0e0" if notes_one_line else "#6b6b8a"))

            # Hover + click en toda la fila
            def _enter(_e, rf=rowf): rf.configure(fg_color="#2a2a4e")
            def _leave(_e, rf=rowf, b=base): rf.configure(fg_color=b)
            for wdg in cells:
                wdg.bind("<Enter>", _enter)
                wdg.bind("<Leave>", _leave)
                wdg.bind("<Button-1>", lambda e, jid=job.id: self._select(jid))

    def _trunc(self, text, col):
        """Recorta el texto al límite de la columna añadiendo '…' si sobra."""
        limit = self._TABLE_TRUNC.get(col)
        text = str(text)
        if limit and len(text) > limit:
            return text[: limit - 1].rstrip() + "…"
        return text

    def _cell_text(self, parent, col, text, color, bold=False):
        lbl = ctk.CTkLabel(
            parent, text=text, anchor="w",
            font=ctk.CTkFont(size=12, weight="bold" if bold else "normal"),
            text_color=color,
        )
        lbl.grid(row=0, column=col, padx=12, pady=11, sticky="w")
        return lbl

    def _cell_badge(self, parent, col, text, colors, bold=False):
        bg, fg = colors
        lbl = ctk.CTkLabel(
            parent, text=f"  {text}  ",
            font=ctk.CTkFont(size=10, weight="bold" if bold else "normal"),
            fg_color=bg, text_color=fg, corner_radius=6,
        )
        lbl.grid(row=0, column=col, padx=10, pady=8, sticky="w")
        return lbl

    # — Kanban —
    def _render_kanban(self):
        wrap = ctk.CTkScrollableFrame(
            self.content_scroll, fg_color="transparent",
            orientation="horizontal", height=560,
            scrollbar_button_color="#3a3a5c",
        )
        wrap.grid(row=0, column=0, sticky="nsew")

        # Solo columnas con tarjetas (para no saturar)
        by_status: dict[str, list[SavedJob]] = {}
        for job in self._jobs:
            by_status.setdefault(job.status, []).append(job)
        visible = [s for s in ESTADOS if s in by_status]

        for ci, status in enumerate(visible):
            bg, fg = STATUS_COLORS.get(status, ("#374151", "#d1d5db"))
            col = ctk.CTkFrame(wrap, fg_color="#13132a", corner_radius=10, width=240)
            col.grid(row=0, column=ci, padx=6, pady=4, sticky="n")
            col.grid_propagate(False)
            col.columnconfigure(0, weight=1)

            head = ctk.CTkLabel(
                col, text=f" {status}  ·  {len(by_status[status])} ",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=bg, text_color=fg, corner_radius=6, anchor="w",
            )
            head.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))

            for ri, job in enumerate(by_status[status], start=1):
                self._kanban_card(col, job, ri, status)

    def _kanban_card(self, parent, job, row, status):
        card = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=8, cursor="hand2")
        card.grid(row=row, column=0, sticky="ew", padx=8, pady=4)
        card.columnconfigure(0, weight=1)
        card.bind("<Button-1>", lambda e: self._select(job.id))

        t = ctk.CTkLabel(
            card, text=job.title, font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ececf6", anchor="w", wraplength=200, justify="left",
        )
        t.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))
        t.bind("<Button-1>", lambda e: self._select(job.id))

        c = ctk.CTkLabel(
            card, text=f"🏢 {job.company or '—'}", font=ctk.CTkFont(size=11),
            text_color="#8080a0", anchor="w",
        )
        c.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))
        c.bind("<Button-1>", lambda e: self._select(job.id))

        # Flechas para mover de estado
        idx = ESTADOS.index(status)
        nav = ctk.CTkFrame(card, fg_color="transparent")
        nav.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 6))
        if idx > 0:
            ctk.CTkButton(
                nav, text="◀", width=28, height=24,
                fg_color="#2a2a3e", hover_color="#3a3a5e",
                command=lambda: self._move_status(job, -1),
            ).pack(side="left", padx=2)
        if idx < len(ESTADOS) - 1:
            ctk.CTkButton(
                nav, text="▶", width=28, height=24,
                fg_color="#2a2a3e", hover_color="#3a3a5e",
                command=lambda: self._move_status(job, +1),
            ).pack(side="right", padx=2)

    def _move_status(self, job, delta):
        idx = ESTADOS.index(job.status)
        new_idx = max(0, min(len(ESTADOS) - 1, idx + delta))
        if new_idx == idx:
            return
        new_status = ESTADOS[new_idx]
        store.update_fields(job.id, status=new_status)
        store.add_timeline(job.id, f"Estado → {new_status}")
        if store.is_applied_status(new_status):
            j = store.get(job.id)
            if j and not j.applied_date:
                store.update_fields(job.id, applied_date=store.today())
        self.refresh()

    # ── Selección + panel de edición ──────────────────────
    def _select(self, jid):
        self._selected_id = jid
        if not self._edit_panel.winfo_ismapped():
            self._edit_panel.grid(row=2, column=1, sticky="nsew", padx=(0, 0), pady=(0, 0))
        self._render_edit()
        self._render_content()   # refresca highlight de fila

    def _render_edit(self):
        for w in self.edit_scroll.winfo_children():
            w.destroy()
        job = next((j for j in self._jobs if j.id == self._selected_id), None)
        if not job:
            return

        r = 0
        # ── Cabecera ───────────────────────────────────────
        ctk.CTkLabel(
            self.edit_scroll, text=job.title,
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#ececf6",
            anchor="w", wraplength=330, justify="left",
        ).grid(row=r, column=0, padx=16, pady=(16, 2), sticky="ew"); r += 1
        ctk.CTkLabel(
            self.edit_scroll,
            text=f"🏢 {job.company or '—'}    📍 {job.location or '—'}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#a0a0c0",
            anchor="w", wraplength=330, justify="left",
        ).grid(row=r, column=0, padx=16, pady=(0, 2), sticky="w"); r += 1
        # Badges modalidad + fuente
        meta = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
        meta.grid(row=r, column=0, padx=16, pady=(2, 6), sticky="w"); r += 1
        type_map = {"remote": ("Remoto", "#93c5fd", "#1d4ed8"),
                    "hybrid": ("Híbrido", "#c4b5fd", "#7c3aed"),
                    "onsite": ("Presencial", "#5eead4", "#0f766e")}
        if job.job_type in type_map:
            lbl, fg, bg = type_map[job.job_type]
            ctk.CTkLabel(meta, text=f"  {lbl}  ", font=ctk.CTkFont(size=10),
                         fg_color=bg, text_color=fg, corner_radius=6).pack(side="left", padx=(0, 5))
        if job.source:
            sb, sf_ = SOURCE_COLORS.get(job.source, ("#374151", "#d1d5db"))
            ctk.CTkLabel(meta, text=f"  {job.source}  ", font=ctk.CTkFont(size=10),
                         fg_color=sb, text_color=sf_, corner_radius=6).pack(side="left", padx=(0, 5))

        # Enlace a la oferta (guardado siempre)
        if job.url:
            ctk.CTkButton(
                self.edit_scroll, text="Ver oferta original",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=ACCENT, hover_color=ACCENT_HOVER,
                command=lambda: webbrowser.open(job.url),
            ).grid(row=r, column=0, padx=16, pady=(4, 8), sticky="ew"); r += 1

        # ════════ DATOS DE LA OFERTA (solo lectura) ════════
        r = self._edit_section(r, "📋  Datos de la oferta")

        # Salario (publicado + estimado)
        scard = ctk.CTkFrame(self.edit_scroll, fg_color="#13132a", corner_radius=8)
        scard.grid(row=r, column=0, padx=16, pady=(0, 6), sticky="ew"); r += 1
        scard.columnconfigure(0, weight=1)
        pub = job.salary_display or "No indicado"
        ctk.CTkLabel(scard, text=f"💰  {pub}", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#4ade80" if pub != "No indicado" and "no indicado" not in pub.lower() else "#a0a0c0",
                     anchor="w").grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")
        if job.salary_estimate:
            ctk.CTkLabel(scard, text=f"Estimación de mercado: {job.salary_estimate}",
                         font=ctk.CTkFont(size=11), text_color="#8080a0",
                         anchor="w").grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")
        else:
            scard.grid_configure(pady=(0, 6))

        # Experiencia / seniority
        if job.seniority:
            erow = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
            erow.grid(row=r, column=0, padx=16, pady=(0, 6), sticky="w"); r += 1
            ctk.CTkLabel(erow, text="Experiencia:", font=ctk.CTkFont(size=11),
                         text_color="#8080a0").pack(side="left", padx=(0, 6))
            ctk.CTkLabel(erow, text=f"  {job.seniority}  ",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         fg_color="#1e2e1a", text_color="#86efac",
                         corner_radius=6).pack(side="left")

        # Cosas a tener en cuenta (señales)
        if job.signals:
            ctk.CTkLabel(
                self.edit_scroll, text="A tener en cuenta:",
                font=ctk.CTkFont(size=11), text_color="#8080a0", anchor="w",
            ).grid(row=r, column=0, padx=16, pady=(2, 4), sticky="w"); r += 1
            for sig in job.signals:
                bg, fg = _SIGNAL_COLORS.get(sig.get("kind", "info"), ("#1e1e2e", "#d1d5db"))
                sc = ctk.CTkFrame(self.edit_scroll, fg_color=bg, corner_radius=8)
                sc.grid(row=r, column=0, padx=16, pady=2, sticky="ew"); r += 1
                sc.columnconfigure(1, weight=1)
                ctk.CTkLabel(sc, text=sig.get("emoji", "•"),
                             font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(10, 5), pady=6)
                ctk.CTkLabel(sc, text=sig.get("label", ""),
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=fg, anchor="w").grid(row=0, column=1, sticky="w")
                if sig.get("detail"):
                    ctk.CTkLabel(sc, text=sig["detail"], font=ctk.CTkFont(size=10),
                                 text_color=fg, anchor="w", wraplength=290,
                                 justify="left").grid(row=1, column=0, columnspan=2,
                                                      padx=12, pady=(0, 6), sticky="w")

        # Descripción (resumida)
        if job.description:
            ctk.CTkLabel(
                self.edit_scroll, text="Descripción:",
                font=ctk.CTkFont(size=11), text_color="#8080a0", anchor="w",
            ).grid(row=r, column=0, padx=16, pady=(6, 4), sticky="w"); r += 1
            dcard = ctk.CTkFrame(self.edit_scroll, fg_color="#13132a", corner_radius=8)
            dcard.grid(row=r, column=0, padx=16, pady=(0, 6), sticky="ew"); r += 1
            dcard.columnconfigure(0, weight=1)
            snippet = job.description[:280] + ("…" if len(job.description) > 280 else "")
            ctk.CTkLabel(dcard, text=snippet, font=ctk.CTkFont(size=11),
                         text_color="#9090b0", wraplength=300, justify="left",
                         anchor="nw").grid(row=0, column=0, padx=12, pady=10, sticky="ew")

        # Tecnologías
        if job.skills:
            ctk.CTkLabel(
                self.edit_scroll, text="Tecnologías:",
                font=ctk.CTkFont(size=11), text_color="#8080a0", anchor="w",
            ).grid(row=r, column=0, padx=16, pady=(6, 4), sticky="w"); r += 1
            sf = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
            sf.grid(row=r, column=0, padx=16, pady=(0, 6), sticky="ew"); r += 1
            for i, sk in enumerate(job.skills[:9]):
                ctk.CTkLabel(sf, text=f"  {sk}  ", font=ctk.CTkFont(size=10),
                             fg_color="#162640", text_color="#93c5fd",
                             corner_radius=6).grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="w")

        # ════════ SEGUIMIENTO (editable) ════════
        r = self._edit_section(r, "✏️  Seguimiento")
        self._e_status   = self._field_option(r, "Estado", ESTADOS, job.status); r += 1
        self._e_interest = self._field_option(r, "Nivel de interés", INTERES, job.interest); r += 1
        self._e_applied  = self._field_date(r, "Fecha de solicitud", job.applied_date); r += 1
        self._e_interview = self._field_date(r, "Fecha de entrevista", job.interview_date); r += 1
        self._e_salary   = self._field_entry(r, "Salario ofrecido", job.salary_offered, "Ej: 35000 EUR"); r += 1
        self._e_contact  = self._field_entry(r, "Persona de contacto", job.contact, "Recruiter / responsable"); r += 1

        # Observaciones
        ctk.CTkLabel(
            self.edit_scroll, text="OBSERVACIONES",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#5a5a80", anchor="w",
        ).grid(row=r, column=0, padx=16, pady=(10, 4), sticky="w"); r += 1
        self._e_notes = ctk.CTkTextbox(
            self.edit_scroll, height=90, fg_color="#13132a",
            border_width=1, border_color="#2a2a4a", font=ctk.CTkFont(size=12),
        )
        self._e_notes.insert("1.0", job.notes or "")
        self._e_notes.grid(row=r, column=0, padx=16, pady=(0, 8), sticky="ew"); r += 1

        # Botones guardar / eliminar
        btns = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
        btns.grid(row=r, column=0, padx=16, pady=(6, 8), sticky="ew")
        btns.columnconfigure(0, weight=1)
        ctk.CTkButton(
            btns, text="Guardar cambios", font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6d6cff", hover_color="#5a59f0", command=self._save_edit,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(
            btns, text=ICON["delete"], width=40, font=icon_font(15),
            fg_color="#3a1a1a", hover_color="#5c1c1c", text_color="#fca5a5",
            command=self._delete,
        ).grid(row=0, column=1)
        r += 1

        # Historial
        if job.timeline:
            r = self._edit_section(r, "🕑  Historial")
            for ev in reversed(job.timeline[-8:]):
                ctk.CTkLabel(
                    self.edit_scroll,
                    text=f"• {ev.get('date','')}  —  {ev.get('event','')}",
                    font=ctk.CTkFont(size=11), text_color="#8080a0",
                    anchor="w", wraplength=330, justify="left",
                ).grid(row=r, column=0, padx=20, pady=1, sticky="w"); r += 1

    def _edit_section(self, row, text):
        ctk.CTkLabel(
            self.edit_scroll, text=text,
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#7070a0", anchor="w",
        ).grid(row=row, column=0, padx=16, pady=(14, 6), sticky="w")
        return row + 1

    # — campo de fecha: entry + 📅 calendario + Hoy —
    def _field_date(self, row, label, value):
        box = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
        box.grid(row=row, column=0, padx=16, pady=(8, 0), sticky="ew")
        box.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box, text=label.upper(),
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#5a5a80", anchor="w",
        ).grid(row=0, column=0, columnspan=3, pady=(0, 2), sticky="w")
        e = ctk.CTkEntry(
            box, placeholder_text="YYYY-MM-DD",
            fg_color="#13132a", border_color="#2a2a4a", border_width=1,
            font=ctk.CTkFont(size=12),
        )
        if value:
            e.insert(0, value)
        e.grid(row=1, column=0, sticky="ew")
        ctk.CTkButton(
            box, text=ICON["calendar"], width=38, font=icon_font(15),
            fg_color=SURFACE, hover_color=SURFACE_2, text_color=TEXT_DIM,
            command=lambda: DatePicker(self, e),
        ).grid(row=1, column=1, padx=(6, 0))
        ctk.CTkButton(
            box, text="Hoy", width=52, fg_color="#1e1e3a", hover_color="#2a2a4e",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self._set_today(e),
        ).grid(row=1, column=2, padx=(6, 0))
        return e

    @staticmethod
    def _set_today(entry):
        entry.delete(0, "end")
        entry.insert(0, store.today())

    # — helpers de campos (label + input en un contenedor por campo) —
    def _field_entry(self, row, label, value, placeholder=""):
        box = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
        box.grid(row=row, column=0, padx=16, pady=(8, 0), sticky="ew")
        box.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box, text=label.upper(),
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#5a5a80", anchor="w",
        ).grid(row=0, column=0, pady=(0, 2), sticky="w")
        e = ctk.CTkEntry(
            box, placeholder_text=placeholder,
            fg_color="#13132a", border_color="#2a2a4a", border_width=1,
            font=ctk.CTkFont(size=12),
        )
        if value:
            e.insert(0, value)
        e.grid(row=1, column=0, sticky="ew")
        return e

    def _field_option(self, row, label, values, value):
        box = ctk.CTkFrame(self.edit_scroll, fg_color="transparent")
        box.grid(row=row, column=0, padx=16, pady=(8, 0), sticky="ew")
        box.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box, text=label.upper(),
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#5a5a80", anchor="w",
        ).grid(row=0, column=0, pady=(0, 2), sticky="w")
        var = StringVar(value=value)
        om = ctk.CTkOptionMenu(
            box, values=values, variable=var,
            fg_color="#13132a", button_color="#3b3b5c",
            button_hover_color="#4f4f7a", dropdown_fg_color="#1e1e2e",
        )
        om.grid(row=1, column=0, sticky="ew")
        om._sel_var = var
        return om

    def _save_edit(self):
        job = next((j for j in self._jobs if j.id == self._selected_id), None)
        if not job:
            return
        new_status = self._e_status._sel_var.get()
        applied = self._e_applied.get().strip()
        # Auto-fecha si pasa a estado aplicado y no hay fecha
        if store.is_applied_status(new_status) and not applied:
            applied = store.today()
        fields = {
            "status":         new_status,
            "interest":       self._e_interest._sel_var.get(),
            "applied_date":   applied,
            "interview_date": self._e_interview.get().strip(),
            "salary_offered": self._e_salary.get().strip(),
            "contact":        self._e_contact.get().strip(),
            "notes":          self._e_notes.get("1.0", "end").strip(),
        }
        if new_status != job.status:
            store.add_timeline(job.id, f"Estado → {new_status}")
        store.update_fields(job.id, **fields)
        self.refresh()

    def _delete(self):
        if self._selected_id:
            store.delete(self._selected_id)
            self._selected_id = None
            self._edit_panel.grid_remove()
            self.refresh()


# ──────────────────────────────────────────────────────────────
#  App principal
# ──────────────────────────────────────────────────────────────
class BuscadorApp(ctk.CTk):
    _BATCH = 10  # ofertas por lote

    def __init__(self):
        super().__init__()
        self.title("Buscador de Ofertas de Trabajo")
        self.geometry("1100x780")
        self.minsize(900, 600)
        self.configure(fg_color="#12121f")
        self._search_thread: threading.Thread | None = None

        # Estado del scroll infinito
        self._all_jobs: list[Job] = []
        self._rendered: int = 0
        self._loading_more: bool = False
        self._current_query: str = ""

        # Búsqueda incremental
        self._search_token: int = 0
        self._found_count: int = 0
        self._loading_active: bool = False

        # Insights de mercado + país de la última búsqueda
        self._market = None
        self._last_country: str = "España"

        # Debounce para auto-búsqueda
        self._debounce_id: str | None = None

        self._build_layout()
        self._show_placeholder()
        self._setup_scroll()        # scroll nativo + detección de fondo

    # ── Layout ────────────────────────────────────────────────
    def _build_layout(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Estado de filtros
        self._filter_layout = "sidebar"   # "sidebar" | "topbar"
        self._salary_value = 0.0
        self._source_labels: dict[str, ctk.CTkLabel] = {}

        # Variables de filtro (una sola vez; persisten entre reconstrucciones)
        self.var_pais   = StringVar(value=PAISES[0])
        self.var_tipo   = StringVar(value="Todos")
        self.var_exp    = StringVar(value=EXPERIENCIA[0])
        self.var_moneda = StringVar(value="EUR")
        self.var_pais.trace_add("write",   lambda *_: self._debounce_search())
        self.var_tipo.trace_add("write",   lambda *_: self._debounce_search())
        self.var_exp.trace_add("write",    lambda *_: self._debounce_search())
        self.var_moneda.trace_add("write", lambda *_: self._debounce_search())

        # Contenedor sidebar (se reconstruye según el modo)
        self._sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=BG_SIDE)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        self._build_main()
        self._build_sidebar()
        self._apply_filter_layout()

        # Vista "Mis Ofertas" — superpuesta a pantalla completa, oculta al inicio
        self._profile_view = MyJobsView(self, on_back=self._close_profile)
        self._profile_view.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self._profile_view.grid_remove()

    # ── Toggle de ubicación de filtros ────────────────────────
    def _toggle_filter_layout(self):
        self._filter_layout = "topbar" if self._filter_layout == "sidebar" else "sidebar"
        self._build_sidebar()
        self._apply_filter_layout()

    def _apply_filter_layout(self):
        for w in self._topbar_inner.winfo_children():
            w.destroy()
        if self._filter_layout == "topbar":
            self._build_filters(self._topbar_inner, horizontal=True)
            self._filters_topbar.grid()
        else:
            self._filters_topbar.grid_remove()

    def _build_sidebar(self):
        sb = self._sidebar
        for w in sb.winfo_children():
            w.destroy()
        full = (self._filter_layout == "sidebar")
        sb.configure(width=260 if full else 78)
        sb.columnconfigure(0, weight=1)

        top = ctk.CTkFrame(sb, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew",
                 padx=16 if full else 10, pady=(24, 16))
        top.columnconfigure(0, weight=1)

        if full:
            # Logo + perfil
            logo = ctk.CTkFrame(top, fg_color="transparent")
            logo.grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(logo, text=ICON["search"], font=icon_font(20),
                         text_color=ACCENT).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(logo, text="JobFinder",
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=TEXT).pack(side="left")
            ctk.CTkButton(top, text=ICON["profile"], width=38, height=38,
                          fg_color=SURFACE, hover_color=SURFACE_2,
                          font=icon_font(16), text_color=TEXT_DIM,
                          command=self._open_profile).grid(row=0, column=1, sticky="e")
            ctk.CTkButton(top, text="Mis Ofertas",
                          font=ctk.CTkFont(size=13, weight="bold"),
                          fg_color="#1e1e3a", hover_color="#2a2a4e", anchor="w",
                          command=self._open_profile).grid(
                              row=1, column=0, columnspan=2, sticky="ew", pady=(14, 0))
            ctk.CTkButton(top, text="Filtros arriba   ⇄",
                          font=ctk.CTkFont(size=11),
                          fg_color="transparent", border_width=1, border_color=BORDER,
                          hover_color=SURFACE, text_color=TEXT_DIM,
                          command=self._toggle_filter_layout).grid(
                              row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

            # Filtros (vertical) en un host propio
            host = ctk.CTkFrame(sb, fg_color="transparent")
            host.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
            host.columnconfigure(0, weight=1)
            self._build_filters(host, horizontal=False)
        else:
            # Barra de iconos compacta
            ctk.CTkLabel(top, text=ICON["search"], font=icon_font(22),
                         text_color=ACCENT).grid(row=0, column=0, pady=(0, 18))
            ctk.CTkButton(top, text=ICON["profile"], width=46, height=42,
                          fg_color=SURFACE, hover_color=SURFACE_2,
                          font=icon_font(16), text_color=TEXT_DIM,
                          command=self._open_profile).grid(row=1, column=0, pady=(0, 8))
            ctk.CTkButton(top, text=ICON["list"], width=46, height=42,
                          fg_color="#1e1e3a", hover_color="#2a2a4e",
                          font=icon_font(16), text_color=TEXT,
                          command=self._open_profile).grid(row=2, column=0, pady=(0, 8))
            ctk.CTkButton(top, text="⇄", width=46, height=42,
                          fg_color="transparent", border_width=1, border_color=BORDER,
                          hover_color=SURFACE, font=ctk.CTkFont(size=15),
                          text_color=TEXT_DIM,
                          command=self._toggle_filter_layout).grid(row=3, column=0, pady=(0, 8))

    # ── Construcción de filtros (vertical=sidebar / horizontal=topbar) ────────
    def _build_filters(self, parent, horizontal: bool):
        if horizontal:
            self._build_filters_horizontal(parent)
        else:
            self._build_filters_vertical(parent)

    def _build_filters_vertical(self, parent):
        parent.columnconfigure(0, weight=1)
        row = 0
        row = self._section(parent, "País", row)
        ctk.CTkOptionMenu(
            parent, values=PAISES, variable=self.var_pais,
            fg_color=SURFACE, button_color="#3b3b5c",
            button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE,
        ).grid(row=row, column=0, padx=16, pady=(0, 14), sticky="ew"); row += 1

        row = self._section(parent, "Tipo de trabajo", row)
        for t in ["Todos", "Remoto", "Híbrido", "Presencial"]:
            ctk.CTkRadioButton(
                parent, text=t, variable=self.var_tipo, value=t,
                radiobutton_width=16, radiobutton_height=16,
                border_width_unchecked=8, border_width_checked=0,
                fg_color=ACCENT, hover_color=ACCENT_HOVER, border_color=SURFACE_2,
                text_color=TEXT_DIM, font=ctk.CTkFont(size=13),
            ).grid(row=row, column=0, padx=20, pady=4, sticky="w"); row += 1
        row += 1

        row = self._section(parent, "Experiencia", row)
        ctk.CTkOptionMenu(
            parent, values=EXPERIENCIA, variable=self.var_exp,
            fg_color=SURFACE, button_color="#3b3b5c",
            button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE,
        ).grid(row=row, column=0, padx=16, pady=(0, 14), sticky="ew"); row += 1

        row = self._section(parent, "Salario anual (mínimo)", row)
        ctk.CTkOptionMenu(
            parent, values=MONEDAS, variable=self.var_moneda, width=80,
            fg_color=SURFACE, button_color="#3b3b5c",
            button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE,
            command=lambda _: self._on_salary_change(self._salary_value),
        ).grid(row=row, column=0, padx=16, pady=(0, 6), sticky="w"); row += 1

        self.salary_label = ctk.CTkLabel(
            parent, text=self._salary_text(), font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM)
        self.salary_label.grid(row=row, column=0, padx=16, sticky="w"); row += 1

        self.salary_slider = ctk.CTkSlider(
            parent, from_=0, to=150000, number_of_steps=30,
            progress_color=ACCENT, button_color="#9b9aff",
            command=self._on_salary_slider)
        self.salary_slider.set(self._salary_value)
        self.salary_slider.grid(row=row, column=0, padx=16, pady=(2, 22), sticky="ew"); row += 1

        # Fuentes activas
        row = self._section(parent, "Fuentes activas", row)
        self._source_labels = {}
        for source in ["LinkedIn", "Adzuna", "Remotive", "Arbeitnow", "Computrabajo"]:
            lbl = ctk.CTkLabel(parent, text=f"  {source}",
                               font=ctk.CTkFont(size=11), text_color=TEXT_MUTE, anchor="w")
            lbl.grid(row=row, column=0, padx=16, pady=1, sticky="w")
            self._source_labels[source] = lbl
            row += 1
        self._refresh_source_badges()
        row += 1

        ctk.CTkButton(
            parent, text="Limpiar filtros", fg_color="transparent",
            border_width=1, border_color=BORDER, hover_color=SURFACE,
            text_color=TEXT_DIM, command=self._reset_filters,
        ).grid(row=row, column=0, padx=16, pady=(4, 20), sticky="ew")

    def _build_filters_horizontal(self, parent):
        self._source_labels = {}

        def group(title):
            g = ctk.CTkFrame(parent, fg_color="transparent")
            g.pack(side="left", padx=(0, 16))
            ctk.CTkLabel(g, text=title.upper(), font=ctk.CTkFont(size=9, weight="bold"),
                         text_color=TEXT_MUTE, anchor="w").pack(anchor="w", pady=(0, 2))
            return g

        g = group("País")
        ctk.CTkOptionMenu(g, values=PAISES, variable=self.var_pais, width=150,
                          fg_color=SURFACE, button_color="#3b3b5c",
                          button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE).pack()
        g = group("Tipo")
        ctk.CTkOptionMenu(g, values=["Todos", "Remoto", "Híbrido", "Presencial"],
                          variable=self.var_tipo, width=120,
                          fg_color=SURFACE, button_color="#3b3b5c",
                          button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE).pack()
        g = group("Experiencia")
        ctk.CTkOptionMenu(g, values=EXPERIENCIA, variable=self.var_exp, width=170,
                          fg_color=SURFACE, button_color="#3b3b5c",
                          button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE).pack()
        g = group("Moneda")
        ctk.CTkOptionMenu(g, values=MONEDAS, variable=self.var_moneda, width=80,
                          fg_color=SURFACE, button_color="#3b3b5c",
                          button_hover_color="#4f4f7a", dropdown_fg_color=SURFACE,
                          command=lambda _: self._on_salary_change(self._salary_value)).pack()
        g = group("Salario mín.")
        sub = ctk.CTkFrame(g, fg_color="transparent")
        sub.pack()
        self.salary_slider = ctk.CTkSlider(sub, from_=0, to=150000, number_of_steps=30,
                                           width=150, progress_color=ACCENT,
                                           button_color="#9b9aff",
                                           command=self._on_salary_slider)
        self.salary_slider.set(self._salary_value)
        self.salary_slider.pack(side="left")
        self.salary_label = ctk.CTkLabel(sub, text=self._salary_text(),
                                         font=ctk.CTkFont(size=11), text_color=TEXT_DIM)
        self.salary_label.pack(side="left", padx=(8, 0))

        ctk.CTkButton(parent, text="Limpiar", width=80, fg_color="transparent",
                      border_width=1, border_color=BORDER, hover_color=SURFACE,
                      text_color=TEXT_DIM, command=self._reset_filters).pack(
                          side="left", padx=(6, 0), pady=(14, 0))

    def _build_main(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="#12121f")
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=0)   # panel detalle (ancho fijo)
        main.rowconfigure(3, weight=1)
        self._main_frame = main

        # Search bar
        sf = ctk.CTkFrame(main, fg_color="#0d0d1a", corner_radius=0)
        sf.grid(row=0, column=0, columnspan=2, sticky="ew")
        sf.columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(sf, fg_color="transparent")
        inner.grid(row=0, column=0, padx=28, pady=20, sticky="ew")
        inner.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner, text="¿Qué tipo de trabajo buscas?",
            font=ctk.CTkFont(size=13), text_color="#a0a0c0", anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.search_entry = ctk.CTkEntry(
            inner,
            placeholder_text='Ej: "Desarrollador Python senior, remoto, mínimo 60k EUR"',
            font=ctk.CTkFont(size=14), height=44,
            fg_color="#1e1e2e", border_color="#3a3a5c", border_width=1,
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12))
        self.search_entry.bind("<Return>", lambda e: self._on_search())

        self.search_btn = ctk.CTkButton(
            inner, text="Buscar", width=110, height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6d6cff", hover_color="#5a59f0",
            command=self._on_search,
        )
        self.search_btn.grid(row=1, column=1)

        # Barra de filtros superior (visible solo en modo "topbar")
        self._filters_topbar = ctk.CTkFrame(main, fg_color="#0d0d1a", corner_radius=0)
        self._filters_topbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._topbar_inner = ctk.CTkFrame(self._filters_topbar, fg_color="transparent")
        self._topbar_inner.pack(fill="x", padx=28, pady=12)
        self._filters_topbar.grid_remove()

        # Stats bar
        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.grid(row=2, column=0, columnspan=2, sticky="ew", padx=28, pady=(16, 8))
        stats.columnconfigure(0, weight=1)

        self.results_label = ctk.CTkLabel(
            stats, text="Introduce un prompt para comenzar la búsqueda",
            font=ctk.CTkFont(size=13), text_color="#6b6b8a", anchor="w",
        )
        self.results_label.grid(row=0, column=0, sticky="w")

        self.var_orden = StringVar(value="Relevancia")
        ctk.CTkOptionMenu(
            stats,
            values=["Relevancia", "Salario (mayor)", "Salario (menor)"],
            variable=self.var_orden, width=160,
            fg_color="#1e1e2e", button_color="#3b3b5c",
            button_hover_color="#4f4f7a", dropdown_fg_color="#1e1e2e",
            command=self._on_sort_change,
        ).grid(row=0, column=1, sticky="e")

        # Results
        self.results_scroll = ctk.CTkScrollableFrame(
            main, fg_color="transparent", scrollbar_button_color="#3a3a5c",
        )
        self.results_scroll.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 16))
        self.results_scroll.columnconfigure(0, weight=1)

        # Panel de detalle (oculto inicialmente, se muestra al clicar una oferta)
        self.detail_panel = JobDetailPanel(
            main, on_close=self._close_detail, on_save=self._save_job,
        )

    # ── Helpers ───────────────────────────────────────────────
    def _section(self, parent, title: str, row: int) -> int:
        ctk.CTkLabel(
            parent, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#5a5a7a", anchor="w",
        ).grid(row=row, column=0, padx=16, pady=(12, 4), sticky="w")
        return row + 1

    def _salary_text(self) -> str:
        return f"{int(self._salary_value):,} {self.var_moneda.get()}".replace(",", ".")

    def _on_salary_change(self, value):
        self._salary_value = float(value)
        if hasattr(self, "salary_label") and self.salary_label.winfo_exists():
            self.salary_label.configure(text=self._salary_text())

    def _on_salary_slider(self, value):
        """Slider: actualiza label y programa búsqueda con debounce largo."""
        self._on_salary_change(value)
        self._debounce_search(delay=1200)  # más delay para el slider

    def _reset_filters(self):
        self._salary_value = 0.0
        self.var_pais.set(PAISES[0])
        self.var_tipo.set("Todos")
        self.var_exp.set(EXPERIENCIA[0])
        self.var_moneda.set("EUR")
        if hasattr(self, "salary_slider") and self.salary_slider.winfo_exists():
            self.salary_slider.set(0)
        if hasattr(self, "salary_label") and self.salary_label.winfo_exists():
            self.salary_label.configure(text=self._salary_text())

    def _refresh_source_badges(self):
        adzuna_ok = adzuna_configured()
        states = {
            "LinkedIn":     (True,      "✓ LinkedIn",                                        "#4ade80"),
            "Adzuna":       (adzuna_ok, "✓ Adzuna" if adzuna_ok else "✗ Adzuna (sin clave)", "#4ade80" if adzuna_ok else "#f87171"),
            "Remotive":     (True,      "✓ Remotive",                                        "#4ade80"),
            "Arbeitnow":    (True,      "✓ Arbeitnow",                                       "#4ade80"),
            "Computrabajo": (True,      "✓ Computrabajo",                                    "#4ade80"),
        }
        for source, (_, text, color) in states.items():
            if source in self._source_labels:
                self._source_labels[source].configure(text=f"  {text}", text_color=color)

    # ── Auto-búsqueda con debounce ────────────────────────────
    def _debounce_search(self, delay: int = 700):
        """Cancela el timer anterior y programa nueva búsqueda."""
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(delay, self._auto_search)

    def _auto_search(self):
        """Lanza búsqueda solo si hay texto en la caja."""
        self._debounce_id = None
        if self.search_entry.get().strip():
            self._on_search()

    # ── Search ────────────────────────────────────────────────
    def _on_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        # Token para descartar resultados de búsquedas anteriores ya obsoletas
        self._search_token += 1
        token = self._search_token

        self._all_jobs = []
        self._rendered = 0
        self._loading_more = False   # resetear siempre al iniciar búsqueda
        self._current_query = query
        self._last_country = self.var_pais.get()
        self._market = None
        self._found_count = 0
        self._close_detail()         # cerrar panel de oferta anterior
        self._clear_results()
        self.search_btn.configure(state="disabled", text="Buscando…")
        self._start_spinner()

        self._search_thread = threading.Thread(
            target=self._run_search,
            args=(
                token,
                query,
                self.var_pais.get(),
                self.var_tipo.get(),
                int(self.salary_slider.get()),
                self.var_moneda.get(),
                self.var_exp.get(),
            ),
            daemon=True,
        )
        self._search_thread.start()

    def _run_search(self, token, prompt, country, job_type, salary_min, currency, experience):
        import traceback

        def on_update(ranked):
            snapshot = list(ranked)
            self.after(0, lambda: self._on_partial(token, snapshot))

        def on_done(ranked, market):
            snapshot = list(ranked)
            self.after(0, lambda: self._on_search_finished(token, snapshot, market))

        try:
            search_jobs_streaming(
                prompt=prompt,
                country=country,
                job_type=job_type,
                salary_min=salary_min,
                currency=currency,
                experience=experience,
                on_update=on_update,
                on_done=on_done,
            )
        except Exception:
            traceback.print_exc()
            self.after(0, lambda: self._on_search_finished(token, [], None))

    # ── Resultados incrementales ──────────────────────────────
    def _on_partial(self, token, jobs):
        """Llega un lote (una fuente respondió). Refrescamos contador y lista."""
        if token != self._search_token:
            return   # búsqueda obsoleta
        self._all_jobs = self._sort_jobs(jobs)
        self._found_count = len(self._all_jobs)
        self._rerender_results()

    def _on_search_finished(self, token, jobs, market):
        if token != self._search_token:
            return
        self._stop_spinner()
        self._all_jobs = self._sort_jobs(jobs)
        self._market = market
        self._found_count = len(self._all_jobs)
        self.search_btn.configure(state="normal", text="Buscar")

        if not self._all_jobs:
            self._show_empty(self._current_query)
            return

        n = self._found_count
        label = f"{n} oferta{'s' if n != 1 else ''} encontrada{'s' if n != 1 else ''}"
        if self._current_query:
            label += f' para "{self._current_query}"'
        self.results_label.configure(text=label, text_color="#ececf6")
        self._rerender_results()

    def _rerender_results(self):
        """Re-pinta el primer lote con el ranking actual (orden puede cambiar)."""
        self._clear_results()
        self._rendered = 0
        self._render_next_batch()

    # ── Spinner de carga ──────────────────────────────────────
    _SPIN_CHARS = ["◐", "◓", "◑", "◒"]

    def _start_spinner(self):
        self._loading_active = True
        self._spin_i = 0
        self._tick_spinner()

    def _tick_spinner(self):
        if not getattr(self, "_loading_active", False):
            return
        ch = self._SPIN_CHARS[self._spin_i % len(self._SPIN_CHARS)]
        self._spin_i += 1
        n = self._found_count
        if n:
            txt = f"{ch}  {n} oferta{'s' if n != 1 else ''} · buscando más…"
        else:
            txt = f"{ch}  Buscando ofertas…"
        self.results_label.configure(text=txt, text_color="#a6a8c8")
        self.after(130, self._tick_spinner)

    def _stop_spinner(self):
        self._loading_active = False

    # ── Renderizado progresivo ────────────────────────────────
    def _render_next_batch(self):
        if self._loading_more:
            return
        batch = self._all_jobs[self._rendered: self._rendered + self._BATCH]
        if not batch:
            return

        self._loading_more = True
        try:
            for job in batch:
                try:
                    row = self._rendered
                    card = JobCard(self.results_scroll, job, on_click=self._show_detail)
                    card.grid(row=row, column=0, sticky="ew", pady=6, padx=4)
                    self._rendered += 1
                except Exception as e:
                    print(f"[JobCard error] {job.title}: {e}")
                    self._rendered += 1  # saltar la oferta problemática
            self._update_spinner()
        except Exception as e:
            print(f"[render error] {e}")
        finally:
            self._loading_more = False  # garantizado siempre

    def _update_spinner(self):
        # Eliminar spinner anterior si existe
        if hasattr(self, "_spinner") and self._spinner.winfo_exists():
            self._spinner.destroy()

        remaining = len(self._all_jobs) - self._rendered
        if remaining <= 0:
            return

        self._spinner = ctk.CTkLabel(
            self.results_scroll,
            text=f"↓  {remaining} ofertas más — sigue bajando",
            font=ctk.CTkFont(size=12),
            text_color="#5a5a7a",
        )
        self._spinner.grid(row=self._rendered, column=0, pady=16)

    # ── Panel de detalle ──────────────────────────────────
    def _show_detail(self, job):
        """Muestra el panel lateral con el análisis de la oferta."""
        if not self.detail_panel.winfo_ismapped():
            self.detail_panel.grid(
                row=3, column=1, sticky="nsew",
                padx=(0, 12), pady=(0, 16),
            )
        self.detail_panel.show(job, self._last_country, self._market)

    def _close_detail(self):
        """Oculta el panel lateral."""
        self.detail_panel.grid_remove()

    # ── Mis Ofertas (perfil) ──────────────────────────────
    def _save_job(self, job):
        """Construye una candidatura desde una oferta y la persiste."""
        from search.analyzer import analyze_job
        ana = analyze_job(job, self._last_country)
        est = ana.salary_estimate
        sj = SavedJob(
            id=make_id(job.url, job.title),
            title=job.title,
            company=job.company,
            location=job.location,
            url=job.url,
            source=job.source,
            job_type=job.job_type,
            salary_display=job.salary_display,
            salary_estimate=est.range_display if est else "",
            description=ana.clean_description[:400],
            skills=ana.hard_skills,
            signals=[
                {"emoji": s.emoji, "label": s.label, "detail": s.detail, "kind": s.kind}
                for s in ana.signals
            ],
            seniority=ana.seniority_detail or job.seniority_label,
            saved_at=store.today(),
            timeline=[{"date": store.today(), "event": "Oferta guardada"}],
        )
        store.upsert(sj)

    def _open_profile(self):
        self._close_detail()
        self._profile_view.refresh()
        self._profile_view.grid()
        self._profile_view.tkraise()

    def _close_profile(self):
        self._profile_view.grid_remove()

    def _setup_scroll(self):
        """
        Scroll robusto para múltiples CTkScrollableFrame en la app.
        - bind_all captura todos los eventos de rueda y los reenvía al canvas
          correcto según dónde esté el cursor (resultados o panel de detalle).
        - Velocidad igualada a la interna de CTkScrollableFrame (delta/6).
        - Polling 300 ms activa la carga del siguiente lote de tarjetas.
        """
        import sys

        def _scroll_canvas(canvas, event) -> bool:
            """Intenta hacer scroll en un canvas. Devuelve True si lo hizo."""
            if event.widget is canvas:
                return False   # el canvas ya gestiona su propio evento
            rx, ry = event.x_root, event.y_root
            cx, cy = canvas.winfo_rootx(), canvas.winfo_rooty()
            if not (cx <= rx <= cx + canvas.winfo_width()
                    and cy <= ry <= cy + canvas.winfo_height()):
                return False
            if sys.platform.startswith("win"):
                canvas.yview_scroll(int(-event.delta / 6), "units")
            elif event.num == 4:
                canvas.yview_scroll(-3, "units")
            elif event.num == 5:
                canvas.yview_scroll(3, "units")
            else:
                canvas.yview_scroll(int(-event.delta / 6), "units")
            return True

        def _scroll(event):
            try:
                # Si la vista "Mis Ofertas" está abierta, solo sus scrolls
                if self._profile_view.winfo_ismapped():
                    targets = [
                        self._profile_view.content_scroll,
                        self._profile_view.edit_scroll,
                    ]
                else:
                    targets = [self.results_scroll, self.detail_panel._body]
                for sf in targets:
                    try:
                        if sf.winfo_ismapped() and _scroll_canvas(sf._parent_canvas, event):
                            return
                    except Exception:
                        pass
            except Exception:
                pass

        self.bind_all("<MouseWheel>", _scroll, add="+")
        self.bind_all("<Button-4>",   _scroll, add="+")
        self.bind_all("<Button-5>",   _scroll, add="+")

        # Polling: detecta cuándo cargar el siguiente lote
        def _poll():
            try:
                canvas = self.results_scroll._parent_canvas
                yv = canvas.yview()
                if (not self._loading_more
                        and self._rendered < len(self._all_jobs)
                        and yv[1] >= 0.88):
                    self._render_next_batch()
            except Exception:
                pass
            self.after(300, _poll)

        self.after(300, _poll)

    def _sort_jobs(self, jobs: list[Job]) -> list[Job]:
        orden = self.var_orden.get()
        if orden == "Salario (mayor)":
            return sorted(jobs, key=lambda j: j.salary_max or j.salary_min or 0, reverse=True)
        if orden == "Salario (menor)":
            return sorted(jobs, key=lambda j: j.salary_min or j.salary_max or 0)
        return jobs

    def _on_sort_change(self, _):
        if self._all_jobs:
            self._clear_results()
            self._rendered = 0
            self._all_jobs = self._sort_jobs(self._all_jobs)
            self._render_next_batch()

    def _clear_results(self):
        self._loading_more = False
        if hasattr(self, "_spinner") and self._spinner.winfo_exists():
            self._spinner.destroy()
        for w in self.results_scroll.winfo_children():
            w.destroy()

    def _show_placeholder(self):
        frame = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        frame.grid(row=0, column=0, pady=80)
        ctk.CTkLabel(frame, text="🔍", font=ctk.CTkFont(size=48)).pack(pady=(0, 12))
        ctk.CTkLabel(
            frame, text="Describe el trabajo que buscas",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#4a4a6a",
        ).pack()
        ctk.CTkLabel(
            frame,
            text='Usa lenguaje natural, por ejemplo:\n"Desarrollador Python senior, remoto, mínimo 60k EUR"',
            font=ctk.CTkFont(size=13), text_color="#3a3a5a", justify="center",
        ).pack(pady=(8, 0))

    def _show_empty(self, query: str):
        frame = ctk.CTkFrame(self.results_scroll, fg_color="transparent")
        frame.grid(row=0, column=0, pady=80)
        ctk.CTkLabel(frame, text="😕", font=ctk.CTkFont(size=48)).pack(pady=(0, 12))
        ctk.CTkLabel(
            frame, text="No se encontraron ofertas",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#4a4a6a",
        ).pack()
        ctk.CTkLabel(
            frame, text="Prueba con otros términos o ajusta los filtros.",
            font=ctk.CTkFont(size=13), text_color="#3a3a5a",
        ).pack(pady=(8, 0))
        self.results_label.configure(
            text=f'Sin resultados para "{query}"', text_color="#6b6b8a"
        )


if __name__ == "__main__":
    app = BuscadorApp()
    app.mainloop()
