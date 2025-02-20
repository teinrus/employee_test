
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

from django.shortcuts import render, get_object_or_404
from .models import TestResult, Question, Answer
from django.shortcuts import render, get_object_or_404, redirect
from .models import Direction, Question, Answer, Theme
from .forms import TestForm

def select_direction(request):
    directions = Direction.objects.all()
    return render(request, 'testing/select_direction.html', {'directions': directions})





def test_view(request, direction_id):
    direction = get_object_or_404(Direction, id=direction_id)

    # Получаем все вопросы, отсортированные по темам
    questions = Question.objects.filter(direction=direction).prefetch_related('themes', 'answers').order_by(
        'themes__name')

    if request.method == 'POST':
        form = TestForm(request.POST, questions=questions)
        if form.is_valid():
            correct_count = 0
            total_questions = questions.count()
            user_answers = {}

            for question in questions:
                selected_answer_id = int(form.cleaned_data[f'question_{question.id}'])
                selected_answer = Answer.objects.get(id=selected_answer_id)

                user_answers[question.id] = selected_answer_id  # Сохраняем ID выбранного ответа


                if selected_answer.is_correct:
                    correct_count += 1


            # Сохраняем данные в сессии
            request.session['test_results'] = {
                'direction_id': direction.id,
                'correct_answers': correct_count,
                'total_questions': total_questions,
            }
            request.session[f'test_answers_{direction.id}'] = user_answers


            return redirect('enter_surname')

    else:
        form = TestForm(questions=questions)

    # Группируем вопросы по темам
    themes = Theme.objects.filter(questions__direction=direction).distinct()
    questions_by_theme = {theme: questions.filter(themes=theme) for theme in themes}

    return render(request, 'testing/test.html', {
        'form': form,
        'direction': direction,
        'questions_by_theme': questions_by_theme
    })


def enter_surname(request):
    if request.method == 'POST':
        surname = request.POST.get('surname')
        test_results = request.session.get('test_results')


        if test_results:
            direction = Direction.objects.get(id=test_results['direction_id'])
            result = TestResult.objects.create(
                surname=surname,
                direction=direction,
                correct_answers=test_results['correct_answers'],
                total_questions=test_results['total_questions'],
            )

            # Получаем сохраненные ответы пользователя
            user_answers = request.session.get(f'test_answers_{direction.id}', {})

            # Сохраняем ответы в сессии, чтобы передать их в test_results
            request.session[f'test_answers_{result.id}'] = user_answers

            # Теперь удаляем только test_results, но НЕ удаляем test_answers_{direction.id}
            del request.session['test_results']

            return redirect('test_results', result_id=result.id)

    return render(request, 'testing/enter_surname.html')



def test_results(request, result_id):
    result = get_object_or_404(TestResult, id=result_id)
    questions = Question.objects.filter(direction=result.direction).prefetch_related('themes', 'answers')

    # Преобразуем ключи user_answers в int
    raw_user_answers = request.session.get(f'test_answers_{result.id}', {})
    user_answers = {int(k): v for k, v in raw_user_answers.items()}  # Преобразуем ключи в int


    themes = Theme.objects.filter(questions__direction=result.direction).distinct()
    questions_by_theme = {theme: list(questions.filter(themes=theme)) for theme in themes}

    return render(request, 'testing/test_results.html', {
        'result': result,
        'questions_by_theme': questions_by_theme,
        'user_answers': user_answers
    })




