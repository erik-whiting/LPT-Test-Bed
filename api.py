import json
import os
from datetime import datetime

import flask
from flask import request, jsonify, abort
from flask import make_response, render_template
from resources.resources import Resources
from resources.sale import Sale
from dotenv import load_dotenv

load_dotenv()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath("test_site/*")))
template_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(template_dir, "css")

app = flask.Flask(__name__, template_folder=template_dir, static_folder=template_dir)
app.config["DEBUG"] = True

r = Resources()


@app.route("/", methods=["GET"])
def home():
    headers = {"Content-Type": "text/html"}
    return make_response(render_template("index.html"), headers)


@app.route("/bands", methods=["GET"])
def bands():
    bands = r.bands(None)
    return make_response(
        render_template("pages/bands.html", bands_object=json.dumps(bands))
    )


@app.route("/bands/<band_id>", methods=["GET"])
def band(band_id):
    band_name = r.bands(band_id)[0]["bandname"]
    albums = r.album_by_band(band_id)
    songs = {}
    for album in albums:
        album["releasedate"] = album["releasedate"].isoformat()
        all_songs = r.song_by_album(album["id"])
        for song in all_songs:
            song["releasedate"] = song["releasedate"].isoformat()
        songs[album["albumname"]] = all_songs
    return make_response(
        render_template(
            "pages/band.html", band_name=band_name, track_list=json.dumps(songs)
        )
    )


@app.route("/albums", methods=["GET"])
def albums():
    albums = r.album_view()
    for album in albums:
        album["releasedate"] = album["releasedate"].isoformat()
    return make_response(
        render_template("pages/albums.html", albums=json.dumps(albums))
    )


@app.route("/sales", methods=["GET"])
def sales():
    sales = r.sales()
    return make_response(render_template("pages/sales.html", sales=json.dumps(sales)))


@app.route("/new_sale", methods=["GET"])
def new_sale_page():
    albums = r.album_view()
    album_sale_hash = r.album_sale_hash()
    for album in albums:
        album["releasedate"] = album["releasedate"].isoformat()
    albums = json.dumps(albums)
    album_sale_hash = json.dumps(album_sale_hash)
    return make_response(
        render_template(
            "pages/make_sale.html", albums=albums, album_sale_hash=album_sale_hash
        )
    )


@app.errorhandler(404)
def page_not_found(e):
    return make_response(jsonify({"error": "not Found"}), 404)


@app.route("/api/v1/resources/bands", methods=["GET"])
def api_bands():
    band_id = request.args.get("id")
    return jsonify(r.bands(band_id))


@app.route("/api/v1/resources/bands", methods=["POST"])
def api_bands_create():
    if not request.json and "band_name" not in request.json:
        return jsonify({"error": "Missing brand_name value in request'"})

    band_name = request.json["band_name"]

    r.band_create(band_name)

    return jsonify(r.band_by_name(band_name)), 201


@app.route("/api/v1/resources/bands/<band_id>", methods=["DELETE"])
def api_bands_delete(band_id):
    if not band_id:
        return jsonify({"error": "Missing band_id in request'"})

    r.brand_delete(band_id)

    return jsonify({"result": "ok"})


@app.route("/api/v1/resources/bands/<band_id>", methods=["PUT"])
def api_bands_update(band_id):
    if not band_id:
        return jsonify({"error": "Missing band_id in request'"})

    if not request.json and "band_name" not in request.json:
        return jsonify({"error": "Missing brand_name value in request'"})

    r.band_update(band_id, request.json["band_name"])

    return jsonify({"result": "ok"})


@app.route("/api/v1/resources/albums", methods=["POST"])
def api_albums_create():
    if not request.json and "album_name" not in request.json:
        return jsonify({"error": "Missing values in request'"})

    release_datetime = datetime.strptime(request.json["release_date"], "%Y-%m-%d")

    # add option to send also songs
    r.album_create(
        request.json["album_name"], release_datetime, request.json["band_id"]
    )

    return jsonify({"result": "ok"}), 201


@app.route("/api/v1/resources/albums/<album_id>", methods=["DELETE"])
def api_albums_delete(album_id):
    if not album_id:
        return jsonify({"error": "Missing album id in request"})

    r.album_delete(album_id)

    return jsonify({"result": "ok"})


@app.route("/api/v1/resources/songs", methods=["GET"])
def api_songs():
    song_id = request.args.get("id")
    return jsonify(r.songs(song_id))


@app.route("/api/v1/resources/track_list/<band_id>", methods=["GET"])
def api_track_list(band_id):
    albums = r.album_by_band(band_id)
    songs = {}
    for album in albums:
        all_songs = r.song_by_album(album["id"])
        songs[album["albumname"]] = all_songs
    return jsonify(songs)


@app.route("/api/v1/resources/make_sale", methods=["POST"])
def api_make_sale():
    if not request.json or "line_items" not in request.json:
        abort(400)
    line_items = request.json["line_items"]
    sale = Sale(line_items)
    return jsonify(sale.commit())


app.run(host="0.0.0.0")
