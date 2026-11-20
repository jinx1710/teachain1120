
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# 1. APPLICATION CONFIGURATION
# ==========================================

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY is not configured")

JWT_EXPIRATION_HOURS = 1


# ==========================================
# 2. DATABASE CONNECTION
# ==========================================

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "database"),
        database=os.getenv("DB_NAME", "tea_chain"),
        user=os.getenv("DB_USER", "tea_admin"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )


# ==========================================
# 3. CREATE JWT TOKEN
# ==========================================

def create_access_token(user):
    payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "branch_id": user["branch_id"],
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=JWT_EXPIRATION_HOURS)
    }

    return jwt.encode(
        payload,
        app.config["JWT_SECRET_KEY"],
        algorithm="HS256"
    )


# ==========================================
# 4. TOKEN AUTHENTICATION
# ==========================================

def token_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Authorization token is required"
            }), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"]
            )

            g.current_user = payload

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# 5. CREATE TEST ACCOUNTS
# ==========================================

@app.route("/api/setup", methods=["POST"])
def setup_users():
    conn = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        accounts = [
            ("owner", "Owner", "owner", None, "Owner123!"),
            ("manager_1", "Manager Taoyuan", "manager", 1, "Manager123!"),
            ("manager_2", "Manager Taipei", "manager", 2, "Manager123!"),
            ("manager_3", "Manager Taichung", "manager", 3, "Manager123!"),
            ("manager_4", "Manager Tainan", "manager", 4, "Manager123!")
        ]

        for username, full_name, role, branch_id, password in accounts:
            password_hash = generate_password_hash(password)

            cur.execute("""
                INSERT INTO users
                    (username, password_hash, full_name, role, branch_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (
                username,
                password_hash,
                full_name,
                role,
                branch_id
            ))

        conn.commit()
        cur.close()

        return jsonify({
            "message": "Test accounts created successfully"
        }), 200

    except Exception:
        app.logger.exception("Setup failed")

        if conn:
            conn.rollback()

        return jsonify({
            "error": "Unable to create test accounts"
        }), 500

    finally:
        if conn:
            conn.close()


# ==========================================
# 6. LOGIN API
# ==========================================

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    conn = None

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                user_id,
                username,
                password_hash,
                full_name,
                role,
                branch_id
            FROM users
            WHERE username = %s
              AND is_active = TRUE
        """, (username,))

        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({
                "error": "Invalid username or password"
            }), 401

        if not check_password_hash(
            user["password_hash"],
            password
        ):
            return jsonify({
                "error": "Invalid username or password"
            }), 401

        user.pop("password_hash")

        access_token = create_access_token(user)

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "user": user
        }), 200

    except Exception:
        app.logger.exception("Login failed")

        return jsonify({
            "error": "Internal server error"
        }), 500

    finally:
        if conn:
            conn.close()


# ==========================================
# 7. HEALTH CHECK API
# ==========================================

@app.route("/api/health", methods=["GET"])
def health():
    try:
        conn = get_db_connection()
        conn.close()

        return jsonify({
            "status": "OK",
            "database": "connected"
        }), 200

    except Exception:
        app.logger.exception("Health check failed")

        return jsonify({
            "status": "ERROR",
            "database": "disconnected"
        }), 500


# ==========================================
# 8. CURRENT USER API
# ==========================================

@app.route("/api/me", methods=["GET"])
@token_required
def get_current_user():
    return jsonify({
        "message": "Token is valid",
        "user": g.current_user
    }), 200


# ==========================================
# 9. START APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
