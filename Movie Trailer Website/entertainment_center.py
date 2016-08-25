import fresh_tomatoes
import media

toy_story = media.Movie("Toy Story", "A story of a boy and his toys that came to life",
                        "http://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg",
                        "https://www.youtube.com/watch?v=vwyZH85NQC4")


avatar = media.Movie("Avatar", "A marine on alien planet",
                     "https://zooscope.english.shef.ac.uk/uploads/public_image/1453734098avatar.jpg",
                     "https://www.youtube.com/watch?v=cRdxXPV9GNQ")

house_of_cards = media.Movie("House of Cards", "A dirty, but smart politician captures America",
                             "http://vignette2.wikia.nocookie.net/house-of-cards/images/a/a8/House_of_Cards_Season_1_Poster.jpg/revision/latest?cb=20140217231358,",
                             "https://www.youtube.com/watch?v=ULwUzF1q5w4")

narcos = media.Movie("Narcos", "How Pablo Escobar got so much money and died",
                     "http://d.christiantoday.com/en/full/36859/narcos.jpg",
                     "https://www.youtube.com/watch?v=U7elNhHwgBU")

inception = media.Movie("Inception", "DiCaprio is fighting the rules of time and physics",
                        "http://www.warnerbros.com/sites/default/files/inception_keyart.jpg",
                        "https://www.youtube.com/watch?v=YoHD9XEInc0")

game_of_thrones = media.Movie("Game of Thrones", "Alcohol, intercourse, and blood - Winter is coming",
                              "https://pbs.twimg.com/profile_images/702545332475981824/Mg7TpOaw.jpg",
                              "https://www.youtube.com/watch?v=EI0ib1NErqg")

intouchable= media.Movie("1+1 Intouchable", "Best movie about friendship and courage",
                              "http://ia.media-imdb.com/images/M/MV5BMTYxNDA3MDQwNl5BMl5BanBnXkFtZTcwNTU4Mzc1Nw@@._V1_UY1200_CR90,0,630,1200_AL_.jpg",
                              "https://www.youtube.com/watch?v=34WIbmXkewU")

movies = [toy_story, avatar, house_of_cards, narcos, inception, game_of_thrones, intouchable ]

fresh_tomatoes.open_movies_page(movies)
