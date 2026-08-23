from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeviceConfig:
    host: str
    username: str
    api_port: int = 80
    rtsp_port: int = 1554
    use_https: bool = False
    verify_tls: bool = False
    prefer_substream: bool = True

    @property
    def api_base_url(self) -> str:
        scheme = "https" if self.use_https else "http"
        return f"{scheme}://{self.host}:{self.api_port}"


@dataclass(frozen=True, slots=True)
class Camera:
    channel_id: int
    name: str
    enabled: bool = True

    def stream_id(self, prefer_substream: bool) -> int:
        return self.channel_id * 100 + (2 if prefer_substream else 1)
