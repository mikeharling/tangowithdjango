from django.http import HttpResponse

def index(request):
    return HttpResponse("<http><body>"
                        "Rango says hey there world!"
                        "<br>"
                        "<a href='about'>About Page</a>"
                        "</body></http>")

def about(request):
    return HttpResponse("<http><body>"
                        "This tutorial has been put together by Michael Harling 2147621."
                        "<br>"
                        "<a href='/rango'>Back to home page</a>"
                        "</body></http>")