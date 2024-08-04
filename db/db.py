from peewee import *
import datetime

db = SqliteDatabase('data/database.db')


class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(unique=True)
    join_date = DateTimeField(default=datetime.datetime.now)

class Session(BaseModel):
    user = ForeignKeyField(User, backref='session')
    session_id = CharField(unique=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    is_active = BooleanField(default=True)

class ScribbleLobby(BaseModel):
    name = CharField(unique=True)
    password = CharField(null=True)
    created_by = ForeignKeyField(User, backref='own_lobbies')
    created_date = DateTimeField(default=datetime.datetime.now)
    running = BooleanField(default=False)
    closed = BooleanField(default=False)

class ScribbleLobbyPlayer(BaseModel):
    lobby = ForeignKeyField(ScribbleLobby, backref='players')
    user = ForeignKeyField(User, backref='lobbies')

class ScribbleGame(BaseModel):
    lobby = ForeignKeyField(ScribbleLobby, backref='games')
    word = CharField()
    created_by = ForeignKeyField(User, backref='scribble_games')
    created_date = DateTimeField(default=datetime.datetime.now)

class ScribbleRightGuess(BaseModel):
    game = ForeignKeyField(ScribbleGame, backref='right_guesses')
    user = ForeignKeyField(User, backref='right_guesses')
    guess = CharField()
    created_date = DateTimeField(default=datetime.datetime.now)


db.connect()
db.create_tables([User, Session, ScribbleLobby, ScribbleLobbyPlayer, ScribbleGame, ScribbleRightGuess])