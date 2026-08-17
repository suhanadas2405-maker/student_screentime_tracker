from flask import Flask, jsonify, request, render_template
from database import initialize_database, get_connection
from datetime import date


# =====================================================
# FLASK APPLICATION
# =====================================================

app = Flask(
    __name__,
    template_folder="dashboard/templates",
    static_folder="dashboard/static"
)

# Initialize database
initialize_database()


# =====================================================
# SUPPORTED APPS
# =====================================================

SUPPORTED_APPS = {
    "YouTube": "com.google.android.youtube",
    "Instagram": "com.instagram.android",
    "Chrome": "com.android.chrome",
    "Facebook": "com.facebook.katana",
    "Google": "com.google.android.googlequicksearchbox",
    "ChatGPT": "com.openai.chatgpt",
    "Snapchat": "com.snapchat.android",
    "WhatsApp": "com.whatsapp",
    "Threads": "com.instagram.barcelona"
}


# =====================================================
# HOME / DASHBOARD
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# GET SUPPORTED APPS
# =====================================================

@app.route("/api/apps", methods=["GET"])
def get_apps():

    return jsonify([
        {
            "app_name": app_name,
            "package_name": package_name
        }

        for app_name, package_name
        in SUPPORTED_APPS.items()
    ])


# =====================================================
# GET ALL STUDENTS
# =====================================================

@app.route("/api/students", methods=["GET"])
def get_students():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        ORDER BY id
    """)

    students = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(student)
        for student in students
    ])


# =====================================================
# ADD NEW STUDENT
# =====================================================

@app.route("/api/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")

    if not name or not email:

        return jsonify({
            "error": "Name and email are required"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO students
            (name, email)
            VALUES (?, ?)
        """, (name, email))

        connection.commit()

        student_id = cursor.lastrowid

        connection.close()

        return jsonify({
            "message": "Student added successfully",
            "student_id": student_id
        }), 201

    except Exception as e:

        connection.close()

        return jsonify({
            "error": str(e)
        }), 400


# =====================================================
# ADD TRACKED APP
# =====================================================

@app.route("/api/tracked-apps", methods=["POST"])
def add_tracked_app():

    data = request.get_json(silent=True) or {}

    student_id = data.get("student_id")
    app_name = data.get("app_name")
    package_name = data.get("package_name")

    if not student_id or not app_name or not package_name:

        return jsonify({
            "error": "Missing required fields"
        }), 400

    # Make sure the app is one of the supported apps
    if (
        app_name not in SUPPORTED_APPS
        or SUPPORTED_APPS[app_name] != package_name
    ):

        return jsonify({
            "error": "This app is not supported"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO tracked_apps
            (
                student_id,
                app_name,
                package_name,
                enabled
            )

            VALUES (?, ?, ?, 1)

            ON CONFLICT(student_id, package_name)
            DO UPDATE SET enabled = 1
        """, (
            student_id,
            app_name,
            package_name
        ))

        connection.commit()
        connection.close()

        return jsonify({
            "message": "App added successfully"
        }), 201

    except Exception as e:

        connection.close()

        return jsonify({
            "error": str(e)
        }), 400


# =====================================================
# GET TRACKED APPS
# =====================================================

@app.route(
    "/api/tracked-apps/<int:student_id>",
    methods=["GET"]
)
def get_tracked_apps(student_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM tracked_apps
        WHERE student_id = ?
        AND enabled = 1
        ORDER BY app_name
    """, (student_id,))

    apps = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(app)
        for app in apps
    ])


# =====================================================
# SAVE DAILY LIMIT
# =====================================================

