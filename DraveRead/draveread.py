#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveRead - voorlezer (tekst-naar-spraak) met natuurlijke, neurale stemmen.
Gebruikt Neuvoice (on-device, offline na eenmalige download) via ONNX Runtime.
Dravenlock-huisstijl. Lokaal, toegankelijk: grote tekst, hoog contrast.
"""
import os
import sys
import json
import shutil
import tempfile

from PyQt6.QtCore import (Qt, QLocale, QUrl, pyqtSignal, pyqtSlot, QThread,
                          QObject)
from PyQt6.QtGui import QPixmap, QIcon, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFrame, QMessageBox, QDialog, QToolButton,
    QStatusBar, QPlainTextEdit, QTextEdit, QFileDialog, QSlider)
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAVE_MEDIA = True
except Exception:
    HAVE_MEDIA = False

APP_NAME = "DraveRead"
APP_VERSION = "0.2.2"
DONATE_URL = "https://paypal.me/roger076"
SUPPORT_MAIL = "service@dravenlock.nl"

# ---- Dravenlock-huisstijl ----
BG = "#0e0e11"
PANEL = "#16161b"
SILVER = "#d4d4d4"
MUTE = "#8a8a94"
ACCENT = "#6fa3d6"
GOOD = "#4fb477"
WARN = "#e0a23a"

VOICES = ["Alina", "Cem", "Cole", "Giray", "Leon", "Lina", "Linda",
          "Mustafa", "Sarp", "Selin", "Sema", "Soras"]

# (code, NL-naam, EN-naam) - Nederlands + Engels eerst, dan alfabetisch
LANGS = [
    ("nl", "Nederlands", "Dutch"), ("en", "Engels", "English"),
    ("ar", "Arabisch", "Arabic"), ("bg", "Bulgaars", "Bulgarian"),
    ("da", "Deens", "Danish"), ("de", "Duits", "German"),
    ("et", "Ests", "Estonian"), ("fi", "Fins", "Finnish"),
    ("fr", "Frans", "French"), ("el", "Grieks", "Greek"),
    ("hi", "Hindi", "Hindi"), ("hu", "Hongaars", "Hungarian"),
    ("id", "Indonesisch", "Indonesian"), ("it", "Italiaans", "Italian"),
    ("ja", "Japans", "Japanese"), ("ko", "Koreaans", "Korean"),
    ("hr", "Kroatisch", "Croatian"), ("lv", "Lets", "Latvian"),
    ("lt", "Litouws", "Lithuanian"), ("pl", "Pools", "Polish"),
    ("pt", "Portugees", "Portuguese"), ("ro", "Roemeens", "Romanian"),
    ("ru", "Russisch", "Russian"), ("sl", "Sloveens", "Slovenian"),
    ("sk", "Slowaaks", "Slovak"), ("es", "Spaans", "Spanish"),
    ("cs", "Tsjechisch", "Czech"), ("tr", "Turks", "Turkish"),
    ("uk", "Oekra\u00efens", "Ukrainian"), ("vi", "Vietnamees", "Vietnamese"),
    ("sv", "Zweeds", "Swedish"),
]

QUALITY = [("Snel", 5), ("Beter", 15), ("Best", 30)]


# ---------------------------------------------------------------------------
# Pad / config
# ---------------------------------------------------------------------------
try:
    from uitspraak import uitspraak as _uitspraak
except Exception:
    try:
        from .uitspraak import uitspraak as _uitspraak
    except Exception:  # zonder uitspraak.py gewoon de tekst zelf
        def _uitspraak(t, taal="nl"):
            return t


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "draveread_config.json")


DEFAULT_CONFIG = {"lang": "", "voice": "Leon", "tts_lang": "nl",
                  "speed": 100, "quality": 0}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal (UI)
# ---------------------------------------------------------------------------
_LANG = "nl"

TRANSLATIONS = {
    "en": {
        "Instellingen\u2026": "Settings\u2026", "Snelgids": "Quick guide",
        "Over": "About", "Sluiten": "Close", "Taal:": "Language:",
        "Automatisch (OS)": "Automatic (OS)", "Nederlands": "Dutch",
        "Engels": "English", "Donatie": "Donate",
        "Sommige instellingen gaan pas in na herstarten.":
            "Some settings apply after a restart.",
        "Openen (.txt)": "Open (.txt)", "Openen\u2026": "Open\u2026",
        "Stem:": "Voice:", "Taal van de tekst:": "Text language:",
        "Documenten (*.txt *.md *.pdf *.docx)": "Documents (*.txt *.md *.pdf *.docx)",
        "Kon document niet lezen": "Could not read document",
        "PDF lezen vereist 'pymupdf'.": "Reading PDF requires 'pymupdf'.",
        "Word (.docx) lezen vereist 'python-docx'.":
            "Reading Word (.docx) requires 'python-docx'.",
        "Oud .doc wordt niet ondersteund; sla op als .docx.":
            "Old .doc is not supported; save as .docx.",
        "Geen leesbare tekst gevonden in dit bestand.":
            "No readable text found in this file.",
        "Snelheid:": "Speed:", "Kwaliteit:": "Quality:",
        "Snel": "Fast", "Beter": "Better", "Best": "Best",
        "Voorlezen": "Read aloud", "Pauze": "Pause", "Hervatten": "Resume", "Stop": "Stop",
        "Opslaan als audio\u2026": "Save as audio\u2026",
        "Plak of typ hier de tekst, of open een .txt-bestand.":
            "Paste or type your text here, or open a .txt file.",
        "Klaar": "Ready",
        "Stemmen worden voorbereid (eenmalige download)\u2026":
            "Preparing voices (one-time download)\u2026",
        "Bezig met genereren\u2026": "Generating\u2026",
        "Aan het voorlezen\u2026": "Reading aloud\u2026",
        "Gepauzeerd": "Paused", "Gestopt": "Stopped",
        "Geen tekst om voor te lezen": "No text to read",
        "Opgeslagen": "Saved", "Kon niet opslaan": "Could not save",
        "WAV-audio (*.wav)": "WAV audio (*.wav)",
        "Tekstbestanden (*.txt)": "Text files (*.txt)",
        "Alle bestanden (*)": "All files (*)",
        "Kon niet openen": "Could not open",
        "Voorlezen mislukt": "Reading failed",
        "Geen audio-ondersteuning gevonden.": "No audio support found.",
        "snelgids_titel": "DraveRead - quick guide",
    }
}


def detect_lang(cfg):
    forced = (cfg.get("lang") or "").strip().lower()
    if forced in ("nl", "en"):
        return forced
    try:
        if QLocale.system().name().lower().startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


def t(s, lang=None):
    lg = lang or _LANG
    if lg == "nl":
        return s
    return TRANSLATIONS.get(lg, {}).get(s, s)


def lang_name(code, ui):
    for c, nl, en in LANGS:
        if c == code:
            return nl if ui == "nl" else en
    return code


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
def _logo_path():
    dirs = [_app_dir()]
    mp = getattr(sys, "_MEIPASS", None)
    if mp:
        dirs.append(mp)
    dirs.append(os.path.join(_app_dir(), "_internal"))
    for d in dirs:
        for name in ("logo.ico", "logo.png"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def app_icon():
    p = _logo_path()
    if p:
        ic = QIcon(p)
        if not ic.isNull():
            return ic
    return QIcon()


def logo_pixmap(size=30):
    p = _logo_path()
    if p:
        pm = QPixmap(p)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    return QPixmap()


# ---------------------------------------------------------------------------
# Document inlezen (txt / md / pdf / docx)
# ---------------------------------------------------------------------------
def extract_pdf(path):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    doc = fitz.open(path)
    try:
        parts = [page.get_text() for page in doc]
    finally:
        doc.close()
    return "\n".join(parts)


def extract_docx(path):
    import docx
    d = docx.Document(path)
    return "\n".join(p.text for p in d.paragraphs)


def read_document(path):
    """Geeft (tekst, foutcode-of-None). Foutcode is een vertaalbare sleutel."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            try:
                return extract_pdf(path), None
            except ImportError:
                return None, "PDF lezen vereist 'pymupdf'."
        if ext == ".docx":
            try:
                return extract_docx(path), None
            except ImportError:
                return None, "Word (.docx) lezen vereist 'python-docx'."
        if ext == ".doc":
            return None, "Oud .doc wordt niet ondersteund; sla op als .docx."
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# TTS-werker (in aparte thread; maakt de motor 1x aan)
# ---------------------------------------------------------------------------
class TtsWorker(QObject):
    ready = pyqtSignal(str, str)     # wav-pad, taak ("play"/"save")
    failed = pyqtSignal(str)
    status = pyqtSignal(str)         # "init" / "gen"

    def __init__(self):
        super().__init__()
        self.tts = None
        self._styles = {}

    @pyqtSlot(str, str, str, float, int, str, str)
    def synth(self, text, voice, lang, speed, steps, out_path, task):
        try:
            if self.tts is None:
                self.status.emit("init")
                from neuvoice import TTS
                self.tts = TTS(auto_download=True)
            self.status.emit("gen")
            style = self._styles.get(voice)
            if style is None:
                style = self.tts.get_voice_style(voice)
                self._styles[voice] = style
            wav, _dur = self.tts.synthesize(
                _uitspraak(text, lang), voice_style=style, lang=lang, speed=speed,
                total_steps=steps)
            self.tts.save_audio(wav, out_path)
            self.ready.emit(out_path, task)
        except Exception as e:
            self.failed.emit("%s: %s" % (type(e).__name__, e))


