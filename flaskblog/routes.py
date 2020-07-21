from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)    # Sets page
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)    # sets how many posts on one page
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])    # Ability to retrieve and post data
def register():
    if current_user.is_authenticated:   # if user is already on system
        return redirect(url_for('home'))       # Go to home page
    form = RegistrationForm()   # Sets instance of registration form
    if form.validate_on_submit():   # If all requirements are satisfied on the form
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')     # Has the password
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)   # Creates instance of user
        db.session.add(user)    # Adds user to be created
        db.session.commit()     # Saves user to database
        flash('Your account has been created successfully! You are now able to log in', 'success')  #   Message pops up
        return redirect(url_for('login'))   # redirects user to log in
    return render_template('register.html', title='Register', form=form)    # Renders page


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:   # if user is already logged in
        return redirect(url_for('home'))
    form = LoginForm()  # sets instance of login form
    if form.validate_on_submit():   # If all requirements are met
        user = User.query.filter_by(email=form.email.data).first()  # finds email in db
        if user and bcrypt.check_password_hash(user.password, form.password.data):  # if email and pass match db
            login_user(user, remember=form.remember.data)   # user logged in and remembers data from file
            next_page = request.args.get('next')    # Redirects to next page, else homepage
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')  # If user and pass do not match
    return render_template('login.html', title='Login', form=form)  # stay in login form with message flashed above


@app.route("/logout")
def logout():
    logout_user()   # Method to log user out
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)   # Saves user pic as a hex name
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext     # adds name to user pic
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)   # saves profile pic into file

    output_size = (125, 125)    # sets size of pic
    i = Image.open(form_picture)    # imports picture
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()  # Calls updateaccountform method from forms.py
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)  # To update picture
            current_user.image_file = picture_file
        current_user.username = form.username.data  # To update username
        current_user.email = form.email.data    # To update password
        db.session.commit()     # Commits changes to database
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account')) # sends user to their page
    elif request.method == 'GET':
        form.username.data = current_user.username  # gets current username already from db
        form.email.data = current_user.email    # gets current email already from db
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)  # save new picture
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()   # takes PostForm instance from forms.py
    if form.validate_on_submit():   # If all criteria have been met
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)    # adds post to be saved to db
        db.session.commit()     # saves post to db
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))    # takes user home
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)   # Returns 404 if page doesn't exist
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post has been updated successfully', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted successfully!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()   # returns 404 error if user is not found
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)