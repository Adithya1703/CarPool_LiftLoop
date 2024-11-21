from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import pandas as pd
import os
import bcrypt
import json

app = Flask(__name__)
# Path to Excel file
EXCEL_FILE = "users_data.xlsx"
app.secret_key = "0123456789"
ADMIN_PASSWORD = "admin123"
ride_excel = "ride_excel.xlsx"
rides =[]

@app.route("/")
def home():
    return render_template("login.html")

@app.route('/main_page')
def main_page():
    if "user" not in session:
        return redirect(url_for("login"))

    logged_in_user = session["user"]["name"]

    try:
        main_pd = pd.read_excel(ride_excel)

        # Ensure `via_routes` is correctly parsed as a list
        def parse_via_routes(value):
            if pd.isna(value):
                return []  # Return empty list if the value is NaN
            if isinstance(value, str):
                try:
                    # Attempt to parse as JSON
                    return json.loads(value)
                except json.JSONDecodeError:
                    # If JSON decoding fails, return as a single-item list
                    return [value.strip()]
            return value  # Return as is for already valid lists

        main_pd["via_routes"] = main_pd["via_routes"].apply(parse_via_routes)

        # Filter rides for the logged-in user
        user_rides = main_pd[main_pd["ride_provider"] == logged_in_user].to_dict(orient="records")

    except FileNotFoundError:
        user_rides = []

    return render_template("main.html", user=session["user"], rides=user_rides)


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
    # Ensure the user is logged in
    if "user" not in session:
        return redirect("/")

    try:
        # Load the Excel file
        df = pd.read_excel(EXCEL_FILE)
        email = session["user"]["email"]

        if request.method == "POST":
            # Find the user's row in the Excel file
            user_index = df[df["Official Email"] == email].index[0]

            # Ensure Mobile Number column is treated as a string
            if "Mobile Number" in df.columns:
                df["Mobile Number"] = df["Mobile Number"].astype(str)

            # Update user details
            df.at[user_index, "Name"] = request.form.get("name")
            df.at[user_index, "Gender"] = request.form.get("gender")
            df.at[user_index, "Date of Birth"] = request.form.get("dob")
            df.at[user_index, "Role"] = request.form.get("role")
            df.at[user_index, "Mobile Number"] = request.form.get("phone")
            df.at[user_index, "Emergency Contact"] = request.form.get("emergencyContact")

            # Handle vehicles
            vehicle_names = request.form.getlist("vehicleName[]")
            vehicle_types = request.form.getlist("vehicleType[]")
            number_plates = request.form.getlist("numberPlate[]")
            vehicles = [{"name": n, "type": t, "numberPlate": p} for n, t, p in zip(vehicle_names, vehicle_types, number_plates)]
            df.at[user_index, "Vehicles"] = str(vehicles)  # Store as a JSON string

            # Save changes to the Excel file
            df.to_excel(EXCEL_FILE, index=False)

            # Update session data
            session["user"] = {
                "Name": request.form.get("name"),
                "Gender": request.form.get("gender"),
                "Date of Birth": request.form.get("dob"),
                "Role": request.form.get("role"),
                "Mobile Number": request.form.get("phone"),
                "Emergency Contact": request.form.get("emergencyContact"),
                "Official Email": email,
                "Vehicles": vehicles,
            }

            # Flash success message
            flash("Your profile has been successfully updated!", "success")
            return redirect("/profile")  # Redirect after saving changes

        # For GET requests: Retrieve user details
        user = df[df["Official Email"] == email].to_dict(orient="records")[0]

        # Parse vehicles from JSON string
        if "Vehicles" in user and isinstance(user["Vehicles"], str):
            user["Vehicles"] = eval(user["Vehicles"])  # Convert JSON string to list

        return render_template("profile.html", user=user)

    except KeyError:
        # Handle missing session email
        return redirect("/")
    except FileNotFoundError:
        flash("Data file not found. Please try again later.", "error")
        return render_template("profile.html")
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return render_template("profile.html")


