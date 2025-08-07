from googleapiclient.discovery import build

api_key = 'AIzaSyBgHT0vZTg1b6cgBu6uu27IXmINseNwsPU'
youtube = build('youtube', 'v3', developerKey=api_key)

request = youtube.channels().list(
    part='statistics',
    forUsername='sentdex'
)

try:
    response = request.execute()
    print(response)
except Exception as e:
    print(f'An error occurred: {e}')