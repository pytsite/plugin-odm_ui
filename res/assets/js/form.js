$('.odm-ui-m-form').on('formForward', function() {
    const form = $(this);

    form.on('formSubmit', function() {
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
