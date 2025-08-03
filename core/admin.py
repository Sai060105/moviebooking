from django.contrib import admin
from decimal import Decimal
from django.utils import timezone
from django.utils.safestring import mark_safe
from .models import Movie, Theater, Show, Seat, Booking,UserProfile, SeatClass, ShowPrice
# ✅ Admin Action to Delete Expired Shows

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "movie",
        "theater",
        "seat_summary",
        "show_time",
        "total_price",
        "user",
        "booking_time",
    )

    readonly_fields = (
        "movie",
        "theater",
        "show",
        "show_time",
        "user",
        "booking_time",
        "seat_summary",
        "total_price",
    )

    # ─────────────────────────────────────
    #  helper columns / fields
    # ─────────────────────────────────────
    @admin.display(description="Theater", ordering="show__theater__name")
    def theater(self, obj):
        return obj.show.theater
    
    @admin.display(ordering="show__show_time", description="Show time")
    def show_time(self, obj):
        return obj.show.show_time

    @admin.display(description="Selected seats")
    def seat_summary(self, obj):
        """
        Break seats down by class:
            A1, A2 – Premium
            C1, C2 – Regular
        """
        rows = []
        for sc in SeatClass.objects.all().order_by("name"):
            nums = obj.seats.filter(seat_class=sc).values_list("seat_number", flat=True)
            if nums:
                rows.append(f"{', '.join(nums)} – {sc.name}")
        return mark_safe("<br>".join(rows))

    @admin.display(description="Total ₹")
    def total_price(self, obj):
        total = Decimal("0.00")
        for seat in obj.seats.select_related("seat_class"):
            price = ShowPrice.objects.filter(
                show=obj.show, seat_class=seat.seat_class
            ).first()
            if price:
                total += price.price
        return total

    # ─────────────────────────────────────
    #  LOCK IT DOWN  (no add / edit / delete)
    # ─────────────────────────────────────
    def has_add_permission(self, request):              # no “Add Booking”
        return False

    def has_change_permission(self, request, obj=None): # fields are read‑only
        return False

    def has_delete_permission(self, request, obj=None): # no delete button
        return True
    

@admin.action(description='Delete all expired shows (before today)')
def delete_expired_shows(modeladmin, request, queryset):
    today = timezone.now().date()
    expired_shows = Show.objects.filter(show_time__date__lt=today)
    count = expired_shows.count()
    expired_shows.delete()
    modeladmin.message_user(request, f"{count} expired show(s) deleted successfully.")


@admin.register(SeatClass)
class SeatClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')


class ShowPriceInline(admin.TabularInline):
    model = ShowPrice
    extra = 0


# ✅ Custom Admin for Show
class ShowAdmin(admin.ModelAdmin):
    list_display = ['movie', 'theater', 'show_time']
    inlines      = [ShowPriceInline]
    actions = [delete_expired_shows]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs
    

# core/admin.py
#@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display  = ('title', 'release_date')
    filter_horizontal = ('available_theaters',)   # nice dual‑list widget


admin.site.register(Theater)
admin.site.register(Movie)
admin.site.register(Seat)
admin.site.register(UserProfile)
admin.site.register(Show, ShowAdmin)