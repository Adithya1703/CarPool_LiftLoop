from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    mobile_number = request.form.get("mobileNumber")
    password = request.form.get("password")

    if not mobile_number or not password:
        return jsonify({"error": "Both fields are required"}), 400

    # Dummy authentication
    if mobile_number == "1234567890" and password == "password":
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(debug=True)
