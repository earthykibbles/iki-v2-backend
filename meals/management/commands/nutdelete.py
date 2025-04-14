# yourapp/management/commands/populate_onboarding_questions.py
from django.core.management.base import BaseCommand
from meals.models import OnboardingQuestion, UserProfile, NutritionPlan

class Command(BaseCommand):
    help = 'Populates the database with onboarding questions'

    def handle(self, *args, **options):
        # Clear existing questions (optional, remove if you don't want to clear)
        NutritionPlan.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing nutrition plans'))

        # # Define the questions
        # questions = [
        #     {
        #         'question_number': 0,
        #         'question_text': "What should we call you?",
        #         'question_type': "textbox_input",
        #         'is_number_specific': False,
        #         'options': None
        #     },
        #     {
        #         'question_number': 1,
        #         'question_text': "What is your current age?",
        #         'question_type': "textbox_input",
        #         'is_number_specific': True,
        #         'options': None
        #     },
        #     {
        #         'question_number': 2,
        #         'question_text': "What is your current height and weight?",
        #         'question_type': "textbox_input",
        #         'is_number_specific': False,
        #         'options': None
        #     },
        #     {
        #         'question_number': 3,
        #         'question_text': "What is your desired weight and height?",
        #         'question_type': "textbox_input",
        #         'is_number_specific': False,
        #         'options': None
        #     },
        #     {
        #         'question_number': 4,
        #         'question_text': "Tell us your favorite foods?",
        #         'question_type': "multiple_choice",
        #         'is_number_specific': False,
        #         'options': ["Pizza", "Sushi", "Pasta", "Salad", "Tacos"]
        #     },
        #     {
        #         'question_number': 5,
        #         'question_text': "Would you consider yourself healthy?",
        #         'question_type': "single_choice",
        #         'is_number_specific': False,
        #         'options': ["Yes", "No"]
        #     },
        #     {
        #         'question_number': 6,
        #         'question_text': "Would you like a personal touch?",
        #         'question_type': "single_choice",
        #         'is_number_specific': False,
        #         'options': ["Yes", "No"]
        #     },
        # ]

        # # Create the questions
        # for question_data in questions:
        #     OnboardingQuestion.objects.create(**question_data)
        #     self.stdout.write(
        #         self.style.SUCCESS(
        #             f"Created question {question_data['question_number']}: {question_data['question_text']}"
        #         )
        #     )

        # self.stdout.write(self.style.SUCCESS('Successfully populated onboarding questions'))