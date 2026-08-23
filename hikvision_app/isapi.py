from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests
from requests.auth import HTTPDigestAuth

from .models import Camera, DeviceConfig


class IsapiError(RuntimeError):
    pass


class IsapiClient:
    def __init__(self, config: DeviceConfig, password: str, timeout: float = 8.0):
        self.config = config
        self._password = password
        self.timeout = timeout

    def discover_cameras(self) -> list[Camera]:
        root = self._get_xml("/ISAPI/System/Video/inputs/channels")
        cameras: list[Camera] = []
        for element in root.iter():
            if _local_name(element.tag) != "VideoInputChannel":
                continue
            channel_id = _child_text(element, "id")
            if not channel_id or not channel_id.isdigit():
                continue
            name = _child_text(element, "name") or f"Camera {channel_id}"
            enabled = (_child_text(element, "videoInputEnabled") or "true").lower() == "true"
            cameras.append(Camera(int(channel_id), name.strip(), enabled))

        if not cameras:
            cameras = self._discover_from_streaming_channels()
        return sorted((camera for camera in cameras if camera.enabled), key=lambda item: item.channel_id)

    def _discover_from_streaming_channels(self) -> list[Camera]:
        root = self._get_xml("/ISAPI/Streaming/channels")
        cameras: dict[int, Camera] = {}
        for element in root.iter():
            if _local_name(element.tag) != "StreamingChannel":
                continue
            stream_id = _child_text(element, "id")
            if not stream_id or not stream_id.isdigit():
                continue
            channel_id = int(stream_id) // 100
            if channel_id < 1:
                continue
            name = _child_text(element, "channelName") or f"Camera {channel_id}"
            cameras.setdefault(channel_id, Camera(channel_id, name.strip()))
        return list(cameras.values())

    def _get_xml(self, path: str) -> ET.Element:
        try:
            response = requests.get(
                f"{self.config.api_base_url}{path}",
                auth=HTTPDigestAuth(self.config.username, self._password),
                headers={"Accept": "application/xml"},
                timeout=self.timeout,
                verify=self.config.verify_tls,
            )
            response.raise_for_status()
            return ET.fromstring(response.content)
        except requests.RequestException as exc:
            raise IsapiError(f"ISAPI connection failed: {exc}") from exc
        except ET.ParseError as exc:
            raise IsapiError("The recorder returned invalid ISAPI XML") from exc

    def rtsp_url(self, camera: Camera) -> str:
        username = quote(self.config.username, safe="")
        password = quote(self._password, safe="")
        stream_id = camera.stream_id(self.config.prefer_substream)
        return (
            f"rtsp://{username}:{password}@{self.config.host}:"
            f"{self.config.rtsp_port}/Streaming/Channels/{stream_id}"
        )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local_name(child.tag) == name:
            return child.text
    return None
