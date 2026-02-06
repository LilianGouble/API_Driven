import boto3
import json

# L'ID de votre instance (récupéré à l'étape précédente)
INSTANCE_ID = 'i-9a58b5d6fe170f3fd'
REGION = 'us-east-1'

def lambda_handler(event, context):
    # Connexion au service EC2
    ec2 = boto3.client('ec2', region_name=REGION)

    # Récupération de l'action demandée (start ou stop) depuis l'URL
    action = 'status'
    if 'queryStringParameters' in event and event['queryStringParameters'] and 'action' in event['queryStringParameters']:
        action = event['queryStringParameters']['action']

    message = f"Action recue : {action}"

    try:
        if action == 'start':
            ec2.start_instances(InstanceIds=[INSTANCE_ID])
            message = f"Instance {INSTANCE_ID} demarrage en cours..."
        elif action == 'stop':
            ec2.stop_instances(InstanceIds=[INSTANCE_ID])
            message = f"Instance {INSTANCE_ID} arret en cours..."
        else:
            message = f"Action inconnue. Utilisez ?action=start ou ?action=stop. ID: {INSTANCE_ID}"
    except Exception as e:
        message = f"Erreur : {str(e)}"

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
