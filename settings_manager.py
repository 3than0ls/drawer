import json


def update_settings(value_type, new_value):
    """update the specified value_type in settings.json with new_value"""
    with open('settings.json', 'r') as settings:
        data = json.load(settings)
        new_values = {
            value_type: new_value
        }
        data.update(new_values)


    with open('settings.json', 'w') as settings:
        json.dump(data, settings, indent=4)

def calibrate(value_type, new_value):
    """update the specified value_type of the locations object in settings.json with new_value. Values should be location values (coordinates) for UI parts"""
    with open('settings.json', 'r') as settings:
        data = json.load(settings)
        locations_temp = data['locations']
        new_location = {
            value_type: new_value
        }
        locations_temp.update(new_location)


    with open('settings.json', 'w') as settings:
        json.dump(data, settings, indent=4)

def logout_reddit():
    """calls the update_settings function with pre-defined settings to remove all reddit auth settings"""
    empty_reddit_auth = {
        "username": None,
        "password": None,
        "secret": None,
        "client_id": None
    }
    update_settings('reddit_auth', empty_reddit_auth)

def logout_cse():
    """calls the update_settings function with pre-defined settings to remove all CSE auth settings"""
    empty_cse_auth = {
        "api_key": None,
        "search_engine_id": None,
    }
    update_settings('cse_auth', empty_cse_auth)
