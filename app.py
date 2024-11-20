from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    mobile_number = request.form.get("mobileNumber")
    password = request.form.get("password")

    if not mobile_number or not password:
        return render_template("login.html", error="Both fields are required.")  # Re-render login page with error

    # Dummy authentication
    if mobile_number == "0123456789" and password == "password":
        return redirect(url_for("main_page"))  # Redirect to the dashboard
    else:
        return render_template("login.html", error="Invalid credentials.")  # Re-render login page with error


@app.route("/app/main")
def main_page():
    return render_template("main.html", user={"name": "Patanjali Chaturvedula", "email": "patanjali2@gmail.com", "phone": "8885134571"})

# Route for the profile page
@app.route("/profile")
def profile():
    user_data = {
        "name": "Patanjali Chaturvedula",
        "email": "patanjali2@gmail.com",
        "phone": "8885134571"
    }
    return jsonify(user_data)

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
