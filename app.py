from flask import Flask, request, jsonify, render_template, session
from textblob import TextBlob
import ollama

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 사용하려면 비밀 키가 필요

# 감정 분석을 통해 사용자 메시지의 감정 상태를 분석
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity  # -1(부정적) ~ 1(긍정적)
    
    # 감정 기준 개선
    if sentiment > 0.1:
        return 'positive'
    elif sentiment < -0.1:
        return 'negative'
    else:
        return 'neutral'

# 감정 통계를 업데이트하는 함수
def update_sentiment_count(sentiment):
    if sentiment == 'positive':
        session['positive_count'] += 1
    elif sentiment == 'negative':
        session['negative_count'] += 1
    elif sentiment == 'neutral':
        session['neutral_count'] += 1

@app.route('/')
def index():
    # 대화가 종료된 상태를 세션에서 체크하여 초기화
    session['conversation_ended'] = False  # 새로 고침 시 대화 상태를 초기화
    
    # 초기 대화 히스토리 및 인사 메시지
    chat_history = []
    greeting_message = '안녕하세요! 저는 감정 지원 챗봇입니다.😊\n오늘 기분이나 감정을 말씀해 주시면, 그에 맞는 응답을 통해 도움을 드리겠습니다. 어떤 기분이신가요?'
    chat_history.append({'role': 'assistant', 'content': greeting_message})

    # 세션에 초기 상태 저장
    session['chat_history'] = chat_history
    session['conversation_ended'] = False  # 대화가 종료되지 않은 상태로 설정
    
    # 감정 카운트 초기화
    session['positive_count'] = 0
    session['negative_count'] = 0
    session['neutral_count'] = 0

    return render_template('chatbot.html', chat_history=chat_history, exit=False)

@app.route('/chat', methods=['POST'])
def chat():
    # 세션에서 대화 히스토리와 대화 종료 상태 가져오기
    chat_history = session.get('chat_history', [])
    conversation_ended = session.get('conversation_ended', False)

    # 대화 종료 상태일 때는 더 이상 응답하지 않음
    if conversation_ended:
        # 감정 통계를 출력
        return jsonify({
            'message': "대화가 종료되었습니다.",
            'exit': True  # 대화 종료 상태
        })

    # 사용자 메시지 받기
    user_message = request.json.get('message').strip()

    # 대화 종료 조건
    if "그만" in user_message or "대화 종료" in user_message:
        session['conversation_ended'] = True  # 대화 종료 상태 설정

        # 감정 통계 제공
        positive_count = session.get('positive_count', 0)
        negative_count = session.get('negative_count', 0)
        neutral_count = session.get('neutral_count', 0)

        total_count = positive_count + negative_count + neutral_count
        if total_count > 0:
            positive_ratio = (positive_count / total_count) * 100
            negative_ratio = (negative_count / total_count) * 100
            neutral_ratio = (neutral_count / total_count) * 100
        else:
            positive_ratio = negative_ratio = neutral_ratio = 0

        return jsonify({
            'message': f"대화를 종료합니다. 언제든지 다시 대화해요! 😊\n감정 통계:\n 긍정적: {positive_ratio:.2f}%\n 부정적: {negative_ratio:.2f}%\n 중립적: {neutral_ratio:.2f}%",
            'exit': True  # 대화 종료 상태
        })

    # 감정 분석
    sentiment = analyze_sentiment(user_message)

    # 감정 통계 업데이트
    update_sentiment_count(sentiment)

    # 대화 히스토리에 사용자 메시지 추가
    chat_history.append({'role': 'user', 'content': user_message})

    try:
        # Ollama 모델을 통해 더 구체적인 답변 생성
        response_from_model = ollama.chat(model='llama3.1', messages=chat_history)
        model_response = response_from_model['message']['content']

        # `\n`을 `<br>`로 변환
        model_response_with_br = model_response.replace("\n", "<br>")

        # 챗봇 응답을 대화 히스토리에 추가
        chat_history.append({'role': 'assistant', 'content': model_response})

        # 세션에 업데이트된 대화 히스토리 저장
        session['chat_history'] = chat_history

        return jsonify({
            'message': model_response_with_br,  # 줄바꿈 처리된 메시지
            'sentiment': sentiment,  # 감정 분석 결과 추가
            'exit': False  # 대화가 계속 진행 중
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
