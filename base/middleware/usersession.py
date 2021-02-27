from django.conf import settings


class UserSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user
            and request.user.is_authenticated
            and not request.user.is_staff
            and not settings.DEBUG
        ):
            #  settings.DEBUG serve para que não ocorra timeout de sessão em desenvolvimento
            request.session.set_expiry(settings.SESSION_COOKIE_AGE_PSCT)

        response = self.get_response(request)
        return response
