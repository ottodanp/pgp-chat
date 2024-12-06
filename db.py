from sqlite3 import connect, Connection
from uuid import uuid4


# noinspection SqlNoDataSourceInspection
class DbHandler:
    _connection: Connection

    def __init__(self, db_name: str):
        self._connection = connect(db_name)

    def up(self):
        commands = [
            """
            CREATE TABLE IF NOT EXISTS keys (
            key_id VARCHAR PRIMARY KEY,
            public_key TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR PRIMARY KEY,
            username TEXT NOT NULL,
            key_id INTEGER NOT NULL,
            FOREIGN KEY (key_id) REFERENCES keys(key_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            to_id VARCHAR NOT NULL,
            from_id VARCHAR NOT NULL,
            message TEXT NOT NULL,
            FOREIGN KEY (to_id) REFERENCES users(user_id),
            FOREIGN KEY (from_id) REFERENCES users(user_id)
            );
            """
        ]

        for command in commands:
            self._connection.execute(command)

    def down(self):
        commands = [
            "DROP TABLE IF EXISTS keys",
            "DROP TABLE IF EXISTS users",
        ]

        for command in commands:
            self._connection.execute(command)

    def insert_key(self, public_key: str) -> str:
        pkid = str(uuid4())
        self._connection.execute("INSERT INTO keys (key_id, public_key) VALUES (?, ?)", (pkid, public_key))
        self._connection.commit()
        return pkid

    def insert_user(self, username: str, public_key_id: str):
        uid = str(uuid4())
        cur = self._connection.cursor()
        cur.execute("SELECT key_id FROM keys WHERE key_id = ?", (public_key_id,))
        if not cur.fetchone():
            raise ValueError("Public key does not exist")

        cur.execute("INSERT INTO users (user_id, username, key_id) VALUES (?, ?, ?)", (uid, username, public_key_id))

        self._connection.commit()

    def get_user_key(self, username: str) -> str:
        cur = self._connection.cursor()
        cur.execute("SELECT key_id FROM users WHERE username = ?", (username,))
        key_id = cur.fetchone()[0]
        cur.execute("SELECT public_key FROM keys WHERE key_id = ?", (key_id,))
        return cur.fetchone()[0]

    def insert_message(self, to_id: str, from_id: str, message: str):
        message_id = str(uuid4())
        self._connection.execute("INSERT INTO messages (message_id, to_id, from_id, message) VALUES (?, ?, ?)",
                                 (message_id, to_id, from_id, message))
        self._connection.commit()
