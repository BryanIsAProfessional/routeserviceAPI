from app import app

online = False

if __name__ == "__main__":
    if(online):
        app.run(host= '0.0.0.0')
    else:
        app.run(debug=True)