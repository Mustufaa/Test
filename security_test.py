import os

def get_user_data(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    os.system("ping " + user_input)

    return query