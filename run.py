from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=7678)  # Change 8080 to any port you prefer
