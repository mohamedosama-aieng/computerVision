from __future__ import annotations

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QImage, QPalette, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .isapi import IsapiClient, IsapiError
from .models import Camera, DeviceConfig
from .security import load_password, save_password
from .settings import load_config, save_config
from .stream import StreamWorker


class ConnectionDialog(QDialog):
    def __init__(self, config: DeviceConfig | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recorder connection")
        self.setMinimumWidth(430)
        self.host = QLineEdit(config.host if config else "192.168.1.100")
        self.username = QLineEdit(config.username if config else "admin")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        if config:
            self.password.setText(load_password(config.host, config.username) or "")
        self.api_port = _port_input(config.api_port if config else 80)
        self.rtsp_port = _port_input(config.rtsp_port if config else 1554)
        self.https = QCheckBox("Use HTTPS for ISAPI")
        self.https.setChecked(config.use_https if config else False)
        self.verify_tls = QCheckBox("Verify recorder TLS certificate")
        self.verify_tls.setChecked(config.verify_tls if config else False)
        self.substream = QCheckBox("Use sub-stream (recommended for camera grid)")
        self.substream.setChecked(config.prefer_substream if config else True)

        form = QFormLayout()
        form.addRow("Recorder IP / Tailscale name", self.host)
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)
        form.addRow("ISAPI port", self.api_port)
        form.addRow("RTSP port", self.rtsp_port)
        form.addRow("", self.https)
        form.addRow("", self.verify_tls)
        form.addRow("", self.substream)
        note = QLabel("Use a read-only DVR account over LAN or Tailscale. No port forwarding is required.")
        note.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        if not self.host.text().strip() or not self.username.text().strip() or not self.password.text():
            QMessageBox.warning(self, "Missing details", "Host, username, and password are required.")
            return
        self.accept()

    def values(self) -> tuple[DeviceConfig, str]:
        return (
            DeviceConfig(
                host=self.host.text().strip(),
                username=self.username.text().strip(),
                api_port=self.api_port.value(),
                rtsp_port=self.rtsp_port.value(),
                use_https=self.https.isChecked(),
                verify_tls=self.verify_tls.isChecked(),
                prefer_substream=self.substream.isChecked(),
            ),
            self.password.text(),
        )


class CameraTile(QWidget):
    def __init__(self, camera: Camera, stream_url: str, detect_motion: bool, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.video = QLabel("Connecting...")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video.setMinimumSize(320, 180)
        self.video.setStyleSheet("background: #101419; color: #9aa5b1;")
        self.title = QLabel(camera.name)
        self.status = QLabel("Starting")
        self.status.setStyleSheet("color: #8d9aa8;")
        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.status)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addLayout(header)
        layout.addWidget(self.video, 1)
        self.worker = StreamWorker(stream_url, detect_motion, self)
        self.worker.frame_ready.connect(self._set_frame)
        self.worker.state_changed.connect(self.status.setText)
        self.worker.start()

    def _set_frame(self, image: QImage) -> None:
        pixmap = QPixmap.fromImage(image).scaled(
            self.video.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video.setPixmap(pixmap)

    def stop(self) -> None:
        self.worker.stop()
        self.worker.wait(3000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hikvision Secure Viewer")
        self.resize(1280, 800)
        self._tiles: list[CameraTile] = []
        self._config = load_config()
        self._motion_enabled = False
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(10, 10, 10, 10)
        self._grid.setSpacing(10)
        self.setCentralWidget(self._grid_host)
        self._build_toolbar()
        self.statusBar().showMessage("Not connected")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Controls")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.configure_and_connect)
        disconnect_action = QAction("Disconnect", self)
        disconnect_action.triggered.connect(self.disconnect_all)
        motion_action = QAction("Motion detection", self)
        motion_action.setCheckable(True)
        motion_action.toggled.connect(self._set_motion)
        toolbar.addAction(connect_action)
        toolbar.addAction(disconnect_action)
        toolbar.addSeparator()
        toolbar.addAction(motion_action)

    def configure_and_connect(self) -> None:
        dialog = ConnectionDialog(self._config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        config, password = dialog.values()
        self.statusBar().showMessage("Discovering cameras...")
        try:
            client = IsapiClient(config, password)
            cameras = client.discover_cameras()
            if not cameras:
                raise IsapiError("No enabled camera channels were reported by the recorder")
            save_password(config.host, config.username, password)
            save_config(config)
            self._config = config
            self._show_cameras(client, cameras)
        except (IsapiError, OSError, RuntimeError) as exc:
            QMessageBox.critical(self, "Connection failed", str(exc))
            self.statusBar().showMessage("Connection failed")

    def _show_cameras(self, client: IsapiClient, cameras: list[Camera]) -> None:
        self.disconnect_all()
        columns = max(1, math.ceil(math.sqrt(len(cameras))))
        for index, camera in enumerate(cameras):
            tile = CameraTile(camera, client.rtsp_url(camera), self._motion_enabled, self)
            self._tiles.append(tile)
            self._grid.addWidget(tile, index // columns, index % columns)
        self.statusBar().showMessage(f"Connected: {len(cameras)} camera(s)")

    def disconnect_all(self) -> None:
        for tile in self._tiles:
            tile.stop()
            self._grid.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()
        self.statusBar().showMessage("Not connected")

    def _set_motion(self, enabled: bool) -> None:
        self._motion_enabled = enabled
        if self._tiles:
            QMessageBox.information(self, "Motion detection", "Reconnect to apply this setting to all streams.")

    def closeEvent(self, event) -> None:
        self.disconnect_all()
        event.accept()


def _port_input(value: int) -> QSpinBox:
    field = QSpinBox()
    field.setRange(1, 65535)
    field.setValue(value)
    return field


def apply_dark_palette(app) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#171c22"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#edf1f5"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#101419"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#202731"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#edf1f5"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#252d37"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#edf1f5"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#218c74"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
