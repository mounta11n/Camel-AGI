from database import *
import urllib.parse
from flask import jsonify,request,session,render_template,redirect,url_for,Blueprint
from requests_oauthlib import OAuth2Session
from flask_login import login_required, login_user, current_user, logout_user
import secrets
from datetime import datetime, date, timedelta, timezone
import os, pickle, codecs
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)

authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
scope = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]
google_client_id = os.environ['google_client_id']
google_client_secret = os.environ['google_client_secret']
word_limit = 50 # word limit for task brainstorming

rp = Blueprint('rp', __name__)


# @rp.route("/rp/isLoggedIn", methods=['GET'])
# def rp_isLoggedIn():
#     url_host = urllib.parse.urlsplit(request.url).hostname
#     if "5000" in request.url:
#         redirect_uri = "http://"+url_host+":5000/rp/google_callback"
#     else:    
#         redirect_uri = "https://"+url_host+"/rp/google_callback"
#     google = OAuth2Session(
#         google_client_id, scope=scope, redirect_uri=redirect_uri)
#     login_url, state = google.authorization_url(authorization_base_url)
#     session['oauth_state'] = google_client_id
#     if current_user.is_authenticated:
#         if current_user.openai_key == "" or current_user.openai_key == None:
#             keyAdded = None
#         else:
#             keyAdded = current_user.openai_key
#         return jsonify(isLoggedIn=current_user.is_authenticated,userId=current_user.id,key_added=keyAdded,image=current_user.profile_image)
#     else:
#         return jsonify(isLoggedIn=False,auth_url=login_url)
@rp.route("/rp/isLoggedIn", methods=['GET'])
def rp_isLoggedIn():
    # Skip the whole OAuth process and just create a user directly.
    if not current_user.is_authenticated:
        getAdmin = Admin(id=secrets.token_urlsafe(24), email="test@example.com", name="Test User")
        db.session.add(getAdmin)
        db.session.commit()
        login_user(getAdmin)

    if current_user.openai_key == "" or current_user.openai_key == None:
            keyAdded = None
    else:
            keyAdded = current_user.openai_key
            
    return jsonify(isLoggedIn=current_user.is_authenticated,
                   userId=current_user.id,
                   key_added=keyAdded,
                   image=current_user.profile_image)



# @rp.route("/rp/google_callback", methods=['GET'])
# def rp_google_callback():
#     url_host = urllib.parse.urlsplit(request.url).hostname
#     if "5000" in request.url:
#         redirect_uri = "http://"+url_host+":5000/rp/google_callback"
#     else:
#         redirect_uri = "https://"+url_host+"/rp/google_callback"
#     google = OAuth2Session(
#         google_client_id, scope=scope, redirect_uri=redirect_uri)
#     token_url = "https://www.googleapis.com/oauth2/v4/token"
#     welcome = False
#     try:
#         google.fetch_token(token_url, client_secret=google_client_secret,
#                         authorization_response=request.url)
#     except:
#         pass
#     response = google.get(
#         'https://www.googleapis.com/oauth2/v1/userinfo').json()
#     email = response["email"].lower()
#     googleId = str(response["id"])
#     name = response["name"]
#     image = response["picture"]
#     getAdmin = Admin.query.filter_by(email=email).first()
#     if getAdmin == None:
#         getAdmin = Admin(id=secrets.token_urlsafe(24), email=email,google_id=googleId, name=name,profile_image=image, created_date=datetime.now())
#         db.session.add(getAdmin)
#         db.session.commit()
#     else:
#         getAdmin.google_id = googleId
#         getAdmin.profile_image = image
#         db.session.commit()
#     login_user(getAdmin, remember=True)
#     return redirect("http://localhost:3000/")
@rp.route("/rp/google_callback", methods=['GET'])
def rp_google_callback():
   # This route is no longer needed because we're skipping Google auth.

    return redirect("http://localhost:3000/")
    pass 

