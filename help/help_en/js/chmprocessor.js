/* 
* chmProcessor - Word converter to CHM
* Copyright (C) 2008 Toni Bennasar Obrador
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

// TODO: Add new needed translations

var pageLayout; // a var is required because this page utilizes: pageLayout.allowOverflow() method


// Returns the last index of a character into a string. Returns < 0 if it was not found
// character: Character to search
if (!String.prototype.lastIndexOf) {
    String.prototype.lastIndexOf = function(character) {
        for (i = (this.length - 1); i >= 0; i--) {
            if (this.charAt(i) == character)
                return i;
        }
        return -1;
    }
}

// Returns the file name of a URL
function getUrlFileName(url) {
    idx = url.lastIndexOf('/');
    if (idx >= 0)
        return url.substring(idx + 1);
    else
        return url;
}

// Loads a URL into the current topic iframe
// url: Relative topic URL to load
function loadUrlOnFrame(url) {

    var iframeSelector = $("#mainFrame");
    try {
        // This will fail on chrome with file:// protocol
        var currentUrl = getUrlFileName(iframeSelector.prop("contentWindow").location.href);
        if (currentUrl.toLowerCase() == url.toLowerCase())
            return;
    }
    catch (ex) { }

    if ("onhashchange" in window)
        // Browser supports hash changes. Use replace because it does not store an history browser point
        iframeSelector.prop("contentWindow").location.replace(url);
    else
        // Browser does not support hash changes. Set the src attribute: It stores an history browser point
        $("#mainFrame").attr("src", url);

}

// Select a tree node by its URL
// url: string with the URL to search
function selectByUrl(url) {
    var fileName = getUrlFileName(url);
    fileName = decodeURIComponent(fileName); // Needed if the hash part(xxx on a.html#xxx) contains spaces, it happens with word generated hashes
    // Do tree selection, with hash:
    var linkSelected = $('#treediv a[href="' + fileName + '"]').first();
    var loadFrame = true;
    if (linkSelected.length == 0) {
        // Not found: Do the selection without hash:
        var parts = fileName.split("#");
        linkSelected = $('#treediv a[href^="' + parts[0] + '"]').first();
        loadFrame = false;
    }
    $("#treediv").jstree("select_node", linkSelected.parent(), loadFrame);
    if( loadFrame )
        // Load the URL on the frame
        loadUrlOnFrame(fileName);
    else if( fileName.indexOf("search.aspx") == 0 ) {
        // We are on the full text search page. Set the hash:
        changeHash(fileName);
    }
};

// Process a tree link text
function cleanTitleText(linkText) {
    // Remove line breaks and leading spaces
    var cleanText = $.trim( linkText.replace("\n", " ") );
    // Replace extra spaces by a single one
    return cleanText.replace(/\s+/g, " ");
}

function parseTitle(title) {
    var result = new Object();
    result.instance = 0;
    result.title = title;
    
    if (title.charAt(0) != "!")
        return result;
    title = title.substring(1);
    var idx = title.indexOf("!");
    if( idx <= 0 )
        return result;
    var number = parseInt(title.substring(0, idx));
    if( isNaN(number) )
        return result;

    result.instance = number - 1;
    result.title = title.substring(idx + 1);
    return result;
}

// Select a tree node by its title
// title: Tree node title to select
function selectByTitle(title) {

    title = cleanTitleText(title).toLowerCase();

    if (title == "")
        // Select the first node
        $("#treediv").jstree("select_node", $("#treediv li:first"), true);
    else {
        // Select the node by title

        // Check for instance number:
        var searchInstance = parseTitle(title);
        var titleSelector = $("#treediv a")
            .filter(function(index) {
                return cleanTitleText($(this).text()).toLowerCase() == searchInstance.title;
            });
        if (searchInstance.instance == 0)
            titleSelector = titleSelector.first();
        else
            titleSelector = titleSelector.eq(searchInstance.instance);
            
        $("#treediv").jstree("select_node",
            titleSelector.parent(),
            true
        );
    }
}

//////////////////////////////////////////////////
// URL HASH HANDLERS
//////////////////////////////////////////////////

// Return the window current hash
function getCurrentHash() {
    // Firefox returns the hash unescaped, so decodeURIComponent fails...
    /*var title = window.location.hash;
    if (title.charAt(0) == '#')
        title = title.substring(1);*/
    var hash = location.href.split("#")[1];
    if (!hash)
        hash = "";
    return hash;
}

// Hash change event handler
function hashChanged() {
    var title = getCurrentHash();
    title = decodeURIComponent(title);
    if (title.indexOf("search.aspx") == 0)
        // Its a full text search URL
        loadUrlOnFrame(title);
    else
        // Its a section title 
        selectByTitle(title);
}

