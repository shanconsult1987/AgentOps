from datetime import datetime

from flask import (
    Flask,
    redirect,
    render_template_string,
    request,
    url_for,
)

from agent import (
    analyze_request,
    validate_plan,
)
from openai_client import get_openai_model
from reviewer import review_plan
from state import load_requests, save_requests
from tools import execute_action


app = Flask(__name__)


HTML = """
<!doctype html>

<html>

<head>

<title>AgentOps Service Desk</title>

<meta http-equiv="refresh" content="10">

<style>

body {
    font-family: Arial, sans-serif;
    background: #f5f7fa;
    margin: 40px;
}

.metrics {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
}

.metric {
    background: white;
    padding: 20px;
    border-radius: 10px;
}

.metric-number {
    font-size: 30px;
    font-weight: bold;
}

.panel {
    background: white;
    padding: 25px;
    border-radius: 10px;
    margin-top: 20px;
}

textarea {
    width: 100%;
    height: 100px;
    box-sizing: border-box;
}

button {
    padding: 10px 20px;
    margin-top: 10px;
}

.request {
    border-top: 1px solid #ddd;
    padding: 20px 0;
}

.tag {
    display: inline-block;
    padding: 5px 10px;
    margin-right: 5px;
    background: #eee;
    border-radius: 5px;
}

li {
    margin-bottom: 6px;
}

</style>

</head>

<body>

<h1>AgentOps Service Desk</h1>

<p>
Planner → Reviewer → Human Approval → Executor
</p>


<div class="metrics">

<div class="metric">
Requests
<div class="metric-number">
{{ total }}
</div>
</div>

<div class="metric">
High Priority
<div class="metric-number">
{{ high }}
</div>
</div>

<div class="metric">
Approval Required
<div class="metric-number">
{{ approval }}
</div>
</div>

<div class="metric">
Approved
<div class="metric-number">
{{ approved }}
</div>
</div>

<div class="metric">
Executed
<div class="metric-number">
{{ executed }}
</div>
</div>

</div>


<div class="panel">

<h2>Create Request</h2>

<form
method="post"
action="{{ url_for('create_request') }}"
>

<textarea
name="message"
placeholder="I cannot access finance."
required
></textarea>

<br>

<button>
Create Agent Plan
</button>

</form>

</div>


<div class="panel">

<h2>Agent Activity</h2>

{% for item in requests %}

<div class="request">

<h3>
Request #{{ item.id }}
</h3>

<p>
{{ item.message }}
</p>

<p>

<span class="tag">
{{ item.category }}
</span>

<span class="tag">
{{ item.priority }}
</span>

<span class="tag">
{{ item.status }}
</span>

</p>


<h4>Plan</h4>

<ol>

{% for step in item.plan %}

<li>
{{ step }}
</li>

{% endfor %}

</ol>


<h4>Proposed Action</h4>

<p>
{{ item.action }}
</p>


<h4>LLM Plan Validation</h4>

<p>
{{ item.plan_validation_summary }}
</p>

{% if item.plan_validation_concerns %}

<ul>

{% for concern in item.plan_validation_concerns %}

<li>
{{ concern }}
</li>

{% endfor %}

</ul>

{% endif %}


<h4>Reviewer</h4>

<p>
{{ item.review_decision }}
</p>


{% if item.status ==
"AWAITING_APPROVAL" %}

<form
method="post"
action="{{ url_for(
'approve_request',
request_id=item.id
) }}"
>

<button>
Approve Action
</button>

</form>

{% endif %}


{% if item.status == "APPROVED" %}

<form
method="post"
action="{{ url_for(
'execute_request',
request_id=item.id
) }}"
>

<button>
Execute Approved Action
</button>

</form>

{% endif %}


{% if item.execution_message %}

<p>
<strong>Execution:</strong>
{{ item.execution_message }}
</p>

{% endif %}

</div>

{% endfor %}

</div>

</body>

</html>
"""


@app.route("/")
def dashboard():

    requests = load_requests()

    total = len(requests)

    high = sum(
        item.get("priority") == "high"
        for item in requests
    )

    approval = sum(
        item.get("status")
        == "AWAITING_APPROVAL"
        for item in requests
    )

    approved = sum(
        item.get("status") == "APPROVED"
        for item in requests
    )

    executed = sum(
        item.get("status") == "EXECUTED"
        for item in requests
    )

    return render_template_string(
        HTML,
        requests=requests,
        total=total,
        high=high,
        approval=approval,
        approved=approved,
        executed=executed,
    )


@app.route(
    "/request",
    methods=["POST"],
)
def create_request():

    message = request.form.get(
        "message",
        "",
    ).strip()

    if not message:

        return redirect(
            url_for("dashboard")
        )

    requests = load_requests()

    next_id = (
        max(
            (
                item.get("id", 0)
                for item in requests
            ),
            default=0,
        )
        + 1
    )

    result = analyze_request(
        message
    )

    validation = validate_plan(
        message,
        result,
    )

    if validation.valid:
        review = review_plan(
            result.category,
            result.priority,
            result.action,
        )

        status = (
            "AWAITING_APPROVAL"
            if review["decision"]
            == "APPROVAL_REQUIRED"
            else "READY"
        )
    else:
        review = {
            "decision": "NOT_REVIEWED",
            "risks": validation.concerns,
        }
        status = "PLAN_REJECTED"

    record = {

        "id": next_id,

        "message": message,

        "category":
            result.category,

        "priority":
            result.priority,

        "summary":
            result.summary,

        "plan":
            result.plan,

        "action":
            result.action,

        "plan_validation_model":
            get_openai_model(),

        "plan_validation_valid":
            validation.valid,

        "plan_validation_summary":
            validation.summary,

        "plan_validation_concerns":
            validation.concerns,

        "review_decision":
            review["decision"],

        "review_risks":
            review["risks"],

        "status":
            status,

        "execution_message":
            "",

        "created":
            datetime.now().isoformat(
                timespec="seconds"
            ),
    }

    requests.insert(
        0,
        record,
    )

    save_requests(requests)

    return redirect(
        url_for("dashboard")
    )


@app.route(
    "/approve/<int:request_id>",
    methods=["POST"],
)
def approve_request(request_id):

    requests = load_requests()

    for item in requests:

        if item.get("id") == request_id:

            if item.get("status") == (
                "AWAITING_APPROVAL"
            ):

                item["status"] = "APPROVED"

            break

    save_requests(requests)

    return redirect(
        url_for("dashboard")
    )


@app.route(
    "/execute/<int:request_id>",
    methods=["POST"],
)
def execute_request(request_id):

    requests = load_requests()

    for item in requests:

        if item.get("id") == request_id:

            if item.get("status") != "APPROVED":

                item["execution_message"] = (
                    "Execution blocked."
                )

                break

            result = execute_action(
                item["category"],
                approved=True,
            )

            if result["success"]:

                item["status"] = "EXECUTED"

            item["execution_message"] = (
                result["message"]
            )

            break

    save_requests(requests)

    return redirect(
        url_for("dashboard")
    )


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )