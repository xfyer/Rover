// Load Functions
setupMaterialUI()

// From https://stackoverflow.com/a/17192845/6828099
function uintToString(uintArray) {
    let encodedString = String.fromCharCode.apply(null, uintArray);

    return decodeURIComponent(escape(encodedString));
}

function lookupNameFromID(twitter_account_id) {
    // TODO: Stop Hardcoding This
    if (twitter_account_id === "25073877") {
        return "Donald Trump"
    }

    if (twitter_account_id === "1323730225067339784") {
        return "Joe Biden"
    }

    if (twitter_account_id === "1536791610") {
        return "Barack Obama"
    }

    return twitter_account_id
}

function generateTableFromTweets(tweets) {
    $(document).ready(function () {
        // Reset Table
        $('#gov-tweets').html("<table id='tweets-table'></table>")

        $('<tr>').append(
            $('<td>').text("Row"),
            $('<td>').text("Tweeter"),
            $('<td>').text("Date"),
            $('<td>').text("Tweet ID"),
            $('<td>').text("Text"),
            $('<td>').text("Device")
        ).appendTo('#tweets-table');

        // Convert String To JSON
        // TODO: This particular function breaks with 22 or more tweets (based on String Size, Not Tweet Count)
        // TODO: It appears that the JSON gets chopped off in JQuery's Internal Code (Only When Embedding JSON)
        response = $.parseJSON(tweets);

        $(function() {
            $.each(response.results, function(i, item) {
                $('<tr>').append(
                    $('<td>').text(i+1),
                    $('<td>').text(lookupNameFromID(item.twitter_user_id)),
                    $('<td>').text(item.date),
                    $('<td>').html("<a href='https://www.twitter.com/REPLACEME/statuses/" + item.id + "'>" + item.id + "</a>"),
                    $('<td>').text(item.text),
                    $('<td>').text(item.device)
                ).appendTo('#tweets-table');
            });
        });
    });
}

// Setup UI Animations and Stuff
function setupMaterialUI() {
    $(document).ready(function () {
        let ripple_buttons = document.querySelectorAll('.ripple-button');

        ripple_buttons.forEach(function(ripple_button) {
            mdc.ripple.MDCRipple.attachTo(ripple_button);
        });
    });
}