from fasthtml.common import *
import routes.auth
import routes.room

def render(room):
    return Li(A(room.name, href=f"/rooms/{room.id}"))


app, rt = fast_app(
    ws_hdr=True, 
    live=True, 
    pico=False,
    default_hdrs=False,
    hdrs=(
        Link(rel="stylesheet", href="/styles/auth.css"),
        Link(rel="stylesheet", href="/styles/base_styles.css"),
        Link(rel="stylesheet", href="https://unpkg.com/franken-wc@0.0.5/dist/css/slate.min.css"),
        Script(src="https://unpkg.com/htmx.org@2.0.1"),
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.1/sse.js"),
        Script(src="https://cdn.jsdelivr.net/npm/uikit@3.21.6/dist/js/uikit.min.js"),
        Script(src="https://cdn.jsdelivr.net/npm/uikit@3.21.6/dist/js/uikit-icons.min.js"),
        Script(src="https://cdn.tailwindcss.com"),
    )
)

routes.room.routes(app)
routes.auth.routes(app)


serve()
