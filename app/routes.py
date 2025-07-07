from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import db
from datetime import datetime, timedelta

main = Blueprint("main", __name__)

# predefined credentials
USERNAME = "Kapture"
PASSWORD = "Kapture"

@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

@main.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("main.login"))

    today = datetime.utcnow().date()
    dates = [today - timedelta(days=i) for i in reversed(range(7))]
    labels = [d.strftime("%a %d") for d in dates]

    total_counts = []
    complete_counts = []
    processing_counts = []
    failed_counts = []

    for d in dates:
        start = datetime.combine(d, datetime.min.time())
        end   = datetime.combine(d, datetime.max.time())

        query_range = { "updated_at": { "$gte": start, "$lte": end } }

        total = db["auto_qa_results"].count_documents(query_range)
        complete = db["auto_qa_results"].count_documents({ **query_range, "auto_qa_status": "complete" })
        processing = db["auto_qa_results"].count_documents({ **query_range, "auto_qa_status": "processing" })
        failed = db["auto_qa_results"].count_documents({ **query_range, "auto_qa_status": "failed" })

        total_counts.append(total)
        complete_counts.append(complete)
        processing_counts.append(processing)
        failed_counts.append(failed)

    return render_template("dashboard.html",
                           labels=labels,
                           total=total_counts,
                           complete=complete_counts,
                           processing=processing_counts,
                           failed=failed_counts)
@main.route("/explore_ticket", methods=["GET", "POST"])
def explore_ticket():
    if "user" not in session:
        return redirect(url_for("main.login"))

    ticket_id = ""
    results = []

    if request.method == "POST":
        ticket_id = request.form.get("ticket_id", "").strip()
        if not ticket_id:
            flash("Please enter a Ticket ID", "danger")
        else:
            results = list(db["auto_qa_results"].find({"ticket_id": ticket_id}))
            if not results:
                flash(f'No results for Ticket ID "{ticket_id}"', "warning")

    return render_template(
        "explore_ticket.html",
        ticket_id=ticket_id,
        results=results
    )

@main.route("/explore_client", methods=["GET", "POST"])
def explore_client():
    if "user" not in session:
        return redirect(url_for("main.login"))

    # Shared: client only bar data
    labels = []
    bar_data = {"complete": [], "processing": [], "failed": []}

    # Pie data placeholders
    pie_data_single = None
    pie_data_range  = None

    # On POST, read which mode
    selected_tab = request.form.get("mode", "bar")

    # 1) If at least client_id provided, compute bar
    client_id = request.form.get("client_id_bar") or request.form.get("client_id_single") or request.form.get("client_id_range")
    if client_id:
        # last 7 days
        today = datetime.utcnow().date()
        dates = [today - timedelta(days=i) for i in reversed(range(7))]
        labels = [d.strftime("%a %d") for d in dates]

        for d in dates:
            start = datetime.combine(d, datetime.min.time())
            end   = datetime.combine(d, datetime.max.time())
            base_q = {"updated_at": {"$gte": start, "$lte": end}, "client_id": client_id}

            bar_data["complete"].append( db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "complete"}) )
            bar_data["processing"].append( db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "processing"}) )
            bar_data["failed"].append( db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "failed"}) )

    # 2) Single-day pie
    if selected_tab == "single":
        date_str = request.form.get("date_single", "")
        if client_id and date_str:
            try:
                d0 = datetime.strptime(date_str, "%Y-%m-%d").date()
                s = datetime.combine(d0, datetime.min.time())
                e = datetime.combine(d0, datetime.max.time())
                base_q = {"updated_at": {"$gte": s, "$lte": e}, "client_id": client_id}
                pie_data_single = {
                    "complete":   db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "complete"}),
                    "processing": db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "processing"}),
                    "failed":     db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "failed"})
                }
            except ValueError:
                flash("Use YYYY-MM-DD for date", "danger")

    # 3) Range pie
    if selected_tab == "range":
        start_str = request.form.get("start_date", "")
        end_str   = request.form.get("end_date", "")
        if client_id and start_str and end_str:
            try:
                d1 = datetime.strptime(start_str, "%Y-%m-%d").date()
                d2 = datetime.strptime(end_str,   "%Y-%m-%d").date()
                s = datetime.combine(min(d1, d2), datetime.min.time())
                e = datetime.combine(max(d1, d2), datetime.max.time())
                base_q = {"updated_at": {"$gte": s, "$lte": e}, "client_id": client_id}
                pie_data_range = {
                    "complete":   db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "complete"}),
                    "processing": db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "processing"}),
                    "failed":     db["auto_qa_results"].count_documents({**base_q, "auto_qa_status": "failed"})
                }
            except ValueError:
                flash("Use YYYY-MM-DD for start/end dates", "danger")

    return render_template(
        "explore_client.html",
        selected_tab=selected_tab,
        labels=labels,
        bar_data=bar_data,
        pie_data_single=pie_data_single,
        pie_data_range=pie_data_range,
        client_id=client_id
    )
@main.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("main.login"))
