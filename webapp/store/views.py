from flask import Blueprint, abort, request, render_template
from webapp.store import models

from jujubundlelib import references

jaasstore = Blueprint(
    "jaasstore",
    __name__,
    template_folder="/templates",
    static_folder="/static",
)


@jaasstore.route("/store")
def store():
    return render_template("store/store.html")


@jaasstore.route("/search")
def search():
    query = request.args.get("q", "").replace("/", " ")
    entity_type = request.args.get("type", None)
    if entity_type not in ["charm", "bundle"]:
        entity_type = None
    series = request.args.get("series", None)
    tags = request.args.get("tags", None)
    sort = request.args.get("sort", None)
    provides = request.args.get("provides", None)
    requires = request.args.get("requires", None)
    if provides:
        results = models.fetch_provides(provides)
    elif requires:
        results = models.fetch_requires(requires)
    else:
        results = models.search_entities(
            query,
            entity_type=entity_type,
            tags=tags,
            sort=sort,
            series=series,
            promulgated_only=False,
        )
    return render_template(
        "store/search.html",
        context={
            "current_series": series,
            "current_sort": sort,
            "current_type": entity_type,
            "results": results,
            "results_count": len(results["recommended"])
            + len(results["community"]),
            "query": query,
        },
    )


@jaasstore.route("/u/<username>")
def user_details(username):
    entities = models.get_user_entities(username)
    if len(entities["charms"]) > 0 or len(entities["bundles"]) > 0:
        return render_template(
            "store/user-details.html",
            context={
                "bundles_count": len(entities["bundles"]),
                "bundles": entities["bundles"],
                "charms_count": len(entities["charms"]),
                "charms": entities["charms"],
                "entities": entities,
                "username": username,
            },
        )
    else:
        return abort(404, "User not found: {}".format(username))


@jaasstore.route("/u/<username>/<charm_or_bundle_name>")
@jaasstore.route("/u/<username>/<charm_or_bundle_name>/<series_or_version>")
@jaasstore.route(
    "/u/<username>/<charm_or_bundle_name>/<series_or_version>/<version>"
)
def user_entity(
    username, charm_or_bundle_name, series_or_version=None, version=None
):
    return details(
        charm_or_bundle_name,
        series_or_version=series_or_version,
        version=version,
    )


@jaasstore.route("/<charm_or_bundle_name>")
@jaasstore.route("/<charm_or_bundle_name>/<series_or_version>")
@jaasstore.route("/<charm_or_bundle_name>/<series_or_version>/<version>")
def details(charm_or_bundle_name, series_or_version=None, version=None):
    reference = None
    try:
        reference = references.Reference.from_jujucharms_url(request.path[1:])
    except ValueError:
        pass

    entity = None
    if reference:
        entity = models.get_charm_or_bundle(reference)

    if entity:
        if entity["is_charm"]:
            return render_template(
                "store/charm-details.html", context={"entity": entity}
            )
        else:
            return render_template(
                "store/bundle-details.html", context={"entity": entity}
            )
    else:
        return abort(404, "Entity not found {}".format(charm_or_bundle_name))
