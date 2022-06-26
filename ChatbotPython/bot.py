import slack
import os
import requests
import re
from threading import Thread
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, jsonify
from slackeventsapi import SlackEventAdapter
from py4j.java_gateway import JavaGateway

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

@app.route('/findsatd', methods=['POST'])
def message_count():
    response_url = request.form.get("response_url")

    print(response_url)

    data = request.form
    thread = Thread(target=backgroundThread, args=[data, response_url])
    thread.start()

    return Response(), 200

def backgroundThread(data, response_url):

    print(data)
    
    channel_id = data.get('channel_id')

    if data.get('text') == "":
        client.chat_postMessage(channel=channel_id, text=f"You have to insert a parameter in order to execute the command.")
        return Response(), 500

    payload = {'repository_url': data.get('text')}

    #inserire un controllo che il comando eseguito sia findSATD
    response = requests.get('http://localhost:8080/retrieveSATD', params=payload)

    commit_identifieds = response.content.decode()

    if "Wrong repository link" in commit_identifieds:
        client.chat_postMessage(channel=channel_id, text=f"You have to insert a valid repository url to identify SATDs.")
        return Response(), 500

    if "Not enough commits required for the classification." in commit_identifieds:
        client.chat_postMessage(channel=channel_id, text=f"Not enough commits required for the classification. Make sure you have at least 5 commits in your repository.")
        return Response(), 500

    if "Repository not found. Make sure the link is correct and try again." in commit_identifieds:
        client.chat_postMessage(channel=channel_id, text=f"Repository not found. Make sure the link is correct and try again.")
        return Response(), 500

    array=re.split('{|}', commit_identifieds)
    array=list(filter(lambda a: a != ',', array))   #mi toglie tutte le virgole dall' array
    array.remove('[')
    array.remove(']')
    messageToPost=''
    for el in array:
        e = el.split('","')
        e[0]='🆔 '+ e[0]+'"'
        e[1]='👤 "'+e[1]+'"'
        e[2]='💬 "'+e[2]+'"'
        e[3]='🕙 "'+e[3]
        messageToPost=messageToPost + e[0] + '\n' + e[1] + '\n' + e[2] + '\n' + e[3] + '\n' + '----------------------------------------------------------------------\n'

    client.chat_postMessage(channel=channel_id, text=f"{len(array)} SATD Detected: \n\n{messageToPost}")
    client.chat_postMessage(channel=channel_id, text=f"Identification terminated successfully.")
    
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)
