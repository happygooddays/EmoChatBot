import ollama

def chatbot():
    print("Chatbot is running. Type 'exit' to quit.")
    messages = []  # 대화 히스토리를 저장할 리스트

    while True:
        # 사용자 입력 받기
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # 사용자 메시지를 대화 히스토리에 추가
        messages.append({'role': 'user', 'content': user_input})

        try:
            # 모델과 대화
            response = ollama.chat(model='llama3.1', messages=messages)
            bot_message = response['message']['content']

            # 챗봇 응답 출력
            print(f"Bot: {bot_message}")

            # 챗봇 메시지를 대화 히스토리에 추가
            messages.append({'role': 'assistant', 'content': bot_message})
        except Exception as e:
            print(f"Error: {e}")
            break

# 실행
if __name__ == "__main__":
    chatbot()
