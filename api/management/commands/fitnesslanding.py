from django.core.management.base import BaseCommand
from api.tasks import generate_fitness_landing_task

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print("Triggering fitness landing task via scheduler...")
        generate_fitness_landing_task.delay()
        self.stdout.write(self.style.WARNING('Fitness landing task has been triggered.'))