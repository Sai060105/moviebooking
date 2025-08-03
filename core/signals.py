from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Movie, Theater, Show, Seat,SeatClass,ShowPrice
from datetime import datetime, time, timedelta

@receiver(post_save, sender=SeatClass)
def sync_show_prices(sender, instance, **kwargs):
    """
    Anytime the admin saves a SeatClass (default_price changed),
    update EVERY ShowPrice that belongs to this class.
    """
    ShowPrice.objects.filter(seat_class=instance) \
                     .update(price=instance.default_price)
    
    
@receiver(post_save, sender=Movie)
def create_default_shows(sender, instance, created, **kwargs):
    if created:
        # Define default show times (you can add more)
        show_times = [time(10, 0), time(13, 0), time(16, 0), time(19, 0)]

        # Get all theaters (or pick a default theater if you want)
        theaters = Theater.objects.all()

        # For each theater and time, create a Show for this movie
        for theater in theaters:
            for show_time in show_times:
                # Create a datetime for today with show_time
                show_datetime = datetime.combine(datetime.today(), show_time)
                # Create show
                Show.objects.create(movie=instance, theater=theater, show_time=show_datetime)


@receiver(post_save, sender=Show)
def create_seats_for_show(sender, instance, created, **kwargs):
    """
    When a Show is first created → generate 50 seats and
    attach the correct SeatClass (A–B = Premium, C–E = Regular)
    """
    if not created:
        return

    premium  = SeatClass.objects.get(name='Premium')
    regular  = SeatClass.objects.get(name='Regular')

    for row in "ABCDE":
        for num in range(1, 11):
            seat_class = premium if row in "AB" else regular
            Seat.objects.get_or_create(
                show        = instance,
                seat_number = f"{row}{num}",
                defaults    = {'seat_class': seat_class}
            )


@receiver(post_save, sender=Show)
def create_prices_for_show(sender, instance, created, **kwargs):
    """
    When a Show is first created → add a ShowPrice row
    for every SeatClass, using its default_price.
    """
    if not created:
        return

    for seat_cls in SeatClass.objects.all():
        ShowPrice.objects.get_or_create(
            show       = instance,
            seat_class = seat_cls,
            defaults   = {'price': seat_cls.default_price}
        )