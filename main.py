import sys
import os
import signal
import random
import math
import json

# ==========================================
# KONFIGURASI SCALING DPI WINDOWS
# ==========================================
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRectF, pyqtProperty,
    QPropertyAnimation, QSequentialAnimationGroup, QPauseAnimation, QEasingCurve,
    QUrl
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QSystemTrayIcon, QMenu, QGraphicsOpacityEffect, QInputDialog
)
from PyQt6.QtGui import (
    QKeySequence, QShortcut, QIcon, QPixmap, QPainter,
    QColor, QBrush, QPen, QFont, QAction
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from pynput import keyboard
from screeninfo import get_monitors

# ==========================================
# PENANGANAN STANDAR OUTPUT UNTUK PYINSTALLER
# ==========================================
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# ==========================================
# SKEMA WARNA & DEFAULT KONFIGURASI
# ==========================================
COLOR_YELLOW = "#ffe88b"

DEFAULT_CONFIG = {
    "work_duration": 15,      # Default: 2 Jam (detik)
    "break_duration": 30,      # Default: 5 Menit (detik)
    "video_choice": "random",   # "random" atau nama file spesifik di assets/videos/
    "sound_choice": "random"    # "random" atau nama file spesifik di assets/sounds/
}


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_config_path():
    if hasattr(sys, "_MEIPASS"):
        base_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "config.json")


def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        cfg = DEFAULT_CONFIG.copy()
                        cfg.update(data)
                        return cfg
        except Exception as e:
            print(f"Gagal membaca config.json: {e}", file=sys.stderr)

    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Gagal menyimpan config.json: {e}", file=sys.stderr)


def get_available_videos():
    """Mengembalikan daftar nama file .mp4 yang ada di folder assets/videos/"""
    videos_dir = get_resource_path(os.path.join("assets", "videos"))
    if os.path.exists(videos_dir) and os.path.isdir(videos_dir):
        return sorted([f for f in os.listdir(videos_dir) if f.lower().endswith(".mp4")])
    return []


def get_available_sounds():
    """Mengembalikan daftar nama file .mp3 yang ada di folder assets/sounds/"""
    sounds_dir = get_resource_path(os.path.join("assets", "sounds"))
    if os.path.exists(sounds_dir) and os.path.isdir(sounds_dir):
        return sorted([f for f in os.listdir(sounds_dir) if f.lower().endswith(".mp3")])
    return []


def resolve_video_path(choice=None):
    """
    Menemukan path file video .mp4 yang sesuai.
    1. Jika choice spesifik dan ada di assets/videos/, gunakan file tersebut.
    2. Jika choice == 'random' atau tidak ditemukan, pilih acak dari assets/videos/.
    3. Fallback: assets/BreakTime1080P.mp4 atau assets/BreakTimeNO.mp4 jika sub-assets belum terisi.
    """
    videos_dir = get_resource_path(os.path.join("assets", "videos"))
    available = []
    if os.path.exists(videos_dir) and os.path.isdir(videos_dir):
        available = [
            os.path.join(videos_dir, f)
            for f in os.listdir(videos_dir)
            if f.lower().endswith(".mp4")
        ]

    # 1. Pilihan file spesifik
    if choice and choice.lower() != "random":
        cand = os.path.join(videos_dir, choice)
        if os.path.exists(cand):
            return cand
        cand_res = get_resource_path(choice)
        if os.path.exists(cand_res):
            return cand_res
        if os.path.exists(choice):
            return choice

    # 2. Pilihan acak dari assets/videos/
    if available:
        return random.choice(available)

    # 3. Fallback otomatis ke assets/BreakTime1080P.mp4
    fb1 = get_resource_path(os.path.join("assets", "BreakTime1080P.mp4"))
    if os.path.exists(fb1):
        return fb1

    # Fallback alternatif jika ada BreakTimeNO.mp4 di root assets
    fb2 = get_resource_path(os.path.join("assets", "BreakTimeNO.mp4"))
    if os.path.exists(fb2):
        return fb2

    assets_dir = get_resource_path("assets")
    if os.path.exists(assets_dir) and os.path.isdir(assets_dir):
        for f in os.listdir(assets_dir):
            if f.lower().endswith(".mp4"):
                return os.path.join(assets_dir, f)

    return None


