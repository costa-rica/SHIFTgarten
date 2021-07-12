from dmrApp import create_app
# from dmrApp import manager

app = create_app()

if __name__ == '__main__':
    # manager.run()
    app.run(debug=True)