// Set a new URL hash
// linkSelector: The jquery tree title link, or a string with the search page URL
function changeHash(linkSelector) {

    if (!("onhashchange" in window))
        // Browser does not support hash change. Do nothing.
        return;

    var newHash = null;
    if (typeof linkSelector == 'string' || linkSelector instanceof String) {
        // Is the url to the search page:
        newHash = linkSelector;
    }
    else {
        newHash = cleanTitleText(linkSelector.text());

        // Check if its a duplicated title
        var titleInstance = linkSelector.prop("titleInstance");
        if (titleInstance)
        // Save instance number:
            newHash = "!" + titleInstance + "!" + newHash;

        // The first node should no have hash:
        if (cleanTitleText($("#treediv a:first").text()) == newHash)
            newHash = "";
    }

    // Avoid to put the same hash twice
    if (window.location.hash == newHash)
        return;

    newHash = encodeURIComponent(newHash);
    window.location.hash = newHash;
}

//////////////////////////////////////////////////
// SET INITIAL TOPIC 
// For compatibilty with frames template ("www.example.com/help/index.html?topic=topic title")
//////////////////////////////////////////////////

// Returns the string value of the parameter strParamName on the url
// Returns an empty string if the parameter was not found
function getURLParam(url, strParamName) {

    var strReturn = "";
    var strHref = url;
    var idxStart = strHref.indexOf("?");
    if (idxStart >= 0) {
        var strQueryString = strHref.substr(idxStart+1);
        var aQueryString = strQueryString.split("&");
        for (var iParam = 0; iParam < aQueryString.length; iParam++) {
            if (aQueryString[iParam].indexOf(strParamName + "=") == 0) {
                var aParam = aQueryString[iParam].split("=");
                strReturn = aParam[1];
                break;
            }
        }
    }
    return decodeURIComponent(strReturn);
}

// Sets the initial topic selection
function setInitialTopic() {

    if (getCurrentHash())
        // There is an initial hash: Select it
        hashChanged();
    else {
        // Check the old way to set the selected topic ("topic" url parameter)
        var initialTopic = getURLParam(window.location.href, "topic");
        if (initialTopic != "")
            // Select the initial topic
            selectByTitle(initialTopic);
        else
            // Select the first node
            $("#treediv").jstree("select_node", $("#treediv li:first"), true);
    }
}

//////////////////////////////////////////////////
// NAVIGATION LINKS (NEXT, PREVIOUS, HOME)
//////////////////////////////////////////////////

// Array with pages file names
var pageNames = new Array();

// Array with first anchor of each page
var anchorNames = new Array();

function getCurrentPageIndex() {
    // Get the current topic page filename. This will fail on chrome local filesystem
    try {
        var fileName = getUrlFileName($("#mainFrame").prop("contentWindow").location.href.split("#")[0]);
        //return pageNames.indexOf(fileName); < Fails on IE
        return jQuery.inArray(fileName, pageNames);
    }
    catch (ex) {
        return -1;
    }
}

// Set the current selected page by its index
function setCurrentPageIndex(idx) {
    if( idx < 0 || idx >= pageNames.length )
        return;
    selectByUrl(pageNames[idx] + "#" + anchorNames[idx]);
}

function increasePageIndex(idxIncrease) {
    var currentIdx = getCurrentPageIndex();
    if (currentIdx < 0)
        return;
    setCurrentPageIndex(currentIdx + idxIncrease);
}

// Setup of home, next and previous links
function initializeNavigationLinks() {

    // Setup arrays
    var lastPage = null;
    var titlesCount = new Array();
    $("#treediv a").each(function() {

        // Setup arrays of each page first anchor 
        var pageHrefParts = $(this).attr("href").split("#");
        if (!lastPage || pageHrefParts[0] != lastPage) {
            // New page:
            pageNames[pageNames.length] = pageHrefParts[0];
            anchorNames[anchorNames.length] = pageHrefParts[1];
            lastPage = pageHrefParts[0];
        }

        // If there is reapeated titles, save its instance number. Used for page hash.
        var title = cleanTitleText($(this).text());
        var count = titlesCount[title];
        if (!count)
            count = 0;
        count++;
        if (count > 1)
            $(this).prop("titleInstance", count);
        titlesCount[title] = count;
        
    });

    // If there is a single page, hide navigation links:
    if (pageNames.length <= 1) {
        $("#lnkPrevious").hide();
        $("#lnkNext").hide();
        $("#lnkHome").hide();
    }
    
    // Link event handlers
    $("#lnkPrevious").click(function(e) {
        e.preventDefault();
        increasePageIndex(-1);
    });
    $("#lnkNext").click(function(e) {
        e.preventDefault();
        increasePageIndex(1);
    });
    $("#lnkHome").click(function(e) {
        e.preventDefault();
        setCurrentPageIndex(0);
    });

    // Other actions
    $("#lnkPrint").click(function(e) {
        e.preventDefault();
        $("#mainFrame").focus().prop("contentWindow").print();
    });
    $("#lnkAbout").click(function(e) {
        e.preventDefault();
        $("#aboutDlg").dialog("open");
    });
}

//////////////////////////////////////////////////
// PAGE INITIALIZATION
//////////////////////////////////////////////////

