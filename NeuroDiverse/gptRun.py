from mira_sdk import MiraClient, Flow
from dotenv import load_dotenv
import os
import re
import json

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("API_KEY")

# Initialize the client
client = MiraClient(config={"API_KEY": api_key})

emoji_flow = Flow(source="emoji_flow.yaml")
summary_flow = Flow(source="summarize_flow.yaml")
def gptResponse(text):
    input_dict = {"topic": "Story", "text": text}

    response = client.flow.test(emoji_flow, input_dict)
    #print(response['result'])
    return response['result']

def getSummary(text):
    input_dict = {"topic": "Story", "text": text}

    response = client.flow.test(summary_flow, input_dict)
    print(response['result'])
    return response['result']

flow = Flow(source="compound_flow.yaml")
adhd_flow = Flow(source="adhd.yaml")


def extract_chapters_and_questions(text):
    data = []
    chapters = re.split(r'Chapter \d+:', text)[1:]  # Split by "Chapter X:"
    chapter_titles = re.findall(r'Chapter \d+: (.+)', text)  # Extract titles

    for idx, chapter in enumerate(chapters):
        parts = re.split(r'Q\d+:', chapter)  # Split by question markers
        chapter_text = parts[0].strip()
        questions = parts[1:]  # Remaining parts are questions

        chapter_data = {
            "chapter_number": idx + 1,
            "title": chapter_titles[idx] if idx < len(chapter_titles) else f"Chapter {idx+1}",
            "text": chapter_text,
            "questions": []
        }

        for q in questions:
            q_match = re.match(r'(.+?)\n\s*a\)\s*(.+?)\s*b\)\s*(.+?)\s*c\)\s*(.+?)\s*d\)\s*(.+?)\s*Correct Answer:\s*(.)', q.strip(), re.DOTALL)
            if q_match:
                question, opt_a, opt_b, opt_c, opt_d, correct = q_match.groups()
                chapter_data["questions"].append({
                    "question": question.strip(),
                    "options": {"a": opt_a.strip(), "b": opt_b.strip(), "c": opt_c.strip(), "d": opt_d.strip()},
                    "correct_answer": correct.strip()
                })

        data.append(chapter_data)

    return data



def gptQuestion(text):
    input_dict = {"topic": "Story", "text": text}

    response = client.flow.test(adhd_flow, input_dict)
    print(response['result'])
    s = extract_chapters_and_questions(response['result'])
    print(s)
    return s

def gptQuestion1():
    input_dict = {"topic": "Story", "text": ''}

    response = client.flow.test(flow, input_dict)
    s = response['result']
    return s

print(gptQuestion1())
