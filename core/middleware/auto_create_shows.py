# core/middleware/auto_create_shows.py
from datetime import datetime, timedelta, time
from django.utils.timezone import make_aware
from core.models import Movie, Theater, Show

class AutoCreateTomorrowShowsMiddleware:
    DEFAULT_TIMES = [time(13,0), time(16,0), time(19,0), time(22,0)]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.maybe_create_shows(request)
        return self.get_response(request)

    def maybe_create_shows(self, request):
        # Optional: only run when admin pages are hit
        if not request.path.startswith('/admin/'):
            return

        tomorrow = datetime.now().date() + timedelta(days=1)

        for movie in Movie.objects.all():
            # Decide which theaters to use
            theaters_qs = (movie.available_theaters.all()
                           if movie.available_theaters.exists()
                           else Theater.objects.all())

            for theatre in theaters_qs:
                for t in self.DEFAULT_TIMES:
                    dt = make_aware(datetime.combine(tomorrow, t))
                    Show.objects.get_or_create(
                        movie     = movie,
                        theater   = theatre,
                        show_time = dt
                    )
