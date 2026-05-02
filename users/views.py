from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegister
from django.contrib.auth.decorators import login_required

from .models import UserBehavior


def log_behavior(request, action, page="", description=""):

    if request.user.is_authenticated:
        UserBehavior.objects.create(
            user=request.user,
            action=action,
            page=page,
            description=description,
            session_id=request.session.session_key,
            ip_address=request.META.get('REMOTE_ADDR')
        )

def register(request):
    if request.method == "POST":
        UserRegister.objects.create(
            username=request.POST['username'],
            password=request.POST['password'],
            email=request.POST['email'],
            dob=request.POST['dob'],
            gender=request.POST['gender'],
            address=request.POST['address'],
            mobile=request.POST['mobile'],
            profile_pic=request.FILES['profile_pic'],
            status='Unauthorized'
        )

        messages.success(request, "Registration Successful!")
        return redirect('register')   # stay on same page OR user_login if you want

    return render(request, 'register.html')

from django.contrib.auth import authenticate
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegister
from django.contrib.auth import login
from django.contrib.auth.models import User


from django.contrib.auth import login
from django.contrib.auth.models import User

def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user_obj = UserRegister.objects.get(
                username=username,
                password=password
            )
        except UserRegister.DoesNotExist:
            messages.error(request, "Please enter valid username or password")
            return redirect("user_login")

        if user_obj.status == "Unauthorized":
            messages.warning(request, "Please wait for admin approval")
            return redirect("user_login")

        if user_obj.status == "Authorized":

            # 🔥 Create Django auth user only first time
            django_user, created = User.objects.get_or_create(username=username)

            if created:
                django_user.set_password(password)
                django_user.save()

            # 🔥 Django login session
            login(request, django_user)
            log_behavior(request, "login", "login_page")
            # 🔥 Your custom session
            request.session["user"] = username

            return redirect("user_home")

    return render(request, "user_login.html")



from django.shortcuts import render
from django.contrib import messages
from .models import Behavior, UserIntention, Intention

def user_home(request):

    username = request.user.username

    # SAFE fetch (no crash)
    user_obj = UserRegister.objects.filter(username=username).first()

    messages.success(request, "Login Successful")

    login = "Login"
    r = "R"
    reg = "Register"

    behavior = Behavior.objects.filter(behavior=login).first()

    if behavior:
        stage1 = f"(({r},{reg}),{behavior.event_id},{behavior.desire_id},n)"

        UserIntention.objects.create(username=username, stage=stage1)
        Intention.objects.create(username=username, uintention=login)
    log_behavior(request, "home_visit", "user_home")

    return render(request, "user_home.html", {
        "user_obj": user_obj
    })

from django.contrib.auth import logout
from .ml_model import train_model

def user_logout(request):

    user_id = request.user.id

    log_behavior(request, "logout", "logout_page")

    # train model for this user
    train_model(user_id)

    logout(request)

    return redirect("user_login")


from django.shortcuts import render
from django.contrib import messages
from .models import UserRegister


from django.shortcuts import redirect