def resolve_sound_path(choice=None):
    """
    Menemukan path file lagu .mp3 yang sesuai.
    1. Jika choice spesifik dan ada di assets/sounds/, gunakan file tersebut.
    2. Jika choice == 'random' atau tidak ditemukan, pilih acak dari assets/sounds/.
    3. Fallback: assets/Sound.mp3 jika sub-assets belum terisi.
    """
    sounds_dir = get_resource_path(os.path.join("assets", "sounds"))
    available = []
    if os.path.exists(sounds_dir) and os.path.isdir(sounds_dir):
        available = [
            os.path.join(sounds_dir, f)
            for f in os.listdir(sounds_dir)
            if f.lower().endswith(".mp3")
        ]

    # 1. Pilihan file spesifik
    if choice and choice.lower() != "random":
        cand = os.path.join(sounds_dir, choice)
        if os.path.exists(cand):
            return cand
        cand_res = get_resource_path(choice)
        if os.path.exists(cand_res):
            return cand_res
        if os.path.exists(choice):
            return choice

    # 2. Pilihan acak dari assets/sounds/
    if available:
        return random.choice(available)

    # 3. Fallback otomatis ke assets/Sound.mp3
    fb1 = get_resource_path(os.path.join("assets", "Sound.mp3"))
    if os.path.exists(fb1):
        return fb1

    assets_dir = get_resource_path("assets")
    if os.path.exists(assets_dir) and os.path.isdir(assets_dir):
        for f in os.listdir(assets_dir):
            if f.lower().endswith(".mp3"):
                return os.path.join(assets_dir, f)

    return None


