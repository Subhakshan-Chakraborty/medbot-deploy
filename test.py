# from flask import Flask, render_template, jsonify, request, redirect, url_for
# from flask_login import LoginManager, login_required, current_user
# from src.models import db, User, ChatHistory
# from src.auth import auth
# from src.helper import download_hugging_face_embeddings
# from langchain_pinecone import PineconeVectorStore
# from langchain_openai import OpenAI
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
# from dotenv import load_dotenv
# from src.prompt import *
# import os

# app = Flask(__name__)
# app.secret_key = "your-secret-key"  # Change this to a strong one in production

# # ✅ DATABASE CONFIG
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # ✅ Initialize DB and Login Manager
# db.init_app(app)

# login_manager = LoginManager()
# login_manager.login_view = 'auth.login'
# login_manager.init_app(app)

# # ✅ User loader
# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

# # ✅ Register Auth Blueprint
# app.register_blueprint(auth)

# # ✅ Load API keys
# load_dotenv()
# PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
# os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# if not PINECONE_API_KEY or not OPENAI_API_KEY:
#     raise ValueError("API Keys are missing! Check your .env file.")

# # ✅ RAG Setup
# embeddings = download_hugging_face_embeddings()
# index_name = "medicalbot"

# docsearch = PineconeVectorStore.from_existing_index(
#     index_name=index_name,
#     embedding=embeddings
# )

# retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# llm = ChatOpenAI(
#     model="gpt-3.5-turbo",
#     temperature=0.4,
#     max_tokens=500,
#     openai_api_key=OPENAI_API_KEY
# )

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "{input}"),
# ])

# question_answer_chain = create_stuff_documents_chain(llm, prompt)
# rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# # ✅ Routes
# @app.route("/about")
# def about():
#     return render_template("about.html")

# @app.route("/clear", methods=["POST"])
# @login_required
# def clear_chat():
#     ChatHistory.query.filter_by(user_id=current_user.id).delete()
#     db.session.commit()
#     return redirect(url_for("index"))

# @app.route("/")
# @login_required
# def index():
#     history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp).all()
#     return render_template('chat.html', chat_history=history)

# @app.route("/get", methods=["POST"])
# @login_required
# def chat():
#     try:
#         msg = request.form.get("msg", "")
#         print(f"✅ Received input: {msg}")

#         if not msg:
#             return jsonify({"error": "No message provided"}), 400

#         # ✅ Fetch last 5 messages to simulate memory
#         past_chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(5).all()
#         past_chats.reverse()  # Oldest to newest

#         chat_history_text = ""
#         for chat in past_chats:
#             chat_history_text += f"Human: {chat.message}\nAssistant: {chat.response}\n"
#         chat_history_text += f"Human: {msg}"

#         # ✅ RAG with memory context
#         response = rag_chain.invoke({"input": chat_history_text})
#         print(f"📝 Response from RAG Chain: {response}")

#         if response and isinstance(response, dict) and "answer" in response:
#             # ✅ Save chat to DB
#             history = ChatHistory(
#                 user_id=current_user.id,
#                 message=msg,
#                 response=response["answer"]
#             )
#             db.session.add(history)
#             db.session.commit()

#             return jsonify({"response": response["answer"]})
#         else:
#             return jsonify({"error": "Invalid response format"}), 500

#     except Exception as e:
#         print(f"❌ Error: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# # ✅ Create DB
# with app.app_context():
#     db.create_all()

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=8080, debug=True)




# # Update-1:

# from flask import Flask, render_template, request, jsonify, redirect, url_for, session as flask_session
# from flask_login import LoginManager, login_required, current_user
# from src.models import db, User, ChatHistory, ChatSession
# from src.auth import auth
# from src.helper import download_hugging_face_embeddings
# from langchain_pinecone import PineconeVectorStore
# from langchain_openai import OpenAI
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
# from dotenv import load_dotenv
# from src.prompt import *
# import os

# app = Flask(__name__)
# app.secret_key = "your-secret-key"

# # DB & Login setup
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)

# login_manager = LoginManager()
# login_manager.login_view = 'auth.login'
# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

# app.register_blueprint(auth)

# load_dotenv()
# PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
# OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
# os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# embeddings = download_hugging_face_embeddings()
# index_name = "medicalbot"

# docsearch = PineconeVectorStore.from_existing_index(
#     index_name=index_name,
#     embedding=embeddings
# )

# retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# llm = ChatOpenAI(
#     model="gpt-3.5-turbo",
#     temperature=0.4,
#     max_tokens=500,
#     openai_api_key=OPENAI_API_KEY
# )

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "{input}"),
# ])

# question_answer_chain = create_stuff_documents_chain(llm, prompt)
# rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# # ---------------------- CHAT ROUTES ----------------------

# @app.route("/")
# @login_required
# def index():
#     # Get all sessions for this user
#     user_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()

#     # Get session_id from query params or use latest one
#     selected_session_id = request.args.get("session_id")
#     if not selected_session_id and user_sessions:
#         selected_session_id = str(user_sessions[0].id)

#     chat_history = []
#     if selected_session_id:
#         chat_history = ChatHistory.query.filter_by(
#             user_id=current_user.id, session_id=selected_session_id
#         ).order_by(ChatHistory.timestamp).all()

#     return render_template(
#         "chat.html",
#         chat_history=chat_history,
#         sessions=user_sessions,
#         active_session_id=int(selected_session_id) if selected_session_id else None
#     )


# @app.route("/get", methods=["POST"])
# @login_required
# def chat():
#     msg = request.form.get("msg")
#     session_id = request.form.get("session_id")

#     # Memory logic: last 5 from this session
#     past_chats = ChatHistory.query.filter_by(
#         user_id=current_user.id, session_id=session_id
#     ).order_by(ChatHistory.timestamp.desc()).limit(5).all()
#     past_chats.reverse()

#     chat_history_text = ""
#     for chat in past_chats:
#         chat_history_text += f"Human: {chat.message}\nAssistant: {chat.response}\n"
#     chat_history_text += f"Human: {msg}"

#     # RAG + response
#     response = rag_chain.invoke({"input": chat_history_text})
#     answer = response["answer"]

#     # Save to DB
#     chat = ChatHistory(
#         user_id=current_user.id,
#         session_id=session_id,
#         message=msg,
#         response=answer
#     )
    
#     db.session.add(chat)
#     db.session.commit()

#     return jsonify({"response": answer})

# @app.route("/new_chat")
# @login_required
# def new_chat():
#     new_session = ChatSession(user_id=current_user.id)
#     db.session.add(new_session)
#     db.session.commit()
#     return redirect(url_for("index", session_id=new_session.id))

# @app.route("/clear", methods=["POST"])
# @login_required
# def clear_chat():
#     session_id = request.form.get("session_id")
#     ChatHistory.query.filter_by(user_id=current_user.id, session_id=session_id).delete()
#     db.session.commit()
#     return redirect(url_for("index", session_id=session_id))

# @app.route("/about")
# def about():
#     return render_template("about.html")

# # ---------------------- DB INIT ----------------------

# with app.app_context():
#     db.create_all()

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8080, debug=True)