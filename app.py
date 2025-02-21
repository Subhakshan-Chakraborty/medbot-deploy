from flask import Flask, render_template, jsonify, request
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from src.prompt import *
import os

app = Flask(__name__)

load_dotenv()

PINECONE_API_KEY=os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# Print the API keys to check if they are loaded correctly
print("Pinecone API Key:", PINECONE_API_KEY)
print("OpenAI API Key:", OPENAI_API_KEY)

# Ensure the keys are set properly
if not PINECONE_API_KEY or not OPENAI_API_KEY:
    raise ValueError("API Keys are missing! Check your .env file.")

embeddings = download_hugging_face_embeddings()


index_name = "medicalbot"

# Embed each chunk and upsert the embeddings into your Pinecone index.
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})


llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.4,
    max_tokens=500,
    openai_api_key=OPENAI_API_KEY
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)


@app.route("/")
def index():
    return render_template('chat.html')


@app.route("/get", methods=["POST"])
def chat():
    try:
        msg = request.form.get("msg", "")
        print(f"✅ Received input: {msg}")  # Log user input

        if not msg:
            return jsonify({"error": "No message provided"}), 400
        
        # Call RAG pipeline
        response = rag_chain.invoke({"input": msg})
        print(f"📝 Response from RAG Chain: {response}")  # Log raw response

        if response:
            if isinstance(response, dict) and "answer" in response:
                print(f"✅ Sending response: {response['answer']}")
                return jsonify({"response": response["answer"]})
            else:
                print("❌ Error: Response format is incorrect!")
                return jsonify({"error": "Invalid response format"}), 500
        else:
            print("❌ Error: No response received from RAG Chain!")
            return jsonify({"error": "No response from model"}), 500

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port= 8080, debug= True)
