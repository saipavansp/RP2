from flask import Flask, session, request, jsonify, render_template
from flask_session import Session
import os
import google.generativeai as genai

app = Flask(__name__)

# Configure the Gemini AI model with your API key
genai.configure(api_key="AIzaSyDuGNmpWhs2_zVB59209uNSAiLIK-gJtLY")  # Replace with your actual Gemini API key
model = genai.GenerativeModel('gemini-1.5-flash-002')

# Secret key for session management
app.secret_key = os.urandom(24)

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'  # Server-side session
Session(app)

# Initial prompt for chatbot
initial_prompt = """
You are Ram's Father, and your son's age is 18 who is looking to study or preferred education in professional/science. You have an excellent CIBIL score of 710. You are considering taking an educational loan for him and are currently conversing with a bank representative from SSS Bank. If the representative calls you by a name other than Ram's Father, kindly let them know you are Ram's Father. Please understand you are the buyer of the loan, not a representative who sells loans. The representative will call you to pitch an Education loan offer. As a customer, you are polite but have firm interest, are slightly hesitant, and are primarily curious about loan details such as repayment terms, hidden fees, and overall suitability. Your responses should be polite but firm, showing some initial reluctance to help the candidate demonstrate their persuasion skills. Give the output in a maximum of 3 lines. Don't expose your profession and name until the user asks explicitly. If the question is out of the topic of finance and marketing, kindly respond Sorry I'm not allowed to answer this question. Ignore the old chats. Don't explicitly ask for loan details until the representative mentions that. If the representative mentions I'll call you later, kindly close the call by thanking and greeting.
"""


@app.route('/')
def question():
    return render_template('question.html')


@app.route('/index')
def index():
    session.clear()
    session['chat_history'] = []
    return render_template('index.html')


@app.route('/api', methods=['POST'])
def chat_api():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        if 'chat_history' not in session:
            session['chat_history'] = []

        chat = model.start_chat()
        chat.send_message(initial_prompt)
        response = chat.send_message(user_message)
        bot_response = response.text

        session['chat_history'].append({
            'user': user_message,
            'bot': bot_response
        })

        return jsonify({"response": bot_response})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process your request."}), 500


@app.route('/end_session', methods=['POST'])
def end_session():
    try:
        conversation_history = session.get('chat_history', [])
        if not conversation_history:
            return jsonify({"error": "No conversation history found"}), 400

        formatted_history = "\n".join([f"User: {msg['user']}\nBot: {msg['bot']}" for msg in conversation_history])

        summary_prompt = f"""
        Based on the following conversation history, summarize the user's performance, highlighting strengths and areas for improvement:
        {formatted_history}
        """

        chat = model.start_chat()
        chat.send_message(initial_prompt)
        response = chat.send_message(summary_prompt)
        summary = response.text

        saved_session = dict(session)
        session['saved_session'] = saved_session
        session.pop('chat_history', None)

        return jsonify({"summary": summary})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to process the summary request."}), 500


@app.route('/summary')
def summary_page():
    saved_session = session.get('saved_session', {})
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'])
    return render_template('summary.html', session_id=session_id, session_data=saved_session)


if __name__ == '__main__':
    app.run(debug=True)

