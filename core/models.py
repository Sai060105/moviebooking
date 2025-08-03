from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    title = models.CharField(max_length=100)
    trailer_link = models.URLField(null=True, blank=True)
    description = models.TextField()
    duration = models.IntegerField(help_text="Duration in minutes")
    release_date = models.DateField()
    poster = models.ImageField(upload_to='posters/',null=False, blank=False, default='posters/default.jpg')

    available_theaters = models.ManyToManyField(
        'Theater',
        blank=True,
        help_text="Leave empty ⟹ schedule in EVERY theater. "
                  "Select one or more ⟹ schedule ONLY in those theaters."
    )
    
    def save(self, *args, **kwargs):
        if self.trailer_link and "youtube.com/watch?v=" in self.trailer_link:
            self.trailer_link = self.trailer_link.replace("watch?v=", "embed/")
        super().save(*args, **kwargs)


    def __str__(self):
        return self.title

class Theater(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.city}"

class Show(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.movie.title} at {self.theater.name} on {self.show_time}"

class SeatClass(models.Model):
    name  = models.CharField(max_length=20, unique=True)  # Premium / Regular
    color = models.CharField(max_length=20, default="#ffc107")  # hex or BS color
    default_price = models.DecimalField(max_digits=6, decimal_places=2, default=150)
    def __str__(self): return self.name

class Seat(models.Model):
    # show = models.ForeignKey(Show, on_delete=models.CASCADE,null=True)
    seat_number = models.CharField(max_length=10)
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="seats")  # 👈 important!
    seat_class = models.ForeignKey(SeatClass, on_delete=models.PROTECT)

    #is_booked = models.BooleanField(default=False)
    class Meta:
        unique_together = ('show', 'seat_number')

    def __str__(self):
        return f"{self.show.id}-{self.seat_number}"
        # return self.seat_number
        # return f"{self.seat_number} - {'Booked' if self.is_booked else 'Available'}"

class ShowPrice(models.Model):
    show        = models.ForeignKey("Show", on_delete=models.CASCADE)
    seat_class  = models.ForeignKey(SeatClass, on_delete=models.CASCADE)
    price       = models.DecimalField(max_digits=6, decimal_places=2)
    class Meta:
        unique_together = ('show', 'seat_class')
    def __str__(self):
        return f"{self.show} / {self.seat_class} = ₹{self.price}"
    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True)
    show = models.ForeignKey(Show, on_delete=models.CASCADE)
    seats = models.ManyToManyField(Seat)
    booking_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.show.movie.title} - {self.booking_time}"
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    #mobile_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return self.user.username