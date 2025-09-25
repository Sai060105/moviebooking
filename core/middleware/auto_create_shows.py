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
'''
# D:\projects\moviebooking\core\middleware\auto_create_shows.py

from django.utils import timezone
from datetime import timedelta, datetime  # 👈 FIX: Import datetime class for combine()
from core.models import Movie, Theater, Show, Seat, SeatClass # 👈 FIX: Import SeatClass

class AutoCreateTomorrowShowsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only run this logic on the first request of the day
        today = timezone.localdate() # Use timezone.localdate() for current date in local TZ
        last_run = request.session.get('last_show_creation_date')

        if last_run != str(today):
            try:
                # 👈 FIX: Fetch a default seat class once
                default_seat_class = SeatClass.objects.first()
            except Exception as e:
                print(f"ERROR: Cannot create shows. No SeatClass found in the database.")
                default_seat_class = None
            
            # 👈 FIX: Only proceed if a SeatClass exists
            if default_seat_class:
                # Define your fixed show times (as time deltas from midnight)
                show_times = [
                    timedelta(hours=10),  # 10:00 AM
                    timedelta(hours=13),  # 1:00 PM
                    timedelta(hours=16),  # 4:00 PM
                    timedelta(hours=19),  # 7:00 PM
                ]
                tomorrow = today + timedelta(days=1)
                
                movies = Movie.objects.filter(available_theaters__isnull=False).distinct()
                theaters = Theater.objects.all()

                for movie in movies:
                    # Filter theaters for the specific movie (using available_theaters M2M field)
                    applicable_theaters = theaters.filter(movie=movie)

                    for theater in applicable_theaters:
                        for show_time_delta in show_times:
                            
                            # 👈 FIX: Correct way to calculate timezone-aware time
                            naive_dt = datetime.combine(tomorrow, datetime.min.time()) + show_time_delta
                            full_show_time = timezone.make_aware(naive_dt)

                            # Use get_or_create to prevent duplicates (relies on model fix from Step 1)
                            show, created = Show.objects.get_or_create(
                                movie=movie,
                                theater=theater,
                                show_time=full_show_time,
                                defaults={'movie': movie, 'theater': theater, 'show_time': full_show_time}
                            )
                            
                            if created:
                                # If a new show was created, also create its seats
                                seat_labels = [f"{row}{num}" for row in "ABCDE" for num in range(1, 11)]
                                for label in seat_labels:
                                    # 👈 FIX: Pass the required seat_class
                                    Seat.objects.create(
                                        show=show, 
                                        seat_number=label,
                                        seat_class=default_seat_class
                                    )

                # Update the session to prevent it from running again today
                request.session['last_show_creation_date'] = str(today)

        response = self.get_response(request)
        return response
'''