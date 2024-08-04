import asyncio

from fasthtml.common import *
import fasthtml.common
import sse_starlette.sse

import db.db as db

def LobbyEntry(lobby: db.ScribbleLobby):
    return A(
        P(lobby.name, cls="uk-h3"),
        P(f"Created by {lobby.created_by.username} on {lobby.created_date}", cls="uk-text-meta"),
        cls="uk-card uk-card-default uk-card-body uk-margin",
        href=f"/lobbys/{lobby.id}"
    )


class LobbyManager:
    def __init__(self):
        self.state_id: int = 0
        self.lobbys: list[db.ScribbleLobby] = [lobby for lobby in db.ScribbleLobby.select().where((db.ScribbleLobby.closed == False) & (db.ScribbleLobby.running == False))]
        print(self.lobbys)

    def get_state_id(self):
        return self.state_id

    def update_state(self):
        if self.state_id == 2**64:
            self.state_id = 0
        self.state_id = self.state_id + 1
        self.lobbys = [lobby for lobby in db.ScribbleLobby.select().where((db.ScribbleLobby.closed == False) & (db.ScribbleLobby.running == False))]
        print(self.state_id)
        print(self.lobbys)

    def add_lobby(self, name: str, user: db.User) -> db.ScribbleLobby | None:
        try:
            lobby = db.ScribbleLobby.create(
                name=name,
                created_by=user
            )
            self.update_state()
            return lobby
        except db.IntegrityError:
            return None

    def start_game(self, lobby_id: int, user: db.User) -> bool:
        try:
            lobby = db.ScribbleLobby.select().where(db.ScribbleLobby.id == lobby_id).get()
        except db.ScribbleLobby.DoesNotExist:
            return False
        
        if lobby.created_by != user:
            return False
        
        db.ScribbleLobby.update(running=True).where(db.ScribbleLobby.id == lobby_id).execute()
        self.update_state()
        return True

    def join_lobby(self, lobby: db.ScribbleLobby, user: db.User) -> bool:
        try :
            db.ScribbleLobbyPlayer.select().where(
                (db.ScribbleLobbyPlayer.lobby == lobby) &
                (db.ScribbleLobbyPlayer.user == user)
            ).get()
            return True
        except db.ScribbleLobbyPlayer.DoesNotExist:
            pass
        try:
            db.ScribbleLobbyPlayer.create(lobby=lobby, user=user)
            self.update_state()
            return True
        except db.IntegrityError:
            return False

    def leave_lobby(self, lobby_id: int, user: db.User) -> bool:
        try:
            db.ScribbleLobbyPlayer.delete().where(
                (db.ScribbleLobbyPlayer.lobby == lobby_id) &
                (db.ScribbleLobbyPlayer.user == user)
            ).execute()
            self.update_state()
            return True
        except db.ScribbleLobbyPlayer.DoesNotExist:
            return False

    def close_lobby(self, lobby_id: int, user: db.User) -> bool:
        try:
            lobby = db.ScribbleLobby.select().where(db.ScribbleLobby.id == lobby_id).get()
        except db.ScribbleLobby.DoesNotExist:
            return False
        
        if lobby.created_by != user:
            return False
        
        db.ScribbleLobby.update(closed=True).where(db.ScribbleLobby.id == lobby_id).execute()
        self.update_state()

        return True

    def get_lobby(self, lobby_id: int) -> db.ScribbleLobby | None:
        try:
            return db.ScribbleLobby.select().where(db.ScribbleLobby.id == lobby_id).get()
        except db.ScribbleLobby.DoesNotExist:
            return None

    def get_lobbys(self) -> list[db.ScribbleLobby]:
        return self.lobbys 

lobby_manager = LobbyManager()


