from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import os
import bcrypt

app = Flask(__name__)
# Path to Excel file
EXCEL_FILE = "users_data.xlsx"
app.secret_key = "0123456789"

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    # Get ZF email ID and password from form
    zf_email = request.form.get("email")
    password = request.form.get("password")

    # Validate inputs
    if not zf_email or not password:
        return render_template("login.html", error="Both fields are required.")  # Re-render login page with error

    try:
        # Load user data from the Excel file
        df = pd.read_excel(EXCEL_FILE)

        # Search for the user by ZF email ID
        user = df[df["Official Email"] == zf_email].to_dict(orient="records")
        if not user:
            return render_template("login.html", error="Invalid credentials.")  # Re-render login page with error

        user = user[0]  # Extract the first match

        # Verify the password
        if not bcrypt.checkpw(password.encode('utf-8'), user["Hashed Password"].encode('utf-8')):
            return render_template("login.html", error="Invalid credentials.")  # Re-render login page with error

        # Store user details in the session
        session["user"] = {
            "name": user["Name"],
            "email": user["Official Email"],
            "phone": user["Mobile Number"],
        }

        # Redirect to the main page after successful login
        return redirect(url_for("main_page"))

    except FileNotFoundError:
        return render_template("login.html", error="User data not found. Please sign up first.")  # Re-render login page with error

    except Exception as e:
        return render_template("login.html", error=f"An error occurred: {str(e)}")  # Re-render login page with error

@app.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Validate required fields
    required_fields = [
        "name", "gender", "dob", "password", "role",
        "mobileNumber", "emergencyContact", "officialEmail"
    ]

    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"Missing required field: {field}"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt())
    user_data = {
        "Name": data["name"],
        "Gender": data["gender"],
        "Date of Birth": data["dob"],
        "Role": data["role"],
        "Mobile Number": data["mobileNumber"],
        "Emergency Contact": data["emergencyContact"],
        "Official Email": data["officialEmail"],
        "Hashed Password": hashed_password.decode('utf-8')  # Store as a readable string
    }

    # Save to Excel
    if not os.path.exists(EXCEL_FILE):
        # Create a new Excel file and save data
        df = pd.DataFrame([user_data])
        df.to_excel(EXCEL_FILE, index=False)
    else:
        # Append to the existing Excel file
        existing_data = pd.read_excel(EXCEL_FILE)
        updated_data = pd.concat([existing_data, pd.DataFrame([user_data])], ignore_index=True)
        updated_data.to_excel(EXCEL_FILE, index=False)

    return jsonify({"message": "Signup successful and data saved to Excel!"}), 200


@app.route("/app/main")
def main_page():
    # Ensure the user is logged in
    if "user" not in session:
        return redirect(url_for("home"))

    # Pass the logged-in user data to the main.html template
    return render_template("main.html", user=session["user"])


@app.route("/profile")
def profile():
    # Ensure the user is logged in
    if "user" not in session:
        return jsonify({"message": "User not logged in."}), 401

    # Return the logged-in user's data as JSON
    return jsonify(session["user"])


# Route for finding a ride
@app.route("/find_ride", methods=["GET", "POST"])
def find_ride():
    if request.method == "POST":
        search_query = request.form.get("search")
        # For now, return the search query as a placeholder
        return jsonify({"message": f"Search results for {search_query}"})
    return render_template("find_ride.html")

@app.route("/post_ride", methods=["GET", "POST"])
def post_ride():
    if request.method == "POST":
        source = request.form.get("source")
        destination = request.form.get("destination")
        # Add logic to store ride in the database
        return jsonify({"message": "Ride posted successfully!"})
    return render_template("post_ride.html")

if __name__ == "__main__":
    app.run(debug=True)
