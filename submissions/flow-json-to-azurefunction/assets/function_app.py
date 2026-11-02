import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="hello")
def hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    name = req.params.get("name")
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = None
        if req_body:
            name = req_body.get("name")

    if name:
        return func.HttpResponse(f"Hello, {name}!")
    return func.HttpResponse(
        "Pass a name in the query string or in the request body.",
        status_code=200,
    )
