import json
import json
import boto3
import requests
from requests_aws4auth import AWS4Auth


def lambda_handler(event, context):
    client = boto3.client('lexv2-runtime') 
    print(event)
    input_text = event['q']
    print(input_text)
    input_text = input_text.lower()
    response = client.recognize_text(
            botId='B88WGUH7TA', # MODIFY HERE
            botAliasId='7RSMCO9FQW', # MODIFY HERE
            localeId='en_US',
            sessionId='testuser',
            text=input_text)
    
    msg_from_lex = response.get('messages', [])
        
    print (msg_from_lex)
    labels = []
    if 'intentName' not in response:
        labels = []
    elif response["interpretations"][0]['intent']['name'] == "Label":
        for slot in response["slots"]:
            e = response["slots"][slot]
            if e is not None:
                labels.append(e)

    print(labels)
    
    query_string = ''
    if len(labels) == 1:
        query_string = '(' + labels[0] + ')'
    elif len(labels) > 1:
        query_string = '(' + labels[0] + ')'
        for i in range(len(labels) - 1):
            query_string = query_string + ' OR (' + labels[i + 1] + ')'
    print(query_string)

    query = {
        "size": 20,
        "query": {
            "query_string": {
                "default_field": "labels",
                "query": query_string
            }
        }
    }
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    host = 'search-photos-7ka2227iannxvqedwmlx62ft7u.us-east-1.es.amazonaws.com'
    index = 'photos4696'
    url = 'https://search-photos4696-arxypijsdhy7fdt6o2x5j5bwma.us-east-1.es.amazonaws.com/photos4696/_search'
    headers = {"Content-Type": "application/json"}

    request = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query)).json()
    print(request)

    result = request["hits"]["hits"]

    result_locations = []

    for res in result:
        key = res["_source"]["objectKey"]
        bucket_name = res["_source"]["bucket"]
        labels = res["_source"]["labels"]
        s3_url = create_presigned_url(bucket_name, key)
        # s3_url='https://'+bucket_name+'.s3.amazonaws.com/' + key

        result_locations.append((s3_url, labels))

    print(result_locations)
    response_results_json_list = []
    for result in result_locations:
        response_results_json = {
            "url": result[0],
            "labels": result[1]
        }
        response_results_json_list.append(response_results_json)
    response = {
        "results": response_results_json_list
    }

    print(json.dumps(response))
    # DEMO code pipeline change
  
    return response
    
    