def create_tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QBrush(QColor("#1e1e2e")))
    painter.setPen(QPen(QColor(COLOR_YELLOW), 4))
    painter.drawEllipse(4, 4, 56, 56)

    painter.setPen(QPen(QColor("#ffffff"), 4))
    painter.drawLine(32, 32, 32, 16)
    painter.drawLine(32, 32, 44, 32)

    painter.setBrush(QBrush(QColor(COLOR_YELLOW)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(29, 29, 6, 6)

    painter.end()
    return QIcon(pixmap)


class AestheticTimerRing(QWidget):
    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.remaining = duration
        self._progress = 1.0
        self._pulse = 0.0
        self._rot_angle = 0.0

        self.setFixedSize(260, 260)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setup_breathing_animation()
        self.setup_rotation_animation()

    @pyqtProperty(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, val):
        self._progress = val
        self.update()

    @pyqtProperty(float)
    def pulse(self):
        return self._pulse

    @pulse.setter
    def pulse(self, val):
        self._pulse = val
        self.update()

    @pyqtProperty(float)
    def rot_angle(self):
        return self._rot_angle

    @rot_angle.setter
    def rot_angle(self, val):
        self._rot_angle = val
        self.update()

    def setup_breathing_animation(self):
        self.anim_inhale = QPropertyAnimation(self, b"pulse")
        self.anim_inhale.setDuration(2600)
        self.anim_inhale.setStartValue(0.0)
        self.anim_inhale.setEndValue(1.0)
        self.anim_inhale.setEasingCurve(QEasingCurve.Type.InOutSine)

        self.anim_pause = QPauseAnimation(600)

        self.anim_exhale = QPropertyAnimation(self, b"pulse")
        self.anim_exhale.setDuration(2600)
        self.anim_exhale.setStartValue(1.0)
        self.anim_exhale.setEndValue(0.0)
        self.anim_exhale.setEasingCurve(QEasingCurve.Type.InOutSine)

        self.breath_group = QSequentialAnimationGroup(self)
        self.breath_group.addAnimation(self.anim_inhale)
        self.breath_group.addAnimation(self.anim_pause)
        self.breath_group.addAnimation(self.anim_exhale)
        self.breath_group.setLoopCount(-1)
        self.breath_group.start()

    def setup_rotation_animation(self):
        self.anim_rot = QPropertyAnimation(self, b"rot_angle")
        self.anim_rot.setDuration(12000)
        self.anim_rot.setStartValue(0.0)
        self.anim_rot.setEndValue(360.0)
        self.anim_rot.setEasingCurve(QEasingCurve.Type.Linear)
        self.anim_rot.setLoopCount(-1)
        self.anim_rot.start()

    def update_countdown(self, remaining):
        self.remaining = remaining
        target = max(0.0, remaining / self.duration) if self.duration > 0 else 0.0

        if hasattr(self, "_prog_anim"):
            self._prog_anim.stop()

        self._prog_anim = QPropertyAnimation(self, b"progress")
        self._prog_anim.setDuration(850)
        self._prog_anim.setStartValue(self._progress)
        self._prog_anim.setEndValue(target)
        self._prog_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._prog_anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # 1. Gelombang ripple ganda (dual concentric breathing ripples)
        r1 = 80 + self._pulse * 18
        painter.setPen(QPen(QColor(255, 232, 139, int(30 * (1.0 - self._pulse * 0.7))), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(cx - r1, cy - r1, r1 * 2, r1 * 2))

        phase2 = (self._pulse + 0.5) % 1.0
        r2 = 80 + phase2 * 22
        painter.setPen(QPen(QColor(255, 232, 139, int(22 * (1.0 - phase2))), 1.0))
        painter.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))

        # 2. Aura pendaran cahaya ambient (ambient breathing glow)
        aura_rad = 84 + self._pulse * 12
        alpha = int(18 + self._pulse * 30)
        painter.setBrush(QColor(255, 232, 139, alpha))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - aura_rad, cy - aura_rad, aura_rad * 2, aura_rad * 2))

        # 3. Indikator garis presisi (radial tick marks seperti dial chronograph)
        for i in range(36):
            deg = i * 10
            rad = math.radians(deg - 90)
            frac = i / 36.0
            is_active = frac <= self._progress
            c = QColor(COLOR_YELLOW) if is_active else QColor(255, 255, 255, 30)
            painter.setPen(QPen(c, 1.5))
            x1 = cx + 67 * math.cos(rad)
            y1 = cy + 67 * math.sin(rad)
            x2 = cx + 72 * math.cos(rad)
            y2 = cy + 72 * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 4. Cincin orbit radar putar luar (rotating tech dashed ring)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._rot_angle)
        dash_pen = QPen(QColor(255, 232, 139, 45), 1.2, Qt.PenStyle.DashLine)
        dash_pen.setDashPattern([3, 14])
        painter.setPen(dash_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(-102, -102, 204, 204))
        painter.restore()

        # 5. Partikel satelit mengorbit (3 orbital drifting star particles)
        particles = [
            (108, self._rot_angle, 3.0, QColor(255, 232, 139, 190)),
            (114, -self._rot_angle * 0.7 + 120, 2.0, QColor(255, 255, 255, 150)),
            (98, self._rot_angle * 1.4 + 240, 2.5, QColor(255, 220, 110, 170))
        ]
        painter.setPen(Qt.PenStyle.NoPen)
        for dist, ang, sz, col in particles:
            ar = math.radians(ang)
            px = cx + dist * math.cos(ar)
            py = cy + dist * math.sin(ar)
            # Soft glow around particle
            painter.setBrush(QColor(col.red(), col.green(), col.blue(), int(col.alpha() * 0.4)))
            painter.drawEllipse(QRectF(px - sz * 2, py - sz * 2, sz * 4, sz * 4))
            # Solid core
            painter.setBrush(col)
            painter.drawEllipse(QRectF(px - sz, py - sz, sz * 2, sz * 2))

        # 6. Jalur latar belakang ring utama (background track)
        radius = 80
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        pen_track = QPen(QColor(255, 255, 255, 35), 6)
        pen_track.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)

        # 7. Busur waktu hitung mundur (progress arc)
        pen_arc = QPen(QColor(COLOR_YELLOW), 6)
        pen_arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_arc)
        span = int(self._progress * 360 * 16)
        painter.drawArc(rect, 90 * 16, -span)

        # 8. Titik jarum bercahaya di ujung busur (glowing indicator head dot)
        if self._progress > 0.005:
            angle_deg = 90.0 - (self._progress * 360.0)
            angle_rad = math.radians(angle_deg)
            tip_x = cx + radius * math.cos(angle_rad)
            tip_y = cy - radius * math.sin(angle_rad)

            tip_glow_r = 6.5 + self._pulse * 2.5
            tip_glow_alpha = int(100 + self._pulse * 90)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 232, 139, tip_glow_alpha))
            painter.drawEllipse(QRectF(tip_x - tip_glow_r, tip_y - tip_glow_r, tip_glow_r * 2, tip_glow_r * 2))

            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(QRectF(tip_x - 3.5, tip_y - 3.5, 7, 7))

        # 9. Tipografi angka waktu hitung mundur
        mins, secs = divmod(int(self.remaining), 60)
        time_text = f"{mins:02d}:{secs:02d}"
        painter.setPen(QColor(COLOR_YELLOW))
        painter.setFont(QFont("Aileron", 34, QFont.Weight.Bold))
        painter.drawText(QRectF(0, cy - 28, w, 44), Qt.AlignmentFlag.AlignCenter, time_text)

        # 10. Label teks bernapas halus di bawah angka (tanpa emoji)
        sub_alpha = int(120 + self._pulse * 100)
        painter.setPen(QColor(255, 255, 255, sub_alpha))
        sub_font = QFont("Aileron", 9, QFont.Weight.Medium)
        sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        painter.setFont(sub_font)
        painter.drawText(QRectF(0, cy + 18, w, 20), Qt.AlignmentFlag.AlignCenter, "REST")

        painter.end()


