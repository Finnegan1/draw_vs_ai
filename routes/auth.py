import datetime
from fasthtml import *
import db.db as db
import uuid


def check_session(session) -> bool:
    if 'session_id' not in session:
        return False
    try:
        session_entry: db.Session = db.Session.select().where(db.Session.session_id == session['session_id']).get()
        if session_entry.user is None:
            return False
        if session_entry.created_date < datetime.datetime.now() - datetime.timedelta(days=1):
            return False
    except db.Session.DoesNotExist:
        return False
    return True


def routes(app: FastHTML):
    @app.get("/login")
    def get(session):
        if check_session(session):
            return RedirectResponse("/")

        return Div(
            Form(
                Fieldset(
                    Legend("Login", cls="uk-legend"),
                    Div(
                        Input(type="text", name="username", placeholder="Username", cls="uk-input"),
                        cls="uk-margin-top",
                    ),
                    Div(
                        Input(type="password", name="password", placeholder="Password", cls="uk-input"),
                        cls="uk-margin-top",
                    ),
                    Button("Login", cls="uk-button uk-button-primary uk-margin-top", hx_post="/login", hx_target="#login-error"),
                    cls="uk-fieldset flex flex-col justify-center items-center",
                ),
                Div(id="login-error"),
                cls="display-flex justify-center items-center",
            ),
            A("Register", href="/register", cls="uk-link-text uk-margin-top uk-text-muted uk-text-small"),
            cls="auth_bg",
        )

    @app.post("/login")
    def post(session, username:str, password:str):
        user = db.User.select().where(db.User.username == username, db.User.password == password).first()
        if user:
            session_id = str(uuid.uuid4())
            created_session: db.Session = db.Session.create(user=user, session_id=session_id)
            session['session_id'] = created_session.session_id
            return Response(None, 303, headers={"hx-redirect": "/"})
        return "Invalid username or password"

    @app.get("/register")
    def get(session):
        if check_session(session):
            return RedirectResponse("/")

        return Div(
            Form(
                Fieldset(
                    Legend("Register", cls="uk-legend"),
                    Div(
                        Input(type="text", name="username", placeholder="Username", cls="uk-input"),
                        cls="uk-margin-top",
                    ),
                    Div(
                        Input(type="password", name="password", placeholder="Password", cls="uk-input"),
                        cls="uk-margin-top",
                    ),
                    Div(
                        Input(type="email", name="email", placeholder="Email", cls="uk-input"),
                        cls="uk-margin-top",
                    ),
                    Button("Register", cls="uk-button uk-button-primary uk-margin-top", hx_post="/register", hx_target="#register-error"),
                    cls="uk-fieldset flex flex-col justify-center items-center",
                ),
                Div(id="register-error"),
                cls="display-flex justify-center items-center",
            ),
            A("Login", href="/login", cls="uk-link-text uk-margin-top uk-text-muted uk-text-small"),
            cls="auth_bg",
        )

    @app.post("/register")
    def post(session, username:str, password:str, email:str):
        users_with_given_information = db.User.select().where(
            (db.User.username == username) | 
            (db.User.email == email)
        ).count()
        if users_with_given_information > 0:
            return "Username or email already exists."

        user = db.User.create(username=username, password=password, email=email)
        if user:
            session_id = str(uuid.uuid4())
            created_session: db.Session = db.Session.create(user=user, session_id=session_id)
            session['session_id'] = created_session.session_id
            return Response(None, 303, headers={"hx-redirect": "/"})

        return "Failed to register."
