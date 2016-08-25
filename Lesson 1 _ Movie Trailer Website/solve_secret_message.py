import os
def rename_files():
    file_list = os.listdir(r"/Users/GrechkoDmytro/Desktop/Udacity/Full-Stack Web Development NanoDegree/prank")
    os.chdir(r"/Users/GrechkoDmytro/Desktop/Udacity/Full-Stack Web Development NanoDegree/prank")
    for file_name in file_list:
        os.rename(file_name, file_name.translate(None, "0123456789"))
rename_files()
