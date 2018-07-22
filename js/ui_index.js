/************************************************
 * Description: UI functions for the index page *
 ************************************************/

/********
 * Init *
 ********/

/*
 * Logging variables
 */
var gvScriptName_uiIndex = 'ui_index';

/*
 * Global variables
 */
// --

/*
 * Initialise the script
 */
(function initialise() {

  var lvFunctionName = 'initialise';
  log(gvScriptName_uiIndex + '.' + lvFunctionName + ': Start', 'INITS');

})();

/*************
 * Listeners *
 *************/

/*********************
 * Page Constructors *
 *********************/

/*
 *
 */
function buildPage() {

  var lvFunctionName = 'buildPage';
  log(gvScriptName_uiIndex + '.' + lvFunctionName + ': Start', 'PROCS');

  var lvHtml = '';

  lvHtml += '<div class="controls">';
  lvHtml += '  <select id="electionFilter">';
  lvHtml += '    <option value="general2017">2017 General Election</option>';
  lvHtml += '    <option value="upcomingLocals" selected>Upcoming Local & By Elections</option>';
  lvHtml += '  </select>';
  lvHtml += '  <select id="sortBy">';
  lvHtml += '    <option value="femaleRep">Sort by female rep (lowest first)</option>';
  lvHtml += '    <option value="date" selected>Sort by date (earliest first)</option>';
  lvHtml += '  </select>';
  lvHtml += '</div>';
  lvHtml += '<div id="results_div">';
  lvHtml += '</div>';

  $('#container_div').html(lvHtml);

  document.getElementById("electionFilter").addEventListener("change", electionFilterChange_listener);
  document.getElementById("sortBy").addEventListener("change", sortByChange_listener);

  lvArgs = {
    dataset: 'upcomingLocals',
    sortBy: 'date'
  };
  getData(lvArgs, buildResults);

}

function getData(pvArgs, pvCallback){

    var lvFunctionName = 'getData';
    log(gvScriptName_main + '.' + lvFunctionName + ': Start','PROCS');

    filename = '';
    switch(pvArgs.dataset) {
      case 'general2017':
        filename = 'ALL_ELECTIONS';
        break;
      case 'upcomingLocals':
        filename = 'upcoming_elections';
        break;
    }

    $.getJSON("data/" + filename + ".json", function(json) {

      if (filename == 'ALL_ELECTIONS'){
        newJson = {
          'parl': {
            'election_type_name': "UK Parliament elections",
            'orgs': {
              'parl.2017-06-08': json.parl.orgs['parl.2017-06-08']
            }
          }
        };
      } else {
        newJson = json;
      }

      console.log(newJson);

      pvCallback(newJson, pvArgs.sortBy);
    });
}