@app.route("/api/limits", methods=["POST"])
def save_limit():

    data = request.get_json(silent=True) or {}

    student_id = data.get("student_id")
    package_name = data.get("package_name")
    daily_limit = data.get("daily_limit_minutes")

    if (
        not student_id
        or not package_name
        or daily_limit is None
    ):

        return jsonify({
            "error": "Required fields are missing"
        }), 400

    try:

        daily_limit = int(daily_limit)

    except (ValueError, TypeError):

        return jsonify({
            "error": "Daily limit must be a number"
        }), 400

    if daily_limit <= 0:

        return jsonify({
            "error": "Daily limit must be greater than 0"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO app_limits
            (
                student_id,
                package_name,
                daily_limit_minutes,
                warnings_enabled,
                warning_percentage
            )

            VALUES (?, ?, ?, 1, 80)

            ON CONFLICT(student_id, package_name)

            DO UPDATE SET

                daily_limit_minutes =
                    excluded.daily_limit_minutes,

                warnings_enabled = 1,

                warning_percentage = 80
        """, (
            student_id,
            package_name,
            daily_limit
        ))

        connection.commit()
        connection.close()

        return jsonify({
            "message": "Daily limit saved"
        })

    except Exception as e:

        connection.close()

        return jsonify({
            "error": str(e)
        }), 400


# =====================================================
# RECORD DAILY USAGE
# =====================================================

@app.route("/api/usage", methods=["POST"])
def record_usage():

    data = request.get_json(silent=True) or {}

    student_id = data.get("student_id")
    package_name = data.get("package_name")
    usage_minutes = data.get("usage_minutes")

    if (
        not student_id
        or not package_name
        or usage_minutes is None
    ):

        return jsonify({
            "error": "Required fields are missing"
        }), 400

    try:

        usage_minutes = int(usage_minutes)

    except (ValueError, TypeError):

        return jsonify({
            "error": "Usage must be a number"
        }), 400

    if usage_minutes < 0:

        return jsonify({
            "error": "Usage cannot be negative"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    # Find tracked app
    cursor.execute("""
        SELECT app_name
        FROM tracked_apps
        WHERE student_id = ?
        AND package_name = ?
        AND enabled = 1
    """, (
        student_id,
        package_name
    ))

    app = cursor.fetchone()

    if not app:

        connection.close()

        return jsonify({
            "error": "App is not selected for tracking"
        }), 400

    app_name = app["app_name"]

    # Get daily limit
    cursor.execute("""
        SELECT
            daily_limit_minutes,
            warning_percentage
        FROM app_limits
        WHERE student_id = ?
        AND package_name = ?
    """, (
        student_id,
        package_name
    ))

    limit_row = cursor.fetchone()

    daily_limit = None
    warning_sent = 0
    limit_reached = 0
    limit_exceeded = 0
    exceeded_by = 0

    if limit_row:

        daily_limit = limit_row[
            "daily_limit_minutes"
        ]

        warning_percentage = limit_row[
            "warning_percentage"
        ]

        warning_threshold = (
            daily_limit *
            warning_percentage /
            100
        )

        # 80% warning
        if usage_minutes >= warning_threshold:

            warning_sent = 1

        # Limit reached
        if usage_minutes >= daily_limit:

            limit_reached = 1

        # Limit exceeded
        if usage_minutes > daily_limit:

            limit_exceeded = 1

            exceeded_by = (
                usage_minutes -
                daily_limit
            )

    today = date.today().isoformat()

    cursor.execute("""
        INSERT INTO daily_usage
        (
            student_id,
            usage_date,
            package_name,
            app_name,
            usage_minutes,
            daily_limit_minutes,
            warning_sent,
            limit_reached,
            limit_exceeded,
            exceeded_by_minutes
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(
            student_id,
            usage_date,
            package_name
        )

        DO UPDATE SET

            usage_minutes =
                excluded.usage_minutes,

            daily_limit_minutes =
                excluded.daily_limit_minutes,

            warning_sent =
                excluded.warning_sent,

            limit_reached =
                excluded.limit_reached,

            limit_exceeded =
                excluded.limit_exceeded,

            exceeded_by_minutes =
                excluded.exceeded_by_minutes
    """, (
        student_id,
        today,
        package_name,
        app_name,
        usage_minutes,
        daily_limit,
        warning_sent,
        limit_reached,
        limit_exceeded,
        exceeded_by
    ))

    connection.commit()
    connection.close()

    warning = None

    if limit_exceeded:

        warning = (
            f"{app_name} exceeded the daily "
            f"limit by {exceeded_by} minutes."
        )

    elif warning_sent:

        warning = (
            f"{app_name} has reached 80% "
            f"of its daily limit."
        )

    return jsonify({

        "message":
            "Usage recorded successfully",

        "app_name":
            app_name,

        "usage_minutes":
            usage_minutes,

        "daily_limit_minutes":
            daily_limit,

        "warning":
            warning,

        "limit_reached":
            bool(limit_reached),

        "limit_exceeded":
            bool(limit_exceeded)

    })


# =====================================================
# GET TODAY'S USAGE
# =====================================================

@app.route(
    "/api/usage/<int:student_id>",
    methods=["GET"]
)
def get_usage(student_id):

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM daily_usage
        WHERE student_id = ?
        AND usage_date = ?
        ORDER BY app_name
    """, (
        student_id,
        today
    ))

    records = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(record)
        for record in records
    ])


# =====================================================
# GET USAGE HISTORY
# =====================================================

@app.route(
    "/api/history/<int:student_id>",
    methods=["GET"]
)
def get_history(student_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM daily_usage
        WHERE student_id = ?
        ORDER BY usage_date DESC, app_name
    """, (student_id,))

    records = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(record)
        for record in records
    ])


# =====================================================
# DASHBOARD SUMMARY
# =====================================================

@app.route(
    "/api/summary/<int:student_id>",
    methods=["GET"]
)
def get_summary(student_id):

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    # Total usage
    cursor.execute("""
        SELECT
            COALESCE(
                SUM(usage_minutes),
                0
            ) AS total_usage

        FROM daily_usage

        WHERE student_id = ?
        AND usage_date = ?
    """, (
        student_id,
        today
    ))

    total_usage = cursor.fetchone()[
        "total_usage"
    ]

    # Number of tracked apps
    cursor.execute("""
        SELECT
            COUNT(*) AS count

        FROM tracked_apps

        WHERE student_id = ?
        AND enabled = 1
    """, (student_id,))

    apps_tracked = cursor.fetchone()[
        "count"
    ]

    # Number of apps over limit
    cursor.execute("""
        SELECT
            COUNT(*) AS count

        FROM daily_usage

        WHERE student_id = ?
        AND usage_date = ?
        AND limit_exceeded = 1
    """, (
        student_id,
        today
    ))

    apps_exceeded = cursor.fetchone()[
        "count"
    ]

    connection.close()

    return jsonify({

        "total_usage_minutes":
            total_usage,

        "apps_tracked":
            apps_tracked,

        "apps_exceeded":
            apps_exceeded
    })


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )