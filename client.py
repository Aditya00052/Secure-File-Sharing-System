import requests

api_url = 'http://127.0.0.1:5000'   # base url

# ##################### client signup ########################
# signup_data = {
#     'username': 'abhishek101',
#     'password': 'abhisheksingh',
#     'email': 'sasuke.uchiha461@yahoo.com'
# }
#
# response = requests.post(f'{api_url}/client-user/signup', headers=signup_data)     # response = requests.post(f'{api_url}/client-user/signup', json=signup_data)
#
# print(response.json())

# ###################### client login ######################
login_data = {
    'username': 'abhishek101',
    'password': 'abhisheksingh',
}

response = requests.post(f'{api_url}/client-user/login', headers=login_data)  # response = requests.post(f'{api_url}/client-user/login', json=login_data)

# print(response.json())

client_token = response.json()['token']

# ####################### Fetching list of all the available files ########################

headers = {
    'Authorization': client_token
}

response = requests.get(f'{api_url}/client-user/list-files', headers=headers)

# print(response.json())

# Printing all the available file:
print('File id\tFile Name\tFile Upload Time')
for file in response.json()['files']:
    print(f'{file["file_id"]}\t{file["filename"]}\t{file["upload_time"]}')


# ################ Downloading a file #############################

file_id = input('Please enter the id of the file you wish to download: ')

response = requests.get(f'{api_url}/client-user/download-file/{file_id}', headers=headers)

print(response.json())


