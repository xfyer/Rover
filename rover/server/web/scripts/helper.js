// From https://stackoverflow.com/a/17192845/6828099
function uintToString(uintArray) {
    let encodedString = String.fromCharCode.apply(null, uintArray);

    return decodeURIComponent(escape(encodedString));
}

function generateTableFromTweets(tweets) {
    $(document).ready(function () {
        // Reset Table
        $('#latest-tweets').html("<table id='tweets-table'></table>")

        $('<tr>').append(
            $('<td>').text("Date"),
            $('<td>').text("Tweet ID"),
            $('<td>').text("Text"),
            $('<td>').text("Device")
        ).appendTo('#tweets-table');

        // convert string to JSON
        response = $.parseJSON(tweets);

        $(function() {
            $.each(response.results, function(i, item) {
                $('<tr>').append(
                    $('<td>').text(item.date),
                    $('<td>').html("<a href='https://www.twitter.com/REPLACEME/statuses/" + item.id + "'>" + item.id + "</a>"),
                    $('<td>').text(item.text),
                    $('<td>').text(item.device)
                ).appendTo('#tweets-table');
            });
        });
    });
}