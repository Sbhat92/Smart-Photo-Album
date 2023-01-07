import logging
import json
import urllib.parse
from elasticsearch import Elasticsearch, RequestsHttpConnection
import boto3
from requests_aws4auth import AWS4Auth

print('Loading function')

s3 = boto3.client('s3')

def my_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    #Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    head_object = boto3.client('s3').head_object(Bucket=bucket, Key=key)
    timestamp = head_object["LastModified"].strftime("%Y-%m-%dT%H:%M:%S")

    s3client = boto3.client('rekognition')

    response = s3client.detect_labels(
                Image={'S3Object': {'Bucket':bucket, 'Name':key}},MaxLabels=100
                )

    labels = [label for label in response["Labels"]]
    custom_label = head_object['Metadata']['customlabels']
    custom_labels = [clabel.strip() for clabel in custom_label.split(',')]

    print("Custom Labels : " + str(custom_labels))
    all_labels = custom_labels + labels
    print(labels)

    es_object = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": timestamp,
        "labels": all_labels
    }

    print(es_object)

    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es', session_token=credentials.token)

    host = "search-photos4696-arxypijsdhy7fdt6o2x5j5bwma.us-east-1.es.amazonaws.com"

    elastic_search = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    elastic_search.index(index="photos4696", id=es_object["objectKey"], body=es_object)

    print(elastic_search.get(index="photos4696", id=es_object["objectKey"]))

    print("checkdone")


    
    