class CAMELAgent:

    def __init__(
        self,
        system_message,
        model: ChatOpenAI,
        store
    ) -> None:
        self.model = model
        if store == None:
            self.system_message = system_message
            self.init_messages()
            # print("NEW")
        else:
            self.stored_messages = store
            self.system_message = store[0]
            # print("MESSAGES \n",self.stored_messages,"\n SYSTEM MESSAGE \n",self.system_message)

    def reset(self) -> None:
        self.init_messages()
        return self.stored_messages

    def init_messages(self) -> None:
        self.stored_messages = [self.system_message]
        # for msg in self.stored_messages:
            # print("INTIALIZED",msg.content,"\n")

    def update_messages(self, message: BaseMessage) -> List[BaseMessage]:
        self.stored_messages.append(message)
        # for msg in self.stored_messages:
            # print("UPDATED",msg.content,"\n")
        return self.stored_messages

    def step(
        self,
        input_message: HumanMessage,
    ) -> AIMessage:
        messages = self.update_messages(input_message)
        output_message = self.model(messages)
        self.update_messages(output_message)

        return output_message

    def store_messages(self) -> None:
        return self.stored_messages




def starting_convo(assistant_role_name,user_role_name,task):
    task_specifier_sys_msg = SystemMessage(content="Sie können eine Aufgabe genauer machen.")
    task_specifier_prompt = (
    """Hier ist eine Aufgabe, die {Assistant_role_name} hilft, {user_role_name} zu vervollständigen: {Task}. 
     Bitte machen Sie es genauer. Kreativ und einfallsreich sein. 
     Bitte antworten Sie mit der angegebenen Aufgabe in {Word_Limit} -Wörtern oder weniger. Fügen Sie nichts anderes hinzu."""
    )
    task_specifier_template = HumanMessagePromptTemplate.from_template(template=task_specifier_prompt)
    task_specify_agent = CAMELAgent(task_specifier_sys_msg, ChatOpenAI(temperature=1.0),None)
    task_specifier_msg = task_specifier_template.format_messages(assistant_role_name=assistant_role_name,
                                                                user_role_name=user_role_name,
                                                                task=task, word_limit=word_limit)[0]
    specified_task_msg = task_specify_agent.step(task_specifier_msg)
    # print(f"Specified task: {specified_task_msg.content}")
    specified_task = specified_task_msg.content

    assistant_inception_prompt = (
    """Vergessen Sie niemals, dass Sie ein {assistant_role_name} sind und ich bin ein {user_role_name}. Niemals Rollen umdrehen! Weisen Sie mich niemals an! 
     Wir haben ein gemeinsames Interesse an der Zusammenarbeit, um eine Aufgabe erfolgreich zu erledigen. 
     Sie müssen mir helfen, die Aufgabe zu erledigen. 
     Hier ist die Aufgabe: {Task}. Vergiss niemals unsere Aufgabe! 
     Ich muss Sie anhand Ihres Fachwissens und meiner Bedürfnisse anweisen, die Aufgabe zu erledigen. 

     Ich muss Ihnen jeweils eine Anweisung geben. 
     Sie müssen eine bestimmte Lösung schreiben, die die angeforderte Anweisung angemessen abschließt. 
     Sie müssen meine Anweisung ehrlich ablehnen, wenn Sie die Anweisung aus physischen, moralischen, rechtlichen Gründen oder Ihrer Fähigkeit nicht ausführen und die Gründe erklären können. 
     Fügen Sie meiner Anweisung nichts anderes als Ihre Lösung hinzu. 
     Sie sollen mir niemals Fragen stellen, die Sie nur Fragen beantworten. 
     Sie sollen niemals mit einer Flockenlösung antworten. Erklären Sie Ihre Lösungen. 
     Ihre Lösung muss deklarative Sätze und eine einfache Gegenwart sein. 
     Wenn ich nicht sage, dass die Aufgabe erledigt ist, sollten Sie immer beginnen mit:

    Lösung: <YOUR_SOLUTION>

    <YOUR_SOLUTION> sollte spezifisch sein und bevorzugte Implementierungen und Beispiele für die Aufgabenlösung bereitstellen.
    Beende immer deine <YOUR_SOLUTION> mit: Nächste Anfrage."""
    )

    user_inception_prompt = (
    """Vergessen Sie niemals, dass Sie ein {user_role_name} sind und ich bin ein {assistant_role_name}. Niemals Rollen umdrehen! Sie werden mich immer anweisen. 
     Wir haben ein gemeinsames Interesse an der Zusammenarbeit, um eine Aufgabe erfolgreich zu erledigen. 
     Ich muss Ihnen helfen, die Aufgabe zu erledigen. 
     Hier ist die Aufgabe: {Task}. Vergiss niemals unsere Aufgabe! 
     Sie müssen mich anhand meines Fachwissens und Ihren Bedürfnissen anweisen, die Aufgabe nur auf die folgenden Arten zu erledigen:

    1. Instruieren Sie eine erforderliche Eingabe:
    Instruktion: <YOUR_INSTRUCTION>
    Eingabe: <YOUR_INPUT>

    2. Ohne Eingabe instruieren:
    Instruktion: <YOUR_INSTRUCTION>
    Input: None

    Die "Instruktion" beschreibt eine Aufgabe oder Frage. Die gepaarte "Eingabe" bietet einen weiteren Kontext oder Informationen für die angeforderte "Anweisung".

    Sie müssen mir jeweils eine Anweisung geben. 
    Ich muss eine Antwort schreiben, die die angeforderte Anweisung angemessen abschließt. 
    Ich muss Ihre Anweisung ehrlich ablehnen, wenn ich die Anweisung aus physischen, moralischen, rechtlichen Gründen oder meiner Fähigkeit nicht ausführen und die Gründe erklären kann. 
    Sie sollten mich anweisen, mir keine Fragen zu stellen. 
    Jetzt müssen Sie anfangen, mich mit den beiden oben beschriebenen Arten zu unterweisen. 
    Fügen Sie nichts anderes als Ihre Anweisung und die optionale entsprechende Eingabe hinzu! 
    Geben Sie mir weiterhin Anweisungen und notwendige Eingaben, bis Sie der Meinung sind, dass die Aufgabe erledigt ist.
    Wenn die Aufgabe abgeschlossen ist, müssen Sie nur mit einem einzigen Wort antworten <CAMEL_TASK_DONE>.
    Sage niemals <CAMEL_TASK_DONE>, es sei denn, meine Antworten haben Ihre Aufgabe gelöst."""
    )
    return specified_task,assistant_inception_prompt,user_inception_prompt

