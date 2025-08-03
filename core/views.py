from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse
from .models import Seat, Show, Movie,UserProfile,Booking,Theater,ShowPrice
from django.contrib.auth import authenticate, login
from .forms import UserRegistrationForm, LoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from decimal import Decimal
# from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
# from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
# from io import BytesIO
# from weasyprint import HTML
# import tempfile
# from collections import defaultdict



@login_required
def download_ticket_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Load the same template you're using for confirmation
    template_path = 'core/booking_confirmation.html'

    context = {
        'booking': booking,
        'movie': booking.movie,
        'total': booking.total_price,
        'show': booking.show,
        'seats': booking.seats.all(),
        'pdf' : True
    }

    # Render the HTML
    template = get_template(template_path)
    html = template.render(context)

    print("Total in PDF view:", total)

    # Create a BytesIO buffer for the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Ticket_{booking.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    seats   = booking.seats.all()

    total = 0
    for seat in seats.select_related("seat_class"):
        price = ShowPrice.objects.filter(
                    show=booking.show,
                    seat_class=seat.seat_class
                ).first()
        total += price.price if price else 0

    return render(request, "core/booking_confirmation.html", {
        "booking": booking,
        "seats":   seats,
        "total":   total,
    })



@login_required
@csrf_exempt
def payment(request, movie_id):
    movie      = get_object_or_404(Movie, id=movie_id)

    show_id     = request.session.get("show_id")
    seat_numbers= request.session.get("seat_numbers", [])

    if not show_id or not seat_numbers:
        messages.error(request, "Session expired – please book again.")
        return redirect("book_movie", movie_id=movie.id)

    show  = get_object_or_404(Show, id=show_id)
    seats = Seat.objects.filter(seat_number__in=seat_numbers, show=show)

    # ── compute total ───────────────────────────────────────
    total = Decimal("0.00")
    for seat in seats.select_related("seat_class"):
        price = ShowPrice.objects.filter(show=show,
                                         seat_class=seat.seat_class).first()
        total += price.price if price else 0

    # ── POST → "Pay now" clicked, create booking ────────────
    if request.method == "POST":
        booking = Booking.objects.create(user=request.user,
                                         movie=movie, show=show)
        booking.seats.set(seats)

        # clear temporary session
        for key in ("show_id", "seat_numbers"):
            request.session.pop(key, None)

        return redirect("booking_confirmation", booking_id=booking.id)

    # ── GET → display mock payment page ─────────────────────
    return render(request, "core/payment.html", {
        "movie": movie,
        "show":  show,
        "seats": seat_numbers,
        "total_price": total,
    })


def get_show_prices(request, show_id):
    prices = (ShowPrice.objects
              .filter(show_id=show_id)
              .select_related('seat_class'))
    data = {p.seat_class.name: float(p.price) for p in prices}
    return JsonResponse({'prices': data})



def get_movies(request, theater_id):
    shows = Show.objects.filter(theater_id=theater_id).select_related('movie')
    # unique movies per theater
    movies = {}
    for s in shows:
        movies[s.movie.id] = s.movie.title
    return JsonResponse(
        {'movies': [{'id': pk, 'title': title} for pk, title in movies.items()]}
    )

def get_shows(request, theater_id, movie_id):
    tomorrow = timezone.now().date() + timedelta(days=1)
    shows = (Show.objects
             .filter(theater_id=theater_id,
                     movie_id=movie_id,
                     show_time__date=tomorrow)
             .order_by('show_time'))

    payload = [
        {'id': s.id,
         'time': s.show_time.strftime('%I:%M %p')}  # → 01:00 PM etc.
        for s in shows
    ]
    return JsonResponse({'shows': payload})


def home(request):
    movies = Movie.objects.all()
    return render(request, 'core/home.html', {'movies': movies})

    
@login_required
def book_movie(request, movie_id):
    movie      = get_object_or_404(Movie, id=movie_id)
    tomorrow   = timezone.now().date() + timedelta(days=1)
    shows      = Show.objects.filter(movie=movie,
                                     show_time__date=tomorrow)
    theaters   = Theater.objects.all()

    # seat‑map building ‑‑ (unchanged) ─────────────────────────
    seat_map = {}
    for show in shows:
        all_seats    = Seat.objects.filter(show=show)          \
                                   .values_list('seat_number', flat=True)
        booked_seats = Booking.objects.filter(show=show)       \
                                      .values_list('seats__seat_number', flat=True)
        seat_map[show.id] = {
            "available": list(all_seats),
            "booked":    list(booked_seats),
        }

    # ─── handle POST (user clicked Confirm) ───────────────────
    if request.method == "POST":
        seat_numbers = request.POST.get("selected_seats", "").split(",")
        seat_numbers = [s for s in seat_numbers if s.strip()]

        if not seat_numbers:
            # re‑render with error
            return render(request, "core/book_movie.html", {
                "movie": movie,
                "shows": shows,
                "theaters": theaters,
                "seat_map_json": json.dumps(seat_map),
                "error": "Please select at least one seat."
            })

        show_id = request.POST.get("show_id")
        # --- save the choices in session ---------------------
        request.session["seat_numbers"] = seat_numbers
        request.session["show_id"]      = show_id
        # ------------------------------------------------------
        return redirect("payment", movie_id=movie.id)

    # ─── GET: render the booking form ─────────────────────────
    return render(request, "core/book_movie.html", {
        "movie": movie,
        "shows": shows,
        "theaters": theaters,
        "seat_map_json": json.dumps(seat_map),
    })


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user, email=user.email)
            
            # ✅ Auto login user after registration
            user = authenticate(username=user.username, password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect('home')  # Go to home after auto-login
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Change to your home page
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'core/login.html')



'''def generate_pdf_ticket(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    context = {
        "theatre_name": booking.show.theater.name,
        # "theatre_address": booking.theater.city,
        "movie_name": booking.movie.name,
        "customer_name": booking.user.first_name,
        # "customer_city": "Surendranagar",
        "customer_email": booking.user.email,
        # "customer_phone": booking.user.phone_number,
        "payment_date": booking.booking_date.strftime("%d-%b-%Y %H:%M:%S"),
        "payment_amount": booking.amount_paid,
        "show_date": booking.show.date.strftime("%d-%b-%Y"),
        "show_time": booking.show.time.strftime("%H:%M"),
        "selected_seats": ', '.join(booking.get_seat_list()),
        "total_seats": booking.total_seats
    }

    template_path = 'ticket_show.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename=booking_{booking_id}.pdf'

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)

    if not pdf.err:
        response.write(result.getvalue())
        return response
    else:
        return HttpResponse('PDF generation failed')'''




'''def register_login_view(request):
    return render(request, 'core/register_login.html')'''


# def generate_seats(request, show_id):
"""
    Generates 50 seats for a specific show.
    Seat format: A1–A10, B1–B10, ..., E1–E10
    
    seat_labels = [f"{row}{num}" for row in "ABCDE" for num in range(1, 11)]  # 50 seats
    try:
        show = Show.objects.get(id=show_id)
        created_count = 0
        for label in seat_labels:
            seat, created = Seat.objects.get_or_create(show=show, seat_number=label)
            if created:
                created_count += 1
        return HttpResponse(f"✅ {created_count} seats created for Show ID {show_id}")
    except Show.DoesNotExist:
        return HttpResponse("❌ Invalid Show ID")"""


'''def hierarchical_booking(request):
    theaters = Theater.objects.all()
    print("DEBUG: theaters =>", theaters)   # will show in runserver console
    return render(request, 'core/hierarchical_booking.html',
                  {'theaters': theaters})'''
