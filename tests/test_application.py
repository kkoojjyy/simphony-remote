from unittest.mock import Mock

import os

from jupyterhub import orm
from tests.temp_mixin import TempMixin
from tornado import gen, testing

from remoteappmanager.application import Application
from remoteappmanager.docker.container import Container
from remoteappmanager.docker.container_manager import ContainerManager
from tests import utils
from tests.db import test_csv_db


class TestApplication(TempMixin, testing.AsyncTestCase):
    def setUp(self):
        super().setUp()

        self._old_proxy_api_token = os.environ.get("PROXY_API_TOKEN", None)

        os.environ["PROXY_API_TOKEN"] = "dummy_token"

        self.sqlite_file_path = os.path.join(self.tempdir, "sqlite.db")
        utils.init_sqlite_db(self.sqlite_file_path)

        self.command_line_config = utils.basic_command_line_config()
        self.file_config = utils.basic_file_config()
        self.file_config.db_url = "sqlite:///"+self.sqlite_file_path

        self.app = Application(self.command_line_config, self.file_config)

    def tearDown(self):
        if self._old_proxy_api_token is not None:
            os.environ["PROXY_API_TOKEN"] = self._old_proxy_api_token
        else:
            del os.environ["PROXY_API_TOKEN"]

        super().tearDown()

    def test_initialization(self):
        app = self.app
        self.assertIsNotNone(app.command_line_config)
        self.assertIsNotNone(app.file_config)

        # Test the configuration options
        self.assertIsNotNone(app.command_line_config.port)
        self.assertIsInstance(app.container_manager, ContainerManager)
        self.assertIsInstance(app.reverse_proxy, orm.Proxy)

    def test_container_url_abspath(self):
        app = self.app
        container = Container(url_id="12345")
        abspath = app.container_url_abspath(container)
        self.assertEqual(abspath, "/user/username/containers/12345")

    @testing.gen_test
    def test_reverse_proxy_operations(self):
        coroutine_out = None

        @gen.coroutine
        def mock_api_request(self, *args, **kwargs):
            nonlocal coroutine_out
            yield gen.sleep(0.1)
            coroutine_out = dict(args=args, kwargs=kwargs)

        app = self.app
        app.reverse_proxy = Mock(spec=orm.Proxy)
        app.reverse_proxy.api_request = mock_api_request

        container = Container(docker_id="12345")
        yield app.reverse_proxy_add_container(container)

        self.assertEqual(coroutine_out["kwargs"]["method"], "POST")

        yield app.reverse_proxy_remove_container(container)

        self.assertEqual(coroutine_out["kwargs"]["method"], "DELETE")

    def test_database_initialization(self):
        app = self.app

        self.assertIsNotNone(app.db)
        self.assertIsNotNone(app.user)

        self.assertEqual(app.user.name, "username")
        self.assertEqual(app.user.orm_user, None)


# FIXME: Some of these tests are the same and should be refactored
# Not doing it now to prevent more merge conflict with PR #52
class TestApplicationWithCSV(TempMixin, testing.AsyncTestCase):
    def setUp(self):
        super().setUp()

        self._old_proxy_api_token = os.environ.get("PROXY_API_TOKEN", None)

        os.environ["PROXY_API_TOKEN"] = "dummy_token"

        self.command_line_config = utils.basic_command_line_config()
        self.file_config = utils.basic_file_config()

        self.csv_file = os.path.join(self.tempdir, 'testing.csv')
        self.file_config.db_url = self.csv_file

        test_csv_db.write_csv_file(self.csv_file,
                                   test_csv_db.GoodTable.headers,
                                   test_csv_db.GoodTable.records)

        self.app = Application(self.command_line_config, self.file_config)

    def tearDown(self):
        if self._old_proxy_api_token is not None:
            os.environ["PROXY_API_TOKEN"] = self._old_proxy_api_token
        else:
            del os.environ["PROXY_API_TOKEN"]

        super().tearDown()

    def test_initialization(self):
        app = self.app
        self.assertIsNotNone(app.command_line_config)
        self.assertIsNotNone(app.file_config)

    def test_database_initialization(self):
        app = self.app

        self.assertIsNotNone(app.db)
        self.assertIsNotNone(app.user)

        self.assertEqual(app.user.name, "username")
        self.assertIsInstance(app.user.orm_user, test_csv_db.CSVUser)
