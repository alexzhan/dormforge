function submitsta() {
    statuscontent =  $("#status").val();
    statusid =  $("#statusid").val();
    if (statuscontent == "") {
        $("#statuscontrol").addClass("error")
            return false;
    }
    if ($("#oldstatus").text() == statuscontent){
        window.location.href="/status/" + statusid;
        return false;
    }
}
