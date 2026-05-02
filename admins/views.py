from django.shortcuts import render, redirect
from django.contrib import messages

def home(request):
    return render(request, 'home.html')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == 'admin' and password == 'admin':
            # set session
            request.session['admin'] = True
            return redirect('admin_home')  
        else:
            return render(request, 'admin_login.html', {
                'error': 'Invalid credentials'
            })

    return render(request, 'admin_login.html')

def admin_home(request):
    # protect admin home
    if not request.session.get('admin'):
        return redirect('admin_login')
    messages.success(request, "Login Successful")
    return render(request, 'admin_home.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from users.models import UserRegister

def view_users(request):
    users = UserRegister.objects.all()
    return render(request, "view_users.html", {"users": users})


def authorize_user(request, username):
    user = UserRegister.objects.get(username=username)
    user.status = "Authorized"
    user.save()
    messages.success(request, "User Authorized")
    return redirect("view_users")


def unauthorize_user(request, username):
    user = UserRegister.objects.get(username=username)
    user.status = "Unauthorized"
    user.save()
    messages.success(request, "User UnAuthorized")
    return redirect("view_users")

from users.models import Post   # make sure this exists


def view_posts(request):
    posts = Post.objects.all()
    return render(request, 'admin_view_posts.html', {
        'posts': posts
    })
from users.models import Video

def view_videos(request):
    videos = Video.objects.all()

    return render(request, 'admin_view_videos.html', {
        'videos': videos
    })


def play_video(request, id):
    video = Video.objects.get(id=id)
    return render(request, 'play_video.html', {'video': video})

from users.models import IntentionSequence

def view_user_intention(request):
    intentions = IntentionSequence.objects.all()

    return render(request,
                  'user_intention.html',
                  {'intentions': intentions})

def admin_logout(request):
    return render(request,'admin_login.html')

from users.ml_model import predict_next
from users.models import UserBehavior

def admin_predict(request):

    user_id = request.GET.get("user_id")

    prediction = None

    if user_id:

        last_action = UserBehavior.objects.filter(
            user_id=user_id
        ).order_by("-timestamp").first()

        if last_action:
            prediction = predict_next(user_id, last_action.action)

    return render(request, "admin_predict.html", {
        "prediction": prediction
    })
from users.models import IntentionSequence

from django.shortcuts import render
from django.contrib.auth.models import User
from users.models import UserBehavior, IntentionSequence
from users.ml_model import predict_next


from django.shortcuts import render
from django.contrib.auth.models import User
from users.models import UserBehavior, IntentionSequence
from users.ml_model import predict_next
from django.utils import timezone

from django.shortcuts import render
from django.contrib.auth.models import User
from users.models import UserBehavior, IntentionSequence
from users.ml_model import predict_next
from users.behavior_analyzer import analyze_behavior


def admin_view_user_intention(request):

    users = User.objects.all()

    for user in users:

        logs = UserBehavior.objects.filter(
            user=user
        ).order_by("timestamp")   # oldest → newest

        if not logs.exists():
            continue

        # 🔥 REAL last action
        actions = [l.action for l in logs if l.action != "logout"]

        if not actions:
            continue

        last_action = actions[-1]   # last non-logout action


        # 🔥 predict next action
        prediction, confidence = predict_next(user.id, last_action)


        # 🔥 last 5 actions
        last_five = logs.reverse()[:5]
        sequence = " → ".join([l.action for l in reversed(last_five)])

        # 🔥 avoid duplicates for same time
        today = timezone.now().date()
        behavior_status = analyze_behavior(user.id)
        exists = IntentionSequence.objects.filter(
            user=user,
            time__date=today
        ).exists()

        if not exists:
            IntentionSequence.objects.create(
                user=user,
                intention=last_action,
                prediction=prediction,
                sequence=sequence,
                confidence=confidence,
                behavior_status=behavior_status 
            )


    data = IntentionSequence.objects.select_related("user").order_by("-time")

    return render(request, "adminviewuserintention.html", {
        "data": data
    })
