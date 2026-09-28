from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render

from .ml_model import train_model
from .models import (
    Behavior, Comment, Friend, FriendRequest, Group, GroupMember,
    GroupRequest, Intention, Message, Post, UserBehavior, UserIntention,
    UserRegister, Video,
)


# ============================================================
# Helpers (these replace code that was repeated in many views)
# ============================================================

def log_behavior(request, action, page="", description=""):
    """Save one row in the behavior log (this is the ML training data)."""
    if request.user.is_authenticated:
        UserBehavior.objects.create(
            user=request.user,
            action=action,
            page=page,
            description=description,
            session_id=request.session.session_key,
            ip_address=request.META.get("REMOTE_ADDR"),
        )


def get_user_obj(username):
    """Profile (UserRegister) for a username, or None."""
    return UserRegister.objects.filter(username=username).first()


def track_intention(username, label):
    """Record an intention stage if the label exists in the Behavior table."""
    behavior = Behavior.objects.filter(behavior=label).first()
    if behavior:
        stage = f"((R,Register),{behavior.event_id},{behavior.desire_id},n)"
        UserIntention.objects.create(username=username, stage=stage)
        Intention.objects.create(username=username, uintention=label)


def session_login_required(view):
    """For views that rely on request.session['user'] instead of Django auth."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user"):
            return redirect("user_login")
        return view(request, *args, **kwargs)
    return wrapper


# ============================================================
# Register / login / logout
# ============================================================

def register(request):
    if request.method == "POST":
        data = dict(
            username=request.POST["username"],
            password=make_password(request.POST["password"]),
            email=request.POST["email"],
            dob=request.POST["dob"],
            gender=request.POST["gender"],
            address=request.POST["address"],
            mobile=request.POST["mobile"],
            status="Unauthorized",
        )
        # Only pass a picture if one was uploaded; otherwise the model default is used.
        pic = request.FILES.get("profile_pic")
        if pic:
            data["profile_pic"] = pic

        UserRegister.objects.create(**data)
        messages.success(request, "Registration Successful!")
        return redirect("register")

    return render(request, "register.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user_obj = get_user_obj(username)
        if user_obj is None or not check_password(password, user_obj.password):
            messages.error(request, "Please enter valid username or password")
            return redirect("user_login")

        if user_obj.status == "Unauthorized":
            messages.warning(request, "Please wait for admin approval")
            return redirect("user_login")

        if user_obj.status == "Authorized":
            # Create the Django auth user only the first time
            django_user, created = User.objects.get_or_create(username=username)
            if created:
                django_user.set_password(password)
                django_user.save()

            login(request, django_user)
            log_behavior(request, "login", "login_page")
            request.session["user"] = username
            return redirect("user_home")

    return render(request, "user_login.html")


def user_home(request):
    username = request.user.username
    messages.success(request, "Login Successful")

    track_intention(username, "Login")
    log_behavior(request, "home_visit", "user_home")

    return render(request, "user_home.html", {"user_obj": get_user_obj(username)})


def user_logout(request):
    user_id = request.user.id
    log_behavior(request, "logout", "logout_page")

    # retrain this user's model with the session that just ended
    train_model(user_id)

    logout(request)
    return redirect("user_login")


# ============================================================
# Friends
# ============================================================

def search_friends(request):
    username = request.user.username

    if request.method == "POST":
        log_behavior(request, "search_friend", "search_page")
        friend = get_user_obj(request.POST.get("username"))

        if friend:
            messages.success(request, "Friend Found!")
            return redirect("friend_details", username=friend.username)
        messages.error(request, "User not found")

    return render(request, "search_friends.html", {"user_obj": get_user_obj(username)})


def friend_details(request, username):
    current_user = request.user.username
    friend = get_user_obj(username)

    if not friend:
        return redirect("search_friends")

    if request.method == "POST":
        log_behavior(request, "send_friend_request", "friend_details", f"to {friend.username}")

        FriendRequest.objects.create(
            uname=current_user,        # sender
            sname=friend.username,     # receiver
            email=friend.email,
            gender=friend.gender,
            status="pending",
        )
        messages.success(request, "Friend Request Sent Successfully")

        track_intention(current_user, "Search")
        return redirect("search_friends")

    return render(request, "friend_details.html", {"friend": friend})


def view_friend_requests(request):
    username = request.user.username
    log_behavior(request, "view_friend_requests", "friend_requests")

    return render(request, "view_friend_requests.html", {
        "incoming_requests": FriendRequest.objects.filter(sname=username, status="pending"),
        "sent_requests": FriendRequest.objects.filter(uname=username, status="pending"),
        "user_obj": get_user_obj(username),
    })


def accept_request(request, id):
    log_behavior(request, "accept_friend", "friend_request")

    fr = FriendRequest.objects.get(id=id)
    fr.status = "accepted"
    fr.save()

    Friend.objects.create(user1=fr.uname, user2=fr.sname)

    messages.success(request, "Friend Added Successfully")
    return redirect("view_friend_requests")


# ============================================================
# Posts, comments, videos
# ============================================================

@login_required
def upload_post(request):
    log_behavior(request, "upload_post", "upload_post")

    if request.method == "POST":
        Post.objects.create(
            name=request.POST.get("name"),
            content=request.POST.get("content"),
            image=request.FILES.get("pic"),
            visibility=request.POST.get("visibility"),
            owner=request.user,
        )
        messages.success(request, "Post Uploaded Successfully")
        return redirect("upload_post")

    return render(request, "upload_post.html")


@login_required
def view_posts(request):
    log_behavior(request, "view_posts", "posts_page")

    username = request.user.username
    posts = (
        Post.objects.filter(Q(visibility="public") | Q(owner=request.user))
        .select_related("owner")
        .order_by("-created_at")
    )

    track_intention(username, "My ZOE")

    return render(request, "view_posts.html", {
        "posts": posts,
        "user_obj": get_user_obj(username),
    })


def add_comment(request):
    if request.method == "POST":
        comment = request.POST.get("comment")
        log_behavior(request, "comment", "post_comment", comment)

        Comment.objects.create(
            imagename=request.POST.get("imagename"),
            content=request.POST.get("content"),
            comment=comment,
            uname=request.user.username,
        )
        messages.success(request, "Comment Added Successfully")

    return redirect("user_view_posts")


@login_required
def upload_video(request):
    log_behavior(request, "upload_video", "video_upload")

    if request.method == "POST":
        video_file = request.FILES.get("file")
        if video_file:
            Video.objects.create(
                filename=video_file.name,
                file=video_file,
                owner=request.user,
                visibility=request.POST.get("visibility"),
            )
            messages.success(request, "Video Uploaded Successfully")
            return redirect("upload_video")

    return render(request, "upload_video.html", {
        "username": request.user.username,
        "user_obj": request.user,
    })


@login_required
def view_videos(request):
    username = request.user.username
    videos = Video.objects.filter(
        Q(visibility="public") | Q(owner=request.user)
    ).order_by("-upload_date")

    return render(request, "view_videos.html", {
        "videos": videos,
        "username": username,
        "user_obj": get_user_obj(username),
    })


# ============================================================
# Messages
# ============================================================

def send_message(request):
    username = request.user.username
    friends = FriendRequest.objects.filter(sname=username, status="Accepted")

    if request.method == "POST":
        fname = request.POST.get("fname")
        msg = request.POST.get("message")

        if not fname:
            messages.error(request, "No friend selected")
            return redirect("send_message")

        Message.objects.create(sender=username, receiver=fname, message=msg)
        log_behavior(request, "send_message", "chat", f"to {fname}: {msg}")
        messages.success(request, "Message Sent Successfully")
        return redirect("send_message")

    return render(request, "send_message.html", {
        "friends": friends,
        "user_obj": get_user_obj(username),
    })


def view_messages(request):
    username = request.user.username
    return render(request, "view_messages.html", {
        "messages_list": Message.objects.filter(receiver=username),
        "user_obj": get_user_obj(username),
    })


# ============================================================
# Groups
# ============================================================

@login_required
def create_group(request):
    username = request.user.username

    if request.method == "POST":
        Group.objects.create(groupname=request.POST.get("groupname"), admin=username)
        messages.success(request, "Group Created Successfully")
        return redirect("create_group")

    return render(request, "create_group.html", {"username": username})


@session_login_required
def add_friends(request):
    username = request.session["user"]
    friends = FriendRequest.objects.filter(sname=username, status="Accepted")

    if request.method == "POST":
        friend = request.POST.get("userlist")

        if friend and friend != "selected":
            group = Group.objects.create(
                groupname=request.POST.get("groupname"),
                admin=username,
            )
            GroupMember.objects.create(group=group, username=friend)

            messages.success(request, "Friend Invited Successfully")
            return redirect("add_friends")

    return render(request, "add_friends.html", {
        "friends": friends,
        "username": username,
        "user_obj": get_user_obj(username),
    })


@session_login_required
def view_group_requests(request):
    username = request.session["user"]
    return render(request, "view_group_request.html", {
        "requests": GroupRequest.objects.filter(name=username, status="pending"),
        "user_obj": get_user_obj(username),
        "username": username,
    })


def accept_group_request(request, id):
    req = GroupRequest.objects.get(id=id)
    req.status = "Accepted"
    req.save()

    messages.success(request, "Group Joined Successfully")
    return redirect("view_group_request")


@session_login_required
def view_group_members(request):
    username = request.session["user"]
    return render(request, "view_group_members.html", {
        "members": GroupRequest.objects.filter(gadmin=username, status="Accepted"),
        "user_obj": get_user_obj(username),
    })