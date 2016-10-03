import importlib

from remoteappmanager.handlers.handler_authenticator import HubAuthenticator
from traitlets import Instance, default
from tornado import web
import tornado.ioloop
from jinja2 import Environment, FileSystemLoader

from tornadowebapi.registry import Registry

from remoteappmanager.db.interfaces import ABCAccounting
from remoteappmanager.handlers.api import HomeHandler
from remoteappmanager.logging.logging_mixin import LoggingMixin
from remoteappmanager.docker.container_manager import ContainerManager
from remoteappmanager.jinja2_adapters import Jinja2LoaderAdapter
from remoteappmanager.user import User
from remoteappmanager.traitlets import as_dict
from remoteappmanager.services.hub import Hub
from remoteappmanager.services.reverse_proxy import ReverseProxy
from remoteappmanager import restresources
from remoteappmanager.utils import url_path_join


class Application(web.Application, LoggingMixin):
    """Tornado main application"""

    user = Instance(User)

    db = Instance(ABCAccounting, allow_none=True)

    reverse_proxy = Instance(ReverseProxy)

    hub = Instance(Hub)

    container_manager = Instance(ContainerManager)

    #: The WebAPI registry
    registry = Instance(Registry)

    @property
    def command_line_config(self):
        return self._command_line_config

    @property
    def file_config(self):
        return self._file_config

    @property
    def environment_config(self):
        return self._environment_config

    def __init__(self,
                 command_line_config,
                 file_config,
                 environment_config):
        """Initializes the application

        config: ApplicationConfiguration
            The application configuration object
        """

        self._command_line_config = command_line_config
        self._file_config = file_config
        self._environment_config = environment_config

        # Observe that settings and config are different things.
        # Config is the external configuration we can change.
        # settings is what we pass as a dictionary to tornado.
        # As a result, settings can contain more information than
        # config.
        settings = {}
        settings.update(as_dict(command_line_config))
        settings.update(as_dict(file_config))
        settings["static_url_prefix"] = (
            self._command_line_config.base_urlpath + "static/")

        self._jinja_init(settings)

        handlers = self._get_handlers()

        super().__init__(handlers, **settings)

    # Initializers
    @default("container_manager")
    def _container_manager_default(self):
        """Initializes the docker container manager."""

        return ContainerManager(
            docker_config=self.file_config.docker_config()
        )

    @default("reverse_proxy")
    def _reverse_proxy_default(self):
        """Initializes the reverse proxy connection object."""
        # Note, we use jupyterhub orm Proxy, but not for database access,
        # just for interface convenience.
        return ReverseProxy(
            endpoint_url=self.command_line_config.proxy_api_url,
            api_token=self.environment_config.proxy_api_token,
        )

    @default("hub")
    def _hub_default(self):
        """Initializes the Hub instance."""
        return Hub(endpoint_url=self.command_line_config.hub_api_url,
                   api_token=self.environment_config.jpy_api_token,
                   )

    @default("db")
    def _db_default(self):
        """Initializes the database connection."""
        class_path = self.file_config.accounting_class
        module_path, _, cls_name = class_path.rpartition('.')
        cls = getattr(importlib.import_module(module_path), cls_name)
        try:
            return cls(**self.file_config.accounting_kwargs)
        except Exception:
            reason = 'The database is not initialised properly.'
            self.log.exception(reason)
            raise web.HTTPError(reason=reason)

    @default("user")
    def _user_default(self):
        """Initializes the user at the database level."""
        user_name = self.command_line_config.user
        user = User(name=user_name)
        user.account = self.db.get_user_by_name(user_name)
        return user

    @default("registry")
    def _registry_default(self):
        reg = Registry()
        reg.authenticator = HubAuthenticator
        for resource_class in [restresources.Application,
                               restresources.Container]:
            reg.register(resource_class)
        return reg

    # Public
    def start(self):
        """Start the application and the ioloop"""

        self.log.info("Starting server with options:")
        for trait_name in self._command_line_config.trait_names():
            self.log.info("{}: {}".format(
                trait_name,
                getattr(self._command_line_config, trait_name)
                )
            )
        self.log.info("Listening for connections on {}:{}".format(
            self.command_line_config.ip,
            self.command_line_config.port))

        self.listen(self.command_line_config.port)

        tornado.ioloop.IOLoop.current().start()

    def urlpath_for_object(self, object):
        """
        Resolves the absolute url path of a given object.
        The object must have a urlpath property.
        """

        return url_path_join(
            self.command_line_config.base_urlpath,
            object.urlpath)

    # Private
    def _get_handlers(self):
        """Returns the registered handlers"""

        base_urlpath = self.command_line_config.base_urlpath
        web_api = self.registry.api_handlers(base_urlpath)
        return web_api+[
            (base_urlpath, HomeHandler),
            (base_urlpath.rstrip('/'),
             web.RedirectHandler, {"url": base_urlpath}),
        ]

    def _jinja_init(self, settings):
        """Initializes the jinja template system settings.
        These will be passed as settings and will be accessible at
        rendering."""
        jinja_env = Environment(
            loader=FileSystemLoader(
                settings["template_path"]
            ),
            autoescape=True
        )

        settings["template_loader"] = Jinja2LoaderAdapter(jinja_env)