# ---------------------------------------------------------------------------
# Snelgids
# ---------------------------------------------------------------------------
GUIDE_NL = """DraveRead - Snelgids

DraveRead leest tekst hardop voor met natuurlijke, neurale stemmen
(Neuvoice). Het werkt op je eigen pc - geen cloud. De eerste keer worden
de stemmen eenmalig gedownload; daarna werkt het offline.

Aan de slag
- Plak of typ tekst in het grote vak, of klik 'Openen...'
  (txt, pdf of Word .docx).
- Kies een Stem en de Taal van de tekst (standaard Nederlands).
- Snelheid en Kwaliteit kun je instellen. 'Snel' is het vlotst; 'Beter'
  en 'Best' klinken mooier maar duren langer om te maken.
- Klik 'Voorlezen'. De eerste keer (en bij een nieuwe tekst) maakt de app
  eerst de audio; dat kan even duren. Daarna speelt het af.
- 'Pauze' pauzeert/hervat, 'Stop' stopt.

Opslaan als audio
- 'Opslaan als audio...' bewaart de voorgelezen tekst als .wav-bestand,
  zodat je het later kunt afspelen of delen.

Tip: voor lange teksten loont 'Snel'; voor een opname die je bewaart kun
je 'Beter' of 'Best' kiezen.

Vragen of een tip? service@dravenlock.nl
"""