$(document).ready(function() {

    // Create the tree
    $("#treediv").jstree({
        // the `plugins` array allows you to configure the active plugins on this instance
        "plugins": ["themes", "html_data", "ui", "hotkeys"],
        // Single selection
        "ui": { "select_limit": 1 },
        // Open/close node animation duration
        "core": { "animation": 100 }
    })
    // Tree node selection event:
    .bind("select_node.jstree", function(event, data) {
        // `data.rslt.obj` is the jquery extended node that was clicked

        // Open the selected node
        $("#treediv").jstree("open_node", data.rslt.obj, false, false);
        
        // Get the tree node link
        var link = data.rslt.obj.find("a:first");
        var url = link.attr("href");

        // Load it as the current topic
        loadUrlOnFrame(url);

        // Set the URL hash with the title
        changeHash(link);

    })
    // Set initial selection
    .bind("loaded.jstree", function(e, data) {

        // Travese the tree nodes to handle repeated titles and next / previous buttons
        initializeNavigationLinks();

        // Set the initial topic
        setInitialTopic();
    });

    // If a link is pressed into the frame, search and select the new URL into the tree:
    $('#mainFrame').load(function() {
        try {
            // This will throw an exception with chrome on local system file
            var url = getUrlFileName($(this).get(0).contentWindow.document.location.href);
            selectByUrl(url);
        }
        catch (ex) { }
    });

    // Create contents tabs
    $(".ui-layout-west").tabs({
        activate: function(event, ui) {
            // Set the focus on the search fields when we change the current tab:
            var tabId = ui.newPanel.attr('id');
            if (tabId == 'tab-index')
                $("#searchTopic").focus();
            else if (tabId == 'tab-search')
                $("#searchText").focus();
        }
    });

    // Create layouts
    pageLayout = $('body').layout({
        west__size: .25
        , center__maskContents: true // IMPORTANT - enable iframe masking
    });

    // Set index events:
    // Topic index textbox:
    $("#searchTopic")
    .keyup(function(e) {
        if (e.which == 13) {
            // Enter was pressed: Load the selected URL:
            selectByUrl($("#topicsList").val());
        }
        else {
            // Select the first list topic starting with the typed text:
            var currentText = $(this).val().toLowerCase();
            $("#topicsList").val(
                $("#topicsList > option")
                .filter(function(index) {
                    return cleanTitleText($(this).text()).toLowerCase().indexOf(currentText) == 0;
                })
                .first()
                .val()
            );
        }
    });
    // Index listbox:
    $("#topicsList")
    .keyup(function(e) {
        if (e.which == 13)
        // Enter was pressed: Load the selected URL:
            selectByUrl($("#topicsList").val());
    })
    .change(function() {
        // Selected topic changed: Set the topic textbox with the title:
        $("#searchTopic").val($("#topicsList > option:selected").text());
    })
    .click(function() {
        // Load the selected URL:
        selectByUrl($("#topicsList").val());
    });

    // Set text search type:
    // Disable submit if there is nothing to search:
    $("#searchText").keyup(function(e) {
        $("#btnSearch").prop('disabled', $("#searchText").val() == '');
    });
    // Initial check:
    $("#btnSearch").prop('disabled', $("#searchText").val() == '');
    if (fullSearch) {
        // Hide the result list:
        $("#searchResult").remove();
        // Handle the submit event:
        $("#searchform").submit(function(e) {
            e.preventDefault();
            loadUrlOnFrame("search.aspx?q=" + encodeURIComponent($("#searchText").val()));
        });
    }
    else {
        // Handle the search form submit event:
        $("#searchform").submit(function(e) {

            var searchText = $("#searchText").val();
            if (searchText == '') {
                // Nothing to search:
                e.preventDefault();
                return;
            }

            // Clear previous search results:
            var searchResultOptions = $("#searchResult").prop("options");
            searchResultOptions.length = 0;

            // Do the search over the tree: All links with the text, case insensitive
            $("#treediv a")
            .filter(function(index) {
                return $(this).text().toLowerCase().indexOf(searchText) >= 0;
            })
            .each(function() {
                // Add an option to the search listbox with the text and the URL of the link:
                searchResultOptions[searchResultOptions.length] =
                    new Option(cleanTitleText($(this).text()), $(this).attr('href'));
            });

            // Cancel submit            
            e.preventDefault();
        });

        $("#searchResult")
        .click(function() {
            // Load the selected URL:
            selectByUrl($("#searchResult").val());
        })
        .keyup(function(e) {
            if (e.which == 13)
            // Enter was pressed: Load the selected URL:
                selectByUrl($("#searchResult").val());
        });
    }

    // About dialog:
    $("#aboutDlg").dialog({
        modal: true,
        autoOpen: false,
        width: "auto",
        buttons: {
            Ok: function() {
                $(this).dialog("close");
            }
        }
    });

    if ("onhashchange" in window) {
        // Browser supports hash change: Add the event handler
        window.onhashchange = hashChanged;
    }

});

