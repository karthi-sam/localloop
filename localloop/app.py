from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from werkzeug.utils import secure_filename
from flask import jsonify
from datetime import datetime

app = Flask(__name__)

db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="officialdream@43",
    database="localloop"
)

cursor = db.cursor()

app = Flask(__name__)
app.secret_key = "4313302002"  # required for session

app.config['UPLOAD_FOLDER'] = 'static/uploads'

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "mov", "webm"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect("/feed")

    error = None

    # ✅ create fresh cursor
    cursor = db.cursor()

    if request.method == "POST":

        action = request.form.get("action")

        email = request.form.get("email")
        password = request.form.get("password")

        # ================= LOGIN =================
        if action == "login":

            cursor.execute(
                "SELECT * FROM users WHERE email=%s",
                (email,)
            )

            user = cursor.fetchone()

            # ✅ clear remaining result
            cursor.fetchall()

            if user and user[6] == password:

                session["user_id"] = user[0]
                session["username"] = user[1]

                cursor.close()

                return redirect("/feed")

            else:
                error = "Invalid email or password"

        # ================= REGISTER =================
        elif action == "register":

            username = request.form.get("username")
            phone = request.form.get("phone")
            category = request.form.get("category")
            location = request.form.get("location")

            company_name = request.form.get("company_name")
            map_link = request.form.get("map_link")

            business_name = request.form.get("business_name")
            service_type = request.form.get("service_type")
            business_mode = request.form.get("business_mode")
            service_description = request.form.get("service_description")

            shop_name = request.form.get("shop_name")
            shop_type = request.form.get("shop_type")

            alert_type = request.form.get("alert_type")
            job_type = request.form.get("job_type")

            # ✅ CHECK EXISTING EMAIL
            cursor.execute(
                "SELECT * FROM users WHERE email=%s",
                (email,)
            )

            existing_user = cursor.fetchone()

            # ✅ clear remaining results
            cursor.fetchall()

            if existing_user:

                error = "Account already exists"

            else:

                cursor.execute("""
                    INSERT INTO users (
                        username,email,phone,category,location,password,
                        company_name,map_link,
                        business_name,service_type,business_mode,service_description,
                        shop_name,shop_type,
                        alert_type,job_type
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    username,
                    email,
                    phone,
                    category,
                    location,
                    password,
                    company_name,
                    map_link,
                    business_name,
                    service_type,
                    business_mode,
                    service_description,
                    shop_name,
                    shop_type,
                    alert_type,
                    job_type
                ))

                db.commit()

                session["user_id"] = cursor.lastrowid
                session["username"] = username

                cursor.close()

                return redirect("/feed")

    cursor.close()

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return redirect("/")

    file = request.files["image"]

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        cursor.execute(
            "UPDATE users SET profile_image=%s WHERE id=%s",
            (filename, session["user_id"])
        )
        db.commit()

    return redirect("/feed")



@app.route('/profile')
def profile():

    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)

    user_id = session["user_id"]

    # USER DETAILS
    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (user_id,)
    )

    user = cursor.fetchone()

    # USER POSTS
    cursor.execute("""
        SELECT *
        FROM posts
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user_id,))

    posts = cursor.fetchall()


    return render_template(
        "profile.html",
        user=user,
        posts=posts
    )

@app.route("/feed")
def feed():

    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)

    # USER
    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )

    user = cursor.fetchone()

    # NORMAL POSTS
    cursor.execute("""
        SELECT
            posts.*,
            users.username,
            users.profile_image,
            'post' AS feed_type
        FROM posts
        JOIN users
        ON posts.user_id = users.id
    """)

    posts = cursor.fetchall()

    # JOB POSTS
    cursor.execute("""
        SELECT
            jobs.*,
            users.username,
            users.profile_image,
            'job' AS feed_type
        FROM jobs
        JOIN users
        ON jobs.user_id = users.id
    """)

    jobs = cursor.fetchall()

    # EVENTS
    cursor.execute("""
        SELECT
            events.*,
            users.username,
            users.profile_image,
            'event' AS feed_type
        FROM events
        JOIN users
        ON events.user_id = users.id
    """)

    events = cursor.fetchall()

    # COMBINE ALL
    feed_data = posts + jobs + events

    # SORT
    feed_data = sorted(
        feed_data,
        key=lambda x: x['created_at'],
        reverse=True
    )

    # DAYS LIVE
    for item in feed_data:

        created = item['created_at']
        today = datetime.now()

        difference = today - created

        item['days_live'] = difference.days

    return render_template(
        "feed.html",
        user=user,
        posts=feed_data
    )

