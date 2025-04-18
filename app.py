from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from src.models import db, User, ChatHistory, ChatSession
from src.auth import auth
from src.helper import download_hugging_face_embeddings, get_initials
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"

# DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# LOGIN
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth)

# ENV & Embeddings
load_dotenv()
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

embeddings = download_hugging_face_embeddings()
index_name = "medicalbot"
docsearch = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.4,
    max_tokens=500,
    openai_api_key=OPENAI_API_KEY
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# ROUTES

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/")
def root():
    return redirect(url_for("home"))

@app.route("/about")
@login_required
def about():
    return render_template("about.html")

@app.route("/chat")
@login_required
def index():
    user_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()

    if not user_sessions:
        new_session = ChatSession(user_id=current_user.id)
        db.session.add(new_session)
        db.session.commit()
        return redirect(url_for("index", session_id=new_session.id))

    selected_session_id = request.args.get("session_id", type=int)
    if not selected_session_id:
        return redirect(url_for("index", session_id=user_sessions[0].id))

    chat_history = ChatHistory.query.filter_by(
        user_id=current_user.id,
        session_id=selected_session_id
    ).order_by(ChatHistory.timestamp).all()

    initials = get_initials(current_user.name) if current_user.name else "U"

    session_previews = []
    for i, session in enumerate(user_sessions):
        latest = ChatHistory.query.filter_by(
            user_id=current_user.id, session_id=session.id
        ).order_by(ChatHistory.timestamp.desc()).first()
        preview = latest.message[:30] + "..." if latest else "No messages yet"
        session_previews.append({
            "id": session.id,
            "title": f"Chat {len(user_sessions) - i}",
            "preview": preview
        })

    return render_template(
        "chat.html",
        chat_history=chat_history,
        sessions=user_sessions,
        session_previews=session_previews,
        active_session_id=selected_session_id,
        user_initials=initials
    )

@app.route("/get", methods=["POST"])
@login_required
def chat():
    try:
        msg = request.form.get("msg", "")
        session_id = request.form.get("session_id")

        if not msg or not session_id:
            return jsonify({"error": "Missing message or session ID"}), 400

        past_chats = ChatHistory.query.filter_by(
            user_id=current_user.id,
            session_id=session_id
        ).order_by(ChatHistory.timestamp.desc()).limit(5).all()
        past_chats.reverse()

        chat_history_text = ""
        for chat in past_chats:
            chat_history_text += f"Human: {chat.message}\nAssistant: {chat.response}\n"
        chat_history_text += f"Human: {msg}"

        response = rag_chain.invoke({"input": chat_history_text})

        if response and isinstance(response, dict) and "answer" in response:
            history = ChatHistory(
                user_id=current_user.id,
                session_id=session_id,
                message=msg,
                response=response["answer"]
            )
            db.session.add(history)
            db.session.commit()
            return jsonify({"response": response["answer"]})
        else:
            return jsonify({"error": "Invalid response format"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/new_chat")
@login_required
def new_chat():
    new_session = ChatSession(user_id=current_user.id)
    db.session.add(new_session)
    db.session.commit()
    return redirect(url_for("index", session_id=new_session.id))

@app.route("/clear", methods=["POST"])
@login_required
def clear_chat():
    session_id = request.form.get("session_id")
    ChatHistory.query.filter_by(user_id=current_user.id, session_id=session_id).delete()
    db.session.commit()
    return redirect(url_for("index", session_id=session_id))

@app.route("/delete_chat/<int:session_id>", methods=["POST"])
@login_required
def delete_chat(session_id):
    session = ChatSession.query.get_or_404(session_id)
    if session.user_id != current_user.id:
        flash("Unauthorized to delete this chat.")
        return redirect(url_for("index"))

    ChatHistory.query.filter_by(session_id=session_id).delete()
    db.session.delete(session)
    db.session.commit()
    return redirect(url_for("index"))

# DB INIT
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