@app.route("/validate_admin", methods=["POST"])
def validate_admin():
    data = request.get_json()
    if data["password"] == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False})


@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "user" not in session:
        return redirect("/")  # Redirect to login if user is not logged in

    if request.method == "POST":
        # Handle profile and ride deletion
        selected_emails = request.form.getlist("selected_profiles")  # Selected profiles for deletion
        selected_rides = request.form.getlist("selected_rides")  # Selected rides for deletion

        # Delete profiles
        if selected_emails:
            try:
                # Load the Excel file
                df = pd.read_excel(EXCEL_FILE)

                # Remove rows with the selected emails
                df = df[~df["Official Email"].isin(selected_emails)]

                # Save the updated data back to the Excel file
                df.to_excel(EXCEL_FILE, index=False)

                flash("Selected profiles have been deleted successfully!", "success")
            except Exception as e:
                flash(f"An error occurred while deleting profiles: {e}", "danger")

        # Delete rides
        if selected_rides:
            try:
                # Load the ride Excel file
                ride_df = pd.read_excel(ride_excel)

                # Remove rows with the selected rides (use a unique identifier if available)
                ride_df = ride_df[~ride_df.index.isin(map(int, selected_rides))]

                # Save the updated data back to the ride Excel file
                ride_df.to_excel(ride_excel, index=False)

                flash("Selected rides have been deleted successfully!", "success")
            except Exception as e:
                flash(f"An error occurred while deleting rides: {e}", "danger")

    # Load profile data
    try:
        profile_df = pd.read_excel(EXCEL_FILE)
        users_data = profile_df.to_dict(orient="records")

        # Convert vehicle strings back to dictionaries (if applicable)
        for user in users_data:
            if isinstance(user.get("Vehicles"), str):
                try:
                    user["vehicles"] = eval(user["Vehicles"])  # Convert JSON string to list
                except Exception:
                    user["vehicles"] = None
            else:
                user["vehicles"] = None
    except Exception as e:
        users_data = []
        flash(f"Error loading profiles: {e}", "danger")

    # Load ride data
    try:
        ride_df = pd.read_excel(ride_excel)
        rides_data = ride_df.to_dict(orient="records")
    except Exception as e:
        rides_data = []
        flash(f"Error loading rides: {e}", "danger")

    return render_template("admin_dashboard.html", users=users_data, rides=rides_data)


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
    if request.method == 'POST':
        # Retrieve form data
        df = pd.read_excel(EXCEL_FILE)
        vehicle_type = request.form.get('vehicle_type')
        start_location = request.form.get('start_location')
        destination = request.form.get('destination')
        via_routes = request.form.getlist('via_routes')
        preferred_start_time = f"{request.form.get('hour')}:{request.form.get('minute')}"
        seats_available = request.form.get('seats_available')
        ride_provider = session["user"]["name"]

        # Create a ride entry
        ride = {
            'vehicle_type': vehicle_type,
            'start_location': start_location,
            'destination': destination,
            'via_routes': [route for route in via_routes if route.strip()],
            'preferred_start_time': preferred_start_time,
            'seats_available': seats_available,
            'ride_provider': ride_provider
        }

        # Save the ride in the mock database
        rides.append(ride)
        try:
            # Check if the Excel file exists
            try:
                main_pd = pd.read_excel(ride_excel)
            except FileNotFoundError:
                main_pd = pd.DataFrame()  # Create an empty DataFrame if file doesn't exist

            # Convert current ride to DataFrame and append it
            new_ride = pd.DataFrame([ride])  # Convert the single ride dict to DataFrame
            main_pd = pd.concat([main_pd, new_ride], ignore_index=True)

            # Save updated data to Excel
            main_pd.to_excel(ride_excel, index=False)

        except Exception as e:
            return f"An error occurred while saving ride details: {str(e)}"

        return redirect(url_for('main_page'))
        return redirect(url_for('admin_dashboard'))

    return render_template('post_ride.html')


if __name__ == "__main__":
    app.run(debug=True)