@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if "user_id" not in session:
        return redirect("/")

    # Fetch user data for the template
    cursor.execute("SELECT id, username, email, phone, category, location, profile_image FROM users WHERE id = %s",
                   (session["user_id"],))
    user = cursor.fetchone()

    # Convert to dictionary for easier access in template
    if user:
        user_dict = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'phone': user[3],
            'category': user[4],
            'location': user[5],
            'profile_image': user[6]
        }
    else:
        user_dict = None

    if request.method == "POST":
        content = request.form.get("content")
        type_ = request.form.get("type")
        location = request.form.get("location")

        media = request.files.get("media")

        image_filename = None
        video_filename = None

        if media and media.filename != "":
            filename = secure_filename(media.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            media.save(filepath)

            # detect type
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                image_filename = filename
            elif filename.lower().endswith((".mp4", ".mov", ".avi")):
                video_filename = filename

        cursor.execute("""
            INSERT INTO posts (user_id, content, type, location, image, video)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session["user_id"], content, type_, location, image_filename, video_filename))

        db.commit()

        return redirect("/feed")

    return render_template("create_post.html", user=user_dict)



@app.route("/post/<int:post_id>")
def view_post(post_id):

    cursor.execute("""
        SELECT posts.*, users.username, users.profile_image
        FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE posts.id = %s
    """, (post_id,))

    post = cursor.fetchone()

    if not post:
        return "Post not found"

    return render_template("single_post.html", post=post)


@app.route("/delete_post/<int:post_id>/<feed_type>", methods=["POST"])
def delete_post(post_id, feed_type):

    if "user_id" not in session:
        return jsonify({"success": False})

    cursor = db.cursor(dictionary=True)

    # DELETE JOB
    if feed_type == "job":

        cursor.execute("""
            DELETE FROM jobs
            WHERE id=%s AND user_id=%s
        """, (post_id, session["user_id"]))

    # DELETE NORMAL/SERVICE POST
    else:

        cursor.execute("""
            DELETE FROM posts
            WHERE id=%s AND user_id=%s
        """, (post_id, session["user_id"]))

    db.commit()

    return jsonify({
        "success": True
    })



@app.route("/services", methods=["GET", "POST"])
def services():

    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        # COMMON
        content = request.form.get("content")
        location = request.form.get("location")
        phone = request.form.get("phone")
        website = request.form.get("website")

        # CATEGORY
        category = request.form.get("category")

        # BUSINESS / SERVICE
        business_mode = request.form.get("business_mode")
        company_name = request.form.get("company_name")
        service_type = request.form.get("service_type")
        map_link = request.form.get("map_link")
        service_description = request.form.get("service_description")

        # SHOP
        shop_name = request.form.get("shop_name")
        shop_type = request.form.get("shop_type")
        shop_map_link = request.form.get("shop_map_link")
        shop_description = request.form.get("shop_description")

        # PUBLIC
        bio = request.form.get("bio")

        file = request.files.get("image")

        filename = None
        if file and file.filename != "":
            from werkzeug.utils import secure_filename
            import os

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        cursor.execute("""
            INSERT INTO posts (
                user_id,
                content,
                type,
                location,
                phone,
                website,
                image,
                category,
                business_mode,
                company_name,
                service_type,
                map_link,
                service_description,
                shop_name,
                shop_type,
                shop_map_link,
                shop_description,
                bio
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user_id"],
            content,
            "job/service",
            location,
            phone,
            website,
            filename,
            category,
            business_mode,
            company_name,
            service_type,
            map_link,
            service_description,
            shop_name,
            shop_type,
            shop_map_link,
            shop_description,
            bio
        ))
        db.commit()

    cursor.execute("SELECT * FROM posts WHERE type='job/service' ORDER BY created_at DESC")
    services = cursor.fetchall()

    return render_template("services.html", services=services)

@app.route('/jobs', methods=['GET', 'POST'])
def jobs():

    if 'user_id' not in session:
        return redirect('/')

    cursor = db.cursor(dictionary=True)

    # CREATE JOB POST
    if request.method == 'POST':

        recruiter_name = request.form.get('recruiter_name')
        organization_name = request.form.get('organization_name')
        job_title = request.form.get('job_title')
        experience = request.form.get('experience')
        employment_type = request.form.get('employment_type')
        job_description = request.form.get('job_description')
        hiring_type = request.form.get('hiring_type')

        walkin_date = request.form.get('walkin_date')
        walkin_start = request.form.get('walkin_start')
        walkin_end = request.form.get('walkin_end')
        walkin_location = request.form.get('walkin_location')

        apply_link = request.form.get('apply_link')

        cursor.execute("""
            INSERT INTO jobs (
                user_id,
                recruiter_name,
                organization_name,
                job_title,
                experience,
                employment_type,
                job_description,
                hiring_type,
                walkin_date,
                walkin_start,
                walkin_end,
                walkin_location,
                apply_link
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session['user_id'],
            recruiter_name,
            organization_name,
            job_title,
            experience,
            employment_type,
            job_description,
            hiring_type,
            walkin_date,
            walkin_start,
            walkin_end,
            walkin_location,
            apply_link
        ))

        db.commit()




    # GET JOBS
    cursor.execute("""
        SELECT jobs.*, users.username
        FROM jobs
        JOIN users ON jobs.user_id = users.id
        ORDER BY jobs.created_at DESC
    """)

    jobs = cursor.fetchall()

    # DAYS LIVE
    for job in jobs:
        created = job['created_at']
        today = datetime.now()
        difference = today - created
        job['days_live'] = difference.days

    return render_template('jobs.html', jobs=jobs)


@app.route('/apply_job/<int:job_id>')
def apply_job(job_id):

    if 'user_id' not in session:
        return redirect('/')

    cursor = db.cursor(dictionary=True)

    # CHECK EXISTING
    cursor.execute(
        "SELECT * FROM job_interactions WHERE user_id=%s AND job_id=%s AND interaction_type='apply'",
        (session['user_id'], job_id)
    )

    existing = cursor.fetchone()

    if not existing:

        cursor.execute(
            "INSERT INTO job_interactions (user_id, job_id, interaction_type) VALUES (%s,%s,%s)",
            (session['user_id'], job_id, 'apply')
        )

        cursor.execute(
            "UPDATE jobs SET applied_count = applied_count + 1 WHERE id=%s",
            (job_id,)
        )

        db.commit()

    return redirect('/jobs')

@app.route('/interested_job/<int:job_id>')
def interested_job(job_id):

    if 'user_id' not in session:
        return redirect('/')

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM job_interactions WHERE user_id=%s AND job_id=%s AND interaction_type='interested'",
        (session['user_id'], job_id)
    )

    existing = cursor.fetchone()

    if not existing:

        cursor.execute(
            "INSERT INTO job_interactions (user_id, job_id, interaction_type) VALUES (%s,%s,%s)",
            (session['user_id'], job_id, 'interested')
        )

        cursor.execute(
            "UPDATE jobs SET interested_count = interested_count + 1 WHERE id=%s",
            (job_id,)
        )

        db.commit()

    return redirect('/jobs')

# CREATE EVENT PAGE
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():

    if request.method == 'POST':

        user_id = session['user_id']

        event_title = request.form['event_title']
        place = request.form['place']
        google_map_link = request.form['google_map_link']

        event_date = request.form['event_date']
        event_day = request.form['event_day']
        event_time = request.form['event_time']
        duration = request.form['duration']

        about_event = request.form['about_event']

        ticket_type = request.form['ticket_type']
        ticket_price = request.form.get('ticket_price')

        if ticket_price == "":
            ticket_price = None

        total_seats = request.form['total_seats']

        # IMAGE
        image = request.files['image']

        filename = ""

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor = db.cursor()

        query = """
        INSERT INTO events
        (
            user_id,
            event_title,
            place,
            google_map_link,
            event_date,
            event_day,
            event_time,
            duration,
            about_event,
            ticket_type,
            ticket_price,
            total_seats,
            image
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            user_id,
            event_title,
            place,
            google_map_link,
            event_date,
            event_day,
            event_time,
            duration,
            about_event,
            ticket_type,
            ticket_price,
            total_seats,
            filename
        )

        cursor.execute(query, values)
        db.commit()

        return redirect('/events')

    return render_template('create_event.html')


# EVENT FEED PAGE
@app.route('/events')
def events():

    cursor = db.cursor(dictionary=True)

    query = """
    SELECT events.*, users.username, users.profile_image
    FROM events
    JOIN users ON events.user_id = users.id
    ORDER BY events.id DESC
    """

    cursor.execute(query)

    events = cursor.fetchall()

    return render_template('events.html', events=events)

if __name__ == "__main__":
    app.run(debug=True)

# Old Code ------------------------------

'''@app.route("/create_post", methods=["GET", "POST"])
def create_post():

    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)

    # USER DETAILS
    cursor.execute("""
        SELECT id, username, email, phone,
               category, location, profile_image
        FROM users
        WHERE id=%s
    """, (session["user_id"],))

    user = cursor.fetchone()

    # CREATE POST
    if request.method == "POST":

        # =========================
        # BASIC POST
        # =========================

        post_type = request.form.get("post_type")

        content = request.form.get("content")
        type_ = request.form.get("type")
        location = request.form.get("location")

        # =========================
        # JOB DETAILS
        # =========================

        organization_name = request.form.get("organization_name")
        recruiter_name = request.form.get("recruiter_name")
        job_title = request.form.get("job_title")
        experience = request.form.get("experience")
        employment_type = request.form.get("employment_type")
        job_description = request.form.get("job_description")
        hiring_type = request.form.get("hiring_type")

        walkin_date = request.form.get("walkin_date")
        walkin_start = request.form.get("walkin_start")
        walkin_end = request.form.get("walkin_end")
        walkin_location = request.form.get("walkin_location")

        apply_link = request.form.get("apply_link")

        # =========================
        # BUSINESS / SERVICE
        # =========================

        category = request.form.get("category")
        phone = request.form.get("phone")
        business_mode = request.form.get("business_mode")
        company_name = request.form.get("company_name")
        service_type = request.form.get("service_type")
        map_link = request.form.get("map_link")
        service_description = request.form.get("service_description")

        # =========================
        # SHOP
        # =========================

        shop_name = request.form.get("shop_name")
        shop_type = request.form.get("shop_type")
        shop_map_link = request.form.get("shop_map_link")
        shop_description = request.form.get("shop_description")

        # =========================
        # PUBLIC
        # =========================

        website = request.form.get("website")
        bio = request.form.get("bio")

        # =========================
        # MEDIA UPLOAD
        # =========================

        image_filename = None
        video_filename = None

        media = request.files.get("media")

        if media and media.filename != "":

            filename = secure_filename(media.filename)

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            media.save(filepath)

            # IMAGE
            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".webp")
            ):

                image_filename = filename

            # VIDEO
            elif filename.lower().endswith(
                (".mp4", ".mov", ".avi", ".mkv")
            ):

                video_filename = filename

        # =========================
        # INSERT POST
        # =========================

        cursor.execute("""
            INSERT INTO posts (

                user_id,
                post_type,

                content,
                type,
                location,

                image,
                video,

                organization_name,
                recruiter_name,
                job_title,
                experience,
                employment_type,
                job_description,
                hiring_type,
                walkin_date,
                walkin_start,
                walkin_end,
                walkin_location,
                apply_link,

                category,
                phone,
                business_mode,
                company_name,
                service_type,
                map_link,
                service_description,

                shop_name,
                shop_type,
                shop_map_link,
                shop_description,

                website,
                bio

            )

            VALUES (

                %s,%s,

                %s,%s,%s,

                %s,%s,

                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,

                %s,%s,%s,%s,%s,
                %s,%s,

                %s,%s,%s,%s,

                %s,%s

            )
        """, (

            session["user_id"],
            post_type,

            content,
            type_,
            location,

            image_filename,
            video_filename,

            organization_name,
            recruiter_name,
            job_title,
            experience,
            employment_type,
            job_description,
            hiring_type,
            walkin_date,
            walkin_start,
            walkin_end,
            walkin_location,
            apply_link,

            category,
            phone,
            business_mode,
            company_name,
            service_type,
            map_link,
            service_description,

            shop_name,
            shop_type,
            shop_map_link,
            shop_description,

            website,
            bio
        ))

        db.commit()

        return redirect("/feed")

    return render_template(
        "create_post.html",
        user=user
    )'''

'''@app.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
    if "user_id" not in session:
        return "Unauthorized", 401

    cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)",
                   (session["user_id"], post_id))
    db.commit()

    return "OK"

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    data = request.get_json()
    text = data['text']

    cursor.execute("""
        INSERT INTO comments (post_id, user_id, text)
        VALUES (%s, %s, %s)
    """, (post_id, session['user_id'], text))

    db.commit()
    return {"status": "ok"}

@app.route('/get_comments/<int:post_id>')
def get_comments(post_id):
    cursor.execute("""
        SELECT comments.text, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.post_id = %s
        ORDER BY comments.id DESC
    """, (post_id,))

    comments = cursor.fetchall()

    result = []
    for c in comments:
        result.append({
            "text": c[0],
            "username": c[1]
        })

    return jsonify(result)'''

'''@app.route("/feed")
def feed():
    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)

    # CURRENT USER
    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )
    user = cursor.fetchone()

    # NORMAL POSTS
    cursor.execute("""
        SELECT
            posts.*,
            users.username,
            users.profile_image
        FROM posts
        JOIN users
            ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """)

    posts = cursor.fetchall()

    # JOB POSTS
    cursor.execute("""
        SELECT
            jobs.*,
            users.username,
            users.profile_image
        FROM jobs
        JOIN users
            ON jobs.user_id = users.id
        ORDER BY jobs.created_at DESC
    """)

    jobs = cursor.fetchall()

    # ADD TYPE FOR JOB
    for job in jobs:
        job["type"] = "job"

        created = job["created_at"]
        today = datetime.now()

        difference = today - created

        job["days_live"] = difference.days

        # REQUIRED FOR FEED DESIGN
        job["content"] = job["job_description"]

        # EMPTY MEDIA
        job["image"] = None
        job["video"] = None

        # JOB POSTS NO LIKE
        job["likes_count"] = 0
        job["liked"] = False

    # LIKE COUNT FOR NORMAL POSTS
    for post in posts:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM likes WHERE post_id=%s",
            (post["id"],)
        )

        like_count = cursor.fetchone()

        post["likes_count"] = like_count["total"]

        cursor.execute(
            "SELECT * FROM likes WHERE user_id=%s AND post_id=%s",
            (session["user_id"], post["id"])
        )

        liked = cursor.fetchone()

        post["liked"] = True if liked else False

    # MERGE POSTS + JOBS
    all_posts = posts + jobs

    # SORT BY CREATED TIME
    all_posts = sorted(
        all_posts,
        key=lambda x: x["created_at"],
        reverse=True
    )

    cursor.close()

    return render_template(
        "feed.html",
        user=user,
        posts=all_posts
    )'''


'''@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):

    if "user_id" not in session:
        return {"success": False}

    user_id = session["user_id"]

    cursor = db.cursor(dictionary=True)

    # CHECK EXISTING LIKE
    cursor.execute(
        "SELECT * FROM likes WHERE user_id=%s AND post_id=%s",
        (user_id, post_id)
    )
    existing = cursor.fetchone()

    if existing:
        # UNLIKE
        cursor.execute(
            "DELETE FROM likes WHERE user_id=%s AND post_id=%s",
            (user_id, post_id)
        )
        liked = False

    else:
        # LIKE
        cursor.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (%s,%s)",
            (user_id, post_id)
        )
        liked = True

    db.commit()

    # NEW LIKE COUNT
    cursor.execute(
        "SELECT COUNT(*) AS total FROM likes WHERE post_id=%s",
        (post_id,)
    )
    total = cursor.fetchone()["total"]

    cursor.close()

    return {
        "success": True,
        "liked": liked,
        "likes_count": total
    }


@app.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):

    if "user_id" not in session:
        return jsonify({"success": False})

    data = request.get_json()

    text = data.get("text")

    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO comments (post_id, user_id, text)
        VALUES (%s,%s,%s)
    """, (
        post_id,
        session["user_id"],
        text
    ))

    db.commit()

    cursor.close()

    return jsonify({"success": True})

@app.route('/get_comments/<int:post_id>')
def fetch_comments(post_id):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT comments.*, users.username
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.post_id=%s
        ORDER BY comments.created_at DESC
    """, (post_id,))

    comments = cursor.fetchall()

    cursor.close()

    return jsonify(comments)'''

'''@app.route("/feed", methods=["GET", "POST"])
def feed():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        content = request.form["content"]
        type_ = request.form["type"]
        location = request.form["location"]

        image_file = request.files.get("image")
        video_file = request.files.get("video")

        image_name = None
        video_name = None


        if image_file and image_file.filename != "":
            image_name = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))


        if video_file and video_file.filename != "":
            video_name = secure_filename(video_file.filename)
            video_file.save(os.path.join(app.config["UPLOAD_FOLDER"], video_name))

        cursor.execute(
            "INSERT INTO posts (user_id, content, type, location, image, video) VALUES (%s,%s,%s,%s,%s,%s)",
            (session["user_id"], content, type_, location, image_name, video_name)
        )
        db.commit()

        return redirect("/feed")

    cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()

    return render_template("feed.html", posts=posts, user=user)

@app.route("/feed", methods=["GET", "POST"])
def feed():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        content = request.form["content"]
        type_ = request.form["type"]
        location = request.form["location"]

        cursor.execute(
            "INSERT INTO posts (user_id, content, type, location) VALUES (%s,%s,%s,%s)",
            (session["user_id"], content, type_, location)
        )
        db.commit()

        # ✅ IMPORTANT FIX
        return redirect("/feed")   # 🔥 prevents duplicate posts

    # GET request only below
    cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()

    return render_template("feed.html", posts=posts, user=user)


@app.route("/feed", methods=["GET", "POST"])
def feed():


    if "user_id" not in session:
        return redirect("/")


    if request.method == "POST":
        content = request.form["content"]
        type_ = request.form["type"]
        location = request.form["location"]

        cursor.execute(
            "INSERT INTO posts (user_id, content, type, location) VALUES (%s,%s,%s,%s)",
            (session["user_id"], content, type_, location)   # ✅ FIXED
        )
        db.commit()


    cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()


    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()


    return render_template("feed.html", posts=posts, user=user)'''

'''@app.route('/profile')
def profile():
    conn = db   # ✅ NOT db()
    cur = conn.cursor(dictionary=True)

    user_id = session['user_id']

    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    cur.execute("""
        SELECT * FROM posts 
        WHERE user_id=%s 
        ORDER BY id DESC
    """, (user_id,))
    posts = cur.fetchall()

    post_count = len(posts)

    return render_template("profile.html", user=user, posts=posts, post_count=len(posts))'''

'''@app.route("/", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect("/feed")

    error = None

    if request.method == "POST":
        action = request.form.get("action")

        email = request.form.get("email")
        password = request.form.get("password")

        # 🔐 LOGIN
        if action == "login":
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user and user[6] == password:
                session["user_id"] = user[0]
                session["username"] = user[1]
                return redirect("/feed")
            else:
                error = "Invalid email or password"

        # 🆕 REGISTER
        elif action == "register":
            username = request.form.get("username")
            phone = request.form.get("phone")
            category = request.form.get("category")
            location = request.form.get("location")

            # check if email exists
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Account already exists. Please login."
            else:
                cursor.execute(
                    "INSERT INTO users (username,email,phone,category,location,password) VALUES (%s,%s,%s,%s,%s,%s)",
                    (username, email, phone, category, location, password)
                )
                db.commit()

                session["user_id"] = cursor.lastrowid
                session["username"] = username

                return redirect("/feed")

    return render_template("login.html", error=error)'''

'''@app.route("/feed")
def feed():

    if "user_id" not in session:
        return redirect("/")

    cursor = db.cursor(dictionary=True)

    # Logged-in user (top right profile)
    cursor.execute("SELECT * FROM users WHERE id=%s", (session["user_id"],))
    user = cursor.fetchone()

    cursor.execute("""
        SELECT posts.*, users.username, users.profile_image
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """)
    posts = cursor.fetchall()

    return render_template("feed.html", user=user, posts=posts)'''