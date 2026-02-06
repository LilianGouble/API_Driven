# TP : Architecture API-Driven avec LocalStack sur Codespaces

Ce projet implémente une architecture "API-Driven" cloud-native simulée. L'objectif est de piloter (démarrer/arrêter) une instance EC2 via une requête HTTP publique, en utilisant AWS Lambda et LocalStack, le tout hébergé au sein d'un GitHub Codespace.

## 🏗 Architecture Cible

L'architecture repose sur le découplage entre le client et l'infrastructure :

1.  **Client** : Envoie une requête HTTP (via `curl` ou Postman).
2.  **Entrée (Function URL)** : Point d'entrée public exposant la Lambda.
3.  **Compute (AWS Lambda)** : Contient la logique Python (`boto3`) pour interpréter l'ordre.
4.  **Infrastructure (AWS EC2)** : La ressource cible simulée dans LocalStack.

**Flux de données :**
`Requête HTTP (POST)` -> `URL Publique Codespace` -> `Lambda Function` -> `LocalStack API (Port 4566)` -> `Action sur EC2`

---

## ⚙️ Pré-requis et Installation

Ce projet est conçu pour être exécuté dans un **GitHub Codespace**.

### 1. Préparer l'environnement
Dans le terminal du Codespace :

```bash
# 1. Création et activation de l'environnement virtuel (bonne pratique)
python3 -m venv venv
source venv/bin/activate

# 2. Installation des dépendances
pip install localstack awscli boto3

# 3. Démarrage de LocalStack en arrière-plan
localstack start -d
```

### 2. Configuration Réseau (CRITIQUE 🚨)

Pour que la Lambda (qui tourne dans un conteneur Docker) puisse communiquer avec l'API LocalStack via l'URL publique, il faut ouvrir les vannes :

* Ouvrir l'onglet PORTS dans VS Code.
* Faire un clic-droit sur le port 4566.
* Changer Port Visibility de Private à Public.
* Copier l'adresse locale (ex: https://...app.github.dev) pour la suite.

### 3. Variables d'environnement

Configurez votre terminal avec les accès nécessaires :
```
# Remplacez par VOTRE URL publique copiée à l'étape précédente (sans slash à la fin)
export ENDPOINT_URL="[https://votre-url-codespace-4566.app.github.dev](https://votre-url-codespace-4566.app.github.dev)"

# Identifiants factices pour AWS CLI (requis par l'outil, même si LocalStack est permissif)
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```
---

## 🚀 Déploiement de l'Infrastructure
### 1. Lancement de l'instance EC2

Nous créons une machine virtuelle simulée qui servira de cible.

```
aws ec2 run-instances \
    --image-id ami-df5de72ade3b4238 \
    --count 1 \
    --instance-type t2.micro \
    --endpoint-url $ENDPOINT_URL \
    --no-verify-ssl
```
Notez l'ID de l'instance retourné dans le JSON (ex: i-xxxxxxxx). Il sera nécessaire pour les tests.

### 2. Déploiement de la Fonction Lambda

La fonction contient le code Python (lambda_function.py) capable d'envoyer des commandes Start/Stop à l'EC2.
```
# 1. Empaquetage du code
zip function.zip lambda_function.py

# 2. Création de la fonction sur LocalStack
aws lambda create-function \
    --function-name MaFonctionAPI \
    --zip-file fileb://function.zip \
    --handler lambda_function.lambda_handler \
    --runtime python3.9 \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --endpoint-url $ENDPOINT_URL \
    --no-verify-ssl

# 3. Configuration de la liaison réseau (Le point clé !)
# On indique à la Lambda où trouver l'API LocalStack via une variable d'environnement.
aws lambda update-function-configuration \
    --function-name MaFonctionAPI \
    --environment "Variables={LOCALSTACK_URL=$ENDPOINT_URL}" \
    --endpoint-url $ENDPOINT_URL \
    --no-verify-ssl
3. Exposition Publique (API)
```

Nous créons une "Function URL" pour rendre la Lambda accessible via HTTP.

```
aws lambda create-function-url-config \
    --function-name MaFonctionAPI \
    --auth-type NONE \
    --endpoint-url $ENDPOINT_URL \
    --no-verify-ssl
```
Récupérez l'URL fournie dans le champ FunctionUrl. Astuce : Si l'URL retournée contient localhost.localstack.cloud, remplacez ce domaine par localhost ou utilisez l'ID de fonction directement si vous testez depuis le même réseau.
---
## 📡 Utilisation (Test de l'API)
Voici comment piloter votre infrastructure via des appels API REST.

Endpoint : Utilisez l'URL obtenue à l'étape précédente (format : http://<function-id>.lambda-url...).

Arrêter l'instance (Stop)
```
curl -X POST \
http://<VOTRE_FUNCTION_URL_ID>.lambda-url.us-east-1.localhost.localstack.cloud:4566 \
-H 'Content-Type: application/json' \
-d '{"action": "stop", "instance_id": "i-xxxxxxxx"}'
Démarrer l'instance (Start)
```

```
curl -X POST \
http://<VOTRE_FUNCTION_URL_ID>.lambda-url.us-east-1.localhost.localstack.cloud:4566 \
-H 'Content-Type: application/json' \
-d '{"action": "start", "instance_id": "i-xxxxxxxx"}'
Vérification
```

Pour confirmer que l'action a bien eu lieu, vous pouvez interroger l'état de l'EC2 :
```
aws ec2 describe-instances --instance-ids i-xxxxxxxx --endpoint-url $ENDPOINT_URL --no-verify-ssl
```
Vous verrez l'état passer de running à stopped (code 80).
