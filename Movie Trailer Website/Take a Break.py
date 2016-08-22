import os
def rename_files():
    file_list = os.listdir("/Users/GrechkoDmytro/Desktop/Udacity/Full-Stack Web Development NanoDegree/prank")
    print file_list
    for file_name in file_list:
        os.rename(file_name, file_name.translate(None, "0123456789"))
    rename_files()
    

# --------------  BREAK TIME ----------------------
#import webbrowser
#import time
#
#total_breaks = 3
#break_count = 0
#
#print 'This program started on' + ' '+ time.ctime()
#while break_count < total_breaks:
#    time.sleep(10)
#   webbrowser.open('https://www.youtube.com/watch?v=28MmnThlYOo')
#    break_count += 1