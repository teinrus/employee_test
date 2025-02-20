from django.db import models

from django.db import models

class Theme(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название темы")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"

class Direction(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название направления")
    themes = models.ManyToManyField(Theme, related_name="directions", verbose_name="Темы")  # M2M связь

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Направление"
        verbose_name_plural = "Направления"

class Question(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name="questions", verbose_name="Направление")
    themes = models.ManyToManyField(Theme, related_name="questions", verbose_name="Темы")  # M2M связь
    text = models.TextField(verbose_name="Текст вопроса")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="Вопрос")
    text = models.CharField(max_length=255, verbose_name="Текст ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

class TestResult(models.Model):
    surname = models.CharField(max_length=255, verbose_name="Фамилия")
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, verbose_name="Направление")
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, verbose_name="Тема", null=True, blank=True)
    correct_answers = models.IntegerField(verbose_name="Правильные ответы")
    total_questions = models.IntegerField(verbose_name="Всего вопросов")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата прохождения")

    class Meta:
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты тестов"
