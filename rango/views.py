#from django.http import HttpResponse
from django.shortcuts import render
# Import the Category model
from rango.models import Category
from rango.models import Page
from rango.models import User
from rango.models import UserProfile
# Forms
from rango.forms import CategoryForm
# Login
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
# Decorators, for restricting access
from django.contrib.auth.decorators import login_required
# For logging out
from django.contrib.auth import logout
# Date and time
from datetime import datetime
# Bing Search
from rango.bing_search import run_query
from django.template import RequestContext
from django.shortcuts import redirect

def index(request):
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order
    # Retreive the top 5 only - or all if less than 5
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 0:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits


    response = render(request,'rango/index.html', context_dict)

    return response

def about(request):
    # If the visits session varible exists, take it and use it.
    # If it doesn't, we haven't visited the site so set the count to zero.
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    # remember to include the visit data
    return render(request, 'rango/about.html', {'visits': count})
 #   return render(request, 'rango/about.html')

def category(request, category_name_slug):
    # Create a context dictionary which we can pass to the template rendering engine.
    context_dict = {}

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception
        # so the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category)

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
        # Pass the slug
        context_dict['category_slug'] = category_name_slug
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
    
    
    if request.method == 'POST':
        query = request.POST.get('query')
        if query:
            query = query.strip()
            result_list = run_query(query)
            context_dict['result_list'] = result_list

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)

# Add Category Form
@login_required
def add_category(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            #Save the new category to the database
            form.save(commit=True)

            # Now call the index() view
            return index(request)
        else:
            # the supplied form contained cerrors - just print them to the terminal
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with the error message (if any).
    return render(request, 'rango/add_category.html', {'form': form})

# Add Page Form
from rango.forms import PageForm

@login_required
def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
                cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                # probably better to use a redirect here.
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form':form, 'category': cat}

    return render(request, 'rango/add_page.html', context_dict)

from rango.forms import UserForm, UserProfileForm

@login_required
def restricted(request):
   # return HttpResponse("Since you are logged in, you can see this text!")
    return render(request, 'rango/restricted.html')

def search(request):

    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        print "here", page_id
        if 'page_id' in request.GET:
            print "here2"
            page_id = request.GET['page_id']
            print "test and ", request.GET.get('page_id')
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                print "didn't work"
    #return HttpResponseRedirect(url)
    print "here3"
    return redirect(url)

def register_profile(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST)
        if profile_form.is_valid():
            if request.user.is_authenticated():
                profile = profile_form.save(commit=False)
                user = User.objects.get(id=request.user.id)
                profile.user = user
                profile.picture = request.FILES.get('picture')
                profile.save()
        return index(request)
    else:
        form = UserProfileForm(request.GET)
    return render(request, 'rango/profile_registration.html', {'profile_form': form})

@login_required
def profile(request, username):
    returnedUser = User.objects.get(username=username)

    try:
        userProfile = UserProfile.objects.get(user=returnedUser)
    except:
        userProfile = None
        
    visits = request.session.get('visits')
    context_dict = {'returneduser': returnedUser, 'userprofile': userProfile, 'visits': visits}
    return render(request, 'rango/profile.html', context_dict)

def users(request):
    users = User.objects.order_by('-username')
    context_dict = {'users': users}
    return render(request, 'rango/users.html', context_dict)