/*************************************************************
 * Description: Logging and error handling functions for app *
 *************************************************************/

/********
 * Init *
 ********/

/*
 * Logging variables
 */
var gvScriptName_log = 'log';

/*
 * Global variables
 */

 /* Logging control */
 var gvLogErrors = true;
 var gvLogProcs  = true;
 var gvLogDebugs = true;
 var gvLogInfos  = true;
 var gvLogInits  = true;
 var gvLogLstnrs = true;
 var gvLogTemps  = true;

/*
 * Initialise the script
 */
(function initialise(){

    var lvFunctionName = 'initialise';
    log(gvScriptName_log + '.' + lvFunctionName + ': Start','INITS');

})();

/*
 * Outputs messages to the console
 */
function log(pvMessage, pvLevel) {
    var lvLevel = pvLevel || 'LOG NOTHING'; // if pvLevel is not populated, set lvLevel to a value that will switch to default

    switch(lvLevel) {

        case 'ERROR':
            if (gvLogErrors) console.log(lvLevel + ': ' + pvMessage);
        break;

        case 'PROCS':
            // Short for "process", these are the ubiquitous logs that
            // track (at the least) the start of every function, as well
            // as other key points
            // On by default
            if (gvLogProcs)  console.log(lvLevel + ': ' + pvMessage);
        break;

        case ' INFO':
            // Additional to PROCS, these don't just track process, they
            // record information as well. Similar to DEBUG.
            // Off by default
            if (gvLogInfos) console.log(lvLevel + ': ' + pvMessage);
        break;

        case 'DEBUG':
            // Useful log points for debugging
            // Off by default
            if (gvLogDebugs) console.log(lvLevel + ': ' + pvMessage);
        break;

        case 'INITS':
            // Rather than putting PROCS in init functions (which always fire
            // and, once the app is working reliably, aren't particularly interesting)
            // Off by default
            if (gvLogInits) console.log(lvLevel + ': ' + pvMessage);
        break;

        case 'LSTNR':
            // Rather than putting PROCS in listeners (which can fire
            // continually in some scenarios), use LSTNR and keep them ...
            // Off by default
            if (gvLogLstnrs) console.log(lvLevel + ': ' + pvMessage);
        break;

        case ' TEMP':
            // What it says on the tin. These should not stay in the code for long
            // On by default
            if (gvLogTemps) console.log(lvLevel + ': ' + pvMessage);
        break;

        default:
            console.log('UNKWN' + ': ' + pvMessage);
    }
}
