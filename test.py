from google_play_scraper import permissions

result = permissions(
    'com.spotify.music',
    lang='en', # defaults to 'en'
    country='us', # defaults to 'us'
)

print(result)