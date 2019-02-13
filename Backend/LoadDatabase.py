from APIClient import *
"""
2019 Cruz Hacks
"""
client = APIClient("people_13")
client.create_database("Known Users")
client.add_person("Pranav", "Your grandchild that loves to sleep", "static/Pranav/*.jpg", "Pranav goes to CHS where he loves to meme")
client.train_data()
client.print_status()
client.print_list()
