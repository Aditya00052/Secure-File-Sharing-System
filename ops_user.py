import requests

api_url = 'http://127.0.0.1:5000'   # base url

# #################### ops_user login ##############################
login_data = {
    'username': 'aditya101',
    'password': 'adityasingh'
}

# Make a POST request to /ops-user/login
response = requests.post(f'{api_url}/ops-user/login', headers=login_data)   # response = requests.post(f'{api_url}/ops-user/login', json=login_data)

# Print the response
print(response.json())

ops_user_token = response.json()['token']
print(ops_user_token)

# ###################### ops_user upload file ######################

file_name = 'test2.xlsx'                        # other options: 'test.pptx', 'test1.docx'
file_path = f'./{file_name}'

# Prepare the file for upload
file = {'file': (f'{file_name}', open(file_path, 'rb'))}

# Set the authorization header with the Ops User token
headers = {'Authorization': ops_user_token}

# Make a POST request to /ops-user/upload-file
upload_response = requests.post(f'{api_url}/ops-user/upload-file', files=file, headers=headers)

# Print the upload response
print(upload_response.json())




