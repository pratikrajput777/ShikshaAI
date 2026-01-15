from django.core.management.base import BaseCommand
  
class Command(BaseCommand):
      help = 'Import ESCO taxonomy data'
      
      def handle(self, *args, **options):
          self.stdout.write('ESCO import command created - implementation pending')