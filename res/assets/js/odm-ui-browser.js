define(['assetman', 'widget-misc-bootstrap-table'], function(assetman, bootstrapTableWidget) {
    assetman.loadCSS('plugins.odm_ui@css/odm-ui-browser.css');

    return function(widget) {
        // Init parent widget
        bootstrapTableWidget(widget);
    };
});
