from project import app, db, bcrypt, login_manager
from project.forms import LoginForm, RegisterForm, ChangeUsernameForm, ChangePasswordForm, ChangeEmailForm, \
    ChangeProfilePictureForm, CreateChat
from project.models import Accounts
from flask_login import login_required, login_user, current_user, logout_user
from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import json, os


@login_manager.user_loader
def load_user(user_id):
    return Accounts.get(user_id)


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        if request.form['logout'] == 'Logout':
            logout_user()
            return redirect(url_for('login'))
    return render_template('home.html', user=current_user)


@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    error = None
    form = LoginForm()
    if form.validate_on_submit():
        user = Accounts.query.filter_by(username=form.username.data).first()
        if user is not None and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('login'))
        else:
            error = "* Invalid login credentials."
    return render_template('login.html', form=form, error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():

    register_form = RegisterForm()

    if register_form.validate_on_submit():
        email = register_form.email.data.lower()
        username = register_form.username.data
        password = bcrypt.generate_password_hash(register_form.password.data, 15)
        following = []
        followers = []
        friends = []
        profile_picture = '/static/img/profile_pictures/no-profile.jpg'

        new_user = Accounts(
            email=email,
            username=username,
            password=password,
            following=json.dumps(following),
            followers=json.dumps(followers),
            friends=json.dumps(friends),
            profile_picture=profile_picture
        )

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=register_form)


@app.route('/forgot')
def forgot_password():
    return "forgot"


@app.route('/dm', methods=['GET', 'POST'])
@login_required
def dm():
    create_chat = CreateChat()

    if create_chat.validate_on_submit():
        pass
    elif create_chat.errors:
        flash('There was an error creating your chat')

    if request.form.get('logout') == 'Logout':
        logout_user()
        return redirect(url_for('login'))

    return render_template(
        'dms.html',
        user=current_user,
        friends=json.loads(current_user.friends),
        create_chat=create_chat
    )


@app.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    following = json.loads(current_user.following)
    followers = json.loads(current_user.followers)
    friends = json.loads(current_user.friends)
    viewed_user = Accounts.query.filter_by(username=username).first()
    viewed_followers = json.loads(viewed_user.followers)
    viewed_frineds = json.loads(viewed_user.friends)
    follow_value = 'Follow'

    if request.form.get('logout') == 'Logout':
        logout_user()
        return redirect(url_for('login'))
    elif request.form.get('submit') == 'Follow':
        viewed_followers.append(current_user.username)
        following.append(viewed_user.username)
        '''
        following button disappears if you are following someone
        '''
        for account in following:
            for follower in followers:
                if account and follower == viewed_user.username:
                    friends.append(viewed_user.username)
                    viewed_frineds.append(current_user.username)

        # update following/followers
        current_user.following = json.dumps(following)
        viewed_user.followers = json.dumps(viewed_followers)
        # update friends
        current_user.friends = json.dumps(friends)
        viewed_user.friends = json.dumps(viewed_frineds)
        db.session.commit()
    elif request.form.get('submit') == 'Following':
        for account in following:
            for follower in followers:
                if account and follower == viewed_user.username:
                    friends.remove(viewed_user.username)
                    viewed_frineds.remove(current_user.username)

        viewed_followers.remove(current_user.username)
        following.remove(viewed_user.username)
        viewed_user.followers = json.dumps(viewed_followers)
        current_user.following = json.dumps(following)

        current_user.friends = json.dumps(friends)
        viewed_user.friends = json.dumps(viewed_frineds)
        db.session.commit()

    for follow in following:
        if follow == viewed_user.username:
            follow_value = 'Following'
    return render_template(
        'profile.html',
        user=current_user,
        viewed_user=viewed_user,
        user_following=json.loads(current_user.following),
        viewed_followers=json.loads(viewed_user.followers),
        viewed_friends=json.loads(viewed_user.friends),
        follow_value=follow_value
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    change_user_form = ChangeUsernameForm()
    change_password_form = ChangePasswordForm()
    change_email_form = ChangeEmailForm()
    change_pic_form = ChangeProfilePictureForm()

    error = None

    if request.form.get('submit') == 'Change Username':
        if change_user_form.validate_on_submit():
            if bcrypt.check_password_hash(current_user.password, change_user_form.password.data):
                current_user.username = change_user_form.username.data
                db.session.commit()
                return redirect(url_for('home'))
            else:
                error = "Password is incorrect"
    elif request.form.get('submit') == 'Change Password':
        if change_password_form.validate_on_submit():
            if bcrypt.check_password_hash(current_user.password, change_password_form.current_password.data):
                current_user.password = bcrypt.generate_password_hash(change_password_form.new_password.data, 15)
                db.session.commit()
                return redirect(url_for('home'))
            else:
                error = "Password is incorrect"
    elif request.form.get('submit') == 'Change Email':
        if change_email_form.validate_on_submit():
            if bcrypt.check_password_hash(current_user.password, change_email_form.password.data):
                current_user.email = change_email_form.new_email.data
                db.session.commit()
                return redirect(url_for('home'))
            else:
                error = "Password is incorrect"
    elif request.form.get('submit') == 'Change Profile Picture':
        if change_pic_form.validate_on_submit():
            file = change_pic_form.profile_pic.data
            filename = secure_filename(file.filename)
            file.save(os.path.join("/static/img/profile_pictures", filename))
            current_user.profile_picture = '/static/img/profile_pictures/' + filename
            db.session.commit()
            return redirect(url_for('home'))
    elif request.form.get('submit') == 'Remove Profile Picture':
        current_user.profile_picture = '/static/img/profile_pictures/no-profile.jpg'
        db.session.commit()
        return redirect(url_for('home'))
    elif request.form.get('logout') == 'Logout':
        logout_user()
        return redirect(url_for('login'))

    return render_template(
        'profile_settings.html',
        user=current_user,
        change_user_form=change_user_form,
        change_password_form=change_password_form,
        change_email_form=change_email_form,
        change_pic_form=change_pic_form,
        error=error
    )
