from hikvision_app.isapi import _child_text, _local_name
from hikvision_app.models import Camera, DeviceConfig

import xml.etree.ElementTree as ET


def test_namespaced_xml_helpers():
    element = ET.fromstring(
        '<VideoInputChannel xmlns="http://www.hikvision.com/ver20/XMLSchema"><id>3</id></VideoInputChannel>'
    )
    assert _local_name(element.tag) == "VideoInputChannel"
    assert _child_text(element, "id") == "3"


def test_stream_id_selects_main_or_substream():
    camera = Camera(channel_id=4, name="Till")
    assert camera.stream_id(False) == 401
    assert camera.stream_id(True) == 402


def test_api_base_url():
    config = DeviceConfig(host="dvr.internal", username="viewer", api_port=8443, use_https=True)
    assert config.api_base_url == "https://dvr.internal:8443"


def test_observed_dvr_defaults():
    config = DeviceConfig(host="192.168.1.100", username="viewer")
    assert config.api_base_url == "http://192.168.1.100:80"
    assert config.rtsp_port == 1554


def test_rtsp_url_uses_configured_external_port():
    from hikvision_app.isapi import IsapiClient

    config = DeviceConfig(host="192.168.1.100", username="viewer", rtsp_port=1554)
    url = IsapiClient(config, "p@ss/word").rtsp_url(Camera(1, "Front"))
    assert url == "rtsp://viewer:p%40ss%2Fword@192.168.1.100:1554/Streaming/Channels/102"
