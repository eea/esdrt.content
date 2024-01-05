document.addEventListener("DOMContentLoaded", function () {
    /* Hide LULUCF Recommendation from MS Expert and MS Coordinator, show for everyone else. */
    var elBody = $("body");

    var needsOneOf = [
        "userrole-manager",
        "userrole-counterpart",
        "userrole-sectorexpert",
        "userrole-qualityexpert",
        "userrole-reviewexpert",
        "userrole-leadreviewer",
        "userrole-reviewerphase1",
        "userrole-reviewerphase2",
        "userrole-auditor",
    ]

    var hideFlag = true;

    for (var i = 0; i < needsOneOf.length; i++) {
        if (elBody.hasClass(needsOneOf[i])) {
            hideFlag = false;
            break;
        }
    }
    if (hideFlag) {
        var cell = $(".observation-details .cell:contains(LULUCF Recommendation)");
        cell.text(cell.text().replace(/[, ]*LULUCF Recommendation/, ""));
    }
});