function buildResults(pvData, sortBy) {

  var lvFunctionName = 'buildResults';
  log(gvScriptName_main + '.' + lvFunctionName + ': Start','PROCS');

  var lvHtml = '';

  var today = new Date();

  for (var elecTypeId in pvData) {

    elecType = pvData[elecTypeId];

    lvHtml += '<div class="elecType">';
    lvHtml += '<p class="electionTypeTitle">' + elecType.election_type_name + '</p>';

    // convert to array so we can sort
    orgArray = [];
    for (var i in elecType.orgs) {
      orgArray.push(elecType.orgs[i]);
    }

    orgArray.sort(function(a, b){
      return sort(a,b,sortBy);
    });

    var lastDate = null;

    for (i in orgArray) {

      org = orgArray[i];

      if (org.poll_open_date != lastDate && sortBy == 'date') {
        lastDate = org.poll_open_date;
        pollOpenDate = new Date(org.poll_open_date);
        Math.abs(pollOpenDate.getTime() - today.getTime());
        timeDiff = Math.abs(pollOpenDate.getTime() - today.getTime());
        diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24));
        lvHtml += '<div class="dateHeader">';
        lvHtml += '<p>' + diffDays + ' days [' + org.poll_open_date + ']</p>';
        lvHtml += '</div>';
      }

      lvHtml += '<div class="org">';
      lvHtml += '  <p class="orgTitle">' + org.election_name + '</p>';

      if (Object.keys(org.ballots).length == 1 && org.genderBD.totalCan > 0) {
        lvHtml += '<p class="orgGenderBD">' + org.genderBD.percentFemale + '% Female | ';
        lvHtml += org.genderBD.percentMale + '% Male | ';
        lvHtml += org.genderBD.percentUnknown + '% Unknown' + '</p>';
      }

      // convert to array so we can sort
      ballotArray = [];
      for (i in org.ballots) {
        ballotArray.push(org.ballots[i]);
      }

      ballotArray.sort(function(a, b){
        return sort(a,b,sortBy);
      });

      for (i in ballotArray) {

        ballot = ballotArray[i];

        if (ballot.seats_contested == null) {
          seatsCount = '';
          plural = 's';
        } else if (ballot.seats_contested == 1) {
          seatsCount = '1';
          plural = '';
        } else if (ballot.seats_contested > 1) {
          seatsCount = ballot.seats_contested;
          plural = 's';
        }

        lvHtml += '<table class="ballot"><tr>';
        lvHtml += '  <td class="ballotText">';
        lvHtml += '    <p class="ballotDesc"><a href="' + ballot.web_url + '" target="_blank">' + ballot.division_name + '</a></p>';

        if (Object.keys(org.ballots).length > 1 && ballot.genderBD.totalCan > 0) {
          lvHtml += '  <p class="ballotGenderBD">' + ballot.genderBD.percentFemale + '% Female | ';
          lvHtml += ballot.genderBD.percentMale + '% Male | ';
          lvHtml += ballot.genderBD.percentUnknown + '% Unknown' + '</p>';
        }

        lvHtml += '    <div class="candidate">';

        if (Object.keys(ballot.cans).length > 0) {

          lvHtml += '    <table class="canTable">';

          for (var canId in ballot.cans) {

            can = ballot.cans[canId];

            gender = 'unknown';
            if (can.gender !== null && can.gender !== '') {
              gender = can.gender.toLowerCase();
            }

            lvHtml += ' <tr>';
            lvHtml += '  <td><a href="' + can.web_url + '" target="_blank">' + can.name + '</a></td>';
            lvHtml += '  <td>';
            if (can.twitter !== '') {
              lvHtml += '<a href="https://twitter.com/' + can.twitter + '" target="_blank"><img src="img/twitter.svg" width="15px" height="15px" /></a>';
            }
            lvHtml += '  </td>';
            lvHtml += '  <td>' + gender + '</td>';

            lvHtml += '</td>';

          }

          lvHtml += '    </table>';
        } else {
          lvHtml += '    <p>No candidate data</p>';
        }

        lvHtml += '    </div>'; // candidate
        lvHtml += '  </td>'; // ballotText
        lvHtml += '  <td class="ballotChart">';
        // Need to replace fullstops in the ids, otherwise they won't work as selectors
        lvHtml += '<div class="ballotChartDiv" id="ballotChart_' + ballot.id.replace(/\./g,'')  + '" data-male="' + ballot.genderBD.percentMale + '" data-female="' + ballot.genderBD.percentFemale + '" data-unknown="' + ballot.genderBD.percentUnknown + '" ></div>';
        lvHtml += '  </td>';
        lvHtml += '</tr></table>'; // ballot

      }

      lvHtml += '</div>';  // org

    }

    lvHtml += '</div>';  // elecType

  }

  $('#results_div').html(lvHtml);
  $('#msg_div').html('');

  $(".ballotChartDiv").each(function() {

    var data = [['female', $(this).attr("data-female")],
                ['male', $(this).attr("data-male")],
                ['unknown', $(this).attr("data-unknown")]];

    var svg = d3.select('#' + $(this).attr('id'))
      .append("svg")
      .attr('height', 100)
      .attr('width', 100);

    var g = svg.append("g")
      .attr("transform", "translate(100,100)");

    var y_scale = d3.scaleLinear()
      .range([100,0])
      .domain([0,100]);

    var x_scale = d3.scaleBand()
      .range([0,100])
      .domain(['Female', 'Male', 'Unknown']);

    var colours = d3.scaleOrdinal()
      .range(["green", "orange", "yellow"]);

    var bars = svg.selectAll(".bar")
      .data(data);

    bars.enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('width', '30px')
      .attr('fill', 'red')
      .attr('height', 100)
      .attr('y', function(d, i){
        return 100 - +d[1];
      })
      .attr('x', function(d,i){ return (i*30);});

    var x_axis = d3.axisBottom(x_scale);

    g.append("g")
      .call(x_axis)
      .attr("transform", "translate(500,400)")
      .selectAll("text")
      .attr("y", 5)
      .attr("x", 9)
      .attr("dy", ".35em")
      .style("text-anchor", "middle");


  });
}

/*************
 * Listeners *
 *************/


function electionFilterChange_listener() {

  $('#results_div').html('<p>Loading</p>');

  lvArgs = {
    dataset: this.value,
    sortBy: document.getElementById("sortBy").value
  };
  getData(lvArgs, buildResults);
}

function sortByChange_listener() {

  $('#results_div').html('<p>Loading</p>');

  lvArgs = {
    dataset: document.getElementById("electionFilter").value,
    sortBy: this.value
  };
  getData(lvArgs, buildResults);
}


/***************
 * Other Funcs *
 ***************/

function sort(a, b, sortBy) {
  if (sortBy == 'femaleRep') {
    if (parseInt(b.genderBD.percentFemale) > parseInt(a.genderBD.percentFemale)) {
      return -1;
    } else if (parseInt(b.genderBD.percentFemale) < parseInt(a.genderBD.percentFemale)) {
      return 1;
    } else {
      return 0;
    }
  } else if (sortBy == 'date'){
    if (b.poll_open_date > a.poll_open_date) {
      return -1;
    } else if (b.poll_open_date < a.poll_open_date) {
      return 1;
    } else {
      return 0;
    }
  }
}
