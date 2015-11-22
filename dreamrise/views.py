from datetime import date
from django.conf import settings
from django.contrib.auth.views import login as contrib_login
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.contrib import *
from dreamrise.forms import *
from dreamrise.models import *

from django.db.models import F, Count, Q
from decimal import *

import stripe
from webapps.settings import *
import ssl
import urllib3
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()

from dreamrise.s3 import *
from django.contrib.auth.tokens import default_token_generator

# Used to send mail from within Django
from django.core.mail import send_mail

#Used for social profile populated
from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login
from allauth.socialaccount.models import SocialAccount

# Django message system to display errors
from django.contrib import messages

from django.core import serializers
import json


# @login_required
def home(request):
    context = {}

    # only display the latest 3 projects in the index page
    context['activities_latest'] = Activity.objects.order_by('id').reverse()[:3]
    context['activities_featured'] = Activity.objects.annotate(num_funders=Count('funder')).order_by('-num_funders')[:3]
    print context['activities_featured']
    return render(request, 'dreamrise/index.html', context)


def explore(request):
    context = {}
    context['activities'] = Activity.objects.all() # display all activities
    return render(request, 'dreamrise/explore.html', context)


@transaction.atomic
def register(request):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        context = {}
    
        # Just display the registration form if this is a GET request
        if request.method == 'GET':
            context['form'] = RegistrationForm()
            return render(request, 'dreamrise/register.html', context)

        form = RegistrationForm(request.POST)
        context['form'] = form
        if not form.is_valid():
            return render(request, 'dreamrise/register.html', context)


        new_user = User.objects.create_user(username=request.POST['username'], # FIXME cleaned_data
                                            first_name=request.POST['first_name'],
                                            last_name=request.POST['last_name'],
                                            email=request.POST['email'],
                                            password=request.POST['password1'],)
        new_user.is_active = False
        new_user.save()
        context['first_name']=new_user.first_name
        context['last_name']=new_user.last_name
        # new
        new_user_profile=UserProfile.objects.create(user=new_user,
                                                    avatar_url='https://s3-bucket-dreamrise.s3.amazonaws.com/default-user-image.png')
        new_user_profile.save()
        token = default_token_generator.make_token(new_user)
        email_body = """
    Welcome to DreamRise! Please click the provided URL link to activate your account: http://%s%s
    """ % (request.get_host(),reverse('confirm', args=(new_user.username, token)))


        send_mail(subject="Verify your email address",
                  message= email_body,
                  from_email="webappteam44@gmail.com",
                  recipient_list=[new_user.email])
        context['email'] = form.cleaned_data['email']

        return render(request,'dreamrise/notification.html',context)


@transaction.atomic
def confirmation(request, username, token):
    context={}
    user = get_object_or_404(User, username=username)

    if not default_token_generator.check_token(user, token):
        raise Http404

    # Otherwise token was valid, activate the user.
    user.is_active = True
    user.save()
    context['first_name']=user.first_name
    context['last_name']=user.last_name
    return render(request, 'dreamrise/confirmation.html', context)


@login_required
@transaction.atomic
def create_activity(request):
    context = {}

    if request.method == 'GET':
        form = ActivityForm()
        form.fields['fund_end'].widget.attrs = {'class': 'datepicker form-control'}
        context['form'] = form
        return render(request, 'dreamrise/create_activity.html', context)


    # errors = []
    new_activity=Activity(starter=request.user)
    form = ActivityForm(request.POST, request.FILES, instance=new_activity)
    # print create_activity_form
    # form.non_field_errors()
    # field_errors = [ (field.label, field.errors) for field in form]
    # print field_errors

    if not form.is_valid():
        print "not true"
        form.fields['fund_end'].widget.attrs = {'class': 'datepicker form-control'}
        context = {'form': form}
        print context
        return render(request, 'dreamrise/create_activity.html',context)

    # form.save()
    # new_activity.save()

    image_url = s3_upload_image(form.cleaned_data['image'])

    # form.save() should be after s3_upload_image method
    form.save()
    # print new_activity.id
    new_activity.image_url = image_url
    new_activity.save()

    new_plan= Planning(activity=new_activity,author=request.user)
    new_plan.save()
    # print(new_activity.image_url)

    print "render to show page"
    return redirect('show_activity', id=new_activity.id)


