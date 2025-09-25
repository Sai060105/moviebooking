# python manage.py import_movies
'''import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from urllib.request import urlretrieve
from core.models import Movie
from datetime import datetime
from django.utils import timezone

class Command(BaseCommand):
    help = 'Imports movie data from OMDb API'
    
    def handle(self, *args, **options):
        # ⚠️ Replace with your OMDb API key ⚠️
        api_key = '29a05ad5'
        
        # OMDb doesn't have a "now playing" list, so we'll search for popular movies.
        # This will be a two-step process: search and then get details.
        
        # 1. Search for a list of movies (e.g., "now playing")
        # search_url = f"http://www.omdbapi.com/?apikey={api_key}&s=now playing&type=movie"

        # Change this line:
        # search_url = f"http://www.omdbapi.com/?apikey={api_key}&s=now playing&type=movie"

        # To one of these to search for different movies:
        search_url = f"http://www.omdbapi.com/?apikey={api_key}&s=popular&type=movie"
        # search_url = f"http://www.omdbapi.com/?apikey={api_key}&s=top rated&type=movie"
        # search_url = f"http://www.omdbapi.com/?apikey={api_key}&s=upcoming&type=movie"
        try:
            search_response = requests.get(search_url)
            search_response.raise_for_status()
            search_data = search_response.json()
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching search data from OMDb: {e}"))
            return

        # 2. Iterate through search results and fetch full details for each
        if search_data.get('Response') == 'True':
            for movie_item in search_data.get('Search', []):
                title = movie_item.get('Title')
                imdb_id = movie_item.get('imdbID')
                
                # Check if movie already exists to avoid duplicates
                if Movie.objects.filter(title=title).exists():
                    self.stdout.write(self.style.WARNING(f"Skipping '{title}' (already exists)"))
                    continue

                # Fetch detailed information for the movie
                details_url = f"http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}"
                try:
                    details_response = requests.get(details_url)
                    details_response.raise_for_status()
                    details_data = details_response.json()
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"Error fetching details for '{title}': {e}"))
                    continue

                # 3. Process the data and download the poster
                if details_data.get('Response') == 'True':
                    # OMDb's data can be a little inconsistent, so we'll check fields
                    poster_url = details_data.get('Poster')
                    if poster_url and poster_url != "N/A":
                        poster_filename = f"{imdb_id}.jpg"
                        poster_full_path = os.path.join(settings.MEDIA_ROOT, 'posters', poster_filename)
                        
                        try:
                            os.makedirs(os.path.join(settings.MEDIA_ROOT, 'posters'), exist_ok=True)
                            urlretrieve(poster_url, poster_full_path)
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error downloading poster for '{title}': {e}"))
                            poster_filename = "default.jpg" # Fallback to a default poster
                    else:
                        poster_filename = "default.jpg" # No poster found
                    
                    release_date_str = details_data.get('Released', '01 Jan 1900')
                    try:
                        release_date = datetime.strptime(release_date_str, '%d %b %Y').date()
                    except ValueError:
                        release_date = datetime.now().date() # Fallback date
                    
                    duration_str = details_data.get('Runtime', '0 min')
                    try:
                        duration = int(duration_str.split(' ')[0])
                    except (ValueError, IndexError):
                        duration = 0

                    # 4. Create the Movie object
                    movie = Movie.objects.create(
                        title=title,
                        description=details_data.get('Plot', ''),
                        duration=duration,
                        release_date=release_date,
                        poster=f'posters/{poster_filename}',
                    )
                    self.stdout.write(self.style.SUCCESS(f"Successfully imported '{movie.title}'"))
        else:
            self.stdout.write(self.style.WARNING(f"OMDb API did not return any search results."))

import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from urllib.request import urlretrieve
from core.models import Movie
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Imports latest Telugu movies from TMDb API'
    
    def handle(self, *args, **options):
        # ⚠️ Replace with your TMDb API Key (v3 auth) ⚠️
        api_key = '8301a21598f8b45668d5711a814f01f6'
        
        # 1. Define Date Range (Previous Week)
        today = timezone.localdate()
        one_week_ago = today - timedelta(days=7)
        
        # TMDb Discover Endpoint for filtering
        base_url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            'api_key': api_key,
            'with_original_language': 'te',  # Filter by Telugu language
            'primary_release_date.gte': one_week_ago.strftime('%Y-%m-%d'),
            'primary_release_date.lte': today.strftime('%Y-%m-%d'),
            'sort_by': 'primary_release_date.desc',
            'include_adult': 'false',
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching data from TMDb: {e}"))
            return

        # 2. Iterate through the filtered movies
        for movie_data in data.get('results', []):
            tmdb_id = movie_data.get('id')
            title = movie_data.get('title')
            poster_path = movie_data.get('poster_path')

            # Constraint 4: Only list movies with available posters (i.e., poster_path is not null)
            if not poster_path:
                self.stdout.write(self.style.WARNING(f"Skipping '{title}' (No poster available)"))
                continue

            # Constraint 3: Prevent Duplicates
            if Movie.objects.filter(title=title).exists():
                self.stdout.write(self.style.WARNING(f"Skipping '{title}' (already exists)"))
                continue

            # 3. Get Movie Details (Duration & Trailer Link)
            details_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            details_params = {'api_key': api_key, 'append_to_response': 'videos'}
            
            try:
                details_response = requests.get(details_url, params=details_params)
                details_response.raise_for_status()
                details = details_response.json()
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error fetching details/trailer for '{title}': {e}"))
                details = {}
            
            # Extract Trailer Link (Constraint 5)
            trailer_link = ""
            videos = details.get('videos', {}).get('results', [])
            for video in videos:
                if video.get('site') == 'YouTube' and video.get('type') == 'Trailer':
                    # Create the embed URL as defined in your Movie model's save method
                    trailer_link = f"https://www.youtube.com/embed/{video.get('key')}"
                    break
            
            # Extract Duration (Runtime)
            duration = details.get('runtime', 0)

            # 4. Download and Save Poster
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            poster_filename = os.path.basename(poster_path)
            poster_full_path = os.path.join(settings.MEDIA_ROOT, 'posters', poster_filename)

            try:
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'posters'), exist_ok=True)
                urlretrieve(poster_url, poster_full_path)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error downloading poster for '{title}': {e}"))
                continue

            # 5. Create the Movie object
            movie = Movie.objects.create(
                title=title,
                description=movie_data.get('overview', ''),
                release_date=datetime.strptime(movie_data['release_date'], '%Y-%m-%d').date(),
                poster=f'posters/{poster_filename}',
                duration=duration,
                trailer_link=trailer_link,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully imported '{movie.title}'"))'''
