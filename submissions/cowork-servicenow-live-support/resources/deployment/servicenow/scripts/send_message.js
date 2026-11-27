(function process(request, response) {
    new CoworkBridge().handle('send_message', request, response);
})(request, response);
