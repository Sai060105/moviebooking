from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
# from .views import generate_pdf_ticket

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    # path('register_login/', views.register_login_view, name='register_login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    # path('generate-seats/<int:show_id>/', views.generate_seats, name='generate_seats'),
    # path('hierarchical-booking/', views.hierarchical_booking, name='hierarchical_booking'),
    path('get-movies/<int:theater_id>/', views.get_movies, name='get_movies'),
    
    path('get-prices/<int:show_id>/', views.get_show_prices, name='get_prices'),

    path("payment/<int:movie_id>/", views.payment, name="payment"),

    path('get-shows/<int:theater_id>/<int:movie_id>/',views.get_shows,name='get_shows'),
    path('book/<int:movie_id>/', views.book_movie, name='book_movie'),
    path("booking-confirmation/<int:booking_id>/",views.booking_confirmation,name="booking_confirmation",),
    
    # path('ticket/pdf/<int:booking_id>/', generate_pdf_ticket, name='generate_pdf_ticket'),
    path("ticket/pdf/<int:booking_id>/", views.download_ticket_pdf, name="download_ticket_pdf"),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    