GUIDE_EN = """DraveRead - Quick guide

DraveRead reads text aloud with natural, neural voices (Neuvoice). It runs
on your own pc - no cloud. The first time, the voices are downloaded once;
after that it works offline.

Getting started
- Paste or type text in the large box, or click 'Open...'
  (txt, pdf or Word .docx).
- Pick a Voice and the Text language (Dutch by default).
- Set Speed and Quality. 'Fast' is quickest; 'Better' and 'Best' sound
  nicer but take longer to generate.
- Click 'Read aloud'. The first time (and for new text) the app generates
  the audio first; this can take a moment. Then it plays.
- 'Pause' pauses/resumes, 'Stop' stops.

Save as audio
- 'Save as audio...' stores the spoken text as a .wav file, so you can play
  or share it later.

Tip: for long texts 'Fast' is handy; for a recording you keep, pick
'Better' or 'Best'.

Questions or feedback? service@dravenlock.nl
"""


class GuideDialog(QDialog):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.setWindowTitle(t("snelgids_titel", lang))
        self.setWindowIcon(app_icon())
        self.resize(560, 560)
        lay = QVBoxLayout(self)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setObjectName("guide")
        box.setPlainText(GUIDE_NL if lang == "nl" else GUIDE_EN)
        lay.addWidget(box)
        row = QHBoxLayout()
        donate = QPushButton("\u2665 " + t("Donatie", lang))
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        row.addWidget(donate)
        row.addStretch(1)
        close = QPushButton(t("Sluiten", lang))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(t("Instellingen\u2026", lang))
        self.setWindowIcon(app_icon())
        self.resize(360, 160)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (OS)", lang), "")
        self.langbox.addItem(t("Nederlands", lang), "nl")
        self.langbox.addItem(t("Engels", lang), "en")
        self.langbox.setCurrentIndex(
            {"": 0, "nl": 1, "en": 2}.get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)
        hint = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang))
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)

    def result_cfg(self):
        self.cfg["lang"] = self.langbox.currentData()
        return self.cfg


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class DraveRead(QMainWindow):
    request = pyqtSignal(str, str, str, float, int, str, str)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.lang = _LANG
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(820, 760)

        self._tmpdir = tempfile.mkdtemp(prefix="draveread_")
        self._counter = 0
        self._cur_key = None
        self._cur_wav = None
        self._pending_key = None
        self._save_to = None
        self._busy = False

        # media
        if HAVE_MEDIA:
            self.audio = QAudioOutput()
            self.player = QMediaPlayer()
            self.player.setAudioOutput(self.audio)
            self.player.positionChanged.connect(self._on_pos)
            self.player.durationChanged.connect(self._on_dur)
            self.player.playbackStateChanged.connect(self._on_state)
        else:
            self.player = None

        # worker-thread
        self.thread = QThread(self)
        self.worker = TtsWorker()
        self.worker.moveToThread(self.thread)
        self.request.connect(self.worker.synth)
        self.worker.ready.connect(self._on_ready)
        self.worker.failed.connect(self._on_failed)
        self.worker.status.connect(self._on_status)
        self.thread.start()

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 14, 16, 14)
        bl.setSpacing(12)
        outer.addWidget(body, 1)

        # bovenbalk: openen + stem + taal
        top = QHBoxLayout()
        top.setSpacing(10)
        self.b_open = QPushButton(t("Openen\u2026", self.lang))
        self.b_open.clicked.connect(self.open_txt)
        top.addWidget(self.b_open)
        top.addWidget(self._sep())
        top.addWidget(QLabel(t("Stem:", self.lang)))
        self.voicebox = QComboBox()
        self.voicebox.addItems(VOICES)
        if cfg.get("voice") in VOICES:
            self.voicebox.setCurrentText(cfg["voice"])
        self.voicebox.currentIndexChanged.connect(self._save_settings)
        top.addWidget(self.voicebox)
        top.addWidget(QLabel(t("Taal van de tekst:", self.lang)))
        self.langbox = QComboBox()
        for code, nl, en in LANGS:
            self.langbox.addItem(nl if self.lang == "nl" else en, code)
        idx = max(0, self.langbox.findData(cfg.get("tts_lang", "nl")))
        self.langbox.setCurrentIndex(idx)
        self.langbox.currentIndexChanged.connect(self._save_settings)
        top.addWidget(self.langbox)
        top.addStretch(1)
        bl.addLayout(top)

        # groot tekstvak
        self.editor = QTextEdit()
        self.editor.setObjectName("reader")
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText(
            t("Plak of typ hier de tekst, of open een .txt-bestand.", self.lang))
        bl.addWidget(self.editor, 1)

        # snelheid + kwaliteit
        sk = QHBoxLayout()
        sk.setSpacing(10)
        sk.addWidget(QLabel(t("Snelheid:", self.lang)))
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setMinimum(70)
        self.speed.setMaximum(200)
        self.speed.setValue(int(cfg.get("speed", 100)))
        self.speed.setFixedWidth(200)
        self.speed.valueChanged.connect(self._on_speed)
        self.speed.valueChanged.connect(self._save_settings)
        sk.addWidget(self.speed)
        self.speed_lbl = QLabel("")
        self.speed_lbl.setObjectName("muted")
        sk.addWidget(self.speed_lbl)
        sk.addWidget(self._sep())
        sk.addWidget(QLabel(t("Kwaliteit:", self.lang)))
        self.qualbox = QComboBox()
        for name, _steps in QUALITY:
            self.qualbox.addItem(t(name, self.lang))
        self.qualbox.setCurrentIndex(int(cfg.get("quality", 0)))
        self.qualbox.currentIndexChanged.connect(self._save_settings)
        sk.addWidget(self.qualbox)
        sk.addStretch(1)
        bl.addLayout(sk)

        # afspeelknoppen
        ctl = QHBoxLayout()
        ctl.setSpacing(10)
        self.b_play = QPushButton("\u25b6  " + t("Voorlezen", self.lang))
        self.b_play.setObjectName("primary")
        self.b_play.clicked.connect(self.play)
        ctl.addWidget(self.b_play)
        self.b_pause = QPushButton("\u2389  " + t("Pauze", self.lang))
        self.b_pause.clicked.connect(self.pause)
        ctl.addWidget(self.b_pause)
        self.b_stop = QPushButton("\u25a0  " + t("Stop", self.lang))
        self.b_stop.clicked.connect(self.stop)
        ctl.addWidget(self.b_stop)
        ctl.addSpacing(12)
        self.b_save = QPushButton(t("Opslaan als audio\u2026", self.lang))
        self.b_save.clicked.connect(self.save_audio)
        ctl.addWidget(self.b_save)
        ctl.addStretch(1)
        bl.addLayout(ctl)

        # voortgang
        prow = QHBoxLayout()
        self.pos_lbl = QLabel("0:00")
        self.pos_lbl.setObjectName("muted")
        prow.addWidget(self.pos_lbl)
        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setEnabled(False)
        self.progress.sliderReleased.connect(self._seek)
        prow.addWidget(self.progress, 1)
        self.dur_lbl = QLabel("0:00")
        self.dur_lbl.setObjectName("muted")
        prow.addWidget(self.dur_lbl)
        bl.addLayout(prow)

        # status
        self.status_lbl = QLabel(t("Klaar", self.lang))
        self.status_lbl.setObjectName("statusline")
        bl.addWidget(self.status_lbl)

        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.addPermanentWidget(QLabel("v" + APP_VERSION))
        donate = QToolButton()
        donate.setText("\u2665 " + t("Donatie", self.lang))
        donate.setObjectName("donate")
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        sb.addPermanentWidget(donate)

        self._on_speed(self.speed.value())
        if not HAVE_MEDIA:
            self.status_lbl.setText(t("Geen audio-ondersteuning gevonden.", self.lang))
        self._update_buttons()

    def _sep(self):
        s = QFrame()
        s.setFrameShape(QFrame.Shape.VLine)
        s.setObjectName("sep")
        return s

    def _header(self):
        w = QWidget()
        w.setObjectName("header")
        w.setFixedHeight(56)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(34))
        lay.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("ver")
        lay.addWidget(ver)
        lay.addStretch(1)
        for label, slot in [(t("Instellingen\u2026", self.lang), self._settings),
                            (t("Snelgids", self.lang), self._guide),
                            (t("Over", self.lang), self._about)]:
            b = QPushButton(label)
            b.setObjectName("headerbtn")
            b.setFixedHeight(34)
            b.clicked.connect(lambda _=False, s=slot: s())
            lay.addWidget(b)
        return w

    # ---- instellingen lezen ----
    def _params(self):
        text = self.editor.toPlainText().strip()
        voice = self.voicebox.currentText()
        lang = self.langbox.currentData()
        speed = self.speed.value() / 100.0
        steps = QUALITY[self.qualbox.currentIndex()][1]
        return text, voice, lang, speed, steps

    def _key(self, text, voice, lang, speed, steps):
        return (text, voice, lang, round(speed, 2), steps)

    def _save_settings(self):
        self.cfg["voice"] = self.voicebox.currentText()
        self.cfg["tts_lang"] = self.langbox.currentData()
        self.cfg["speed"] = self.speed.value()
        self.cfg["quality"] = self.qualbox.currentIndex()
        save_config(self.cfg)

    # ---- afspelen ----
    def play(self):
        if not HAVE_MEDIA or self._busy:
            return
        # hervatten vanuit pauze?
        if (self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState):
            self.player.play()
            return
        text, voice, lang, speed, steps = self._params()
        if not text:
            self.status_lbl.setText(t("Geen tekst om voor te lezen", self.lang))
            return
        self._save_settings()
        key = self._key(text, voice, lang, speed, steps)
        if key == self._cur_key and self._cur_wav and os.path.exists(self._cur_wav):
            self._start_play(self._cur_wav)
            return
        self._generate(text, voice, lang, speed, steps, "play")

    def _generate(self, text, voice, lang, speed, steps, task):
        self._busy = True
        self._pending_key = self._key(text, voice, lang, speed, steps)
        self._counter += 1
        out = os.path.join(self._tmpdir, "read_%d.wav" % self._counter)
        self.status_lbl.setText(t("Bezig met genereren\u2026", self.lang))
        self._update_buttons()
        self.request.emit(text, voice, lang, speed, steps, out, task)

    def _start_play(self, path):
        self.player.setSource(QUrl())
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def pause(self):
        if not HAVE_MEDIA:
            return
        st = self.player.playbackState()
        if st == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif st == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()

    def stop(self):
        if HAVE_MEDIA:
            self.player.stop()

    def save_audio(self):
        if self._busy:
            return
        text, voice, lang, speed, steps = self._params()
        if not text:
            self.status_lbl.setText(t("Geen tekst om voor te lezen", self.lang))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t("Opslaan als audio\u2026", self.lang), "voorlezing.wav",
            t("WAV-audio (*.wav)", self.lang))
        if not path:
            return
        if not path.lower().endswith(".wav"):
            path += ".wav"
        self._save_settings()
        key = self._key(text, voice, lang, speed, steps)
        if key == self._cur_key and self._cur_wav and os.path.exists(self._cur_wav):
            self._do_copy(self._cur_wav, path)
            return
        self._save_to = path
        self._generate(text, voice, lang, speed, steps, "save")

    def _do_copy(self, src, dst):
        try:
            shutil.copyfile(src, dst)
            self.status_lbl.setText("%s %s" % (t("Opgeslagen", self.lang),
                                               os.path.basename(dst)))
        except Exception as e:
            QMessageBox.warning(self, t("Kon niet opslaan", self.lang), str(e))

    # ---- worker-signalen ----
    def _on_status(self, kind):
        if kind == "init":
            self.status_lbl.setText(
                t("Stemmen worden voorbereid (eenmalige download)\u2026", self.lang))
        elif kind == "gen":
            self.status_lbl.setText(t("Bezig met genereren\u2026", self.lang))

    def _on_ready(self, path, task):
        self._busy = False
        self._cur_key = self._pending_key
        self._cur_wav = path
        if task == "play" and HAVE_MEDIA:
            self._start_play(path)
        elif task == "save" and self._save_to:
            self._do_copy(path, self._save_to)
            self._save_to = None
        self._update_buttons()

    def _on_failed(self, msg):
        self._busy = False
        self._save_to = None
        self.status_lbl.setText(t("Voorlezen mislukt", self.lang))
        QMessageBox.warning(self, t("Voorlezen mislukt", self.lang), msg)
        self._update_buttons()

    # ---- media-signalen ----
    def _on_state(self, st):
        if not HAVE_MEDIA:
            return
        if st == QMediaPlayer.PlaybackState.PlayingState:
            self.status_lbl.setText(t("Aan het voorlezen\u2026", self.lang))
            self.b_pause.setText("\u2389  " + t("Pauze", self.lang))
        elif st == QMediaPlayer.PlaybackState.PausedState:
            self.status_lbl.setText(t("Gepauzeerd", self.lang))
            self.b_pause.setText("\u25b6  " + t("Hervatten", self.lang))
        else:
            self.b_pause.setText("\u2389  " + t("Pauze", self.lang))
            if self.status_lbl.text() == t("Aan het voorlezen\u2026", self.lang):
                self.status_lbl.setText(t("Gestopt", self.lang))
        self._update_buttons()

    def _on_pos(self, ms):
        if not self.progress.isSliderDown():
            self.progress.setValue(ms)
        self.pos_lbl.setText(self._fmt(ms))

    def _on_dur(self, ms):
        self.progress.setMaximum(max(0, ms))
        self.progress.setEnabled(ms > 0)
        self.dur_lbl.setText(self._fmt(ms))

    def _seek(self):
        if HAVE_MEDIA:
            self.player.setPosition(self.progress.value())

    @staticmethod
    def _fmt(ms):
        s = int(ms / 1000)
        return "%d:%02d" % (s // 60, s % 60)

    def _on_speed(self, val):
        self.speed_lbl.setText("%.2fx" % (val / 100.0))

    def _update_buttons(self):
        playing = bool(HAVE_MEDIA and self.player and
                       self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState)
        self.b_play.setEnabled(HAVE_MEDIA and not self._busy)
        self.b_pause.setEnabled(HAVE_MEDIA and not self._busy and playing)
        self.b_stop.setEnabled(HAVE_MEDIA and not self._busy and playing)
        self.b_save.setEnabled(not self._busy)

    # ---- bestand ----
    def open_txt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("Openen\u2026", self.lang), "",
            t("Documenten (*.txt *.md *.pdf *.docx)", self.lang)
            + ";;" + t("Alle bestanden (*)", self.lang))
        if not path:
            return
        text, err = read_document(path)
        if err:
            QMessageBox.warning(self, t("Kon document niet lezen", self.lang),
                                t(err, self.lang))
            return
        if not (text and text.strip()):
            QMessageBox.information(
                self, t("Kon document niet lezen", self.lang),
                t("Geen leesbare tekst gevonden in dit bestand.", self.lang))
            return
        self.editor.setPlainText(text)

    # ---- menu's ----
    def _settings(self):
        dlg = SettingsDialog(self, dict(self.cfg), self.lang)
        if dlg.exec():
            self.cfg = dlg.result_cfg()
            save_config(self.cfg)

    def _guide(self):
        GuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(
            self, t("Over", self.lang),
            "%s v%s\n\n%s\nNeuvoice (on-device).\nDravenlock\n%s\n%s"
            % (APP_NAME, APP_VERSION,
               "Voorlezer met neurale stemmen." if self.lang == "nl"
               else "Reader with neural voices.",
               SUPPORT_MAIL, DONATE_URL))

    def closeEvent(self, ev):
        try:
            if HAVE_MEDIA:
                self.player.stop()
            self.thread.quit()
            self.thread.wait(2000)
        except Exception:
            pass
        try:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
        except Exception:
            pass
        ev.accept()