@login_required
@transaction.atomic
def edit_activity(request, id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    context = {}
    context['activity'] = activity

    # Access control
    if not request.user == activity.starter:
        return render(request, 'dreamrise/not_found.html', context)

    if request.method == 'GET':
        form = ActivityEditForm(instance=activity)
        form.fields['fund_end'].widget.attrs = {'class': 'datepicker form-control'}
        context['form'] = form
        return render(request, 'dreamrise/edit_activity.html', context)
    else:
        form = ActivityEditForm(request.POST, request.FILES, instance=activity)

        if not form.is_valid():
            context['form'] = form
            form.fields['fund_end'].widget.attrs = {'class': 'datepicker'}
            return render(request, 'dreamrise/edit_activity.html', context)

        if form.cleaned_data['image']:
            print 'image:', form.cleaned_data['image']
            image_url = s3_upload_image(form.cleaned_data['image'])
            activity.image_url = image_url
            # activity.save()
            # print image_url
            # print user_profile.avatar_url

        form.save()

    return redirect('show_activity', id=id)


@login_required
def make_plans(request,id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    context = {}

    # Access control
    if request.user == activity.starter:
        planning = Planning.objects.get(activity=activity)
        phases = Phase.objects.filter(planning=planning)
        context['activity'] = activity
        context['phases'] = phases
        context['form'] = TodoForm()
        return render(request, 'dreamrise/make_plans.html', context)
    else:
        return render(request,'dreamrise/not_found.html',context)


@login_required
def phase(request, id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    context = {}

    # Access control
    if request.user == activity.starter:
        form = PhaseForm()
        context['form'] = form
        context['activity'] = Activity.objects.get(id=id)
        # return render_to_response('dreamrise/add_update.html')
        return render(request, 'dreamrise/make_plans_phase.html', context)
    else:
        return render(request,'dreamrise/not_found.html',context)


@login_required
@transaction.atomic
def add_phase(request, id):
    context = {}

    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    planning = Planning.objects.get(activity=activity)
    form = PhaseForm(request.POST)
    context['form'] = form

    if not form.is_valid():
        print "not valid"  ###
        context['activity'] = Activity.objects.get(id=id)
        return render(request, 'dreamrise/make_plans_phase.html', context)

    new_phase = Phase.objects.create(title=form.cleaned_data['title'],
                                     description=form.cleaned_data['description'],
                                     due_date=form.cleaned_data['due_date'],
                                     author=request.user,
                                     planning=planning,)
    new_phase.save()

    # form = UpdateForm()
    # context['form'] = form
    # return render_to_response('dreamrise/add_update.html')
    return redirect(make_plans, id)


@login_required
@transaction.atomic
def add_todo(request, id1, id2): # id1 = activity id, id2 = phase id
    # POST method should be used
    if request.method != 'POST':
        messages.error(request, 'Invalid request. POST method must be used.')
        return redirect(reverse('home'))

    context = {}

    if request.method != 'POST':
        context['form'] = TodoForm() ###
        return render(request, 'dreamrise/make_plans.html', context)

    activity = get_object_or_404(Activity, id=id1)
    # activity = Activity.objects.get(id=id1)
    planning = Planning.objects.get(activity=activity)
    phases = Phase.objects.filter(planning=planning)


    form = TodoForm(request.POST)
    context['form'] = form
    context['activity'] = activity
    context['phases'] = phases

    if not form.is_valid():
        form.phase_id = id2
        print form.phase_id
        print "not valid"  ###
        context['todo_phase_id'] = int(id2)
        return render(request, 'dreamrise/make_plans.html', context)

    new_todo = Todo.objects.create(phase=Phase.objects.get(id=id2),
                                   author=request.user,
                                   content=form.cleaned_data['content'])
    new_todo.save()

    return redirect(make_plans, id1)


@login_required
@transaction.atomic
def delete_todo(request,id1,id2,id3):  # id1 = activity id, id2 = phase id,id3= todo id
    # POST method should be used for deleting
    # if request.method != 'POST':
    #     messages.error(request, 'Invalid request. POST method must be used.')
    #     return redirect(reverse('home'))

    # Deletes item if the logged-in user has an item matching the id
    try:
        todo_delete = get_object_or_404(Todo, phase=Phase.objects.get(id=id2),author=request.user,id= id3)
        # todo_delete = Todo.objects.get(phase=Phase.objects.get(id=id2),author=request.user,id= id3)
        todo_delete.delete()
    except ObjectDoesNotExist:
        print "enter error"
        # errors.append(' Sorry, You do not have a right to delete this todo')
    return redirect(make_plans, id1)


@login_required
@transaction.atomic
def delete_phase(request,id1,id2):  # id1 = activity id, id2 = phase id
    # POST method should be used for deleting
    # if request.method != 'POST':
    #     messages.error(request, 'Invalid request. POST method must be used.')
    #     return redirect(reverse('home'))

    # Deletes item if the logged-in user has an item matching the id
    activity = get_object_or_404(Activity, id=id1)
    # activity = Activity.objects.get(id=id1)
    planning = Planning.objects.get(activity=activity)

    try:
        phase_delete = Phase.objects.get(planning=planning,id=id2,author=request.user)
        phase_delete.delete()
    except ObjectDoesNotExist:
        print "enter error"
        # errors.append(' Sorry, You do not have a right to delete this todo')
    return redirect(make_plans, id1)


# def display_plans(request):
#     planning = Planning.objects.all()
#     phase = Phase.objects.all()
#     todo = Todo.objects.all()
#     context={'planning':planning,'phases':phase, 'todos':todo}
#     return render(request, 'dreamrise/display_planning.html', context)


# @login_required
@transaction.atomic
def show_activity(request, id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    updates = Update.objects.filter(activity=activity)

    comments = Comment.objects.filter(activity=activity)

    context={}

    comment_form = CommentForm()

    context['activity'] = activity
    context['comments'] = comments
    context['form'] = comment_form
    context['logged_user'] = request.user
    context['updates'] = updates
    context['fund_goal'] = activity.fund_goal
    print activity.fund_goal
    context['days_left'] = (activity.fund_end - activity.fund_start).days
    context['fundings'] = Funding_Transaction.objects.filter(activity=activity, status='C')

    if request.user.is_authenticated():
        user_likes_this = activity.like_activity_set.filter(user=request.user) and True or False
        print 'user_likes_this', user_likes_this ###
        context['logged'] = True
        context['user_likes_this'] = user_likes_this

    return render(request, 'dreamrise/show_activity.html', context)


@login_required
@transaction.atomic
def add_comment(request, id):
    # POST method should be used for adding activity
    if request.method != 'POST':
        messages.error(request, 'Invalid request. POST method must be used.')
        return redirect(show_activity, id)

    context = {}
    activity = get_object_or_404(Activity, id=id)
    updates = Update.objects.filter(activity=activity)
    comments = Comment.objects.filter(activity=activity)

    comment_form = CommentForm(request.POST)

    if not comment_form.is_valid():
        context['activity'] = activity
        context['comments'] = comments
        context['form'] = comment_form
        context['logged_user'] = request.user
        context['updates'] = updates
        context['fund_goal'] = activity.fund_goal
        context['days_left'] = (activity.fund_end - activity.fund_start).days
        context['fundings'] = Funding_Transaction.objects.filter(activity=activity, status='C')
        context['user_likes_this'] = activity.like_activity_set.filter(user=request.user) and True or False
        return render(request,'dreamrise/show_activity.html', context)

    new_comment = Comment.objects.create(user=request.user,
                                         activity=activity,
                                         comment=comment_form.cleaned_data['comment'])
    # comment_form.save()
    # temp=comment_form
    # comment_form=CommentForm()
    new_comment.save()

    return redirect(show_activity, id)


@login_required
@transaction.atomic
def like_activity(request, id):
    # POST method should be used for funding pages
    if request.method != 'POST':
        messages.error(request, 'Invalid request. POST method must be used.')
        return redirect(show_activity, id)

    activity = get_object_or_404(Activity, id=id)

    new_like, created = Like_Activity.objects.get_or_create(user=request.user, activity=activity)
    new_like.save()
    if not created:
        new_like.delete()
    #     the user already liked this picture before
    # else:
    #     create new like

    return redirect(show_activity, id)


@login_required
@transaction.atomic
def like_activity_json(request, id):
    # POST method should be used for funding pages
    if request.method != 'POST':
        raise Http404

    # Validate data from Ajax request, check whether param is passed and whether the value exists
    # Check whether param is digit and whether the id is zero or positive
    if not id.isdigit() or id <= 0:
        raise Http404

    activity = get_object_or_404(Activity, id=id)

    new_like, created = Like_Activity.objects.get_or_create(user=request.user, activity=activity)
    new_like.save()
    if not created:
        new_like.delete()

    number_of_likes = activity.like_activity_set.all().count()
    response_json = json.dumps({'created': created, 'number_of_likes': number_of_likes})
    return HttpResponse(response_json, content_type='application/json')


@login_required
def fund_activity(request, id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)

    if request.user == activity.starter:
        messages.error(request, "Oops! You cannot fund your own activity.")
        return redirect(show_activity, id)

    form = FundForm()
    context = {'activity': activity, 'form': form}
    return render(request, 'dreamrise/fund_activity.html', context)


@login_required
@transaction.atomic
def fund_activity_payment(request, id):
    # POST method should be used for funding pages
    if request.method != 'POST':
        messages.error(request, 'Invalid request. POST method must be used.')
        return redirect(reverse('home'))

    context = {}
    form = FundForm(request.POST)
    # activity = Activity.objects.get(id=id)
    activity = get_object_or_404(Activity, id=id)

    if request.user == activity.starter:
        messages.error(request, "Oops! You cannot fund your own activity.")
        return redirect(show_activity, id)

    context['form'] = form
    context['activity'] = activity

    if not form.is_valid():
        print "not valid"  ###
        return render(request, 'dreamrise/fund_activity.html', context)

    # Fetch funding amount
    fund_amount = form.cleaned_data['fund_amount']

    # Create new transaction with incomplete status
    new_transaction = Funding_Transaction.objects.create(uuid=uuid.uuid1().hex,
                                                         activity=activity,
                                                         funder=request.user,
                                                         amount=fund_amount,
                                                         status='I')
    new_transaction.save()

    context['amount'] = fund_amount
    context['amount_in_cent'] = fund_amount * 100
    context['funder'] = request.user
    context['transaction_id'] = new_transaction.uuid
    context['stripe_public_key'] = STRIPE_PUBLIC_KEY

    return render(request, 'dreamrise/payment_checkout.html', context)


@login_required
@transaction.atomic
def fund_activity_checkout(request, id):
    # POST method should be used for funding checkout
    if request.method != 'POST':
        messages.error(request, 'Invalid request. POST method must be used.')
        return redirect(reverse('home'))

    context = {}

    activity = get_object_or_404(Activity, id=id)

    if request.user == activity.starter:
        messages.error(request, "Oops! You cannot fund your own activity.")
        return redirect(show_activity, id)

    # TODO use form?

    if 'transaction_id' not in request.POST or not request.POST['transaction_id']:
        raise Http404
    transaction_id = request.POST['transaction_id']

    # Check if the passed transaction id is valid; if not valid, raise 404
    transaction = get_object_or_404(Funding_Transaction, uuid=transaction_id)

    # Check if the passed transaction is already completed
    if transaction.status == 'C':
        raise Http404

    # Check if the passed transaction belongs to this user; if not valid, raise 404
    funder = transaction.funder
    if not funder == request.user:
        raise Http404

    amount = transaction.amount
    amount_in_cent = amount * 100
    amount_as_int = int(amount_in_cent)

    # Set secret key: remember to change this to your live secret key in production
    # See stripe keys here https://dashboard.stripe.com/account/apikeys
    stripe.api_key = STRIPE_SECRET_KEY
    # print(STRIPE_SECRET_KEY)

    # Get the credit card details submitted by the form
    if 'stripeToken' not in request.POST or not request.POST['stripeToken']:
        raise Http404
    token = request.POST['stripeToken']
    print token ###

    if 'stripeEmail' not in request.POST or not request.POST['stripeEmail']:
        raise Http404
    email = request.POST['stripeEmail']

    # Create the charge on Stripe's servers - this will charge the user's card
    try:
        charge = stripe.Charge.create(
            amount=amount_as_int,  # amount in cents, again
            currency="usd",
            source=token,
            description=email
        )
    except stripe.CardError, e:
        # The card has been declined
        pass

    # Update raised amount and funder list for this activity
    Activity.objects.filter(id=id).update(fund_amount=F('fund_amount') + amount)
    # activity = Activity.objects.get(id=id)

    activity.funder.add(request.user)

    transaction.stripe_token = token
    Funding_Transaction.objects.filter(uuid=transaction_id).update(status='C')

    context['activity'] = activity
    context['first_name']=funder.first_name
    context['last_name']=funder.last_name

    return render(request, 'dreamrise/payment_result.html', context)


# @login_required
# @transaction.atomic
# def get_image(request,id):
#     print "get_image",
#     print id
#     new_activity = Activity.objects.get(id=id)
#     if not new_activity.image:
#         raise Http404
#     return HttpResponse(new_activity.image, content_type=new_activity.content_type)
#
#
# # @login_required
# # @transaction.atomic
# def get_avatar(request,id):
#
#     user_profile =UserProfile.objects.get(id=id)
#     if not user_profile.avatar:
#         raise Http404
#     return HttpResponse(user_profile.avatar, content_type=user_profile.content_type)


@login_required
@transaction.atomic
def edit_user_profile(request):
    context={}
    if request.method == 'GET':
        user_profile = UserProfile.objects.get(user=request.user)
        form = UserProfileForm(instance=user_profile)
        name = User.objects.get(username = request.user)
        context = {'user_profile':user_profile,'form':form, 'user_form': UserForm(instance = name)}
        return render(request, 'dreamrise/edit_profile.html', context)

    else:
        user = request.user
        user_profile = UserProfile.objects.select_for_update().get(user=user)
        user_form = UserForm(request.POST, instance=user)
        # print "user_form", user_form
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        # print "aaa"
        if not form.is_valid():
            context={'form': form, 'user_form': user_form, 'user_profile': user_profile}#if request.method is get, we need to show what was here in the database on the website
            return render(request, 'dreamrise/edit_profile.html', context)

        if not user_form.is_valid():
            context={'form': form, 'user_form': user_form, 'user_profile': user_profile}#if request.method is get, we need to show what was here in the database on the website
            return render(request, 'dreamrise/edit_profile.html', context)

        print hasattr(form.cleaned_data['avatar'], 'content_type')
        if form.cleaned_data['avatar'] and hasattr(form.cleaned_data['avatar'], 'content_type'):
            print 'avatar:', form.cleaned_data['avatar'].content_type
            avatar_url = s3_upload_avatar(form.cleaned_data['avatar'], user.id)
            user_profile.avatar_url = avatar_url
            print avatar_url
            print user_profile.avatar_url

        form.save()
        user_form.save()
        user_profile.save()
        context = {'user_profile': user_profile,'form': form,'user_form': user_form}
        return redirect('profile',user.id)


@login_required
@transaction.atomic
def change_password(request):
    context = {}

    user = request.user
    if request.method == 'GET':
        form = PasswordForm()
        context['form'] = form
        return render(request, 'dreamrise/change_password.html', context)

    form = PasswordForm(request.POST, instance=user)

    if not form.is_valid():
        context['form'] = form
        # print form
        return render(request, 'dreamrise/change_password.html', context)

    user.set_password(form.cleaned_data['password1'])
    user.save()

    messages.info(request, 'Password has been successfully changed! Please login again.')
    return redirect(reverse('login'))


@login_required
@transaction.atomic
def edit_todo(request,id1,id2,id3):  # id1 = activity id, id2 = phase id,id3= todo id
    if request.method == 'GET':
        context={}

        activity = get_object_or_404(Activity, id=id1)
        # activity = Activity.objects.get(id=id1)
        planning = Planning.objects.get(activity=activity)

        phase = get_object_or_404(Phase, id=id2)
        # phase = Phase.objects.get(id=id2)

        todo_edit = get_object_or_404(Todo,
                                      phase=phase,
                                      author=request.user,
                                      id=id3)
        # todo_edit = Todo.objects.get(phase=phase,author=request.user,id= id3)
        form = TodoForm(instance=todo_edit)
        context['activity'] = activity
        context['phase'] = phase
        context['form'] = form
        context['todo'] =todo_edit
        return render(request, 'dreamrise/edit_todo.html', context)
    else:
        context ={}
        activity = get_object_or_404(Activity, id=id1)
        # activity = Activity.objects.get(id=id1)
        planning = Planning.objects.get(activity=activity)
        phase = get_object_or_404(Phase, id=id2)
        context['activity'] = activity
        context['phase'] = phase
        todo_edit = get_object_or_404(Todo,
                                      phase=phase,
                                      author=request.user,
                                      id=id3)
        form = TodoForm(request.POST, instance=todo_edit)
        context['form'] = form
        if not form.is_valid():
            print "not valid"  ###
            return render(request, 'dreamrise/make_plans.html', context)
        form.save()
        todo_edit.save()
        return redirect(make_plans, id1)


@login_required
@transaction.atomic
def edit_phase(request,id1,id2):  # id1 = activity id, id2 = phase id,id3= todo id
    if request.method == 'GET':
        context={}
        activity = get_object_or_404(Activity, id=id1)
        # activity = Activity.objects.get(id=id1)
        planning = Planning.objects.get(activity=activity)
        phase_edit = get_object_or_404(Phase, id=id2)
        # phase_edit=Phase.objects.get(id=id2)
        form = PhaseForm(instance=phase_edit)
        context['activity'] = activity
        context['phase'] = phase_edit
        context['form'] = form
        return render(request, 'dreamrise/edit_phase.html', context)
    else:
        context ={}
        activity = get_object_or_404(Activity, id=id1)
        # activity = Activity.objects.get(id=id1)
        planning = Planning.objects.get(activity=activity)
        phase_edit = get_object_or_404(Phase, id=id2)
        # phase_edit=Phase.objects.get(id=id2)
        context['activity'] = activity
        context['phase'] = phase_edit
        form = PhaseForm(request.POST, instance=phase_edit)
        context['form'] = form
        if not form.is_valid():
            print "not valid"  ###
            return render(request, 'dreamrise/make_plans.html', context)
        form.save()
        phase_edit.save()
        return redirect(make_plans, id1)


def profile(request, id):
    user = get_object_or_404(User, id=id)
    # user = User.objects.get(id=id)
    context={}

    user_profile=UserProfile.objects.filter(user=user)
    print 'profile print', user_profile
    if not user_profile:
        user_profile=UserProfile.objects.create(user=user)

    created_activities = Activity.objects.filter(starter=user)
    funded_activities = Activity.objects.filter(funder=user)

    # print funded_activities
        # form=UserProfileForm(instance=user_profile)
        # name = User.objects.get(username = request.user)
    context['user_profile'] = user.userprofile
    context['created_activities'] = created_activities
    context['funded_activities'] = funded_activities
    context['profile_user'] = user
    context['request_user']= request.user
    # print 'user',user
    # print 'request_user',request.user
    return render(request, 'dreamrise/profile.html', context)


@login_required
def update(request, id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    context = {}
    if request.user == activity.starter:
        form = UpdateForm()
        context['form'] = form
        context['activity'] = Activity.objects.get(id=id)
        # return render_to_response('dreamrise/add_update.html')
        return render(request, 'dreamrise/add_update.html', context)
    else:
        return render(request, 'dreamrise/not_found.html', context)


@login_required
@transaction.atomic
def add_update(request, id):
    activity = get_object_or_404(Activity, id=id)
    # activity = Activity.objects.get(id=id)
    context = {}
    if request.user == activity.starter:
        form = UpdateForm(request.POST)
        context['form'] = form

        if not form.is_valid():
            print "not valid"  ###
            context['activity'] = Activity.objects.get(id=id)
            return render(request, 'dreamrise/add_update.html', context)

        new_update = Update.objects.create(title=form.cleaned_data['title'],
                                           content=form.cleaned_data['content'],
                                           author=request.user,
                                           activity=Activity.objects.get(id=id),)
        new_update.save()

        # form = UpdateForm()
        # context['form'] = form
        # return render_to_response('dreamrise/add_update.html')
        return redirect(show_activity, id)
    else:
        return render(request, 'dreamrise/not_found.html', context)


def show_original_update(request, id1, id2):
    context={}
    activity = get_object_or_404(Activity, id=id1)
    # activity = Activity.objects.get(id=id1)
    user = activity.starter

    if request.method == 'GET':
        update = Update.objects.get(activity = activity,id=id2)
        context['activity'] = activity
        context['update'] = update
        context['original_update_user'] = user
        context['request_user']= request.user
        return render(request, 'dreamrise/original_update.html', context)


@login_required
@transaction.atomic
def show_update(request, id1, id2):
    context={}
    activity = get_object_or_404(Activity, id=id1)
    # activity = Activity.objects.get(id=id1)
    user = activity.starter
    if request.user == user:
        if request.method == 'GET':

            update = Update.objects.get(activity = activity,id=id2)
            form = UpdateForm(instance=update)
            context['activity'] = activity
            context['update'] = update
            context['form'] = form
            return render(request, 'dreamrise/show_update.html', context)
        else:

            update_edit = Update.objects.get(activity=activity,id=id2)
            form = UpdateForm(request.POST, instance=update_edit)
            context['update'] = update_edit
            context['activity'] = activity
            context['form'] = form
            if not form.is_valid():
                print "not valid"  ###
                return render(request, 'dreamrise/show_update.html', context)
            form.save()
            update_edit.save()
            print 'form.content',update_edit.content
            print 'form.title',update_edit.title
            return redirect('show_original_update', id1=activity.id,id2=update_edit.id)
            # return render(request, 'dreamrise/show_activity.html', context)
    else:
        return render(request, 'dreamrise/not_found.html', context)


@transaction.atomic
#for social authentication fetch information from facebook/google
def social_redirect(request):
    print "goes to social-redirect"
    context = {}
    context['activities'] = Activity.objects.order_by('id').reverse()[:3]
    fid = SocialAccount.objects.filter(provider='facebook', user_id=request.user.id)
    print fid[0].extra_data
    picture_url = 'http://graph.facebook.com/{0}/picture'.format(fid[0].extra_data['id'])
    print picture_url
    user_profile = UserProfile.objects.filter(user=request.user)
    if user_profile:
        return render(request, 'dreamrise/index.html', context)
    else:
        user_profile =UserProfile.objects.create(user=request.user,avatar_url =picture_url)
        return render(request, 'dreamrise/index.html', context)


# Redirect already logged in users from login page
def custom_login(request, **kwargs):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL) #settings belongs to django.conf
    else:
        return contrib_login(request, **kwargs)


def search(request):
    if request.method == 'POST':
        messages.error(request, 'Invalid request. GET method must be used.')
        return redirect(reverse('home'))

    context = {}

    query = request.GET['q']

    activities = Activity.objects.filter(Q(title__icontains=query) | Q(description__icontains=query)).order_by('fund_start')

    context['activities'] = activities
    return render(request, 'dreamrise/search_result.html', context)

