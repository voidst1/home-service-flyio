from django import forms

from .models import Customer, Appointment
from crispy_forms.layout import Submit, Layout, Hidden
from crispy_forms.helper import FormHelper
from django.core import serializers
from django.core.exceptions import ValidationError

class BookingHoursForm(forms.Form):
    hours = forms.ChoiceField(
        choices = Appointment.HOURS_CHOICES
    )

class NewCustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ['affiliate', 'user', 'preferred_worker']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Profile'))
        self.fields['frequency'].label = "How often do you need our service?"

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)

        if user:
            instance.user = user
            #instance.affiliate = user # TODO: add referral code
            
        if commit:
            instance.save()
        return instance


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ['affiliate', 'user'] # check if user can add additional params on their own
        #fields = '__all__' # or ['name', 'email', 'message']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Profile'))
        self.fields['frequency'].label = "How often do you need our service?"


class BookSlotForm(forms.Form):
    def __init__(self, start_time, end_time, hours, price, *args, **kwargs):

        self.start_time = start_time
        self.hours = hours
        self.price = price
        self.end_time = end_time

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_tag = False
        self.helper.layout = Layout(
            Hidden('start_time', start_time),
            Hidden('hours', hours),
            Submit('submit', 'Book', css_class='btn btn-primary')
        )


