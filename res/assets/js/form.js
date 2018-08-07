$('.odm-ui-m-form').on('forward:form:pytsite', function() {
    const form = $(this);

    form.on('submit:form:pytsite', function() {
        form.attr('data-changed', false);
    });

    form.change(function(e) {
        form.attr('data-changed', true);
    });

    window.onbeforeunload = function confirmExit() {
        if (form.attr('data-changed') === 'true')
            return true;
    }
});
