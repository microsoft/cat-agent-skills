(function process(request, response) {
    new CoworkBridge().handle('open_chat', request, response);
})(request, response);
