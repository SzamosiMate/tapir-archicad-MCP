import hmac


class BearerTokenMiddleware:
    """
    Minimal ASGI middleware that rejects HTTP requests without a valid
    'Authorization: Bearer <token>' header. Used to protect the HTTP-based
    transports; stdio does not need it.
    """

    def __init__(self, app, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"").decode("latin-1")
        expected = f"Bearer {self.token}"

        if not hmac.compare_digest(authorization, expected):
            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"www-authenticate", b"Bearer"),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "Unauthorized: missing or invalid bearer token."}',
                }
            )
            return

        await self.app(scope, receive, send)
