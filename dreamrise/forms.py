from collections import OrderedDict
from datetime import *
import datetime as datetime_alt
from django import forms
from django.contrib.auth.models import User
import re
# from django.utils.datetime_safe import datetime
from models import *

MAX_UPLOAD_SIZE = 2500000

class MyModelAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.ImageField: {
            'widget': forms.FileInput
        },
    }


class RegistrationForm(forms.Form):
    # FIXME
    # error_css_class = 'err-msg'
    username = forms.CharField(max_length = 20,initial='' )
    first_name = forms.CharField(max_length = 20,initial='')
    last_name = forms.CharField(max_length = 20,initial='')
    email = forms.EmailField(max_length = 40, initial='')
    password1 = forms.CharField(max_length = 200,
                                label='Password',
                                widget = forms.PasswordInput(),
                                initial='',)
    password2 = forms.CharField(max_length = 200,
                                label='Confirm password',
                                widget = forms.PasswordInput(),
                                initial='',)

    # Customizes form validation for properties that apply to more
    # than one field.  Overrides the forms.Form.clean function.
    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super(RegistrationForm, self).clean()

        # Confirms that the two password fields match
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        # We must return the cleaned data we got from our parent.
        return cleaned_data

    # Customizes form validation for the username field.
    def clean_username(self):
        # Confirms that the username is not already present in the
        # User model database.
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")

        # We must return the cleaned data we got from the cleaned_data
        # dictionary
        return username

    def clean_email(self):
        # Confirms that the username is not already present in the
        # User model database.
        email = self.cleaned_data.get('email')

        if User.objects.filter(email__exact=email):
            raise forms.ValidationError('Email is already taken.')
        if re.match(r'\b[\w.-]+@[\w.-]+.\w{2,4}\b', email) == None:
            raise forms.ValidationError('Email is not valid.')

        # We must return the cleaned data we got from the cleaned_data dictionary
        return email


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = (
            'content_type',
            'funder',
            'starter',
            'fund_amount',
            'image_url',
        )

    def clean_image(self):
        image = self.cleaned_data['image']
        # if not image:
            # raise forms.ValidationError('Image should be added')
        if not hasattr(image, 'content_type'):
            return None
        if not image.content_type or not image.content_type.startswith('image'):
            raise forms.ValidationError('File type is not image')
        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
        return image

    def clean_fund_end(self):
        fund_end = self.cleaned_data['fund_end']
        fund_start = datetime_alt.date.today()

        # if not fund_end:
            # raise forms.ValidationError('This field is required')
        if fund_end <= fund_start:
            raise forms.ValidationError('End date should be after start date!')

        # End date should be within 90 days
        datetime_fund_end = datetime.strptime(str(fund_end), "%Y-%m-%d").date()
        datetime_fund_start = datetime.strptime(str(fund_start), "%Y-%m-%d").date()
        days_diff = (datetime_fund_end - datetime_fund_start).days
        if days_diff >= 90:
            raise forms.ValidationError('End date should be within 90 days!')

        return fund_end


class ActivityEditForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = (
            'title',
            'image',
            'description',
            'fund_end',
            'fund_goal',
            'country',
            'city',
        )

    def clean_fund_end(self):
        fund_end = self.cleaned_data['fund_end']
        # Get self start date
        fund_start = self.instance.fund_start

        if fund_end <= fund_start:
            raise forms.ValidationError('End date should be after start date!')

        # End date should be within 90 days
        datetime_fund_end = datetime.strptime(str(fund_end), "%Y-%m-%d").date()
        datetime_fund_start = datetime.strptime(str(fund_start), "%Y-%m-%d").date()
        days_diff = (datetime_fund_end - datetime_fund_start).days
        if days_diff >= 90:
            raise forms.ValidationError('End date should be within 90 days!')

        return fund_end

    def clean_image(self):
        image = self.cleaned_data['image']

        if not image:
            return None
        if not hasattr(image, 'content_type'):
            return None
        if not image.content_type or not image.content_type.startswith('image'):
            raise forms.ValidationError('File type is not image')
        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
        return image


class FundForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = (
            'fund_amount',
        )

    def clean_fund_amount(self):
        fund_amount = self.cleaned_data['fund_amount']
        # The smallest amount that a customer can be charged in Stripe is $0.50 (50 cents).
        if fund_amount < 0.5:
            raise forms.ValidationError('Please enter a pledge amount greater than or equal to $0.5 USD')
        return fund_amount


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']

        if first_name == None or len(first_name) == 0:
            raise forms.ValidationError('Please enter your first name')
        return first_name
    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if last_name ==None or len(last_name) == 0:
            raise forms.ValidationError('Please enter your last name')
        return last_name


class PasswordForm(forms.ModelForm):
    password1 = forms.CharField(max_length=200,
                                label='Password',
                                widget=forms.PasswordInput(),
                                initial='', )
    password2 = forms.CharField(max_length=200,
                                label='Confirm password',
                                widget=forms.PasswordInput(),
                                initial='',)

    class Meta:
        model = User
        fields = (
            'password',
        )

    def clean(self):
        # Calls our parent (forms.Form) .clean function, gets a dictionary
        # of cleaned data as a result
        cleaned_data = super(PasswordForm, self).clean()

        # Confirms that the two password fields match
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        password = cleaned_data.get('password')
        if not self.instance.check_password(password):
            raise forms.ValidationError("Your old password was entered incorrectly. Please enter it again.")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        # We must return the cleaned data we got from our parent.
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model=UserProfile
        exclude = (
            'user',
            'content_type',
            'avatar_url',
        )
        # widgets = {
        #      'avatar': forms.TextInput(attrs={'class': 'blog-post form-control'}),
        # }
    def clean_picture(self):
        picture = self.cleaned_data['avatar']

        if not picture:
            return None
        if not hasattr(picture, 'content_type'):
            return None
        if not picture.content_type or not picture.content_type.startswith('avatar'):
            raise forms.ValidationError('File type is not image')
        if picture.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
        return picture

    fields = ['avatar','bio','phone_number'] # FIXME


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude=(
            'user',
            'activity',
            'time',
        )


class UpdateForm(forms.ModelForm):
    class Meta:
        model = Update
        exclude = (
            'author',
            'activity',
            'date',
        )


class PlanningForm(forms.ModelForm):
    class Meta:
        model = Planning


class PhaseForm(forms.ModelForm):
    class Meta:
        model = Phase
        exclude = (
            'planning',
            'author',
            # 'deadline',
        )

    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']
        if not due_date:
            return None
        return due_date


class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        exclude = (
            'phase',
            'author',
            'status', #FIXME
        )

