import json
import boto3
import os

def lambda_handler(event, context):
    # 1. Récupération de l'URL LocalStack (passée en variable d'environnement)
    endpoint_url = os.environ.get('LOCALSTACK_URL')
    
    if not endpoint_url:
        return {
            'statusCode': 500, 
            'body': json.dumps("Erreur : La variable d'environnement LOCALSTACK_URL est manquante.")
        }

    # 2. Connexion au client EC2
    # verify=False est important ici pour éviter les erreurs SSL avec le proxy Codespace
    ec2 = boto3.client('ec2', endpoint_url=endpoint_url, region_name='us-east-1', verify=False)

    # 3. Parsing des paramètres (action et instance_id)
    try:
        body = event
        # Si la requête vient d'une URL publique, le corps est une string JSON dans 'body'
        if 'body' in event and event['body']:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']

        action = body.get('action')
        instance_id = body.get('instance_id')
    except Exception as e:
        return {'statusCode': 400, 'body': json.dumps(f"Erreur lecture JSON: {str(e)}")}

    if not action or not instance_id:
        return {'statusCode': 400, 'body': json.dumps("Parametres manquants : 'action' et 'instance_id' sont requis.")}

    # 4. Exécution de l'action
    try:
        if action == 'stop':
            ec2.stop_instances(InstanceIds=[instance_id])
            message = f"Instance {instance_id} en cours d'arret..."
        elif action == 'start':
            ec2.start_instances(InstanceIds=[instance_id])
            message = f"Instance {instance_id} en cours de demarrage..."
        else:
            return {'statusCode': 400, 'body': json.dumps(f"Action inconnue : {action}")}

        print(message)
        return {
            'statusCode': 200,
            'body': json.dumps(message)
        }

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps(f"Erreur EC2: {str(e)}")}
