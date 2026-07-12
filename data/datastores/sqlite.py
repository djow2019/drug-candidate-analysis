from data.datastores.datastore import Datastore

class SqliteDatastore(Datastore):

    def connection_url(self, db):
        return "sqlite:///" + db + ".db"

    def name(self):
        return "sqlite"

