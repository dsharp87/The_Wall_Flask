from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re
import datetime
import md5
app = Flask(__name__)
app.secret_key = 'KeepItSecretKeepItSafe'
mysql = MySQLConnector(app,'the_wall')
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wall')
def wall():
    if "current_user_id" not in session:
        flash ("please log in to access the wall")  ##this denies entry if no one is logged in
        return redirect ('/')
    #create query to grab all post and comment info
    query_posts = "SELECT users.first_name, users.last_name, posts.id, posts.post, DATE_FORMAT(posts.created_at, '%M %D, %Y - %l:%i%p') AS 'created_at', posts.created_at AS 'created_time' FROM posts JOIN users ON posts.user_id = users.id ORDER BY created_time DESC"
    query_comments = "SELECT users.first_name, users.last_name, comments.id, comments.post_id, comments.comment, DATE_FORMAT(comments.created_at, '%M %D %Y - %l:%i%p') AS 'created_at', comments.created_at AS 'created_time' FROM comments JOIN users ON users.id = comments.user_id ORDER BY created_time"
    #create data
    #run query and store it
    feed_post_result = mysql.query_db(query_posts)
    print feed_post_result
    feed_comment_result = mysql.query_db(query_comments)
    print "NEXT"
    print feed_comment_result
    #pass query result to template render
    return render_template('wall.html' , current_user_name = session["current_user_name"], feed_post_result = feed_post_result, feed_comment_result = feed_comment_result)

@app.route('/new_post', methods=['POST'])
def new_post():
    print len(request.form['new_post'])
    if len(request.form['new_post']) == 0:
        flash("Post must have at least 1 character", "error")
        return redirect('/wall')
    #create query
    query = "INSERT INTO posts (user_id, post, created_at, updated_at) VALUES(:user_id, :post, NOW(), NOW())"
    #create data
    data = {
    "user_id": session["current_user_id"],
    "post": request.form['new_post']     #grab content of post
    }
    #run query
    mysql.query_db(query, data)
    #new information for wall is grabbed by wall route
    return redirect('/wall')

@app.route('/new_comment/<post_id>', methods=['POST']) #need to grab post id somehow from comment button
def new_comment(post_id):
    print len(request.form['new_comment'])
    if len(request.form['new_comment']) == 0:
        flash("Comment must have at least 1 character", "error")
        return redirect('/wall')
    #create query
    query = "INSERT INTO comments (user_id, post_id, comment, created_at, updated_at) VALUES(:user_id, :post_id, :comment, NOW(), NOW())"
    #create data
    data = {
    "user_id": session["current_user_id"],
    "post_id": post_id,
    "comment": request.form['new_comment']     #grab content of post
    }
    #run query
    mysql.query_db(query, data)
    #new information for wall is grabbed by wall route
    return redirect('/wall')

@app.route('/register', methods=['POST'])
def registration():
    flash_length = 0
    if len(request.form['first_name']) < 2:
        flash("First Name must be at least two characters", "error")
        flash_length +=1
    if not request.form['first_name'].isalpha():
        flash("Your First Name can be only letters(no numbers, spaces, or symbols)", "error")
        flash_length +=1
    if len(request.form['last_name']) < 2:
        flash("Last Name must be at least two characters", "error")
        flash_length +=1
    if not request.form['last_name'].isalpha():
        flash("Your Last Name can be only letters(no numbers, spaces, or symbols)", "error")
        flash_length +=1
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Email must be of valid format 'xxx@xxx.xxx'", "error")
        flash_length += 1
    upper_count = 0
    num_count = 0
    for char in range(0, len(request.form['password'])):
        if request.form['password'][char].isupper():
            upper_count += 1
        if request.form['password'][char].isdigit():
            num_count += 1
    if len(request.form['password']) < 8:
        flash("Password must be at least 8 characters", "error")
        flash_length +=1
    if upper_count == 0 or num_count == 0:
        flash("Password must contain at least one upper case letter and one number", "error")
        flash_length +=1
    if not request.form['password'] == request.form['password_comfirmation']:
        flash("Password Confirmation must match Password", "error")
        flash_length +=1
    if flash_length == 0:
        flash("Thanks for submitting your information! You are now registered and logged in.", "success")
        password = md5.new(request.form['password']).hexdigest()
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
        data = {
        "first_name": request.form['first_name'],
        "last_name": request.form['last_name'],
        "email": request.form['email'],
        "password": password
        }
        current_user_id = mysql.query_db(query, data)
        id_query = "SELECT users.id FROM users"  # there is probably a better way to grab the ID upon registration, than running a second query.  INSERT is suposed to return the last row inserted??
        user_list = mysql.query_db(id_query)
        current_user_id = user_list[len(user_list)-1]['id']
        session["current_user_name"] = request.form['first_name']
        session["current_user_id"] = current_user_id
        return redirect ('/wall') #succuessful login will need to rerout to wall
    else:
        print flash_length       
        return redirect ("/")

@app.route('/login', methods=['POST'])
def login():
    query = "SELECT * FROM users WHERE users.email = :email AND users.password = :password"
    data = { 'email': request.form['email'], 'password': md5.new(request.form['password']).hexdigest()}
    compare_table =  mysql.query_db(query, data)
    if compare_table:
        flash("You are now logged in.", "success")
        session["current_user_id"] = compare_table[0]["id"]
        session["current_user_name"] = compare_table[0]["first_name"]
        return redirect ('/wall') #succuessful login will need to rerout to wall
    else:
        flash("failed log in. Try again")
        return redirect ("/") 
#this will need to get deleted or disabled before the end, and succuessful login will need to rerout to wall
# @app.route("/success") 
# def logged_in():
#     query = "SELECT * FROM users"              
#     users = mysql.query_db(query)                         
#     return render_template('success.html', users = users, current_user_name = session["current_user_name"]) 

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    flash("you are now logged out", "success")
    session.clear()
    return redirect ('/')

# @app.route('/delete/<this_user>')
# def delete(this_user):
#     print this_user
#     print "im bouts to delete stuff"
#     query = "DELETE FROM users WHERE users.id =" + str(this_user)
#     mysql.query_db(query)
#     return redirect ('/success')

app.run(debug=True)