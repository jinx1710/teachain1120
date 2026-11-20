import os
from decimal import Decimal
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-secret-to-a-long-random-value")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60 * 12
CORS(app)
JWTManager(app)

def conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST","localhost"), dbname=os.getenv("DB_NAME","tea_chain"),
        user=os.getenv("DB_USER","tea_admin"), password=os.getenv("DB_PASSWORD","tea_password_123"),
        port=os.getenv("DB_PORT","5432")
    )

def query(sql, params=(), one=False, commit=False):
    with conn() as c:
        with c.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            data = cur.fetchone() if one else (cur.fetchall() if cur.description else None)
            if commit: c.commit()
            return data

def seed_users():
    defaults = [
        ("owner","Owner123!","System Owner","owner",None),
        ("manager1","manager123","Branch Manager 1","manager",1),
        ("manager2","manager123","Branch Manager 2","manager",2),
        ("manager3","manager123","Branch Manager 3","manager",3),
        ("manager4","manager123","Branch Manager 4","manager",4),
        ("manager5","manager123","Branch Manager 5","manager",5),
        ("manager6","manager123","Branch Manager 6","manager",6),
        ("staff1","staff123","Staff Member","staff",1),
    ]
    with conn() as c:
        with c.cursor() as cur:
            for username,password,name,role,branch in defaults:
                cur.execute("""INSERT INTO users(username,password_hash,full_name,role,branch_id)
                    VALUES(%s,%s,%s,%s,%s) ON CONFLICT(username) DO NOTHING""",
                    (username,generate_password_hash(password),name,role,branch))
        c.commit()

def money(v):
    return float(v or 0)

@app.get("/api/health")
def health():
    try:
        query("SELECT 1", one=True)
        return jsonify(status="OK", database="connected")
    except Exception as e:
        return jsonify(status="ERROR", message=str(e)), 500

@app.post("/api/login")
def login():
    body=request.get_json(silent=True) or {}
    user=query("SELECT * FROM users WHERE username=%s",(body.get("username",""),),one=True)
    if not user or not check_password_hash(user["password_hash"],body.get("password","")):
        return jsonify(message="Tên đăng nhập hoặc mật khẩu không đúng"),401
    identity={"id":user["id"],"username":user["username"],"name":user["full_name"],
              "role":user["role"],"branch_id":user["branch_id"]}
    token=create_access_token(identity=str(user["id"]), additional_claims={"user": identity})
    return jsonify(token=token,user=identity)

def current_user():
    return get_jwt()["user"]

@app.get("/api/me")
@jwt_required()
def me():
    return jsonify(user=current_user())

@app.get("/api/branches")
@jwt_required()
def branches():
    rows=query("""SELECT b.id,b.name,b.city,b.description,
      COALESCE(SUM(o.total),0) AS revenue, COUNT(o.id) AS order_count
      FROM branches b LEFT JOIN orders o ON o.branch_id=b.id
      GROUP BY b.id ORDER BY b.id""")
    for r in rows: r["revenue"]=money(r["revenue"])
    return jsonify(branches=rows)

@app.get("/api/products")
@jwt_required()
def products():
    branch_id=request.args.get("branch_id",type=int)
    if branch_id:
        rows=query("""SELECT * FROM products WHERE active=TRUE AND
          (is_shared=TRUE OR branch_id=%s) ORDER BY is_shared DESC,id""",(branch_id,))
    else:
        rows=query("SELECT * FROM products WHERE active=TRUE ORDER BY is_shared DESC,id")
    for r in rows: r["price"]=money(r["price"])
    return jsonify(products=rows)

