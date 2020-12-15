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
        // Convert String To JSON
        // TODO: This particular function breaks with 22 or more tweets (based on String Size, Not Tweet Count)
        // TODO: It appears that the JSON gets chopped off in JQuery's Internal Code (Only When Embedding JSON)
        response = $.parseJSON(tweets);

        $(function() {
            let cards = ""
            $.each(response.results, function(i, item) {
                cards += "<div class=\"mdc-card tweet-card\">\n" +
                    "    <div class=\"mdc-card__primary-action mdc-theme--text-primary-on-dark mdc-theme--primary-bg card__content\" tabindex=\"0\">\n" +
                    "        <div>\n" +
                    "            <h2 class=\"card__title mdc-typography mdc-typography--headline6\">Tweet</h2>\n" +
                    "            <h3 class=\"card__subtitle mdc-typography mdc-typography--subtitle2\">by " + lookupNameFromID(item.twitter_user_id) + " on " + item.date + " UTC</h3>\n" +
                    "        </div>\n" +
                    "        <div class=\"card__text mdc-typography mdc-typography--body2\">" + item.text + "</div>\n" +
                    "    </div>\n" +
                    "    <div class=\"mdc-card__actions mdc-theme--text-secondary-on-dark mdc-theme--secondary-bg card__actions\">\n" +
                    "        <div class=\"mdc-card__action-buttons\">\n" +
                    "            <button class=\"mdc-button mdc-card__action mdc-card__action--button mdc-button--raised\">  <span class=\"mdc-button__ripple\"></span> " + item.device + "</button>\n" +
                    "            <button class=\"mdc-button mdc-card__action mdc-card__action--button mdc-button--raised\" onclick=\" window.open('https://www.twitter.com/REPLACEME/statuses/" + item.id + "','_blank')\">  <span class=\"mdc-button__ripple\"></span> View Tweet</button>\n" +
                    "        </div>\n" +
                    "    </div>\n" +
                    "</div>"
            });

            $('#gov-tweets').html(cards)
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