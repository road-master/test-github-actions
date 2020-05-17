import re
from urllib.parse import urlparse, parse_qs

import pytest

from radiko.recorder import RadikoRecorder


class TestRecorder:
    @staticmethod
    @pytest.mark.parametrize("station", [
        "TBS",
        "QRR",
        "LFR",
        "RN1",
        "RN2",
        "INT",
        "FMT",
        "FMJ",
        "JORF",
        "NACK5",
        "YFM",
        "HOUSOU-DAIGAKU",
        "JOAK",
        "JOAK-FM",
    ])
    def test_make_master_playlist_url(station, requests_mock):
        radiko_authtoken_example = "HrUNR0zyrGseqvlPl1-khQ"
        radiko_key_length_example = "16"
        radiko_key_offset_example = "16"
        requests_mock.get("https://radiko.jp/v2/api/auth1",
                          headers={
                              "X-Radiko-AUTHTOKEN": radiko_authtoken_example,
                              "X-Radiko-KeyLength": radiko_key_length_example,
                              "X-Radiko-KeyOffset": radiko_key_offset_example,
                          })
        requests_mock.get("https://radiko.jp/v2/api/auth2")
        radiko_recorder = RadikoRecorder(station, 30, None)
        parse_result_url = urlparse(
            radiko_recorder._make_master_playlist_url())
        assert parse_result_url.scheme == "https"
        assert parse_result_url.netloc == "rpaa.smartstream.ne.jp"
        assert parse_result_url.path == "/so/playlist.m3u8"
        assert parse_result_url.params == ""
        parsed_result_query = parse_qs(parse_result_url.query)
        assert parsed_result_query["l"] == ["15"]
        assert re.match(r'^[a-fA-F0-9]{38}$', parsed_result_query["lsid"][0])
        assert parsed_result_query["station_id"] == [station]
        assert parsed_result_query["type"] == ["b"]
        assert parse_result_url.fragment == ""