def search_friends(request):
    log_behavior(request, "search_friend", "search_page")

    username = request.user.username
    user_obj = UserRegister.objects.filter(username=username).first()

    if request.method == "POST":
        search_name = request.POST.get("username")

        friend = UserRegister.objects.filter(username=search_name).first()

        if friend:
            messages.success(request, "Friend Found!")

            # ✅ REDIRECT TO DETAILS PAGE
            return redirect('friend_details', username=friend.username)

        else:
            messages.error(request, "User not found")

    return render(request, "search_friends.html", {
        "user_obj": user_obj
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegister, Behavior, UserIntention, Intention


def friend_details(request, username):

    current_user = request.user.username
    friend = UserRegister.objects.filter(username=username).first()
    log_behavior(
            request,
            "send_friend_request",
            "friend_details",
            f"to {friend.username}"
        )
    if request.method == "POST":

        # ✅ Save friend request in DB
        FriendRequest.objects.create(
            uname=current_user,          # sender
            sname=friend.username,       # receiver
            email=friend.email,
            gender=friend.gender,
            status="pending"
        )
        messages.success(request, "Friend Request Sent Successfully")

        # ===== Behavior tracking (same as JSP) =====
        search = "Search"
        r = "R"
        reg = "Register"

        behavior = Behavior.objects.filter(behavior=search).first()

        if behavior:
            stage2 = f"(({r},{reg}),{behavior.event_id},{behavior.desire_id},n)"

            UserIntention.objects.create(
                username=current_user,
                stage=stage2
            )

            Intention.objects.create(
                username=current_user,
                uintention=search
            )

        return redirect('search_friends')

    return render(request, "friend_details.html", {
        "friend": friend
    })


from django.shortcuts import render, redirect
from .models import FriendRequest, UserRegister


def view_friend_requests(request):

    username = request.user.username
    log_behavior(request, "view_friend_requests", "friend_requests")
    user_obj = UserRegister.objects.filter(username=username).first()

    # ✅ Requests others sent TO me
    incoming_requests = FriendRequest.objects.filter(
        sname=username,
        status='pending'
    )

    # ✅ Requests I sent to others
    sent_requests = FriendRequest.objects.filter(
        uname=username,
        status='pending'
    )

    return render(request, "view_friend_requests.html", {
        "incoming_requests": incoming_requests,
        "sent_requests": sent_requests,
        "user_obj": user_obj
    })

from .models import Friend
def accept_request(request, id):
    log_behavior(request, "accept_friend", "friend_request")

    fr = FriendRequest.objects.get(id=id)

    fr.status = "accepted"
    fr.save()

    # ✅ create friendship
    Friend.objects.create(
        user1=fr.uname,
        user2=fr.sname
    )

    messages.success(request, "Friend Added Successfully")

    return redirect("view_friend_requests")

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Post


from django.contrib.auth.decorators import login_required

@login_required
def upload_post(request):
    log_behavior(request, "upload_post", "upload_post")

    if request.method == "POST":

        name = request.POST.get("name")
        content = request.POST.get("content")
        image = request.FILES.get("pic")
        visibility = request.POST.get("visibility")

        Post.objects.create(
            name=name,
            content=content,
            image=image,
            visibility=visibility,
            owner=request.user  # 👈 save owner
        )

        messages.success(request, "Post Uploaded Successfully")
        return redirect("upload_post")

    return render(request, "upload_post.html")

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import FriendRequest, Message, UserRegister


def send_message(request):
    

    username = request.user.username

    user_obj = UserRegister.objects.filter(username=username).first()

    # accepted friends only
    friends = FriendRequest.objects.filter(
        sname=username,
        status='Accepted'
    )

    if request.method == "POST":

        fname = request.POST.get("fname")
        msg = request.POST.get("message")

        if not fname:
            messages.error(request, "No friend selected")
            return redirect("send_message")

        Message.objects.create(
            sender=username,
            receiver=fname,
            message=msg
        )
        log_behavior(request, "send_message", "chat", msg)
        log_behavior(request, "send_message", "chat", f"to {fname}")
        messages.success(request, "Message Sent Successfully")
        return redirect("send_message")
   
    return render(request, "send_message.html", {
        "friends": friends,
        "user_obj": user_obj
    })
from django.shortcuts import render
from .models import Message, UserRegister

def view_messages(request):

    username = request.user.username

    user_obj = UserRegister.objects.filter(username=username).first()

    # received messages
    messages_list = Message.objects.filter(receiver=username)

    return render(request, "view_messages.html", {
        "messages_list": messages_list,
        "user_obj": user_obj
    })

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Group, UserRegister


@login_required
def create_group(request):

    username = request.user.username

    if request.method == "POST":
        groupname = request.POST.get("groupname")

        Group.objects.create(
            groupname=groupname,
            admin=username
        )

        messages.success(request, "Group Created Successfully")
        return redirect("create_group")

    return render(request, "create_group.html", {
        "username": username
    })

from django.shortcuts import render
from .models import Post, UserRegister, Behavior, UserIntention, Intention


from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
def view_posts(request):
    log_behavior(request, "view_posts", "posts_page")

    username = request.user.username
    user_obj = UserRegister.objects.filter(username=username).first()

    # ✅ IMPORTANT CHANGE HERE
    posts = Post.objects.filter(
        Q(visibility='public') | Q(owner=request.user)
    ).select_related('owner').order_by('-created_at')


    # ===== Behavior tracking (same as JSP) =====
    viewposts = "My ZOE"
    r = "R"
    reg = "Register"

    behavior = Behavior.objects.filter(behavior=viewposts).first()

    if behavior:
        stage = f"(({r},{reg}),{behavior.event_id},{behavior.desire_id},n)"
        UserIntention.objects.create(username=username, stage=stage)
        Intention.objects.create(username=username, uintention=viewposts)

    return render(request, "view_posts.html", {
        "posts": posts,
        "user_obj": user_obj
    })

from django.shortcuts import redirect
from .models import Comment, Behavior, UserIntention, Intention


from django.shortcuts import redirect
from django.contrib import messages
from .models import Comment


def add_comment(request):
    log_behavior(request, "comment", "post_comment")

    if request.method == "POST":

        imagename = request.POST.get("imagename")
        content = request.POST.get("content")
        comment = request.POST.get("comment")
        username = request.user.username
        log_behavior(request, "comment", "post_comment", comment)
        # Save to DB
        Comment.objects.create(
            imagename=imagename,
            content=content,
            comment=comment,
            uname=username
        )

        # success message
        messages.success(request, "Comment Added Successfully")

        return redirect("user_view_posts")
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserRegister, FriendRequest, GroupMember   # adjust model names

def add_friends(request):

    username = request.session.get("user")   # your login system

    if not username:
        return redirect("user_login")

    user_obj = UserRegister.objects.filter(username=username).first()

    friends = FriendRequest.objects.filter(
        sname=username,
        status="Accepted"
    )

    if request.method == "POST":
        groupname = request.POST.get("groupname")
        friend = request.POST.get("userlist")

        if friend and friend != "selected":

            # create group first
            group = Group.objects.create(
                groupname=groupname,
                admin=username
            )

            # add member to group
            GroupMember.objects.create(
                group=group,
                username=friend
            )

            messages.success(request, "Friend Invited Successfully")
            return redirect("add_friends")

    return render(request, "add_friends.html", {
        "friends": friends,
        "username": username,
        "user_obj": user_obj
    })
# users/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import GroupRequest, UserRegister

def view_group_requests(request):

    username = request.session.get("user")

    if not username:
        return redirect("user_login")

    user_obj = UserRegister.objects.filter(username=username).first()

    # 🔥 same as: select * from grouprequest where name=user and status='pending'
    requests = GroupRequest.objects.filter(
        name=username,
        status="pending"
    )

    return render(request, "view_group_request.html", {
        "requests": requests,
        "user_obj": user_obj,
        "username": username
    })
def accept_group_request(request, id):

    req = GroupRequest.objects.get(id=id)
    req.status = "Accepted"
    req.save()

    messages.success(request, "Group Joined Successfully")

    return redirect("view_group_request")
# users/views.py

from django.shortcuts import render, redirect
from .models import GroupRequest, UserRegister

def view_group_members(request):

    username = request.session.get("user")

    if not username:
        return redirect("user_login")

    user_obj = UserRegister.objects.filter(username=username).first()

    # 🔥 SAME AS YOUR SQL
    members = GroupRequest.objects.filter(
        gadmin=username,
        status="Accepted"
    )

    return render(request, "view_group_members.html", {
        "members": members,
        "user_obj": user_obj
    })
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Video, UserRegister

from django.contrib.auth.decorators import login_required

@login_required
def upload_video(request):
    log_behavior(request, "upload_video", "video_upload")

    user_obj = request.user

    if request.method == "POST":

        video_file = request.FILES.get("file")
        visibility = request.POST.get("visibility")

        if video_file:
            Video.objects.create(
                filename=video_file.name,
                file=video_file,
                owner=user_obj,
                visibility=visibility
            )

            messages.success(request, "Video Uploaded Successfully")
            return redirect("upload_video")

    return render(request, "upload_video.html", {
        "username": request.user.username,
        "user_obj": user_obj
    })


from .models import Video, UserRegister

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Video, UserRegister

@login_required
def view_videos(request):

    username = request.user.username
    user_obj = UserRegister.objects.filter(username=username).first()

    # ✅ FILTER LOGIC (same like posts)
    videos = Video.objects.filter(
        Q(visibility='public') | Q(owner=request.user)
    ).order_by('-upload_date')

    return render(request, "view_videos.html", {
        "videos": videos,
        "username": username,
        "user_obj": user_obj
    })
