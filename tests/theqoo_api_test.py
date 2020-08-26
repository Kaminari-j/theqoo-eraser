import unittest
from unittest.mock import MagicMock
import os
from pathlib import Path
from varname import nameof
import requests
import ini
from api import theqoo_api as api
from tests import test_setting
import responses

path = Path(test_setting.TEST_FILE_DIR)
path.mkdir(parents=True, exist_ok=True)

# Set True when do you want to 'real' test
TEST_INSTRUMENTED = True


class DeleteCommentTestCase_Instrumented(unittest.TestCase):
    def delete_comment_success(self, session: requests.Session, comment_srl):
        result = api.delete_comment(session, comment_srl)
        self.assertIsInstance(result, str)

    def delete_comment_fail_with_runtime_error(self, session: requests.Session, comment_srl):
        with self.assertRaises(RuntimeError):
            api.delete_comment(session, comment_srl)

    @unittest.skipUnless(TEST_INSTRUMENTED, f'Test only when {nameof(TEST_INSTRUMENTED)} is True')
    def test_delete_comment_success_instrumented(self):
        with api.get_former_session(session_file_name=test_setting.FILE_WITH_SESSION) as s:
            self.delete_comment_success(s, 1580192797)

    @responses.activate
    def test_delete_comment_success(self):
        res = '﻿<?xml version="1.0" encoding="UTF-8"?>' \
              '<response>' \
              '<error>0</error>' \
              '<message>댓글이 삭제되었습니다. </message>' \
              '<message_type></message_type>' \
              '</response>'
        responses.add(responses.POST, api.INIT_URL, json=res, status=200)
        with requests.session() as s:
            self.delete_comment_success(s, 1580192797)

    @responses.activate
    def test_delete_comment_fail_with_connection_error(self):
        # Not Logged In
        responses.add(responses.POST, api.INIT_URL, status=404)
        with requests.session() as s:
            with self.assertRaises(ConnectionError):
                api.delete_comment(s, 1580192797)

    @unittest.skipUnless(TEST_INSTRUMENTED, f'Test only when {nameof(TEST_INSTRUMENTED)} is True')
    def test_delete_comment_fail_with_runtime_error_instrumented(self):
        # Not Logged In
        with requests.session() as s:
            self.delete_comment_fail_with_runtime_error(s, 1580192797)

    @responses.activate
    def test_delete_comment_fail_with_runtime_error(self):
        result_xml = f'<?xml version="1.0" encoding="utf-8" ?>' \
                  f'<response>' \
                  f'<error>-1</error>' \
                  f'<message>잘못된 요청입니다.</message>' \
                  f'<message_type></message_type>' \
                  f'</response>'
        responses.add(responses.POST, api.INIT_URL, json=result_xml, status=200)
        # Not Logged In
        with requests.session() as s:
            self.delete_comment_fail_with_runtime_error(s, 1580192797)


class GetUserCommentsTestCase(unittest.TestCase):
    def get_user_comments_success(self, session: requests.Session):
        result = api.get_user_comments(session)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for comment in result:
            self.assertRegex(comment, '[0-9]+')

    @unittest.skipUnless(TEST_INSTRUMENTED, f'Test only when {nameof(TEST_INSTRUMENTED)} is True')
    def test_get_user_comments_success_instrumented(self):
        with api.get_former_session(session_file_name=test_setting.FILE_WITH_SESSION) as s:
            self.get_user_comments_success(s)

    @responses.activate
    def test_get_user_comments_success(self):
        body = '<tr>' \
               '<td class="no">149</td>' \
               '<td class="title">' \
               '<div class="origin_document">' \
               '<a href="/1585915956" target="_blank">직장인 : <span style="">Article Title</span></a>' \
               '</div>' \
               '<a href="/1585915956#comment_1585918700" target="_blank">Comment</a>' \
               '</td>' \
               '<td class="nowr date">2020-08-26 14:16:50</td>' \
               '<td class="nowr action" style="width:40px;text-align:center;">' \
               '</tr>'
        url1 = f'{api.INIT_URL}?act={api.Actions.OWN_COMMENTS}&mid={api.INDEX_PAGE_ID}&page=1'
        responses.add(responses.GET, url1, body=body, status=200)
        url2 = f'{api.INIT_URL}?act={api.Actions.OWN_COMMENTS}&mid={api.INDEX_PAGE_ID}&page=2'
        responses.add(responses.GET, url2, status=200)
        with requests.session() as s:
            self.get_user_comments_success(s)

    @responses.activate
    def test_get_user_comments_fail(self):
        url = f'{api.INIT_URL}?act={api.Actions.OWN_COMMENTS}&mid={api.INDEX_PAGE_ID}&page=1'
        responses.add(responses.GET, url, status=404)
        with requests.session() as s:
            with self.assertRaises(ConnectionError):
                api.get_user_comments(s)


class GetFormerSessionTestCase_With_Session(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.exists(test_setting.FILE_WITH_SESSION):
            with requests.session() as s:
                api.do_login(s, ini.THEQOO_ID, ini.THEQOO_PW, test_setting.FILE_WITH_SESSION)

    def test_get_former_session_got_session(self):
        res = api.get_former_session(session_file_name=test_setting.FILE_WITH_SESSION)
        self.assertIsNotNone(res)
        self.assertIsInstance(res, requests.Session)


class GetFormerSessionTestCase_With_No_Session(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not os.path.exists(test_setting.FILE_NO_SESSION):
            try:
                with requests.session() as s:
                    api.do_login(session=s,
                                 login_id='fakeId', login_pw='fakePw',
                                 session_file_name=test_setting.FILE_NO_SESSION)
            except ConnectionError:
                pass

    def test_get_former_session_no_session_file(self):
        # When There's No File
        res = api.get_former_session('File Nothing')
        self.assertIsNone(res, "None should be returned when there's no file")

    def test_get_former_session_no_session(self):
        res = api.get_former_session(session_file_name=test_setting.FILE_NO_SESSION)
        self.assertIsNone(res)


if __name__ == '__main__':
    unittest.main()
