import urllib


def read_text():
    quotes = open(
        "/Users/GrechkoDmytro/Desktop/Udacity/Full-Stack Web Development NanoDegree/Movie Trailer Website/movie_quotes.txt")
    contents = quotes.read()
    # print contents
    quotes.close()
    check_profanity(contents)


def check_profanity(text_to_check):
    connection = urllib.urlopen("http://www.wdylike.appspot.com/?q=shot" + text_to_check)
    output = connection.read()
    # print output
    connection.close()
    if "true" in output:
        print "Profanity Alert!!"
    elif "false" in output:
        print "This document has no curse words!"
    else:
        print "Couldn't scan the document properly"


read_text()
