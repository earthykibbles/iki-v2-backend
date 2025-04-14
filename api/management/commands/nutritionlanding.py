from django.core.management.base import BaseCommand
from api.tasks import generate_nutrition_landing_task

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print("Triggering nutrition landing task via scheduler...")
        generate_nutrition_landing_task.delay()
        self.stdout.write(self.style.WARNING('Nutrition landing task has been triggered.'))