def pdf_results(request, result_id):
    result = get_object_or_404(TestResult, id=result_id)
    questions = Question.objects.filter(direction=result.direction).prefetch_related('themes', 'answers')
    user_answers = {int(k): v for k, v in request.session.get(f'test_answers_{result.id}', {}).items()}


    # Подключаем кириллический шрифт
    font_path = os.path.join("static", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont('DejaVu', font_path))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Результат_{result.surname}.pdf"'

    # Создаём PDF-документ
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Фирменные цвета
    primary_red = colors.Color(203/255, 39/255, 43/255)
    secondary_red = colors.Color(227/255, 30/255, 36/255)
    dark_blue = colors.Color(16/255, 61/255, 110/255)
    black = colors.Color(43/255, 42/255, 41/255)
    light_gray = colors.Color(197/255, 204/255, 212/255)

    # Стили
    title_style = ParagraphStyle(name="TitleStyle", fontName="DejaVu", fontSize=18, leading=22, textColor=primary_red, alignment=TA_CENTER)
    normal_style = ParagraphStyle(name="NormalStyle", fontName="DejaVu", fontSize=12, leading=14, textColor=black)
    answer_style = ParagraphStyle(name="AnswerStyle", fontName="DejaVu", fontSize=10, leading=12, wordWrap=True, textColor=black)
    theme_style = ParagraphStyle(name="ThemeStyle", fontName="DejaVu", fontSize=14, leading=18, textColor=dark_blue, spaceAfter=10)

    # Заголовок
    elements.append(Paragraph("Результаты теста", title_style))
    elements.append(Spacer(1, 10))

    # Информация о тесте
    info = [
        ["Фамилия:", result.surname],
        ["Направление:", result.direction.name],
        ["Правильных ответов:", f"{result.correct_answers} из {result.total_questions}"]
    ]
    table = Table(info, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), "DejaVu"),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))



    # Группируем вопросы по темам
    themes = Theme.objects.filter(questions__direction=result.direction).distinct()
    questions_by_theme = {theme: list(questions.filter(themes=theme)) for theme in themes}




    data = [["Вопрос", "Ответ"]]
    table_styles = [
        ('FONTNAME', (0, 0), (-1, -1), "DejaVu"),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('BACKGROUND', (0, 0), (-1, 0), primary_red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]



    # Заголовок матрицы компетенций
    elements.append(Paragraph("Матрица компетенций", title_style))
    elements.append(Spacer(1, 10))

    # **Добавляем стиль для автоматического переноса строк**
    wrapped_text_style = ParagraphStyle(name="WrappedText", fontName="DejaVu", fontSize=10, leading=12,
                                        textColor=black, wordWrap='CJK')

    competence_data = [
        [Paragraph("Тема", wrapped_text_style), "Всего", "Правильных", "Процент", "Уровень"]
    ]
    competence_styles = [
        ('FONTNAME', (0, 0), (-1, -1), "DejaVu"),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('BACKGROUND', (0, 0), (-1, 0), primary_red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ]

    themes = Theme.objects.filter(questions__direction=result.direction).distinct()
    questions_by_theme = {theme: list(questions.filter(themes=theme)) for theme in themes}

    for theme, theme_questions in questions_by_theme.items():
        total_questions = len(theme_questions)
        correct_answers = sum(1 for q in theme_questions if
                              q.id in user_answers and Answer.objects.get(id=user_answers[q.id]).is_correct)
        percentage = round((correct_answers / total_questions) * 100) if total_questions > 0 else 0

        # Определяем уровень компетенции (по новой шкале 0-3)
        if percentage == 0:
            level = 0
        elif percentage <= 50:
            level = 1
        elif percentage < 100:
            level = 2
        else:  # 100%
            level = 3

        # Цветовая схема для новой шкалы (0-3)
        bg_color = (
            colors.lightgreen if level == 3 else
            colors.yellow if level == 2 else
            light_gray if level == 1 else
            secondary_red
        )

        # **Применяем `Paragraph` с `wordWrap='CJK'` для переносов**
        theme_paragraph = Paragraph(theme.name, wrapped_text_style)

        competence_data.append([theme_paragraph, total_questions, correct_answers, f"{percentage}%", level])


        competence_styles.append(
            ('BACKGROUND', (0, len(competence_data) - 1), (-1, len(competence_data) - 1), bg_color))

    competence_table = Table(competence_data, colWidths=[160, 80, 80, 80, 80])  # Уменьшил ширину столбца "Тема"
    competence_table.setStyle(TableStyle(competence_styles))
    elements.append(competence_table)
    elements.append(Spacer(1, 20))

    # Оформляем подписи
    signatures = [
        ["Аттестуемый", f"{result.surname}", "____________________"],
        ["Наставник", "______________________", "____________________"],
        ["Руководитель", "______________________", "____________________"],
    ]
    sig_table = Table(signatures, colWidths=[150, 200, 200])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), "DejaVu"),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (0, 0), (-1, -1), dark_blue),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(sig_table)


    # Добавляем разрыв страницы перед матрицей компетенций
    elements.append(PageBreak())
    # Подзаголовок "Подробные результаты"
    elements.append(Paragraph("Подробные результаты:", title_style))
    elements.append(Spacer(1, 10))

    for theme, theme_questions in questions_by_theme.items():
        elements.append(Paragraph(theme.name if theme != "Без темы" else "Без темы", theme_style))
        elements.append(Spacer(1, 5))

        data = [["Вопрос", "Ответ"]]
        table_styles = [
            ('FONTNAME', (0, 0), (-1, -1), "DejaVu"),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BACKGROUND', (0, 0), (-1, 0), primary_red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]

        for question in sorted(theme_questions, key=lambda q: q.id):  # Сортируем вопросы по ID
            question_paragraph = Paragraph(question.text, answer_style)
            data.append([question_paragraph, ""])

            for answer in question.answers.all():
                text = answer.text
                bg_color = colors.white

                selected_answer_id = user_answers.get(question.id, None)

                if selected_answer_id is not None:
                    if answer.id == selected_answer_id:
                        if answer.is_correct:
                            text = f" {text} (Ваш ответ, правильный)"
                            bg_color = colors.lightgreen
                        else:
                            text = f" {text} (Ваш ответ, неправильный)"
                            bg_color = secondary_red
                    elif answer.is_correct:
                        text = f" {text} (Правильный ответ)"
                        bg_color = colors.lightgreen

                answer_paragraph = Paragraph(text, answer_style)
                data.append(["", answer_paragraph])
                table_styles.append(('BACKGROUND', (1, len(data) - 1), (1, len(data) - 1), bg_color))

        table = Table(data, colWidths=[200, 300])
        table.setStyle(TableStyle(table_styles))
        elements.append(table)
        elements.append(Spacer(1, 20))

    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle(table_styles))
    elements.append(table)
    elements.append(Spacer(1, 20))



    doc.build(elements)
    return response