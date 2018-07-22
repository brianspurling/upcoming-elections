/*****************************************************************
 * Description: Generic UI functions required on all/many pages  *
 *****************************************************************/

/********
 * Init *
 ********/

/*
 * Logging variables
 */
var gvScriptName_uiMain = 'ui_main';

/*
 * Global variables
 */
// --

/*
 * Initialise the script
 */
(function initialise(){

    var lvFunctionName = 'initialise';
    log(gvScriptName_uiMain + '.' + lvFunctionName + ': Start','INITS');

    window.addEventListener('DOMContentLoaded', DOMContentLoaded_listener);

})();

/*************
 * Listeners *
 *************/

/*
 *
 */
function DOMContentLoaded_listener(){

    var lvFunctionName = 'DOMContentLoaded_listener';
    log(gvScriptName_uiMain + '.' + lvFunctionName + ': Start','LSTNR');

    // Get the name of the page that's just loaded
    var lvURL = window.location.pathname;
    var lvPageName = lvURL.substring(lvURL.lastIndexOf('/')+1);

    // buildMenu(lvPageName);
    buildPage(); // This will call the buildPage function from the active page's UI script (i.e. ui_<page name>.js)
}

/*************
 * Functions *
 *************/

/*
 *
 */
function buildMenu(pvPageName){

    var lvFunctionName = 'buildMenu';
    log(gvScriptName_uiMain + '.' + lvFunctionName + ': Start','PROCS');


    var lvHtmlString = '';

    // If the page is active, set the relevant page's class to active using these vars
    var lvIndexActiveClassHTML = '';

    switch (pvPageName) {
        case 'index.html':
            lvIndexActiveClassHTML = 'class="active"';
        break;
    }

    lvHtmlString += '<nav class="top-bar" data-topbar>';

    // Title Area
    lvHtmlString += '    <ul class="title-area">';
    lvHtmlString += '        <li class="name"><h1></h1></li>';
    lvHtmlString += '        <li class="toggle-topbar menu-icon"><a><span></span></a></li>';
    lvHtmlString += '    </ul>';

    // Menu
    lvHtmlString += '    <section class="top-bar-section">';

    // Left Section
    lvHtmlString += '        <ul class="left">';
    lvHtmlString += '            <li><a href="index.html">Home</a></li>';
    lvHtmlString += '        </ul>';
    // Right Section
    lvHtmlString += '        <ul class="right">';
    lvHtmlString += '        </ul>';

    lvHtmlString += '    </section>';
    lvHtmlString += '</nav>';

    $('#menu_div').html(lvHtmlString);
}
