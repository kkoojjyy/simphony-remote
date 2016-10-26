from tornado import gen

from tornadowebapi import exceptions
from tornadowebapi.resource import Resource

from remoteappmanager.webapi.decorators import authenticated
from remoteappmanager.db import exceptions as db_exceptions


class User(Resource):
    def validate(self, representation):
        representation["name"] = str(representation["name"])

    @gen.coroutine
    @authenticated
    def delete(self, identifier):
        """Removes the user."""
        db = self.application.db
        try:
            id = int(identifier)
        except ValueError:
            raise exceptions.BadRequest("id")

        try:
            db.remove_user(id=id)
            self.log.info("Removed user with id {}".format(id))
        except db_exceptions.NotFound:
            raise exceptions.NotFound()
        except db_exceptions.UnsupportedOperation:
            raise exceptions.Unable()

    @gen.coroutine
    @authenticated
    def create(self, representation):
        image_name = representation["name"]

        db = self.application.db
        try:
            id = db.create_user(image_name)
        except db_exceptions.Exists:
            raise exceptions.Exists()
        except db_exceptions.UnsupportedOperation:
            raise exceptions.Unable()

        return id
