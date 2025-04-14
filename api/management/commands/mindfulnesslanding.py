from django.core.management.base import BaseCommand
from api.tasks import generate_mindfulness_landing_task

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print("Triggering mindfulness landing task via scheduler...")
        generate_mindfulness_landing_task.delay()
        self.stdout.write(self.style.WARNING('Mindfulness landing task has been triggered.'))