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

@app.route('/main_page')
def main_page():
    if "user" not in session:
        return redirect(url_for("login"))  # Redirect to login if not logged in
    return render_template("main.html", user=session["user"])

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

@app.route("/logout")
def logout():
    # Clear the user session
    session.clear()
    # Redirect to the login page
    return redirect(url_for("home"))


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
        "Hashed Password": hashed_password.decode('utf-8'), # Store as a readable string
        "Vehicles": data.get("vehicles", [])  # Defaults to an empty list if no vehicles are provided
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


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            # Load the Excel file
            df = pd.read_excel(EXCEL_FILE)

            # Find the user's row based on email
            email = session["user"]["email"]
            user_index = df[df["Official Email"] == email].index[0]

            # Update the user's details
            df.at[user_index, "Name"] = request.form.get("name")
            df.at[user_index, "Gender"] = request.form.get("gender")
            df.at[user_index, "Date of Birth"] = request.form.get("dob")
            df.at[user_index, "Role"] = request.form.get("role")
            df.at[user_index, "Mobile Number"] = request.form.get("phone")
            df.at[user_index, "Emergency Contact"] = request.form.get("emergencyContact")

            # Save the updated data to the Excel file
            df.to_excel(EXCEL_FILE, index=False)

            # Update the session with the new data
            session["user"] = {
                "name": request.form.get("name"),
                "gender": request.form.get("gender"),
                "dob": request.form.get("dob"),
                "role": request.form.get("role"),
                "phone": request.form.get("phone"),
                "emergencyContact": request.form.get("emergencyContact"),
                "email": email
            }

            return redirect("/profile")

        except PermissionError:
            error_message = "File is open or permission denied. Please close the file and try again."
            return render_template("profile.html", user=session["user"], error=error_message)

        except Exception as e:
            error_message = f"An error occurred: {e}"
            return render_template("profile.html", user=session["user"], error=error_message)

    # GET request: Fetch user details from the Excel file
    try:
        df = pd.read_excel(EXCEL_FILE)
        email = session["user"]["email"]
        user = df[df["Official Email"] == email].to_dict(orient="records")[0]

        return render_template("profile.html", user=user)

    except FileNotFoundError:
        return render_template("profile.html", error="Data file not found. Please try again later.")
    except Exception as e:
        return render_template("profile.html", error=f"An error occurred: {e}")

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
