function submitsta() {
    statuscontent =  $("#status").val();
    statusid =  $("#statusid").val();
    if (statuscontent == "") {
        $("#statuscontrol").addClass("error")
            return false;
    }
}
