from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy import desc
import requests


MOVIE_API_KEY = YOUR_API_KEY HERE
MOVIE_API_SEARCH = "https://api.themoviedb.org/3/search/movie"
MOVIE_API_SELECT = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500/"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new-books-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(200), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.title


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


db.create_all()

all_movies_list = []

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    for movie in all_movies:
        print(movie.ranking)
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    """
    This function edits the movie
    :return:
    """
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_to_update = Movie.query.get(movie_id)

    if form.validate_on_submit():
        # movie_id = request.args.get("id")
        # print(movie_id)
        # movie_to_update = Movie.query.get(movie_id)
        # # print(movie_to_update)
        movie_to_update.rating = float(form.rating.data)
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie_to_update, form=form)


@app.route("/delete")
def delete():
    """
    This function deletes the movie
    :return:
    """
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        title = form.title.data
        # print(title)
        params = {
            "query": title,
            "api_key": MOVIE_API_KEY
        }
        response = requests.get(MOVIE_API_SEARCH, params=params)
        movies_data = response.json()['results']
        # print(movies_data)

        for movie in movies_data:
            new_movie = {
                "id": movie['id'],
                "title": movie['original_title'],
                "release_date": movie['release_date'],
            }
            all_movies_list.append(new_movie)
        # print(all_movies)
        return render_template("select.html", movies=all_movies_list)
    return render_template("add.html", form=form)


@app.route("/select",  methods=["GET", "POST"])
def select_movie():
    selected_movie_id = request.args.get("id")
    if selected_movie_id:
        # movie_to_add = Movie.query.get(selected_movie_id)
        # print(movie_to_add)
        params = {
            "api_key": MOVIE_API_KEY,
        }
        response = requests.get(f"{MOVIE_API_SELECT}/{selected_movie_id}", params=params)
        selected_movie = response.json()
        # print(selected_movie)
        new_movie = Movie(
            title=selected_movie['original_title'],
            year=selected_movie['release_date'].split("-")[0],
            description=selected_movie['overview'],
            rating=selected_movie['vote_average'],
            img_url=f"{MOVIE_DB_IMAGE_URL}{selected_movie['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()

        movie_to_add = Movie.query.filter_by(title=selected_movie['original_title']).first()
        print(movie_to_add.id)

        return redirect(url_for('edit', id=movie_to_add.id))


if __name__ == '__main__':
    app.run(debug=True)
