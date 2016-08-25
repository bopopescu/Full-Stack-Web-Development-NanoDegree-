import webbrowser

# I initially wanted to create a parent class Film and make Movie and Series classes as children, but it doesn't
# change the output in the browser due to fresh_tomatoes configuration. So, I decided not to do it.

class Movie():
    """ This class provides a way to store movie related information """

    VALID_RATINGS = ["G", "PG", "PG-13", "R"] # Possible ratings of the movies (they aren't displayed on the website)

    def __init__(self, movie_title, movie_storyline, poster_image, trailer_yourtube):
        self.title = movie_title
        self.storyline = movie_storyline
        self.poster_image_url = poster_image
        self.trailer_youtube_url = trailer_yourtube

    def show_trailer(self):
        webbrowser.open(self.trailer_youtube_url)