@app.post("/api/orders")
@jwt_required()
def create_order():
    user=current_user()
    body=request.get_json(silent=True) or {}
    branch_id=body.get("branch_id")
    items=body.get("items",[])
    if not branch_id or not items:
        return jsonify(message="Vui lòng chọn chi nhánh và món"),400
    if user["role"]=="staff" and user["branch_id"]!=branch_id:
        return jsonify(message="Bạn không có quyền tạo đơn tại chi nhánh này"),403
    try:
        with conn() as c:
            with c.cursor(cursor_factory=RealDictCursor) as cur:
                total=Decimal("0")
                normalized=[]
                for item in items:
                    cur.execute("""SELECT id,name,price FROM products WHERE id=%s AND active=TRUE
                      AND (is_shared=TRUE OR branch_id=%s)""",(item.get("product_id"),branch_id))
                    p=cur.fetchone()
                    qty=int(item.get("quantity",0))
                    if not p or qty<1: raise ValueError("Sản phẩm hoặc số lượng không hợp lệ")
                    subtotal=p["price"]*qty
                    total+=subtotal
                    normalized.append((p,qty,subtotal))
                cur.execute("INSERT INTO orders(branch_id,user_id,total) VALUES(%s,%s,%s) RETURNING id",
                            (branch_id,user["id"],total))
                order_id=cur.fetchone()["id"]
                for p,qty,subtotal in normalized:
                    cur.execute("""INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,subtotal)
                      VALUES(%s,%s,%s,%s,%s,%s)""",(order_id,p["id"],p["name"],qty,p["price"],subtotal))
            c.commit()
        return jsonify(message="Đã tạo đơn hàng",order_id=order_id,total=money(total)),201
    except ValueError as e:
        return jsonify(message=str(e)),400

@app.get("/api/reports")
@jwt_required()
def reports():
    user=current_user()
    # Theo đề bài, Owner và Manager được xem thống kê của toàn bộ chi nhánh.
    rows=query("""SELECT b.id,b.name,b.city,COALESCE(SUM(o.total),0) revenue,
      COUNT(o.id) order_count FROM branches b LEFT JOIN orders o ON o.branch_id=b.id
      GROUP BY b.id ORDER BY b.id""")
    for r in rows: r["revenue"]=money(r["revenue"])
    total=sum(r["revenue"] for r in rows)
    return jsonify(branches=rows,total_revenue=total,total_orders=sum(r["order_count"] for r in rows))

@app.get("/api/orders")
@jwt_required()
def orders():
    branch_id=request.args.get("branch_id",type=int)
    sql="""SELECT o.id,o.branch_id,b.name branch_name,o.total,o.status,o.created_at,
      u.full_name created_by FROM orders o JOIN branches b ON b.id=o.branch_id
      LEFT JOIN users u ON u.id=o.user_id"""
    params=()
    if branch_id:
        sql+=" WHERE o.branch_id=%s"; params=(branch_id,)
    sql+=" ORDER BY o.created_at DESC LIMIT 100"
    rows=query(sql,params)
    for r in rows: r["total"]=money(r["total"]); r["created_at"]=r["created_at"].isoformat()
    return jsonify(orders=rows)

@app.post("/api/products")
@jwt_required()
def add_product():
    user=current_user()
    if user["role"] not in ("owner","manager"):
        return jsonify(message="Không đủ quyền"),403
    body=request.get_json(silent=True) or {}
    branch_id=body.get("branch_id")
    if user["role"]=="manager" and user["branch_id"]!=branch_id:
        return jsonify(message="Manager chỉ được thêm món cho chi nhánh của mình"),403
    if not body.get("name") or not body.get("price") or not branch_id:
        return jsonify(message="Thiếu tên món, giá hoặc chi nhánh"),400
    row=query("""INSERT INTO products(name,description,price,branch_id,is_shared)
      VALUES(%s,%s,%s,%s,FALSE) RETURNING id""",
      (body["name"],body.get("description",""),body["price"],branch_id),one=True,commit=True)
    return jsonify(message="Đã thêm món riêng",id=row["id"]),201

if __name__=="__main__":
    import time
    for _ in range(30):
        try:
            query("SELECT 1",one=True); break
        except Exception: time.sleep(2)
    seed_users()
    app.run(host="0.0.0.0",port=5000)
