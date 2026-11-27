(function process(request, response) {
    new CoworkBridge().handle('close_chat', request, response);
})(request, response);
