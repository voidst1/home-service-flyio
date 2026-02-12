import csv
import time
import io
import httpx
from django.core.management.base import BaseCommand
from django.apps import apps

from myapp.models import Affiliate, Customer
from postal_codes.models import PostalCode  # For dynamic model access

class Command(BaseCommand):
    help = 'Imports data from a source'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='URL to import file')

    def handle(self, *args, **options):
        url = options['url']
        response = httpx.get(url)

        #print(response.status_code)  # Outputs: 200
        #print(response.text)         # Outputs the page content

        reader = csv.DictReader(io.StringIO(response.text))
        print(reader.fieldnames)
        for row in reader:
            name = row['name']
            phone = row['phone']
            postal_code = row['postal_code']
            unit = row['unit']
            affiliate = row['affiliate']
            print(affiliate)


            affiliate_obj, created = Affiliate.objects.get_or_create(
                name=affiliate,
            )

            try:
                postal_code_obj, created = PostalCode.objects.get_or_create(
                    name=postal_code,
                )
                time.sleep(0.1)
            except Exception as e:
                print(f"An error occurred: {e}") 
                break

            customer_obj = Customer.objects.filter(phone_number=phone).first()
            if not customer_obj:
                    customer_obj = Customer(
                        name=name,
                        phone_number=phone,
                        postal_code=postal_code_obj,
                        unit_number=unit,
                        affiliate=affiliate_obj
                    )
                    customer_obj.save()



        #self.stdout.write(self.style.SUCCESS(f'Starting import from {url}'))
        
        # Example: Import CSV data into a model
        #Model = apps.get_model('yourapp', 'YourModel')
        # Read/parse file_path here, e.g., using csv module
        # Model.objects.bulk_create(instances)
        
        #self.stdout.write(self.style.SUCCESS('Import complete'))