def get_sys_msgs(assistant_role_name: str, user_role_name: str, task: str,assistant_inception_prompt,user_inception_prompt):
    
    assistant_sys_template = SystemMessagePromptTemplate.from_template(template=assistant_inception_prompt)
    assistant_sys_msg = assistant_sys_template.format_messages(assistant_role_name=assistant_role_name, user_role_name=user_role_name, task=task)[0]
    
    user_sys_template = SystemMessagePromptTemplate.from_template(template=user_inception_prompt)
    user_sys_msg = user_sys_template.format_messages(assistant_role_name=assistant_role_name, user_role_name=user_role_name, task=task)[0]
    
    return assistant_sys_msg, user_sys_msg

@rp.route("/rp/start", methods=['POST'])
def start_rp():
    if not current_user.is_authenticated:
        return redirect("/agent_convo")
    os.environ["OPENAI_API_KEY"] = current_user.openai_key
    assistant_role_name = request.json["role1"]
    user_role_name = request.json["role2"]
    task = request.json["task"]
    sessId = request.json["sessId"]
    if sessId == 0:
        getSession = Agent_Session(role_1=assistant_role_name,role_2=user_role_name,task=task,admin_id=current_user.id)
        db.session.add(getSession)
        db.session.commit()
        specified_task,assistant_inception_prompt,user_inception_prompt = starting_convo(assistant_role_name, user_role_name, task)
        assistant_sys_msg, user_sys_msg = get_sys_msgs(assistant_role_name, user_role_name, specified_task,assistant_inception_prompt,user_inception_prompt)
        assistant_agent = CAMELAgent(assistant_sys_msg, ChatOpenAI(temperature=0.2),None)
        user_agent = CAMELAgent(user_sys_msg, ChatOpenAI(temperature=0.2),None)
        # Reset agents
        assistant_agent.reset()
        user_agent.reset()

        # Initialize chats 
        assistant_msg = HumanMessage(
            content=(f"{user_sys_msg.content}. "
                        "Geben Sie mir nun Einführungen nacheinander. "
                        "Antworten Sie nur mit der Instruktion und der Eingabe."))

        user_msg = HumanMessage(content=f"{assistant_sys_msg.content}")
        user_msg = assistant_agent.step(user_msg)
    else:
        getSession = Agent_Session.query.filter_by(id=sessId).first()
        user_store = pickle.loads(codecs.decode((getSession.user_store).encode(), "base64"))
        assistant_store = pickle.loads(codecs.decode((getSession.assistant_store).encode(), "base64"))
        user_agent = CAMELAgent(None, ChatOpenAI(temperature=0.2),user_store)
        assistant_agent = CAMELAgent(None, ChatOpenAI(temperature=0.2),assistant_store)
        assistant_msg = HumanMessage(
            content=(f"{assistant_store[-1].content}"))

    # chat_turn_limit, n = 10, 0
    # while n < chat_turn_limit:
        # n += 1
    user_ai_msg = user_agent.step(assistant_msg)
    user_msg = HumanMessage(content=user_ai_msg.content)
    userMsg = user_msg.content.replace("Instruktion: ","").replace("Eingabe: None","").replace("Eingabe: None.","")
    # print(f"AI User ({user_role_name}):\n\n{user_msg.content}\n\n")
    assistant_ai_msg = assistant_agent.step(user_msg)
    assistant_msg = HumanMessage(content=assistant_ai_msg.content)
    assistantMsg = assistant_msg.content.replace("Lösung: ","").replace("Nächste Anfrage.","")
    # print(f"AI Assistant ({assistant_role_name}):\n\n{assistant_msg.content}\n\n")
    convoEnd = False
    if "<CAMEL_TASK_DONE>" in user_msg.content:
        convoEnd = True
    getUserStore = user_agent.store_messages()
    getSession.user_store = codecs.encode(pickle.dumps(getUserStore), "base64").decode()
    getAssistantStore = assistant_agent.store_messages()
    getSession.assistant_store = codecs.encode(pickle.dumps(getAssistantStore), "base64").decode()
    db.session.commit()
    return jsonify(sessId=getSession.id,userMsg=userMsg,assistantMsg=assistantMsg,convoEnd=convoEnd)


@rp.route("/rp/get_chat", methods=['get'])
def rp_get_chat():
    sessId = request.args.get('sessId')
    getSession = Agent_Session.query.filter_by(id=sessId).first()
    assistant_store =  pickle.loads(codecs.decode((getSession.assistant_store).encode(), "base64"))
    messages = []
    for store in assistant_store[2:]:
        if str(type(store)) == "<class 'langchain.schema.HumanMessage'>":
            messages.append({"role":0,"msg":store.content.replace("Instruktion: ","").replace("Eingabe: None","").replace("Eingabe: None.","")})
        elif str(type(store)) == "<class 'langchain.schema.AIMessage'>":
            messages.append({"role":1,"msg":store.content.replace("Lösung: ","").replace("Nächste Anfrage.","")})
    return jsonify(role1=getSession.role_1,role2=getSession.role_2,task=getSession.task,messages=messages)
