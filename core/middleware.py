import logging
logger = logging.getLogger("audit")

class AuditViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)
        if request.user.is_authenticated and request.path.startswith("/admin/"):
            logger.info(
                "user=%s method=%s path=%s status=%s",
                request.user.username,
                request.method,
                request.path,
                getattr(resp, "status_code", "?"),
            )
        if request.path.startswith("/verify/"):
            logger.info("public_verify ip=%s path=%s", request.META.get("REMOTE_ADDR"), request.path)
        return resp
