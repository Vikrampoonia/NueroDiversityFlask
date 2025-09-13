import re

def format_chapters_to_html(structured_data: list) -> str:
    """
    Formats the structured chapter data from the AI into a
    clean HTML string, ready for PDF conversion. This keeps the
    Celery worker focused on orchestration, not formatting.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: sans-serif; line-height: 1.6; padding: 2em; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h3 { color: #34495e; margin-top: 2em; }
            p { margin-bottom: 1em; }
            ul { list-style-type: none; padding-left: 0; }
            li { margin-bottom: 0.5em; background-color: #f8f9f9; padding: 8px; border-left: 4px solid #bdc3c7; }
            em { color: #27ae60; font-style: normal; font-weight: bold;}
        </style>
    </head>
    <body>
    """
    for chapter in structured_data:
        html += f"<h1>Chapter {chapter.get('chapter_number', '')}: {chapter.get('title', 'Untitled')}</h1>\n"
        html += f"<p>{chapter.get('text', '')}</p>\n"
        if chapter.get('questions'):
            html += "<h3>Quiz Questions:</h3>\n"
            for q in chapter['questions']:
                html += f"<p><strong>{q.get('question', '')}</strong></p>\n"
                html += "<ul>"
                for key, option in q.get('options', {}).items():
                    html += f"<li>{key.upper()}) {option}</li>\n"
                html += f"<li><em>Correct Answer: {q.get('correct_answer', '').upper()}</em></li>\n"
                html += "</ul>"
    html += "</body></html>"
    return html


def extract_chapters_and_questions(text: str) -> list:
    """
    Parses raw text from an AI model into a structured list of chapters and questions.
    """
    data = []
    chapters = [c.strip() for c in re.split(r'Chapter \d+:', text) if c.strip()]
    chapter_titles = re.findall(r'Chapter \d+: (.*)', text)

    for idx, chapter_content in enumerate(chapters):
        parts = re.split(r'Q\d+:', chapter_content)
        chapter_text = parts[0].strip()
        questions_raw = parts[1:]

        chapter_data = {
            "chapter_number": idx + 1,
            "title": chapter_titles[idx].strip() if idx < len(chapter_titles) else f"Chapter {idx + 1}",
            "text": chapter_text,
            "questions": []
        }

        for q_text in questions_raw:
            q_match = re.search(
                r'(.+?)\s*a\)\s*(.+?)\s*b\)\s*(.+?)\s*c\)\s*(.+?)\s*d\)\s*(.+?)\s*Correct Answer:\s*([a-d])',
                q_text,
                re.DOTALL | re.IGNORECASE
            )
            if q_match:
                question, opt_a, opt_b, opt_c, opt_d, correct = q_match.groups()
                chapter_data["questions"].append({
                    "question": question.strip(),
                    "options": {"a": opt_a.strip(), "b": opt_b.strip(), "c": opt_c.strip(), "d": opt_d.strip()},
                    "correct_answer": correct.strip().lower()
                })
        data.append(chapter_data)
    return data