QSS = """
* { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid #23232b; }
#title { font-size: 19px; font-weight: 700; }
#ver { color: %(mute)s; font-size: 12px; }
#muted, #hint { color: %(mute)s; font-size: 12px; }
#statusline { color: %(accent)s; font-size: 14px; font-weight: 600; }
QFrame#sep { color: #2c2c36; }
QPushButton { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 9px 14px; color: %(silver)s; min-height: 40px; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton:disabled { color: #55555e; border-color: #23232b; }
QPushButton#headerbtn { min-height: 0; padding: 5px 12px; font-size: 13px; }
QPushButton#primary { background: %(accent)s; color: #08131f; font-weight: 800;
                      border: none; font-size: 16px; }
QPushButton#primary:hover { background: #87b6e3; }
QPushButton#primary:disabled { background: #2c4257; color: #6a7b88; }
QToolButton#donate { border: none; background: transparent; color: %(accent)s; }
QComboBox { background: #14141a; border: 1px solid #2c2c36; border-radius: 8px;
            padding: 7px 10px; min-height: 34px; }
QComboBox QAbstractItemView { background: #16161b; color: %(silver)s;
            selection-background-color: %(accent)s; selection-color: #08131f; }
QTextEdit#reader { background: #14141a; border: 1px solid #2c2c36; border-radius: 10px;
                   padding: 12px 14px; font-size: 19px; color: %(silver)s;
                   selection-background-color: %(accent)s; selection-color: #08131f; }
QSlider::groove:horizontal { height: 6px; background: #23232b; border-radius: 3px; }
QSlider::handle:horizontal { background: %(accent)s; width: 16px; margin: -6px 0;
                             border-radius: 8px; }
QSlider::sub-page:horizontal { background: %(accent)s; border-radius: 3px; }
QStatusBar { background: %(panel)s; }
QDialog { background: %(bg)s; }
QPlainTextEdit#guide { background: %(panel)s; border: 1px solid #2c2c36;
                       border-radius: 8px; padding: 10px; }
""" % {"bg": BG, "panel": PANEL, "silver": SILVER, "mute": MUTE, "accent": ACCENT}


def _install_excepthook():
    import traceback

    def hook(exctype, value, tb):
        msg = "".join(traceback.format_exception(exctype, value, tb))
        try:
            with open(os.path.join(_app_dir(), "draveread-fout.txt"),
                      "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "DraveRead - fout",
                                     "Er ging iets mis:\n\n" + msg[-1500:]
                                     + "\n\n(Ook opgeslagen in draveread-fout.txt)")
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = hook


def main():
    global _LANG
    _install_excepthook()
    app = QApplication(sys.argv)
    try:
        cfg = load_config()
        _LANG = detect_lang(cfg)
        app.setStyleSheet(QSS)
        win = DraveRead(cfg)
        win.show()
    except Exception:
        sys.excepthook(*sys.exc_info())
        return
    try:  # Dravenlock: stille update-check (uit te zetten; Ctrl+Shift+U = met de hand)
        import drave_update
        drave_update.start(win, 'DraveRead', APP_VERSION)
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