class AlertBreakOverlay(QWidget):
    emergency_requested = pyqtSignal()

    def __init__(self, monitor_geometry, video_path=None, break_duration=30, is_primary=False):
        super().__init__()
        self.is_primary = is_primary
        self.break_duration = break_duration
        self.remaining_time = break_duration
        self.video_path = video_path
        self.current_frame = None

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.setGeometry(
            monitor_geometry.x,
            monitor_geometry.y,
            monitor_geometry.width,
            monitor_geometry.height
        )

        # ── 1. IMPLEMENTASI VIDEO BACKGROUND (QVideoSink) ─────────────────────
        if self.video_path and os.path.exists(self.video_path):
            self.bg_player = QMediaPlayer(self)
            self.bg_audio = QAudioOutput(self)
            self.bg_audio.setMuted(True)
            self.bg_player.setAudioOutput(self.bg_audio)

            self.video_sink = QVideoSink(self)
            self.video_sink.videoFrameChanged.connect(self._on_video_frame)
            self.bg_player.setVideoSink(self.video_sink)

            self.bg_player.setSource(QUrl.fromLocalFile(self.video_path))
            self.bg_player.setLoops(QMediaPlayer.Loops.Infinite)
            self.bg_player.play()
        else:
            self.setStyleSheet("background-color: #11111b;")

        # ── 2. CONTAINER UI TRANSPARAN DI ATAS VIDEO ───────────────────────────
        if self.is_primary:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)

            self.content_box = QWidget(self)
            self.content_box.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.content_box.setStyleSheet("background: transparent;")

            content_layout = QVBoxLayout(self.content_box)
            content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.setSpacing(25)

            # Timer Ring Hitung Mundur (#ffe88b)
            self.timer_ring = AestheticTimerRing(self.break_duration)

            # Tombol Buka Kunci Darurat
            self.emergency_btn = QPushButton("Emergency Unlock (Ctrl+Shift+E)")
            self.emergency_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.emergency_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(0, 0, 0, 0.55);
                    color: {COLOR_YELLOW};
                    border: 1.5px solid {COLOR_YELLOW};
                    border-radius: 20px;
                    padding: 10px 28px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_YELLOW};
                    color: #111;
                }}
            """)
            self.emergency_btn.clicked.connect(self.emergency_requested.emit)

            content_layout.addWidget(self.timer_ring, alignment=Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(self.emergency_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            main_layout.addWidget(self.content_box)
            # Paksa container melayang tepat di depan video background
            self.content_box.raise_()

        self.shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        self.shortcut.activated.connect(self.emergency_requested.emit)

    def _on_video_frame(self, frame):
        self.current_frame = frame.toImage()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.current_frame and not self.current_frame.isNull():
            painter.drawImage(self.rect(), self.current_frame)
        else:
            painter.fillRect(self.rect(), QColor("#11111b"))
        painter.end()

    def resizeEvent(self, event):
        """Memastikan posisi video dan timer ring selalu sempurna pas di tengah layar"""
        super().resizeEvent(event)
        if hasattr(self, "content_box"):
            self.content_box.raise_()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "content_box"):
            self.content_box.raise_()

    def closeEvent(self, event):
        if hasattr(self, "bg_player") and self.bg_player:
            self.bg_player.stop()
        super().closeEvent(event)

    def update_countdown(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            if self.is_primary and hasattr(self, "timer_ring"):
                self.timer_ring.update_countdown(self.remaining_time)
            return False
        return True


class GlobalKeyboardWorker(QObject):
    emergency_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_keys = set()
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.daemon = True
        self.listener.start()

    def _is_ctrl(self, key):
        return (
            key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)
            or getattr(key, "vk", None) in (17, 162, 163)
        )

    def _is_shift(self, key):
        return (
            key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r)
            or getattr(key, "vk", None) in (16, 160, 161)
        )

    def _is_e(self, key):
        return (
            getattr(key, "vk", None) == 69
            or getattr(key, "char", None) in ("e", "E", "\x05")
            or key == keyboard.KeyCode.from_char("e")
            or key == keyboard.KeyCode.from_char("E")
        )

    def on_key_press(self, key):
        self.current_keys.add(key)
        has_ctrl = any(self._is_ctrl(k) for k in self.current_keys)
        has_shift = any(self._is_shift(k) for k in self.current_keys)
        has_e = any(self._is_e(k) for k in self.current_keys)

        if has_ctrl and has_shift and has_e:
            self.emergency_signal.emit()

    def on_key_release(self, key):
        try:
            self.current_keys.discard(key)
        except Exception:
            pass

    def reset_keys(self):
        self.current_keys.clear()

    def stop(self):
        try:
            self.listener.stop()
        except Exception:
            pass


class AppController:
    def __init__(self):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Muat konfigurasi yang tersimpan
        self.config = load_config()

        self.overlays = []
        self.state = "WORKING"
        self.is_paused = False
        self.current_work_time = self.config.get("work_duration", 7200)

        # Audio Output untuk Lagu Relaksasi
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

        # System Tray & Menu
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self.app)
        self.setup_tray_menu()
        self.tray_icon.show()

        # Timer Detik
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.tick)
        self.clock_timer.start(1000)

        # Global Hotkey Listener
        self.keyboard_worker = GlobalKeyboardWorker()
        self.keyboard_worker.emergency_signal.connect(self.end_break)

        self.update_tray_tooltip()

        # Tampilkan notifikasi tray & terminal saat aplikasi dimulai
        self.tray_icon.showMessage(
            "BreakTime Aktif",
            f"Timer kerja dimulai ({self.format_time(self.current_work_time)}). Berjalan di background/tray.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
        print(f"[BreakTime] Aktif di background. Durasi kerja: {self.current_work_time}s, Durasi istirahat: {self.config.get('break_duration', 30)}s.")
        print("[BreakTime] Layar penuh akan otomatis muncul saat hitungan mundur selesai (atau klik tray menu 'Mulai Istirahat Sekarang').")

    def setup_tray_menu(self):
        self.tray_menu = QMenu()

        # Status Action (Disabled, hanya sebagai display)
        self.status_action = self.tray_menu.addAction("Status: Memulai...")
        self.status_action.setEnabled(False)
        self.tray_menu.addSeparator()

        # Pause / Resume Action
        self.action_pause = self.tray_menu.addAction("⏸️ Pause Timer")
        self.action_pause.triggered.connect(self.toggle_pause)

        # Quick Actions
        self.action_break_now = self.tray_menu.addAction("☕ Mulai Istirahat Sekarang")
        self.action_break_now.triggered.connect(self.start_break)

        self.action_reset_work = self.tray_menu.addAction("🔄 Reset Waktu Kerja")
        self.action_reset_work.triggered.connect(self.reset_work_timer)

        self.tray_menu.addSeparator()

        # Sub-Menu Pengaturan Waktu & Media
        self.settings_menu = self.tray_menu.addMenu("⚙️ Pengaturan Waktu & Media")
        self.settings_menu.aboutToShow.connect(self.update_settings_menu)

        self.menu_work = self.settings_menu.addMenu("⏱️ Waktu Kerja")
        self.menu_break = self.settings_menu.addMenu("☕ Waktu Istirahat")
        self.settings_menu.addSeparator()
        self.menu_video = self.settings_menu.addMenu("🎬 Video Background")
        self.menu_sound = self.settings_menu.addMenu("🎵 Lagu Relaksasi")

        self.update_settings_menu()

        self.tray_menu.addSeparator()
        self.action_quit = self.tray_menu.addAction("❌ Keluar Aplikasi")
        self.action_quit.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(self.tray_menu)

    def update_settings_menu(self):
        """Memperbarui item dan checkmark pada sub-menu Pengaturan Waktu & Media."""
        # 1. Sub-Menu Waktu Kerja
        self.menu_work.clear()
        work_presets = [
            (15, "15 Detik (Testing)"),
            (20, "20 Detik (Testing)"),
            (3600, "1 Jam"),
            (5400, "1.5 Jam"),
            (7200, "2 Jam")
        ]
        current_work = self.config.get("work_duration", 7200)
        matched_work = False

        for sec, label in work_presets:
            act = self.menu_work.addAction(label)
            act.setCheckable(True)
            if current_work == sec:
                act.setChecked(True)
                matched_work = True
            act.triggered.connect(lambda checked, s=sec: self.set_work_duration(s))

        self.menu_work.addSeparator()
        if matched_work:
            custom_label = "✏️ Kustom (Menit)..."
        else:
            custom_mins = current_work / 60
            custom_label = f"✏️ Kustom ({custom_mins:g} Menit)"

        act_custom = self.menu_work.addAction(custom_label)
        act_custom.setCheckable(True)
        if not matched_work:
            act_custom.setChecked(True)
        act_custom.triggered.connect(self.prompt_custom_work_duration)

        # 2. Sub-Menu Waktu Istirahat
        self.menu_break.clear()
        break_presets = [
            (15, "15 Detik (Testing)"),
            (30, "30 Detik (Testing)"),
            (300, "5 Menit"),
            (600, "10 Menit"),
            (900, "15 Menit")
        ]
        current_break = self.config.get("break_duration", 300)

        for sec, label in break_presets:
            act = self.menu_break.addAction(label)
            act.setCheckable(True)
            if current_break == sec:
                act.setChecked(True)
            act.triggered.connect(lambda checked, s=sec: self.set_break_duration(s))

        # 3. Sub-Menu Video Background
        self.menu_video.clear()
        current_video = self.config.get("video_choice", "random")

        act_rand_video = self.menu_video.addAction("🔀 Acak / Random")
        act_rand_video.setCheckable(True)
        if current_video == "random":
            act_rand_video.setChecked(True)
        act_rand_video.triggered.connect(lambda: self.set_video_choice("random"))

        self.menu_video.addSeparator()
        videos = get_available_videos()
        if videos:
            for v_file in videos:
                act = self.menu_video.addAction(v_file)
                act.setCheckable(True)
                if current_video == v_file:
                    act.setChecked(True)
                act.triggered.connect(lambda checked, f=v_file: self.set_video_choice(f))
        else:
            act_none = self.menu_video.addAction("(Folder assets/videos/ kosong)")
            act_none.setEnabled(False)

        # 4. Sub-Menu Lagu Relaksasi
        self.menu_sound.clear()
        current_sound = self.config.get("sound_choice", "random")

        act_rand_sound = self.menu_sound.addAction("🔀 Acak / Random")
        act_rand_sound.setCheckable(True)
        if current_sound == "random":
            act_rand_sound.setChecked(True)
        act_rand_sound.triggered.connect(lambda: self.set_sound_choice("random"))

        self.menu_sound.addSeparator()
        sounds = get_available_sounds()
        if sounds:
            for s_file in sounds:
                act = self.menu_sound.addAction(s_file)
                act.setCheckable(True)
                if current_sound == s_file:
                    act.setChecked(True)
                act.triggered.connect(lambda checked, f=s_file: self.set_sound_choice(f))
        else:
            act_none = self.menu_sound.addAction("(Folder assets/sounds/ kosong)")
            act_none.setEnabled(False)

    def set_work_duration(self, seconds):
        self.config["work_duration"] = int(seconds)
        save_config(self.config)
        self.current_work_time = self.config["work_duration"]
        self.update_tray_tooltip()
        self.update_settings_menu()

    def prompt_custom_work_duration(self):
        current_minutes = max(1, round(self.config.get("work_duration", 7200) / 60))
        minutes, ok = QInputDialog.getInt(
            None,
            "Kustom Waktu Kerja",
            "Masukkan durasi kerja (menit):",
            value=current_minutes,
            min=1,
            max=720,
            step=1
        )
        if ok and minutes > 0:
            self.set_work_duration(minutes * 60)

    def set_break_duration(self, seconds):
        self.config["break_duration"] = int(seconds)
        save_config(self.config)
        self.update_settings_menu()

    def set_video_choice(self, choice):
        self.config["video_choice"] = choice
        save_config(self.config)
        self.update_settings_menu()

    def set_sound_choice(self, choice):
        self.config["sound_choice"] = choice
        save_config(self.config)
        self.update_settings_menu()

    def toggle_pause(self):
        if self.state != "WORKING":
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.action_pause.setText("▶️ Resume Timer")
        else:
            self.action_pause.setText("⏸️ Pause Timer")
        self.update_tray_tooltip()

    def format_time(self, seconds):
        mins, secs = divmod(int(seconds), 60)
        return f"{mins:02d}:{secs:02d}"

    def update_tray_tooltip(self):
        if self.state == "WORKING":
            time_str = self.format_time(self.current_work_time)
            if self.is_paused:
                msg = f"BreakTime: Di-Pause ({time_str})"
                self.status_action.setText(f"Status: Di-Pause ({time_str})")
            else:
                msg = f"BreakTime: Sedang Bekerja ({time_str})"
                self.status_action.setText(f"Status: Bekerja ({time_str})")
            self.action_pause.setEnabled(True)
            self.action_break_now.setEnabled(True)
        else:
            msg = "BreakTime: Waktu Istirahat!"
            self.status_action.setText("Status: Sedang Istirahat")
            self.action_pause.setEnabled(False)
            self.action_break_now.setEnabled(False)

        self.tray_icon.setToolTip(msg)

    def tick(self):
        if self.state == "WORKING":
            if self.is_paused:
                # Timer dijeda, tidak mengurangi countdown
                return

            self.current_work_time -= 1
            self.update_tray_tooltip()

            if self.current_work_time <= 0:
                self.start_break()

        elif self.state == "RESTING":
            finished_any = False
            for overlay in self.overlays:
                if overlay.update_countdown():
                    finished_any = True

            if finished_any:
                self.end_break()

    def start_break(self):
        if self.state == "RESTING":
            return

        self.state = "RESTING"
        self.is_paused = False
        self.action_pause.setText("⏸️ Pause Timer")
        self.overlays.clear()
        self.keyboard_worker.reset_keys()
        self.update_tray_tooltip()

        # Putar Lagu Relaksasi
        sound_path = resolve_sound_path(self.config.get("sound_choice", "random"))
        if sound_path and os.path.exists(sound_path):
            self.player.setSource(QUrl.fromLocalFile(sound_path))
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
            self.player.play()

        # Siapkan Video Background & Durasi Istirahat
        video_path = resolve_video_path(self.config.get("video_choice", "random"))
        break_duration = self.config.get("break_duration", 300)

        monitors = get_monitors()
        if not monitors:
            screen = QApplication.primaryScreen()
            geo = screen.geometry()

            class FallbackMonitor:
                x = geo.x()
                y = geo.y()
                width = geo.width()
                height = geo.height()

            monitors = [FallbackMonitor()]

        for i, m in enumerate(monitors):
            overlay = AlertBreakOverlay(
                monitor_geometry=m,
                video_path=video_path,
                break_duration=break_duration,
                is_primary=(i == 0)
            )
            overlay.emergency_requested.connect(self.end_break)
            overlay.showFullScreen()
            if i == 0:
                overlay.activateWindow()
                overlay.raise_()
                overlay.setFocus()
            self.overlays.append(overlay)

    def end_break(self):
        if self.state != "RESTING":
            return

        # Hentikan Lagu Relaksasi
        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()

        self.state = "WORKING"
        self.is_paused = False
        self.action_pause.setText("⏸️ Pause Timer")
        self.current_work_time = self.config.get("work_duration", 7200)

        self.keyboard_worker.reset_keys()

        for overlay in self.overlays:
            overlay.close()
            overlay.deleteLater()
        self.overlays.clear()

        self.update_tray_tooltip()

    def reset_work_timer(self):
        if self.state == "WORKING":
            self.current_work_time = self.config.get("work_duration", 7200)
            self.update_tray_tooltip()

    def quit_app(self):
        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
        self.clock_timer.stop()
        self.keyboard_worker.stop()
        for overlay in self.overlays:
            overlay.close()
            overlay.deleteLater()
        self.overlays.clear()
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()