import logging
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
from callee import Regex

import webapp


@pytest.fixture
def api():
    return webapp.api


class TestWebApp:
    @staticmethod
    def test(mocker, api, caplog):
        # Patches by mocker since webapp.api from Responder will break when use request_mock.
        #
        # > raise exceptions.NoMockAddress(request)
        # E requests_mock.exceptions.NoMockAddress:
        #   No mock address:
        #     GET http://;/record?station=TBS&program=hoge&rtime=1
        #
        # And, patches in method body since side_effect will be recognize as generator when patch by annotation.
        #
        # File "/app/radiko/recorder.py", line 56, in _get_media_playlist_url
        #   if r.status_code != 200:
        # AttributeError: 'generator' object has no attribute 'status_code'
        mock_ffmpeg_run = mocker.patch('ffmpeg.run')
        mock_ffmpeg_run.side_effect = AacFileCreator().create
        mock_request = mocker.patch(
            'radiko.recorder.Requester.request_media_playlist_url')
        mock_request.side_effect = ResponseIterator().response
        mock_upload = mocker.patch('gcloud.storage.upload_blob')
        response = api.requests.get("/record",
                                    params={
                                        "station": "TBS",
                                        "program": "hoge",
                                        "rtime": "1",
                                    })
        assert response.text == "{\"success\": true}"
        time.sleep(75)
        assert 'WARNING' not in caplog.text
        mock_upload.assert_called_once_with(
            'radiko-recorder',
            Regex(r'\./tmp/\d{8}_\d{4}_TBS_hoge.aac'),
            Regex(r'\d{8}_\d{4}_TBS_hoge.aac'),
        )


@dataclass
class Response:
    status_code: int
    content: bytes


class ResponseIterator:
    def __init__(self):
        self.first_time = True

    def response(self, url, headers):
        if self.first_time:
            self.first_time = False
            return Response(200, (
                "#EXTM3U\n"
                "#EXT-X-VERSION:6\n"
                "#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=52973,CODECS=\"mp4a.40.5\"\n"
                "https://rpaa.smartstream.ne.jp/medialist?session=Q3fHC9Smzp8x49j9AqicBL"
            ).encode('utf-8'))
        else:
            return Response(200, (
                "#EXTM3U\n"
                "#EXT-X-VERSION:6\n"
                "#EXT-X-TARGETDURATION:5\n"
                "#EXT-X-ALLOW-CACHE:NO\n"
                "#EXT-X-MEDIA-SEQUENCE:3267061\n"
                "#EXT-X-DISCONTINUITY-SEQUENCE:0\n"
                "#EXT-X-PROGRAM-DATE-TIME:2020-05-18T03:06:20.000+09:00\n"
                "#EXTINF:4.992,\n"
                "https://rpaa.smartstream.ne.jp/segments/o/B/o/o/XLZqVBVWByx5ZsGnXTB4.aac\n"
                "#EXT-X-PROGRAM-DATE-TIME:2020-05-18T03:06:25.000+09:00\n"
                "#EXTINF:4.992,\n"
                "https://rpaa.smartstream.ne.jp/segments/o/B/4/5/MtbTGXTG2MgWmnQZbgjC.aac\n"
                "#EXT-X-PROGRAM-DATE-TIME:2020-05-18T03:06:30.000+09:00\n"
                "#EXTINF:5.035,\n"
                "https://rpaa.smartstream.ne.jp/segments/o/B/4/g/yaFCNTRefmTkmDoJD3kf.aac"
            ).encode('utf-8'))


class AacFileCreator:
    def __init__(self):
        self.time = 0
        self.path_current_directory = Path(__file__).parent

    def create(self, stream, capture_stdout):
        if self.time == 0:
            self.time = 1
            logging.debug(
                f'Path to file:{self.path_current_directory / "tmp/2020-05-18 03:06:20+09:00.aac"}'
            )
            (self.path_current_directory /
             'tmp/2020-05-18 03:06:20+09:00.aac').write_bytes(b'')
        elif self.time == 1:
            self.time = 2
            (self.path_current_directory /
             'tmp/2020-05-18 03:06:25+09:00.aac').write_bytes(b'')
        elif self.time == 2:
            self.time = 3
            (self.path_current_directory /
             'tmp/2020-05-18 03:06:30+09:00.aac').write_bytes(b'')
        else:
            (self.path_current_directory /
             'tmp/20200518_0106_TBS_hoge.aac').write_bytes(b'')