def routes(app: FastHTML):
    @app.get("/")
    def get(session):
        if 'session_id' not in session:
            return RedirectResponse("/login")
        try:
            session_entry: db.Session = db.Session.select().where(db.Session.session_id == session['session_id']).get()
        except db.Session.DoesNotExist:
            return RedirectResponse("/login")

        create_lobby = Div(
            Form(
                Input(id="name", name="name", placeholder="New Lobby Name", cls="uk-input w-1/2 uk-margin-right"),
                Button("Create Lobby", cls="uk-button uk-button-default"),
                hx_post="/lobbys",
                hx_target="#lobby-creation-error",
                cls="flex uk-margin",
            ),
            Div(id="lobby-creation-error"),
            cls="uk-margin",
        )

        return Div(
            Titled(
                H1(f"Hi, {session_entry.user.username}!", cls="uk-h1 uk-margin"),
                create_lobby,
                Div(
                    Div(
                        *[
                            LobbyEntry(lobby) 
                            for lobby 
                            in lobby_manager.get_lobbys()
                        ], 
                        id="lobby-list",
                    ),
                    sse_swap="lobbyList",
                ),
            ),
            hx_ext="sse", 
            sse_connect="/lobbys",
            cls="uk-container uk-margin-top",
        )
    
    @app.post("/lobbys")
    def post(session, name:str):
        print(session)
        if 'session_id' not in session:
            return RedirectResponse("/login")
        try:
            session_entry: db.Session = db.Session.select().where(db.Session.session_id == session['session_id']).get()
        except db.Session.DoesNotExist:
            return RedirectResponse("/login")

        lobby_error_alert = Div(
            A(cls="uk-alert-close", uk_close=True),
            Div(
                "Error creating lobby",
                cls="uk-alert-description"
            ),
            cls="uk-alert uk-alert-danger",
            uk_alert=True
        ),

        if len(name) < 3:
            return lobby_error_alert

        lobby = lobby_manager.add_lobby(name, session_entry.user)
        
        if lobby is None:
            return lobby_error_alert

        return Response(None, status_code=201)


    @app.get("/lobbys")
    async def lobbys_sse(session, request):
        if 'session_id' not in session:
            return Response(None, status_code=401)
        try:
            session_entry: db.Session = db.Session.select().where(db.Session.session_id == session['session_id']).get()
        except db.Session.DoesNotExist:
            return Response(None, status_code=401)

        async def event_generator():
            last_send_lobby_state = 0
            while True:
                if await request.is_disconnected():
                    break
                if lobby_manager.get_state_id() != last_send_lobby_state:
                    last_send_lobby_state = lobby_manager.get_state_id()
                    yield sse_starlette.sse.ServerSentEvent(
                        fasthtml.common.to_xml(
                            Div(
                                *[
                                    LobbyEntry(lobby) 
                                    for lobby 
                                    in lobby_manager.get_lobbys()
                                ], 
                                id="lobby-list",
                            ),
                        ),
                        event="lobbyList"
                    )
                await asyncio.sleep(0.5)
        return sse_starlette.sse.EventSourceResponse(event_generator())


    @app.get("/lobbys/{lobby_id}")
    def get(session, lobby_id:int):
        if 'session_id' not in session:
            return RedirectResponse("/login")
        try:
            session_entry: db.Session = db.Session.select().where(db.Session.session_id == session['session_id']).get()
        except db.Session.DoesNotExist:
            return RedirectResponse("/login")

        lobby = lobby_manager.get_lobby(lobby_id)
        if lobby is None:
            return Response("Lobby not found", status_code=404)
        
        joining_result = lobby_manager.join_lobby(lobby, session_entry.user)
        if not joining_result:
            return Response("Failed to join lobby", status_code=500)

        players = [player.user for player in lobby.players]
        print(players)

        admin_options = Div()

        if lobby.created_by == session_entry.user:
            admin_options = Div(
                Button("Start Game", hx_post=f"/lobbys/{lobby_id}/start", cls="uk-button uk-button-primary"),
                Button("Close Lobby", cls="uk-button uk-button-danger"),
                cls="uk-margin"
            )

        return Div(
            H1(lobby.name, cls="uk-h1"),
            P("Players: " + ", ".join([player.username for player in players]),cls="uk-text-meta"),
            P(f"Created by {lobby.created_by.username} on {lobby.created_date}", cls="uk-text-meta"),
            admin_options,
            cls="uk-container uk-margin-top"
        )
    
    @app.post("/lobbys/{lobby_id}/start")
    def post(session, lobby_id:int):
        if 'session_id' not in session:
            return RedirectResponse("/login")
        try:
            session_entry: db.Session = db.Session.select().where(db.Session.session_id == session['session_id']).get()
        except db.Session.DoesNotExist:
            return RedirectResponse("/login")

        game_started = lobby_manager.start_game(lobby_id, session_entry.user)
        if not game_started:
            return Response("Lobby not found", status_code=404)
        
        return Response(None, status_code=204)
    
            
